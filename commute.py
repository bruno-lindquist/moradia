# ENTRYPOINT 4: calcula o tempo a pe e de bicicleta de cada imovel COM NOTA ate a
# referencia (Shopping Morumbi) e grava no banco (colunas walk_seconds/bike_seconds).
# Rode com:  python commute.py
#
# Usa o OSRM publico (roteamento sobre o OpenStreetMap), um perfil para cada modo.
# Processa do maior score para o menor e deduplica por localizacao: imoveis no mesmo
# ponto (mesmo predio) geram UMA so consulta, replicada para todos do grupo.

import json
import time
import urllib.request
import urllib.error

import config
import database
import ranking

# OSRM publico. Cada perfil (walking/cycling) tem seu proprio host de demonstracao.
OSRM_HOSTS = {
    "walking": "https://routing.openstreetmap.de/routed-foot",
    "cycling": "https://routing.openstreetmap.de/routed-bike",
}
REQUEST_PAUSE_SECONDS = 1.0  # boa cidadania com o servidor publico


def _route_seconds(profile, origin_lat, origin_lon):
    # Consulta o OSRM e retorna a duracao (segundos) da rota origem -> referencia.
    # Retorna None se a rota nao for encontrada ou a requisicao falhar.
    host = OSRM_HOSTS[profile]
    # OSRM espera lon,lat (nao lat,lon) e a ordem origem;destino.
    coordinates = f"{origin_lon},{origin_lat};{config.REFERENCE_LON},{config.REFERENCE_LAT}"
    url = f"{host}/route/v1/{profile}/{coordinates}?overview=false"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"      ! falha no OSRM ({profile}): {error}")
        return None
    routes = data.get("routes") or []
    if not routes:
        return None
    return round(routes[0]["duration"])


def route_times(latitude, longitude):
    # Tempo a pe e de bike (segundos) ate a referencia, com pausa entre as consultas
    # (boa cidadania com o OSRM publico). Retorna (walk_seconds, bike_seconds);
    # cada um pode ser None se a rota nao for encontrada.
    walk = _route_seconds("walking", latitude, longitude)
    time.sleep(REQUEST_PAUSE_SECONDS)
    bike = _route_seconds("cycling", latitude, longitude)
    time.sleep(REQUEST_PAUSE_SECONDS)
    return walk, bike


def _properties_to_process(connection):
    # Imoveis com nota (>=1), ordenados por score desc, que ainda nao tem os dois tempos.
    # compute_scores ja ordena por score decrescente.
    properties = ranking.compute_scores(
        ranking.load_properties(connection, "aluguel", include_inactive=True)
    )
    pending = []
    for property in properties:
        if (property.get("rating") or 0) < 1:
            continue
        if property["latitude"] is None or property["longitude"] is None:
            continue
        pending.append(property)
    return pending


def _existing_times(connection, property_id):
    row = connection.execute(
        "SELECT walk_seconds, bike_seconds FROM imoveis WHERE id = ?", (property_id,)
    ).fetchone()
    return (row["walk_seconds"], row["bike_seconds"])


def main():
    connection = database.connect()

    properties = _properties_to_process(connection)
    print(f"{len(properties)} imovel(is) com nota para processar (maior score primeiro).")

    # Agrupa por localizacao arredondada: mesma coordenada = uma consulta so.
    cache = {}  # (lat, lon) -> (walk_seconds, bike_seconds)
    api_calls = 0

    for property in properties:
        walk, bike = _existing_times(connection, property["id"])
        if walk is not None and bike is not None:
            continue  # ja calculado: nao regasta a API

        location = (round(property["latitude"], 6), round(property["longitude"], 6))
        if location not in cache:
            print(f"  score {property['score']:5} | {property['address'] or property['id']}")
            walk_seconds, bike_seconds = route_times(*location)
            api_calls += 2
            cache[location] = (walk_seconds, bike_seconds)
            if walk_seconds is not None:
                print(f"      a pe {walk_seconds // 60} min | bike {(bike_seconds or 0) // 60} min")
        else:
            walk_seconds, bike_seconds = cache[location]
            print(f"  score {property['score']:5} | mesma localizacao -> reaproveita (sem nova consulta)")

        connection.execute(
            "UPDATE imoveis SET walk_seconds = ?, bike_seconds = ? WHERE id = ?",
            (walk_seconds, bike_seconds, property["id"]),
        )
        connection.commit()  # grava a cada imovel: se falhar no meio, nao perde o feito

    connection.close()
    print(f"Pronto: {api_calls} consultas ao OSRM, "
          f"{len(cache)} localizacao(es) unica(s). Tempos gravados em {config.DB_PATH}.")


if __name__ == "__main__":
    main()
