# Geocodificacao (endereco -> coordenadas) e calculo de distancia ate o shopping.
# Usa Nominatim (OpenStreetMap): gratuito e sem chave de API.

import re
import time

from geopy.geocoders import Nominatim
from geopy.distance import distance as geopy_distance

import config

# user_agent e obrigatorio pelo Nominatim; identifica nossa aplicacao
_geolocator = Nominatim(user_agent="moradia-mvp-morumbi")

_REFERENCE = (config.REFERENCE_LAT, config.REFERENCE_LON)


def geocode(connection, address):
    # Retorna (latitude, longitude) ou (None, None) se nao encontrar.
    # Usa cache no banco para nao repetir a mesma consulta ao Nominatim.
    if not address:
        return None, None

    cached = connection.execute(
        "SELECT latitude, longitude FROM geocache WHERE endereco = ?", (address,)
    ).fetchone()
    if cached is not None:
        return cached["latitude"], cached["longitude"]

    # Deixa so o logradouro: corta o bairro (apos a 1a virgula) e numeros/complemento.
    # O Nominatim acha melhor "Rua X" do que "Rua X, Bairro Y" (a forma com bairro falha).
    street = address.split(",")[0]
    street = re.sub(r"\d.*$", "", street).strip(" ,-")
    location, failed = _try_geocode(f"{street}, Sao Paulo, SP, Brasil")

    # Se a CHAMADA falhou (rede/rate-limit), NAO cacheia: assim tentamos de novo depois.
    # So cacheia quando o Nominatim respondeu de fato (achou, ou disse que nao existe).
    if failed:
        return None, None

    latitude = location.latitude if location else None
    longitude = location.longitude if location else None

    connection.execute(
        "INSERT OR REPLACE INTO geocache (endereco, latitude, longitude) VALUES (?, ?, ?)",
        (address, latitude, longitude),
    )
    return latitude, longitude


def _try_geocode(query):
    # Retorna (location, failed). failed=True significa erro na chamada (nao "nao encontrado").
    failed = False
    try:
        location = _geolocator.geocode(query)
    except Exception:
        location = None
        failed = True
    # Nominatim pede no maximo 1 req/seg, mas pune rajadas longas: usamos 2s para
    # nao sermos limitados (respostas vazias) durante reprocessamentos grandes.
    time.sleep(2.0)
    return location, failed


def distance_to_reference(latitude, longitude):
    # Distancia em km em linha reta (Haversine) entre o imovel e o shopping.
    if latitude is None or longitude is None:
        return None
    return round(geopy_distance((latitude, longitude), _REFERENCE).km, 2)
