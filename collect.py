# ENTRYPOINT 1: coleta imoveis do QuintoAndar e grava um snapshot no banco.
# Rode com:  python collect.py
#
# Fluxo: scraper -> geocodifica endereco -> calcula distancia -> grava no SQLite.

import config
import database
import geo
import scraper


def _save_properties(connection, properties, now):
    # Geocodifica e grava uma lista de imoveis. Retorna (saved, new_count).
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
        saved += 1
    return saved, new_count


def main():
    connection = database.connect()
    database.create_tables(connection)
    now = database.now_iso()

    neighborhoods = database.active_neighborhoods(connection)
    already_detailed = database.detailed_ids(connection)  # nao reabrir paginas ja capturadas
    print(f"Coletando imoveis de aluguel no QuintoAndar em {len(neighborhoods)} bairro(s)...")
    print(f"  {len(already_detailed)} imoveis ja detalhados serao pulados.")

    total_saved = total_new = 0
    # Um navegador para todos os bairros, mas salvando o banco a CADA bairro:
    # se algo falhar no meio, o que ja foi coletado nao se perde.
    with scraper.open_browser() as page:
        for slug, name in neighborhoods:
            properties = scraper.scrape_neighborhood(page, slug, name, already_detailed)
            saved, new_count = _save_properties(connection, properties, now)
            connection.commit()  # grava este bairro antes de ir para o proximo
            # marca os detalhados nesta run para nao reabri-los se aparecerem em outro bairro
            already_detailed.update(p["id"] for p in properties if p.get("detailed"))
            total_saved += saved
            total_new += new_count
            print(f"    {name}: {saved} imoveis salvos ({new_count} novos). [total: {total_saved}]")

    connection.close()

    print(f"Pronto: {total_saved} imoveis com preco gravados ({total_new} novos).")
    print(f"Snapshot de {now} salvo em {config.DB_PATH}.")
    print("Rode 'python ranking.py' para ver o ranking de custo-beneficio.")


if __name__ == "__main__":
    main()
