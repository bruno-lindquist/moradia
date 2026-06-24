# Configuracoes centrais do MVP. Tudo que voce pode querer ajustar fica aqui.

# Coordenadas do Shopping Morumbi (Av. Roque Petroni Jr, 1089, Sao Paulo).
# Validar na 1a execucao; se a distancia parecer errada, conferir aqui.
REFERENCE_NAME = "Shopping Morumbi"
REFERENCE_LAT = -23.6235
REFERENCE_LON = -46.6997

# URLs de busca do QuintoAndar.
# O QuintoAndar busca por bairro (nao por rua), e bairro + filtros vao na propria URL.
# Os bairros ficam na tabela 'bairros' do banco (veja database.py). Aqui ficam os moldes
# de URL: {slug} e trocado pelo slug do bairro (ex.: "jardim-das-acacias").
#
# RENT_FILTERS: segmentos de filtro do QuintoAndar anexados a busca de aluguel.
#   preco (de-500-a-3000-reais) / tipos (apartamento, kitnet, casacondominio) / area (de-20-a-30-m2)

# Limites para DESCARTAR no scraper o que nao bate com RENT_FILTERS.
# Necessario porque o QuintoAndar mistura imoveis "recomendados" fora do filtro
# (search_results_flexible) quando a busca e restritiva. Mantenha em sincronia com RENT_FILTERS.
PRICE_MIN = 500
PRICE_MAX = 3200
AREA_MIN = 10
AREA_MAX = 40


# Para mudar os filtros, ajuste esta string. Para nao filtrar, deixe "".
RENT_FILTERS = f"/de-{PRICE_MIN}-a-{PRICE_MAX}-reais/apartamento/kitnet/casacondominio/de-10-a-{AREA_MAX}-m2"

RENT_URL_TEMPLATE = "https://www.quintoandar.com.br/alugar/imovel/{slug}-sao-paulo-sp-brasil" + RENT_FILTERS



# Compra desativada de proposito: buscamos so aluguel (ver operacao "aluguel" em scraper.py).

# Quantas vezes clicar em "Ver mais" por bairro (cada clique traz ~12 imoveis).
# Limite de seguranca: para de clicar quando o botao some, mesmo antes deste maximo.
MAX_LOAD_MORE_CLICKS = 15

# Pausa (segundos) entre acoes, para nao parecer um robo agressivo e reduzir risco de bloqueio
PAUSE_SECONDS = 2.0

# HEADLESS=False abre o Chrome visivel (bom para a 1a vez, da pra ver acontecendo).
# Depois que confiar, troque para True para rodar sem abrir janela.
HEADLESS = False

# Caminho do banco SQLite (um arquivo so, na pasta do projeto)
DB_PATH = "moradia.db"


def clean_url(url):
    # Remove a query string (tudo apos "?"): deixa a URL do anuncio limpa para exibir.
    return (url or "").split("?")[0]
