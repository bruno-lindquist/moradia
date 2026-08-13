# ENTRYPOINT 5 (correcao pontual): reabre a pagina de CADA imovel (maior score
# primeiro) e:
#  - se o anuncio saiu do ar, marca o imovel como inativo (ativo = 0) e para por aqui;
#  - se continua no ar, grava um snapshot do valor atual e atualiza a coordenada exata
#    fornecida pelo QuintoAndar (mais precisa que geocodificar pelo nome da rua),
#    a distancia e o tempo a pe ate a estacao no banco.
# Rode com:  python fix_coords.py
#
# Por que existe: enderecos sem numero (a maioria, pois o site nao expoe o numero)
# geocodificavam para um ponto arbitrario da rua -- erro de ate ~1,5 km em ruas longas.

import random
import time

import commute
import config
import database
import geo
import ranking
import scraper

# Pausa extra entre imoveis (anti-bloqueio), alem das pausas internas do scraper.
PAUSE_MIN_SECONDS = 1
PAUSE_MAX_SECONDS = 3


def _rated_properties(connection):
    # Apenas imoveis com nota (>=1) e URL para reabrir, maior score primeiro.
    # Inclui inativos (include_inactive=True) para detectar os que voltaram ao ar.
    properties = ranking.compute_scores(
        ranking.load_properties(connection, "aluguel", include_inactive=True)
    )
    return [
        property for property in properties
        if property.get("url") and (property.get("rating") or 0) >= 1
    ]


def fix_one(connection, page, property):
    # Reabre a pagina. Se o anuncio saiu do ar, marca como inativo. Senao, grava um
    # snapshot do valor atual e, se a coordenada mudou, atualiza coordenada/distancia/tempos.
    # Retorna "inativo", "ok", "sem-coord" ou "inalterado".
    scraper._scrape_details(page, property)  # popula coord, price e total_price do site
    if scraper.is_unavailable(page):
        database.deactivate_property(connection, property["id"])
        return "inativo"

    # Snapshot do valor (mesmo que a coordenada nao mude, o preco pode ter mudado).
    # save_price so grava se o valor mudou; comita apenas quando houve gravacao.
    if property.get("price") is not None:
        if database.save_price(
            connection, property["id"], property["price"],
            property.get("total_price"), database.now_iso(),
        ):
            connection.commit()

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
    station_seconds, station_name = commute.station_time(latitude, longitude)
    connection.execute(
        """
        UPDATE imoveis
        SET latitude = ?, longitude = ?, distancia_km = ?,
            estacao_segundos = ?, estacao_nome = ?
        WHERE id = ?
        """,
        (latitude, longitude, distance_km, station_seconds, station_name, property["id"]),
    )
    connection.commit()  # grava a cada imovel: se falhar no meio, nao perde o feito
    print(f"      coord {old['latitude']:.5f},{old['longitude']:.5f} -> {latitude:.5f},{longitude:.5f}"
          f" | {distance_km} km | estacao {(station_seconds or 0)//60} min ({station_name})")
    return "ok"


def main(limit=None):
    connection = database.connect()
    properties = _rated_properties(connection)
    if limit:
        properties = properties[:limit]
    print(f"{len(properties)} imovel(is) com nota para verificar (maior score primeiro).")

    counts = {"ok": 0, "sem-coord": 0, "inalterado": 0, "inativo": 0}
    with scraper.open_browser() as page:
        for index, property in enumerate(properties):
            print(f"  score {property['score']:5} | {property['id']} | {property['address']}")
            result = fix_one(connection, page, property)
            if result == "inativo":
                print("      saiu do ar -> marcado como inativo")
            counts[result] += 1
            if index < len(properties) - 1:  # nao espera depois do ultimo
                time.sleep(random.uniform(PAUSE_MIN_SECONDS, PAUSE_MAX_SECONDS))

    connection.close()
    print(f"Pronto: {counts['ok']} corrigidos, {counts['inalterado']} ja certos, "
          f"{counts['sem-coord']} sem coordenada no site, {counts['inativo']} inativos. "
          f"Banco: {config.DB_PATH}.")


if __name__ == "__main__":
    import sys
    # Opcional: 'python fix_coords.py 1' processa so o 1o (maior score) -- para validar.
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit)
