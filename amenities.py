# Fonte unica das amenidades manuais (marcadas a mao no relatorio).
# Para adicionar/remover uma amenidade, edite SO esta lista: dela derivam as colunas do
# banco (database.py), a allowlist de UPDATE, os pontos do score (ranking.py), os dicts de
# traducao ingles<->portugues (app.py/ranking.py) e as colunas/popup do front (report.html).
#
# Campos:
#   key    -> chave em ingles usada pelo front (DATA.rentals) e pela API
#   column -> nome da coluna no banco (portugues)
#   points -> peso no score de custo-beneficio (0 = exibida mas nao pontua, como bicicletario)
#   icon   -> emoji exibido na tabela/popup do relatorio
#   label  -> texto do tooltip/legenda no relatorio
#   front  -> True se ganha coluna na tabela e linha no popup (sauna fica so no score)
#
# Nao inclui 'mobiliado': tem regra propria (flag mobiliado_manual, tambem vem do scraping),
# tratada a parte em database.py/ranking.py e com coluna propria no front.
AMENITIES = [
    {"key": "pool",      "column": "piscina",         "points": 5, "icon": "🏊",  "label": "Piscina",         "front": True},
    {"key": "gym",       "column": "academia",        "points": 3, "icon": "🏋️", "label": "Academia",        "front": True},
    {"key": "sauna",     "column": "sauna",           "points": 3, "icon": "🧖",  "label": "Sauna",           "front": False},
    {"key": "bike",      "column": "bicicletario",    "points": 0, "icon": "🚲",  "label": "Bicicletário",    "front": True},
    {"key": "bed",       "column": "cama",            "points": 5, "icon": "🛌🏻", "label": "Cama",            "front": True},
    {"key": "stove",     "column": "fogao",           "points": 5, "icon": "🔥",  "label": "Fogão",           "front": True},
    {"key": "fridge",    "column": "geladeira",       "points": 5, "icon": "❄️",  "label": "Geladeira",       "front": True},
    {"key": "wardrobe",  "column": "guarda_roupa",    "points": 5, "icon": "👕",  "label": "Guarda-roupas",   "front": True},
    {"key": "kitchen",   "column": "armario_cozinha", "points": 5, "icon": "🥂",  "label": "Armário cozinha", "front": True},
    {"key": "ac",        "column": "ar_condicionado", "points": 5, "icon": "𖣘",  "label": "Ar-condicionado", "front": True},
    {"key": "microwave", "column": "microondas",      "points": 5, "icon": "📡",  "label": "Micro-ondas",     "front": True},
    {"key": "airfryer",  "column": "airfryer",        "points": 5, "icon": "🍟",  "label": "Air fryer",       "front": True},
    {"key": "workspace", "column": "workspace",       "points": 5, "icon": "💻",  "label": "Workspace",       "front": True},
]
