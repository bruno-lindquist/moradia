# Configuracoes centrais do MVP. Tudo que voce pode querer ajustar fica aqui.

# Coordenadas do Shopping Morumbi (Av. Roque Petroni Jr, 1089, Sao Paulo).
# Validar na 1a execucao; se a distancia parecer errada, conferir aqui.
SHOPPING_NOME = "Shopping Morumbi"
SHOPPING_LAT = -23.6235
SHOPPING_LON = -46.6997

# URLs de busca do QuintoAndar.
# O QuintoAndar busca por bairro (nao por rua), e bairro + filtros vao na propria URL.
# Os bairros ficam na tabela 'bairros' do banco (veja db.py). Aqui ficam os moldes
# de URL: {slug} e trocado pelo slug do bairro (ex.: "jardim-das-acacias").
#
# FILTROS_ALUGUEL: segmentos de filtro do QuintoAndar anexados a busca de aluguel.
#   preco (de-500-a-3000-reais) / tipos (apartamento, kitnet, casacondominio) / area (de-20-a-30-m2)
# Para mudar os filtros, ajuste esta string. Para nao filtrar, deixe "".
FILTROS_ALUGUEL = "/de-500-a-3000-reais/apartamento/kitnet/casacondominio/de-10-a-30-m2"

URL_ALUGUEL_MOLDE = "https://www.quintoandar.com.br/alugar/imovel/{slug}-sao-paulo-sp-brasil" + FILTROS_ALUGUEL

# Limites para DESCARTAR no scraper o que nao bate com FILTROS_ALUGUEL.
# Necessario porque o QuintoAndar mistura imoveis "recomendados" fora do filtro
# (search_results_flexible) quando a busca e restritiva. Mantenha em sincronia com FILTROS_ALUGUEL.
PRECO_MIN = 500
PRECO_MAX = 3000
AREA_MIN = 10
AREA_MAX = 30

# No relatorio, nao mostrar imoveis acima desta distancia do shopping (km).
# Tambem descarta erros de geocodificacao (ruas homonimas em outro lugar da cidade).
DISTANCIA_MAX_KM = 2
# Compra desativada (buscamos so aluguel). Para reativar, descomente a linha abaixo
# e a operacao "compra" em scraper.py.
# URL_COMPRA_MOLDE = "https://www.quintoandar.com.br/comprar/imovel/{slug}-sao-paulo-sp-brasil"

# Quantas vezes clicar em "Ver mais" por bairro (cada clique traz ~12 imoveis).
# Limite de seguranca: para de clicar quando o botao some, mesmo antes deste maximo.
MAX_VER_MAIS = 15

# Pausa (segundos) entre acoes, para nao parecer um robo agressivo e reduzir risco de bloqueio
PAUSA_SEGUNDOS = 2.0

# HEADLESS=False abre o Chrome visivel (bom para a 1a vez, da pra ver acontecendo).
# Depois que confiar, troque para True para rodar sem abrir janela.
HEADLESS = False

# Caminho do banco SQLite (um arquivo so, na pasta do projeto)
DB_PATH = "moradia.db"
