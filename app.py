# ENTRYPOINT 3: servidor web local que serve o relatorio interativo (mapa + tabela)
# COM os botoes de dar nota e desativar anuncios.
# Rode com:  python app.py   (depois abra http://localhost:8765 no navegador)
#
# Por que existe: o relatorio precisa gravar no banco (nota e "desativar"), o que um
# arquivo HTML estatico nao consegue. Este servidor pequeno (Flask) faz essa ponte.
# O HTML/CSS/JS fica no arquivo report.html (renderizado via Jinja2 com os dados).

from flask import Flask, abort, render_template, send_from_directory

import config
import database
import ranking

# template_folder="." faz o Flask achar report.html na raiz do projeto (sem pasta templates/).
app = Flask(__name__, template_folder=".")


def _to_minutes(seconds):
    # Converte segundos -> minutos arredondados; None se ainda nao calculado.
    if seconds is None:
        return None
    return round(seconds / 60)


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
    rentals = [
        {
            "id": property["id"],
            "rating": property.get("rating", 0),
            "score": property["score"],
            "price": property["price"],
            "total_price": property.get("total_price"),
            "price_per_m2": round(property["price_per_m2"]),
            "distance_km": property["distance_km"],
            "bedrooms": property["bedrooms"],
            "area_m2": round(property["area_m2"]),
            "parking": property.get("parking") or 0,
            "furnished": property.get("furnished"),
            "floor": property.get("floor"),
            "accepts_pet": property.get("accepts_pet"),
            "active": property.get("active", 1),
            "gym": property.get("gym"),
            "pool": property.get("pool"),
            "bike": property.get("bike"),
            "sauna": property.get("sauna"),
            "bed": property.get("bed"),
            "stove": property.get("stove"),
            "fridge": property.get("fridge"),
            "wardrobe": property.get("wardrobe"),
            "kitchen": property.get("kitchen"),
            "ac": property.get("ac"),
            "microwave": property.get("microwave"),
            "airfryer": property.get("airfryer"),
            "workspace": property.get("workspace"),
            "address": property["address"] or "",
            "url": (property["url"] or "").split("?")[0],
            "lat": property["latitude"],
            "lon": property["longitude"],
            # tempo ate o shopping em minutos (None = ainda nao calculado por commute.py)
            "walk_min": _to_minutes(property.get("walk_seconds")),
            "bike_min": _to_minutes(property.get("bike_seconds")),
            "change": ranking.price_change(connection, property["id"]),
        }
        for property in properties
    ]
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
    database.create_tables(connection)
    data = build_report_data(connection)
    connection.close()
    return render_template(
        "report.html", data=data, highlight_rating=ranking.HIGHLIGHT_RATING
    )


# Rede de metro/CPTM (estacoes + traçados das linhas) lida via fetch pelo report.html.
# Arquivo fixo gerado a partir do OpenStreetMap; ver transit.json na raiz.
@app.route("/transit.json")
def transit():
    return send_from_directory(".", "transit.json")


@app.route("/deactivate/<property_id>", methods=["POST"])
def deactivate(property_id):
    connection = database.connect()
    database.create_tables(connection)
    exists = connection.execute("SELECT 1 FROM imoveis WHERE id = ?", (property_id,)).fetchone()
    if not exists:
        connection.close()
        abort(404)
    database.deactivate_property(connection, property_id)
    connection.close()
    return "", 204  # 204 = sucesso, sem conteudo


@app.route("/reactivate/<property_id>", methods=["POST"])
def reactivate(property_id):
    connection = database.connect()
    database.create_tables(connection)
    exists = connection.execute("SELECT 1 FROM imoveis WHERE id = ?", (property_id,)).fetchone()
    if not exists:
        connection.close()
        abort(404)
    database.reactivate_property(connection, property_id)
    connection.close()
    return "", 204  # 204 = sucesso, sem conteudo


@app.route("/rate/<property_id>/<value>", methods=["POST"])
def rate(property_id, value):
    # value vem como texto porque o conversor <int:> do Flask nao aceita negativos.
    # Aceitamos -1 ("visto", so um traco), 0 (sem nota) e 1 a 5 (estrelas).
    try:
        value = int(value)
    except ValueError:
        abort(400)
    connection = database.connect()
    database.create_tables(connection)
    exists = connection.execute("SELECT 1 FROM imoveis WHERE id = ?", (property_id,)).fetchone()
    if not exists:
        connection.close()
        abort(404)
    new_rating = database.set_rating(connection, property_id, value)
    connection.close()
    return {"rating": new_rating}  # devolve a nota gravada para o JS atualizar as estrelas


# O front usa chaves em ingles (DATA.rentals); o banco usa portugues. Traduz aqui.
AMENITY_KEY_TO_COLUMN = {
    "pool": "piscina",
    "gym": "academia",
    "bike": "bicicletario",
    "sauna": "sauna",
    "furnished": "mobiliado",
    "bed": "cama",
    "stove": "fogao",
    "fridge": "geladeira",
    "wardrobe": "guarda_roupa",
    "kitchen": "armario_cozinha",
    "ac": "ar_condicionado",
    "microwave": "microondas",
    "airfryer": "airfryer",
    "workspace": "workspace",
}


@app.route("/amenity/<property_id>/<amenity>/<value>", methods=["POST"])
def amenity(property_id, amenity, value):
    # value vem como texto: "1" (tem), "0" (nao tem) ou "null" (nao verificado).
    # Texto porque o conversor <int:> do Flask nao aceita None/vazio.
    parsed = None if value == "null" else value
    column = AMENITY_KEY_TO_COLUMN.get(amenity)
    if column is None:
        abort(400)  # chave de amenidade desconhecida
    connection = database.connect()
    database.create_tables(connection)
    exists = connection.execute("SELECT 1 FROM imoveis WHERE id = ?", (property_id,)).fetchone()
    if not exists:
        connection.close()
        abort(404)
    try:
        new_value = database.set_amenity(connection, property_id, column, parsed)
    except ValueError:
        connection.close()
        abort(400)  # amenidade fora da allowlist
    connection.close()
    return {"value": new_value}  # devolve o valor gravado para o JS atualizar o icone


if __name__ == "__main__":
    # Porta 8765: a 5000 e usada pelo AirPlay do macOS e a 8000 pelo Docker.
    # Esta e incomum, entao dificilmente conflita.
    PORT = 8765
    print(f"Servidor em http://localhost:{PORT}  (Ctrl+C para parar)")
    # debug=True liga o reloader: ao salvar um .py o servidor reinicia sozinho,
    # entao durante o desenvolvimento basta atualizar a pagina (sem Ctrl+C toda vez).
    app.run(port=PORT, debug=True)
