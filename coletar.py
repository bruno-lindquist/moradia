# ENTRYPOINT 1: coleta imoveis do QuintoAndar e grava um snapshot no banco.
# Rode com:  python coletar.py
#
# Fluxo: scraper -> geocodifica endereco -> calcula distancia -> grava no SQLite.

import config
import db
import geo
import scraper


def _salvar_imoveis(conexao, imoveis, agora):
    # Geocodifica e grava uma lista de imoveis. Retorna (salvos, novos).
    salvos = novos = 0
    for imovel in imoveis:
        if imovel.get("valor") is None:  # sem valor nao da para analisar
            continue
        latitude, longitude = geo.geocodificar(conexao, imovel.get("endereco"))
        imovel["latitude"] = latitude
        imovel["longitude"] = longitude
        imovel["distancia_km"] = geo.distancia_ate_shopping(latitude, longitude)

        if not db.imovel_ja_existe(conexao, imovel["id"]):
            novos += 1
        db.salvar_imovel(conexao, imovel, agora)
        db.salvar_preco(conexao, imovel["id"], imovel["valor"], imovel.get("valor_total"), agora)
        salvos += 1
    return salvos, novos


def main():
    conexao = db.conectar()
    db.criar_tabelas(conexao)
    agora = db.agora_iso()

    bairros = db.bairros_ativos(conexao)
    ja_detalhados = db.ids_detalhados(conexao)  # nao reabrir paginas ja capturadas
    print(f"Coletando imoveis de aluguel no QuintoAndar em {len(bairros)} bairro(s)...")
    print(f"  {len(ja_detalhados)} imoveis ja detalhados serao pulados.")

    total_salvos = total_novos = 0
    # Um navegador para todos os bairros, mas salvando o banco a CADA bairro:
    # se algo falhar no meio, o que ja foi coletado nao se perde.
    with scraper.abrir_navegador() as pagina:
        for slug, nome in bairros:
            imoveis = scraper.coletar_bairro(pagina, slug, nome, ja_detalhados)
            salvos, novos = _salvar_imoveis(conexao, imoveis, agora)
            conexao.commit()  # grava este bairro antes de ir para o proximo
            # marca os detalhados nesta run para nao reabri-los se aparecerem em outro bairro
            ja_detalhados.update(im["id"] for im in imoveis if im.get("detalhado"))
            total_salvos += salvos
            total_novos += novos
            print(f"    {nome}: {salvos} imoveis salvos ({novos} novos). [total: {total_salvos}]")

    conexao.close()

    print(f"Pronto: {total_salvos} imoveis com preco gravados ({total_novos} novos).")
    print(f"Snapshot de {agora} salvo em {config.DB_PATH}.")
    print("Rode 'python analisar.py' para ver o ranking de custo-beneficio.")


if __name__ == "__main__":
    main()
