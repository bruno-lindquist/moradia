# Geocodificacao (endereco -> coordenadas) e calculo de distancia ate o shopping.
# Usa Nominatim (OpenStreetMap): gratuito e sem chave de API.

import re
import time

from geopy.geocoders import Nominatim
from geopy.distance import distance as geopy_distance

import config

# user_agent e obrigatorio pelo Nominatim; identifica nossa aplicacao
_geolocalizador = Nominatim(user_agent="moradia-mvp-morumbi")

_SHOPPING = (config.SHOPPING_LAT, config.SHOPPING_LON)


def geocodificar(conexao, endereco):
    # Retorna (latitude, longitude) ou (None, None) se nao encontrar.
    # Usa cache no banco para nao repetir a mesma consulta ao Nominatim.
    if not endereco:
        return None, None

    cacheado = conexao.execute(
        "SELECT latitude, longitude FROM geocache WHERE endereco = ?", (endereco,)
    ).fetchone()
    if cacheado is not None:
        return cacheado["latitude"], cacheado["longitude"]

    # Deixa so o logradouro: corta o bairro (apos a 1a virgula) e numeros/complemento.
    # O Nominatim acha melhor "Rua X" do que "Rua X, Bairro Y" (a forma com bairro falha).
    rua = endereco.split(",")[0]
    rua = re.sub(r"\d.*$", "", rua).strip(" ,-")
    local, falhou = _tentar_geocodificar(f"{rua}, Sao Paulo, SP, Brasil")

    # Se a CHAMADA falhou (rede/rate-limit), NAO cacheia: assim tentamos de novo depois.
    # So cacheia quando o Nominatim respondeu de fato (achou, ou disse que nao existe).
    if falhou:
        return None, None

    latitude = local.latitude if local else None
    longitude = local.longitude if local else None

    conexao.execute(
        "INSERT OR REPLACE INTO geocache (endereco, latitude, longitude) VALUES (?, ?, ?)",
        (endereco, latitude, longitude),
    )
    return latitude, longitude


def _tentar_geocodificar(consulta):
    # Retorna (local, falhou). falhou=True significa erro na chamada (nao "nao encontrado").
    falhou = False
    try:
        local = _geolocalizador.geocode(consulta)
    except Exception:
        local = None
        falhou = True
    # Nominatim pede no maximo 1 req/seg, mas pune rajadas longas: usamos 2s para
    # nao sermos limitados (respostas vazias) durante reprocessamentos grandes.
    time.sleep(2.0)
    return local, falhou


def distancia_ate_shopping(latitude, longitude):
    # Distancia em km em linha reta (Haversine) entre o imovel e o shopping.
    if latitude is None or longitude is None:
        return None
    return round(geopy_distance((latitude, longitude), _SHOPPING).km, 2)
