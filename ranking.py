# ENTRYPOINT 2: le o banco, calcula custo-beneficio e mostra o ranking + variacoes de preco.
# Rode com:  python ranking.py
#
# Score de custo-beneficio (0 a 100, maior = melhor):
#   - custo mensal  (34%) -> VALOR TOTAL cheio (aluguel+condominio+IPTU); mais barato pontua mais
#   - distancia km  (25%) -> mais perto do shopping pontua mais
#   - nota manual   (15%) -> sua avaliacao de 1 a 5 estrelas (normalizada)
#   - mobiliado     (9%) -> ponto cheio se for mobiliado
#   - vaga          (9%) -> ponto cheio se tiver 1+ vaga de garagem
#   - andar 4o+     (4%) -> ponto cheio se o andar for 4o ou acima
#   - sem pet       (4%) -> ponto cheio se NAO aceita pet
# Os pesos sao uma escolha: priorizamos o bolso um pouco acima da localizacao.
# Cada metrica e normalizada de 0 a 1 no conjunto de imoveis carregado.

import database

WEIGHT_PRICE = 0.34
WEIGHT_DISTANCE = 0.25
WEIGHT_RATING = 0.15        # nota manual de 1 a 5 (sua avaliacao)
WEIGHT_FURNISHED = 0.09
WEIGHT_PARKING = 0.09
WEIGHT_FLOOR = 0.04         # andar 4o ou acima
WEIGHT_NO_PET = 0.04        # NAO aceita pet

HIGHLIGHT_RATING = 4        # nota a partir da qual destaca a linha e o pin

MIN_GOOD_FLOOR = 4


def _latest_price_by_property(connection):
    # Pega o preco mais recente de cada imovel (ultimo snapshot).
    rows = connection.execute(
        """
        SELECT p.imovel_id, p.valor, p.valor_total
        FROM precos p
        JOIN (
            SELECT imovel_id, MAX(coletado_em) AS ultima
            FROM precos GROUP BY imovel_id
        ) u ON u.imovel_id = p.imovel_id AND u.ultima = p.coletado_em
        """
    ).fetchall()
    return {row["imovel_id"]: (row["valor"], row["valor_total"]) for row in rows}


def load_properties(connection, operation):
    # Carrega imoveis de uma operacao. Os filtros (preco/tipo/area) ja sao aplicados
    # na URL de busca do QuintoAndar (veja config.RENT_FILTERS), entao aqui nao
    # refiltramos por preco/quartos -- so exigimos area e distancia para o score.
    # As colunas vem em portugues (do banco); montamos o dict com chaves em ingles.
    rows = connection.execute(
        """
        SELECT id, titulo, endereco, area_m2, quartos, vagas, distancia_km, url,
               latitude, longitude, nota, mobiliado, andar, aceita_pet
        FROM imoveis
        WHERE operacao = ?
          AND ativo = 1
        """,
        (operation,),
    ).fetchall()

    prices = _latest_price_by_property(connection)
    properties = []
    for row in rows:
        price = prices.get(row["id"])
        if price is None:
            continue
        value, total_value = price
        if value is None:
            continue
        if not row["area_m2"] or not row["distancia_km"]:
            continue
        properties.append(
            {
                "id": row["id"],
                "title": row["titulo"],
                "address": row["endereco"],
                "area_m2": row["area_m2"],
                "bedrooms": row["quartos"],
                "parking": row["vagas"],
                "distance_km": row["distancia_km"],
                "url": row["url"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "rating": row["nota"],
                "furnished": row["mobiliado"],
                "floor": row["andar"],
                "accepts_pet": row["aceita_pet"],
                "price": value,
                "total_price": total_value,
                # cost = valor TOTAL cheio (aluguel + condominio + IPTU). E o que baseia
                # o score: ranqueia pelo que se paga no mes, nao pelo custo por m2.
                # Se o site nao informou o total, usa o aluguel base como aproximacao.
                "cost": (total_value or value),
                # price_per_m2 fica so para exibir na coluna "R$/m2" do relatorio.
                "price_per_m2": (total_value or value) / row["area_m2"],
            }
        )
    return properties


def _normalize_inverted(values):
    # Retorna funcao que mapeia um valor para 0..1, onde MENOR valor -> 1 (melhor).
    if not values:
        return lambda v: 0.0
    lowest, highest = min(values), max(values)
    if highest == lowest:
        return lambda v: 1.0
    return lambda v: (highest - v) / (highest - lowest)


def compute_scores(properties):
    norm_price = _normalize_inverted([p["cost"] for p in properties])
    norm_distance = _normalize_inverted([p["distance_km"] for p in properties])
    for property in properties:
        # bonus: 1 ponto cheio se atende, 0 se nao atende/desconhecido
        bonus_furnished = 1 if property.get("furnished") == 1 else 0
        bonus_parking = 1 if (property.get("parking") or 0) >= 1 else 0
        floor = property.get("floor")
        bonus_floor = 1 if (floor is not None and floor >= MIN_GOOD_FLOOR) else 0
        bonus_no_pet = 1 if property.get("accepts_pet") == 0 else 0  # NAO aceita pet e positivo
        # nota manual (1..5) normalizada para 0..1; sem nota (0) nao soma nada.
        # nota -1 = "visto" (apenas marcacao, sem estrela) tambem nao soma -> trata como 0.
        bonus_rating = max(0, property.get("rating") or 0) / 5
        score = (
            WEIGHT_PRICE * norm_price(property["cost"])
            + WEIGHT_DISTANCE * norm_distance(property["distance_km"])
            + WEIGHT_RATING * bonus_rating
            + WEIGHT_FURNISHED * bonus_furnished
            + WEIGHT_PARKING * bonus_parking
            + WEIGHT_FLOOR * bonus_floor
            + WEIGHT_NO_PET * bonus_no_pet
        )
        property["score"] = round(score * 100, 1)
    # Ordena pelo score (a nota ja esta embutida nele, como voce pediu - sem viés de
    # jogar nota alta forcadamente para o topo; ela influencia via peso).
    properties.sort(key=lambda p: p["score"], reverse=True)
    return properties


def price_change(connection, property_id):
    # Compara o 1o e o ultimo snapshot do imovel. Retorna simbolo + diferenca.
    rows = connection.execute(
        "SELECT valor, coletado_em FROM precos WHERE imovel_id = ? ORDER BY coletado_em",
        (property_id,),
    ).fetchall()
    if len(rows) < 2:
        return "novo"
    first, last = rows[0]["valor"], rows[-1]["valor"]
    if last > first:
        return f"subiu R$ {last - first:,.0f}"
    if last < first:
        return f"caiu R$ {first - last:,.0f}"
    return "estavel"


def _print_ranking(connection, title, properties):
    print(f"\n{'=' * 70}\n{title} ({len(properties)} imoveis)\n{'=' * 70}")
    if not properties:
        print("  Nenhum imovel encontrado com os filtros atuais.")
        return
    for position, property in enumerate(properties, start=1):
        change = price_change(connection, property["id"])
        print(
            f"\n#{position}  score {property['score']}  |  R$ {property['price']:,.0f}"
            f"  ({property['price_per_m2']:.0f}/m2)  |  {property['distance_km']} km do shopping  |  {change}"
        )
        print(f"     {property['bedrooms']} quarto(s), {property['area_m2']:.0f} m2, {property.get('parking') or 0} vaga(s)")
        if property["address"]:
            print(f"     {property['address']}")
        clean_url = property["url"].split("?")[0] if property["url"] else ""
        print(f"     {clean_url}")


def main():
    connection = database.connect()
    database.create_tables(connection)

    rentals = compute_scores(load_properties(connection, "aluguel"))

    _print_ranking(connection, "ALUGUEL  (filtros aplicados na busca do site)", rentals)

    connection.close()


if __name__ == "__main__":
    main()
