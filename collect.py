# ENTRYPOINT 1: coleta imoveis do QuintoAndar e grava um snapshot no banco.
# Rode com:  python collect.py
#
# Fluxo: scraper -> geocodifica endereco -> calcula distancia -> grava no SQLite.

import config
import database
import geo
import scraper


def _save_properties(connection, properties, now):
    # Geocodifica e grava os imoveis um a um, COM COMMIT A CADA UM: o scraper entrega
    # cada imovel assim que o coleta, e aqui ele ja vai para o disco. Se a coleta cair
    # no meio (internet, Ctrl+C, bloqueio do site), tudo que veio antes esta gravado.
    # 'properties' e um gerador: iterar sobre ele e o que dispara a coleta seguinte.
    # Retorna (saved, new_count).
    saved = new_count = 0
    for property in properties:
        if property.get("price") is None:  # sem valor nao da para analisar
            continue
        latitude, longitude = geo.geocode(connection, property.get("address"))
        property["latitude"] = latitude
        property["longitude"] = longitude
        property["distance_km"] = geo.distance_to_reference(latitude, longitude)

        if not database.property_exists(connection, property["id"]):
            new_count += 1
        database.save_property(connection, property, now)
        database.save_price(connection, property["id"], property["price"], property.get("total_price"), now)
        connection.commit()  # grava este imovel antes de partir para o proximo
        saved += 1
    return saved, new_count


def main():
    connection = database.connect()
    now = database.now_iso()

    neighborhoods = database.active_neighborhoods(connection)
    print(f"Coletando imoveis de aluguel no QuintoAndar em {len(neighborhoods)} bairro(s)...")

    total_saved = total_new = 0
    # Um navegador para todos os bairros; a gravacao acontece imovel a imovel dentro de
    # _save_properties, entao nao ha lote pendente para se perder se algo falhar no meio.
    with scraper.open_browser() as page:
        for slug, name in neighborhoods:
            # Relido a cada bairro: como cada imovel ja foi commitado, o banco e a fonte
            # atualizada de quem foi detalhado, inclusive nesta mesma run. Evita reabrir a
            # pagina de um imovel que aparece em dois bairros vizinhos.
            already_detailed = database.detailed_ids(connection)
            properties = scraper.scrape_neighborhood(page, slug, name, already_detailed)
            saved, new_count = _save_properties(connection, properties, now)
            total_saved += saved
            total_new += new_count
            print(f"    {name}: {saved} imoveis salvos ({new_count} novos). [total: {total_saved}]")

    connection.close()

    print(f"Pronto: {total_saved} imoveis com preco gravados ({total_new} novos).")
    print(f"Snapshot de {now} salvo em {config.DB_PATH}.")
    print("Rode 'python ranking.py' para ver o ranking de custo-beneficio.")


if __name__ == "__main__":
    main()
