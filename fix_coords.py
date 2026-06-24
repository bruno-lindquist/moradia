# ENTRYPOINT 5 (correcao pontual): reabre a pagina de cada imovel COM NOTA, le a
# coordenada exata fornecida pelo QuintoAndar (mais precisa que geocodificar pelo nome
# da rua) e atualiza latitude/longitude, distancia e os tempos a pe/bike no banco.
# Rode com:  python fix_coords.py
#
# Por que existe: enderecos sem numero (a maioria, pois o site nao expoe o numero)
# geocodificavam para um ponto arbitrario da rua -- erro de ate ~1,5 km em ruas longas.

import commute
import config
import database
import geo
import ranking
import scraper


def _rated_properties(connection):
    # Imoveis com nota (>=1), maior score primeiro, que tem URL para reabrir.
    properties = ranking.compute_scores(
        ranking.load_properties(connection, "aluguel", include_inactive=True)
    )
    return [p for p in properties if (p.get("rating") or 0) >= 1 and p.get("url")]


def fix_one(connection, page, property):
    # Reabre a pagina, le a coordenada do site e, se mudou, atualiza tudo no banco.
    # Retorna "ok", "sem-coord" ou "inalterado".
    scraper._scrape_details(page, property)  # popula property["latitude"]/["longitude"] do site
    latitude = property.get("latitude")
    longitude = property.get("longitude")
    if latitude is None:
        return "sem-coord"

    old = connection.execute(
        "SELECT latitude, longitude FROM imoveis WHERE id = ?", (property["id"],)
    ).fetchone()
    if old["latitude"] == latitude and old["longitude"] == longitude:
        return "inalterado"

    distance_km = geo.distance_to_reference(latitude, longitude)
    walk_seconds, bike_seconds = commute.route_times(latitude, longitude)
    connection.execute(
        """
        UPDATE imoveis
        SET latitude = ?, longitude = ?, distancia_km = ?, walk_seconds = ?, bike_seconds = ?
        WHERE id = ?
        """,
        (latitude, longitude, distance_km, walk_seconds, bike_seconds, property["id"]),
    )
    connection.commit()  # grava a cada imovel: se falhar no meio, nao perde o feito
    print(f"      coord {old['latitude']:.5f},{old['longitude']:.5f} -> {latitude:.5f},{longitude:.5f}"
          f" | {distance_km} km | a pe {(walk_seconds or 0)//60} min | bike {(bike_seconds or 0)//60} min")
    return "ok"


def main(limit=None):
    connection = database.connect()
    properties = _rated_properties(connection)
    if limit:
        properties = properties[:limit]
    print(f"{len(properties)} imovel(is) com nota para corrigir (maior score primeiro).")

    counts = {"ok": 0, "sem-coord": 0, "inalterado": 0}
    with scraper.open_browser() as page:
        for property in properties:
            print(f"  score {property['score']:5} | {property['id']} | {property['address']}")
            result = fix_one(connection, page, property)
            counts[result] += 1

    connection.close()
    print(f"Pronto: {counts['ok']} corrigidos, {counts['inalterado']} ja certos, "
          f"{counts['sem-coord']} sem coordenada no site. Banco: {config.DB_PATH}.")


if __name__ == "__main__":
    import sys
    # Opcional: 'python fix_coords.py 1' processa so o 1o (maior score) -- para validar.
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit)
