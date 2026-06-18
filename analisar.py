# ENTRYPOINT 2: le o banco, calcula custo-beneficio e mostra o ranking + variacoes de preco.
# Rode com:  python analisar.py
#
# Score de custo-beneficio (0 a 100, maior = melhor):
#   - custo mensal  (34%) -> VALOR TOTAL cheio (aluguel+condominio+IPTU); mais barato pontua mais
#   - distancia km  (25%) -> mais perto do shopping pontua mais
#   - nota manual   (15%) -> sua avaliacao de 1 a 5 estrelas (normalizada)
#   - mobiliado     (9%) -> ponto cheio se for mobiliado
#   - vaga          (9%) -> ponto cheio se tiver 1+ vaga de garagem
#   - andar 4o+     (4%) -> ponto cheio se o andar for 4o ou acima
#   - sem pet       (4%) -> ponto cheio se NAO aceita pet
# Os pesos sao uma escolha: priorizamos o bolso um pouco acima da localizacao.
# Cada metrica e normalizada de 0 a 1 no conjunto de imoveis carregado.

import db

PESO_PRECO = 0.34
PESO_DISTANCIA = 0.25
PESO_NOTA = 0.15        # nota manual de 1 a 5 (sua avaliacao)
PESO_MOBILIADO = 0.09
PESO_VAGA = 0.09
PESO_ANDAR = 0.04       # andar 4o ou acima
PESO_SEM_PET = 0.04     # NAO aceita pet

NOTA_DESTAQUE = 4       # nota a partir da qual destaca a linha e o pin

ANDAR_MINIMO_BOM = 4


def _ultimo_preco_por_imovel(conexao):
    # Pega o preco mais recente de cada imovel (ultimo snapshot).
    linhas = conexao.execute(
        """
        SELECT p.imovel_id, p.valor, p.valor_total
        FROM precos p
        JOIN (
            SELECT imovel_id, MAX(coletado_em) AS ultima
            FROM precos GROUP BY imovel_id
        ) u ON u.imovel_id = p.imovel_id AND u.ultima = p.coletado_em
        """
    ).fetchall()
    return {linha["imovel_id"]: (linha["valor"], linha["valor_total"]) for linha in linhas}


def _carregar(conexao, operacao):
    # Carrega imoveis de uma operacao. Os filtros (preco/tipo/area) ja sao aplicados
    # na URL de busca do QuintoAndar (veja config.FILTROS_ALUGUEL), entao aqui nao
    # refiltramos por preco/quartos -- so exigimos area e distancia para o score.
    linhas = conexao.execute(
        """
        SELECT id, titulo, endereco, area_m2, quartos, vagas, distancia_km, url,
               latitude, longitude, nota, mobiliado, andar, aceita_pet
        FROM imoveis
        WHERE operacao = ?
          AND ativo = 1
        """,
        (operacao,),
    ).fetchall()

    precos = _ultimo_preco_por_imovel(conexao)
    imoveis = []
    for linha in linhas:
        preco = precos.get(linha["id"])
        if preco is None:
            continue
        valor, valor_total = preco
        if valor is None:
            continue
        if not linha["area_m2"] or not linha["distancia_km"]:
            continue
        imoveis.append(
            {
                "id": linha["id"],
                "titulo": linha["titulo"],
                "endereco": linha["endereco"],
                "area_m2": linha["area_m2"],
                "quartos": linha["quartos"],
                "vagas": linha["vagas"],
                "distancia_km": linha["distancia_km"],
                "url": linha["url"],
                "latitude": linha["latitude"],
                "longitude": linha["longitude"],
                "nota": linha["nota"],
                "mobiliado": linha["mobiliado"],
                "andar": linha["andar"],
                "aceita_pet": linha["aceita_pet"],
                "valor": valor,
                "valor_total": valor_total,
                # custo = valor TOTAL cheio (aluguel + condominio + IPTU). E o que baseia
                # o score: ranqueia pelo que se paga no mes, nao pelo custo por m2.
                # Se o site nao informou o total, usa o aluguel base como aproximacao.
                "custo": (valor_total or valor),
                # preco_m2 fica so para exibir na coluna "R$/m2" do relatorio.
                "preco_m2": (valor_total or valor) / linha["area_m2"],
            }
        )
    return imoveis


def _normalizar_invertido(valores):
    # Retorna funcao que mapeia um valor para 0..1, onde MENOR valor -> 1 (melhor).
    if not valores:
        return lambda v: 0.0
    menor, maior = min(valores), max(valores)
    if maior == menor:
        return lambda v: 1.0
    return lambda v: (maior - v) / (maior - menor)


def _calcular_scores(imoveis):
    norm_preco = _normalizar_invertido([i["custo"] for i in imoveis])
    norm_dist = _normalizar_invertido([i["distancia_km"] for i in imoveis])
    for imovel in imoveis:
        # bonus: 1 ponto cheio se atende, 0 se nao atende/desconhecido
        bonus_mobiliado = 1 if imovel.get("mobiliado") == 1 else 0
        bonus_vaga = 1 if (imovel.get("vagas") or 0) >= 1 else 0
        andar = imovel.get("andar")
        bonus_andar = 1 if (andar is not None and andar >= ANDAR_MINIMO_BOM) else 0
        bonus_sem_pet = 1 if imovel.get("aceita_pet") == 0 else 0  # NAO aceita pet e positivo
        # nota manual (1..5) normalizada para 0..1; sem nota (0) nao soma nada.
        # nota -1 = "visto" (apenas marcacao, sem estrela) tambem nao soma -> trata como 0.
        bonus_nota = max(0, imovel.get("nota") or 0) / 5
        score = (
            PESO_PRECO * norm_preco(imovel["custo"])
            + PESO_DISTANCIA * norm_dist(imovel["distancia_km"])
            + PESO_NOTA * bonus_nota
            + PESO_MOBILIADO * bonus_mobiliado
            + PESO_VAGA * bonus_vaga
            + PESO_ANDAR * bonus_andar
            + PESO_SEM_PET * bonus_sem_pet
        )
        imovel["score"] = round(score * 100, 1)
    # Ordena pelo score (a nota ja esta embutida nele, como voce pediu - sem viés de
    # jogar nota alta forcadamente para o topo; ela influencia via peso).
    imoveis.sort(key=lambda i: i["score"], reverse=True)
    return imoveis


def _variacao(conexao, imovel_id):
    # Compara o 1o e o ultimo snapshot do imovel. Retorna simbolo + diferenca.
    linhas = conexao.execute(
        "SELECT valor, coletado_em FROM precos WHERE imovel_id = ? ORDER BY coletado_em",
        (imovel_id,),
    ).fetchall()
    if len(linhas) < 2:
        return "novo"
    primeiro, ultimo = linhas[0]["valor"], linhas[-1]["valor"]
    if ultimo > primeiro:
        return f"subiu R$ {ultimo - primeiro:,.0f}"
    if ultimo < primeiro:
        return f"caiu R$ {primeiro - ultimo:,.0f}"
    return "estavel"


def _imprimir(conexao, titulo, imoveis):
    print(f"\n{'=' * 70}\n{titulo} ({len(imoveis)} imoveis)\n{'=' * 70}")
    if not imoveis:
        print("  Nenhum imovel encontrado com os filtros atuais.")
        return
    for posicao, imovel in enumerate(imoveis, start=1):
        variacao = _variacao(conexao, imovel["id"])
        print(
            f"\n#{posicao}  score {imovel['score']}  |  R$ {imovel['valor']:,.0f}"
            f"  ({imovel['preco_m2']:.0f}/m2)  |  {imovel['distancia_km']} km do shopping  |  {variacao}"
        )
        print(f"     {imovel['quartos']} quarto(s), {imovel['area_m2']:.0f} m2, {imovel.get('vagas') or 0} vaga(s)")
        if imovel["endereco"]:
            print(f"     {imovel['endereco']}")
        url_limpa = imovel["url"].split("?")[0] if imovel["url"] else ""
        print(f"     {url_limpa}")


def main():
    conexao = db.conectar()
    db.criar_tabelas(conexao)

    aluguel = _calcular_scores(_carregar(conexao, "aluguel"))

    _imprimir(conexao, "ALUGUEL  (filtros aplicados na busca do site)", aluguel)

    conexao.close()


if __name__ == "__main__":
    main()
