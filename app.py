# ENTRYPOINT 3: servidor web local que serve o relatorio interativo (mapa + tabela)
# COM os botoes de dar nota e desativar anuncios.
# Rode com:  python app.py   (depois abra http://localhost:8765 no navegador)
#
# Por que existe: o relatorio precisa gravar no banco (nota e "desativar"), o que um
# arquivo HTML estatico nao consegue. Este servidor pequeno (Flask) faz essa ponte.
# O HTML/CSS/JS fica no arquivo report.html (renderizado via Jinja2 com os dados).

from functools import wraps

from flask import Flask, abort, render_template, send_from_directory

import amenities
import config
import database
import ranking

# template_folder="." faz o Flask achar report.html na raiz do projeto (sem pasta templates/).
app = Flask(__name__, template_folder=".")


def with_property(handler):
    # Decorator para as rotas que agem sobre um imovel: abre a conexao, confere que o
    # property_id existe (senao 404), passa a connection ao handler e fecha no fim.
    # Remove o preambulo repetido (connect/exists/abort/close) das 4 rotas.
    @wraps(handler)
    def wrapper(property_id, *args, **kwargs):
        connection = database.connect()
        try:
            exists = connection.execute(
                "SELECT 1 FROM imoveis WHERE id = ?", (property_id,)
            ).fetchone()
            if not exists:
                abort(404)
            return handler(connection, property_id, *args, **kwargs)
        finally:
            connection.close()

    return wrapper


def _to_minutes(seconds):
    # Converte segundos -> minutos arredondados; None se ainda nao calculado.
    if seconds is None:
        return None
    return round(seconds / 60)


def _rental_dict(connection, property):
    # Monta o dict de um imovel para o front. As chaves de amenidade (pool, gym, ...) sao
    # derivadas da fonte unica (amenities.py); os demais campos sao explicitos.
    rental = {
        "id": property["id"],
        "rating": property.get("rating", 0),
        "score": property["score"],
        "price": property["price"],
        "total_price": property.get("total_price"),
        "price_per_m2": round(property["price_per_m2"]),
        "distance_km": property["distance_km"],
        "bedrooms": property["bedrooms"],
        "area_m2": round(property["area_m2"]),
        "furnished": property.get("furnished"),
        "floor": property.get("floor"),
        "accepts_pet": property.get("accepts_pet"),
        "active": property.get("active", 1),
        "address": property["address"] or "",
        "url": config.clean_url(property["url"]),
        "lat": property["latitude"],
        "lon": property["longitude"],
        # tempo a pe ate a estacao de metro/trem mais proxima, e o nome dela
        # (None = ainda nao calculado por commute.py)
        "station_min": _to_minutes(property.get("station_seconds")),
        "station_name": property.get("station_name"),
        "change": ranking.price_change(connection, property["id"]),
    }
    amenities.copy_keys(property, rental)
    return rental


def build_report_data(connection):
    # Monta a lista de imoveis (com score e variacao) pronta para o template.
    # Ja vem ordenada por score. Elimina os ATIVOS fora da faixa de preco/distancia
    # (ranking.within_range); mantem os ocultos para o filtro "so ocultos" do relatorio.
    # As chaves abaixo (em ingles) sao lidas diretamente pelo JS de report.html.
    # include_inactive=True traz tambem os ocultos.
    properties = ranking.compute_scores(
        ranking.load_properties(connection, "aluguel", include_inactive=True)
    )
    properties = [
        property
        for property in properties
        if property.get("active") == 0 or ranking.within_range(property)
    ]
    rentals = [_rental_dict(connection, property) for property in properties]
    return {
        "rentals": rentals,
        "reference": {
            "name": config.REFERENCE_NAME,
            "lat": config.REFERENCE_LAT,
            "lon": config.REFERENCE_LON,
        },
    }


@app.route("/")
def index():
    connection = database.connect()
    data = build_report_data(connection)
    connection.close()
    # So as amenidades exibidas (front=True), com os campos que o JS usa para montar
    # as colunas/popup. Mantem a ordem da fonte unica (amenities.py).
    front_amenities = [
        {"key": amenity["key"], "icon": amenity["icon"], "label": amenity["label"]}
        for amenity in amenities.AMENITIES
        if amenity["front"]
    ]
    return render_template(
        "report.html",
        data=data,
        highlight_rating=ranking.HIGHLIGHT_RATING,
        max_score=ranking.MAX_SCORE,
        amenities=front_amenities,
    )


# Rede de metro/CPTM (estacoes + traçados das linhas) lida via fetch pelo report.html.
# Arquivo fixo gerado a partir do OpenStreetMap; ver transit.json na raiz.
@app.route("/transit.json")
def transit():
    return send_from_directory(".", "transit.json")


@app.route("/deactivate/<property_id>", methods=["POST"])
@with_property
def deactivate(connection, property_id):
    database.deactivate_property(connection, property_id)
    return "", 204  # 204 = sucesso, sem conteudo


@app.route("/reactivate/<property_id>", methods=["POST"])
@with_property
def reactivate(connection, property_id):
    database.reactivate_property(connection, property_id)
    return "", 204  # 204 = sucesso, sem conteudo


@app.route("/rate/<property_id>/<value>", methods=["POST"])
@with_property
def rate(connection, property_id, value):
    # value vem como texto porque o conversor <int:> do Flask nao aceita negativos.
    # Aceitamos -1 ("visto", so um traco), 0 (sem nota) e 1 a 5 (estrelas).
    try:
        value = int(value)
    except ValueError:
        abort(400)
    new_rating = database.set_rating(connection, property_id, value)
    return {"rating": new_rating}  # devolve a nota gravada para o JS atualizar as estrelas


# O front usa chaves em ingles (DATA.rentals); o banco usa portugues. Traduz aqui.
# Derivado da fonte unica + 'furnished' (mobiliado tem regra propria, ver database.set_amenity).
AMENITY_KEY_TO_COLUMN = {amenity["key"]: amenity["column"] for amenity in amenities.AMENITIES}
AMENITY_KEY_TO_COLUMN["furnished"] = "mobiliado"


@app.route("/amenity/<property_id>/<amenity>/<value>", methods=["POST"])
@with_property
def amenity(connection, property_id, amenity, value):
    # value vem como texto: "1" (tem), "0" (nao tem) ou "null" (nao verificado).
    # Texto porque o conversor <int:> do Flask nao aceita None/vazio.
    parsed = None if value == "null" else value
    column = AMENITY_KEY_TO_COLUMN.get(amenity)
    if column is None:
        abort(400)  # chave de amenidade desconhecida
    try:
        new_value = database.set_amenity(connection, property_id, column, parsed)
    except ValueError:
        abort(400)  # amenidade fora da allowlist
    return {"value": new_value}  # devolve o valor gravado para o JS atualizar o icone


if __name__ == "__main__":
    # Porta 8765: a 5000 e usada pelo AirPlay do macOS e a 8000 pelo Docker.
    # Esta e incomum, entao dificilmente conflita.
    PORT = 8765
    print(f"Servidor em http://localhost:{PORT}  (Ctrl+C para parar)")
    # debug=True liga o reloader: ao salvar um .py o servidor reinicia sozinho,
    # entao durante o desenvolvimento basta atualizar a pagina (sem Ctrl+C toda vez).
    app.run(port=PORT, debug=True)
