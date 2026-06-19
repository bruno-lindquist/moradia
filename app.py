# ENTRYPOINT 3: servidor web local que serve o relatorio interativo (mapa + tabela)
# COM os botoes de dar nota e desativar anuncios.
# Rode com:  python app.py   (depois abra http://localhost:8765 no navegador)
#
# Por que existe: o relatorio precisa gravar no banco (nota e "desativar"), o que um
# arquivo HTML estatico nao consegue. Este servidor pequeno (Flask) faz essa ponte.
# O HTML/CSS/JS fica no arquivo report.html (renderizado via Jinja2 com os dados).

from flask import Flask, abort, render_template

import config
import database
import ranking

# template_folder="." faz o Flask achar report.html na raiz do projeto (sem pasta templates/).
app = Flask(__name__, template_folder=".")


def build_report_data(connection):
    # Monta a lista de imoveis (com score e variacao) pronta para o template.
    # Ja vem ordenada por score. Descarta o que esta alem do raio (config.MAX_DISTANCE_KM).
    # As chaves abaixo (em ingles) sao lidas diretamente pelo JS de report.html.
    properties = ranking.compute_scores(ranking.load_properties(connection, "aluguel"))
    properties = [p for p in properties if p["distance_km"] <= config.MAX_DISTANCE_KM]
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
            "address": property["address"] or "",
            "url": (property["url"] or "").split("?")[0],
            "lat": property["latitude"],
            "lon": property["longitude"],
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


if __name__ == "__main__":
    # Porta 8765: a 5000 e usada pelo AirPlay do macOS e a 8000 pelo Docker.
    # Esta e incomum, entao dificilmente conflita.
    PORT = 8765
    print(f"Servidor em http://localhost:{PORT}  (Ctrl+C para parar)")
    app.run(port=PORT, debug=False)
