# ENTRYPOINT 4: calcula o tempo a pe de cada imovel ate a estacao de metro/trem mais
# proxima e grava no banco (colunas estacao_segundos/estacao_nome).
# Rode com:  python commute.py
#
# Usa o OSRM publico (roteamento a pe sobre o OpenStreetMap).
# Processa do maior score para o menor e deduplica por localizacao: imoveis no mesmo
# ponto (mesmo predio) geram UMA so consulta, replicada para todos do grupo.

import json
import time
import urllib.request
import urllib.error

from geopy.distance import distance as geopy_distance

import config
import database
import ranking

# OSRM publico, perfil a pe (host de demonstracao do OpenStreetMap).
OSRM_WALK_HOST = "https://routing.openstreetmap.de/routed-foot"
REQUEST_PAUSE_SECONDS = 1.0  # boa cidadania com o servidor publico

# Estacoes de metro/CPTM (mesmo arquivo que o mapa usa). Carregado uma vez no modulo.
TRANSIT_PATH = "transit.json"


def _load_stations():
    # Le as estacoes do transit.json: lista de (nome, lat, lon). Inclui metro E trem
    # (CPTM), pois queremos a estacao de transporte mais proxima de qualquer tipo.
    with open(TRANSIT_PATH, encoding="utf-8") as file:
        transit = json.load(file)
    return [(s["name"], s["lat"], s["lon"]) for s in transit["stations"]]


STATIONS = _load_stations()


def nearest_station(latitude, longitude):
    # Estacao mais proxima em LINHA RETA (Haversine). So escolhe qual estacao; o tempo
    # a pe real (rota) e calculado depois, so para essa uma. Retorna (nome, lat, lon).
    return min(
        STATIONS,
        key=lambda station: geopy_distance((latitude, longitude), (station[1], station[2])).km,
    )


def _walk_seconds(origin_lat, origin_lon, dest_lat, dest_lon):
    # Consulta o OSRM e retorna a duracao (segundos) da caminhada origem -> destino.
    # Retorna None se a rota nao for encontrada ou a requisicao falhar.
    # OSRM espera lon,lat (nao lat,lon) e a ordem origem;destino.
    coordinates = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    url = f"{OSRM_WALK_HOST}/route/v1/walking/{coordinates}?overview=false"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"      ! falha no OSRM: {error}")
        return None
    routes = data.get("routes") or []
    if not routes:
        return None
    return round(routes[0]["duration"])


def station_time(latitude, longitude):
    # Tempo (segundos) a pe ate a estacao de metro/trem mais proxima, e o nome dela.
    # A estacao e escolhida em linha reta; so para ela consultamos a rota real.
    # A pausa e boa cidadania com o OSRM publico. O tempo pode ser None se a rota falhar.
    station_name, station_lat, station_lon = nearest_station(latitude, longitude)
    seconds = _walk_seconds(latitude, longitude, station_lat, station_lon)
    time.sleep(REQUEST_PAUSE_SECONDS)
    return seconds, station_name


def _properties_to_process(connection):
    # Todos os imoveis com coordenada, do maior score para o menor
    # (compute_scores ja ordena por score decrescente).
    properties = ranking.compute_scores(
        ranking.load_properties(connection, "aluguel", include_inactive=True)
    )
    return [
        property
        for property in properties
        if property["latitude"] is not None and property["longitude"] is not None
    ]


def _existing_station_seconds(connection, property_id):
    row = connection.execute(
        "SELECT estacao_segundos FROM imoveis WHERE id = ?", (property_id,)
    ).fetchone()
    return row["estacao_segundos"]


def main():
    connection = database.connect()

    properties = _properties_to_process(connection)
    print(f"{len(properties)} imovel(is) para processar (maior score primeiro).")

    # Agrupa por localizacao arredondada: mesma coordenada = uma consulta so.
    cache = {}  # (lat, lon) -> (station_seconds, station_name)
    api_calls = 0

    for property in properties:
        if _existing_station_seconds(connection, property["id"]) is not None:
            continue  # ja calculado: nao regasta a API

        location = (round(property["latitude"], 6), round(property["longitude"], 6))
        if location not in cache:
            print(f"  score {property['score']:5} | {property['address'] or property['id']}")
            cache[location] = station_time(*location)
            api_calls += 1
            seconds, name = cache[location]
            if seconds is not None:
                print(f"      estacao {seconds // 60} min ({name})")
        else:
            print(f"  score {property['score']:5} | mesma localizacao -> reaproveita (sem nova consulta)")
        station_seconds, station_name = cache[location]

        connection.execute(
            "UPDATE imoveis SET estacao_segundos = ?, estacao_nome = ? WHERE id = ?",
            (station_seconds, station_name, property["id"]),
        )
        connection.commit()  # grava a cada imovel: se falhar no meio, nao perde o feito

    connection.close()
    print(f"Pronto: {api_calls} consultas ao OSRM, "
          f"{len(cache)} localizacao(es) unica(s). Tempos gravados em {config.DB_PATH}.")


if __name__ == "__main__":
    main()
