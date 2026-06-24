# ENTRYPOINT 2: le o banco, calcula custo-beneficio e mostra o ranking + variacoes de preco.
# Rode com:  python ranking.py
#
# Score de custo-beneficio = SOMA DE PONTOS com faixas FIXAS (0 a 145, maior = melhor).
# As faixas sao fixas (nao dependem dos outros imoveis), entao o score de um imovel nao
# muda quando outro entra/sai da lista -- da pra comparar o ranking de dias diferentes.
#   - preco        (35 pts) -> faixa R$ 1.800 (cheio) a R$ 3.200 (zero); mais barato pontua mais
#   - distancia    (35 pts) -> faixa 0,3 km (cheio) a 3 km (zero); mais perto pontua mais
#   - mobiliado    (10 pts) -> ponto cheio se for mobiliado
#   - vaga          (6 pts) -> ponto cheio se tiver 1+ vaga de garagem
#   - andar 4o+     (3 pts) -> ponto cheio se o andar for 4o ou acima
#   - nota manual   (5 pts) -> sua avaliacao de 1 a 5 estrelas (normalizada)
#   - amenidades manuais (piscina, academia, sauna, cama, fogao, ...) -> pontos definidos
#     na fonte unica amenities.AMENITIES (campo "points"); ponto cheio se marcado "tem".
# Imoveis ATIVOS fora da faixa (preco ou distancia) sao ELIMINADOS do ranking.
# "aceita pet" e "bicicletario" sao apenas EXIBIDOS na tabela; nao entram no score
# (bicicletario tem points=0 na fonte unica).

import amenities
import config
import database

# Faixas fixas: o limite "bom" da pontos cheios, o limite "ruim" da zero.
PRICE_MIN = 1800            # custo mensal (R$) -> pontuacao cheia
PRICE_MAX = 3200            # custo mensal (R$) -> zero pontos / acima disso elimina
DISTANCE_MIN = 0.3          # km do shopping -> pontuacao cheia
DISTANCE_MAX = 3.0          # km do shopping -> zero pontos / acima disso elimina

# Pontos dos criterios com logica propria (faixa fixa, flag). Os pontos das amenidades
# manuais (piscina, academia, sauna, cama, ...) vem da fonte unica amenities.AMENITIES.
POINTS_PRICE = 35
POINTS_DISTANCE = 35
POINTS_FURNISHED = 10
POINTS_PARKING = 6
POINTS_FLOOR = 3          # andar 4o ou acima
POINTS_RATING = 5         # nota manual de 1 a 5 (sua avaliacao)

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


def load_properties(connection, operation, include_inactive=False):
    # Carrega imoveis de uma operacao. Os filtros (preco/tipo/area) ja sao aplicados
    # na URL de busca do QuintoAndar (veja config.RENT_FILTERS), entao aqui nao
    # refiltramos por preco/quartos -- so exigimos area e distancia para o score.
    # As colunas vem em portugues (do banco); montamos o dict com chaves em ingles.
    # include_inactive=True traz tambem os ocultos (ativo=0), para o relatorio
    # poder mostrar "so os ocultos" e oferecer restaurar.
    active_filter = "" if include_inactive else "AND ativo = 1"
    # Colunas das amenidades vem da fonte unica (amenities.py), na mesma ordem.
    amenity_columns = ", ".join(amenity["column"] for amenity in amenities.AMENITIES)
    rows = connection.execute(
        f"""
        SELECT id, titulo, endereco, area_m2, quartos, vagas, distancia_km, url,
               latitude, longitude, nota, mobiliado, andar, aceita_pet, ativo,
               walk_seconds, bike_seconds, {amenity_columns}
        FROM imoveis
        WHERE operacao = ?
          {active_filter}
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
        property = {
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
            "active": row["ativo"],
            "walk_seconds": row["walk_seconds"],
            "bike_seconds": row["bike_seconds"],
            "price": value,
            "total_price": total_value,
            # cost = valor TOTAL cheio (aluguel + condominio + IPTU). E o que baseia
            # o score: ranqueia pelo que se paga no mes, nao pelo custo por m2.
            # Se o site nao informou o total, usa o aluguel base como aproximacao.
            "cost": (total_value or value),
            # price_per_m2 fica so para exibir na coluna "R$/m2" do relatorio.
            "price_per_m2": (total_value or value) / row["area_m2"],
        }
        # amenidades (fonte unica): traduz coluna PT do banco -> chave EN do dict.
        for amenity in amenities.AMENITIES:
            property[amenity["key"]] = row[amenity["column"]]
        properties.append(property)
    return properties


def _fixed_fraction(value, best, worst):
    # Mapeia value para 0..1 numa faixa FIXA: best -> 1.0, worst -> 0.0.
    # Trava (clamp) em 0..1. Funciona com best < worst (preco/distancia: menor e melhor).
    fraction = (worst - value) / (worst - best)
    return max(0.0, min(1.0, fraction))


def within_range(property):
    # True se o imovel esta dentro das faixas de preco E distancia (custo-beneficio aceitavel).
    return (
        PRICE_MIN <= property["cost"] <= PRICE_MAX
        and DISTANCE_MIN <= property["distance_km"] <= DISTANCE_MAX
    )


def compute_scores(properties):
    # Pontua TODOS os imoveis (inclusive ocultos e fora da faixa). A ELIMINACAO de quem
    # esta fora da faixa e feita por quem chama (CLI e app.py), para nao descartar os
    # ocultos que o relatorio precisa exibir no filtro "so ocultos".
    for property in properties:
        # bonus: 1 ponto cheio se atende, 0 se nao atende/desconhecido
        bonus_furnished = 1 if property.get("furnished") == 1 else 0
        bonus_parking = 1 if (property.get("parking") or 0) >= 1 else 0
        floor = property.get("floor")
        bonus_floor = 1 if (floor is not None and floor >= MIN_GOOD_FLOOR) else 0
        # nota manual (1..5) normalizada para 0..1; sem nota (0) nao soma nada.
        # nota -1 = "visto" (apenas marcacao, sem estrela) tambem nao soma -> trata como 0.
        bonus_rating = max(0, property.get("rating") or 0) / 5
        score = (
            POINTS_PRICE * _fixed_fraction(property["cost"], PRICE_MIN, PRICE_MAX)
            + POINTS_DISTANCE * _fixed_fraction(property["distance_km"], DISTANCE_MIN, DISTANCE_MAX)
            + POINTS_FURNISHED * bonus_furnished
            + POINTS_PARKING * bonus_parking
            + POINTS_FLOOR * bonus_floor
            + POINTS_RATING * bonus_rating
        )
        # amenidades manuais (fonte unica): ponto cheio so quando marcado como "tem" (1).
        for amenity in amenities.AMENITIES:
            if property.get(amenity["key"]) == 1:
                score += amenity["points"]
        property["score"] = round(score, 1)
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
        print(f"     {config.clean_url(property['url'])}")


def main():
    connection = database.connect()
    database.create_tables(connection)

    rentals = compute_scores(load_properties(connection, "aluguel"))
    rentals = [property for property in rentals if within_range(property)]

    _print_ranking(connection, "ALUGUEL  (filtros aplicados na busca do site)", rentals)

    connection.close()


if __name__ == "__main__":
    main()
