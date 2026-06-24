# Amenidades manuais (marcadas a mao no relatorio). Os dados vivem na tabela 'amenidades'
# do banco (moradia.db); aqui apenas os carregamos para o codigo usar.
# Para adicionar/remover uma amenidade, edite a tabela do banco (e, se for nova, a coluna
# correspondente em 'imoveis'). Daqui derivam: a allowlist de UPDATE e os dicts de traducao
# (database.py/app.py), os pontos do score e o SELECT (ranking.py) e as colunas/popup (report.html).
#
# Cada item e um dict com as chaves:
#   key    -> chave em ingles usada pelo front (DATA.rentals) e pela API
#   column -> nome da coluna em 'imoveis' (portugues)
#   points -> peso no score de custo-beneficio (0 = exibida mas nao pontua, como bicicletario)
#   icon   -> emoji exibido na tabela/popup do relatorio
#   label  -> texto do tooltip/legenda no relatorio
#   front  -> True se ganha coluna na tabela e linha no popup (sauna fica so no score)
#
# Nao inclui 'mobiliado': tem regra propria (flag mobiliado_manual, tambem vem do scraping).

import sqlite3

import config


def _load():
    # Le a tabela 'amenidades' do banco, na ordem definida. Carregado uma vez no import.
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT chave, coluna, pontos, icone, rotulo, front FROM amenidades ORDER BY ordem"
    ).fetchall()
    connection.close()
    return [
        {
            "key": row["chave"],
            "column": row["coluna"],
            "points": row["pontos"],
            "icon": row["icone"],
            "label": row["rotulo"],
            "front": bool(row["front"]),
        }
        for row in rows
    ]


AMENITIES = _load()


def read_from_row(row, target):
    # Le cada amenidade de uma linha do banco (coluna em portugues) e grava no dict
    # target com a chave em ingles. Usado ao montar imoveis a partir do SQL.
    for amenity in AMENITIES:
        target[amenity["key"]] = row[amenity["column"]]


def copy_keys(source, target):
    # Copia as chaves de amenidade (em ingles) de um dict para outro. Usado ao reformatar
    # um imovel ja em ingles para enviar ao front.
    for amenity in AMENITIES:
        target[amenity["key"]] = source.get(amenity["key"])
