# 🏠 Moradia perto do Shopping Morumbi

Um programa que procura apartamentos para **alugar** perto do Shopping Morumbi (São Paulo),
organiza tudo num banco de dados e mostra um **relatório com mapa**, já indicando os
imóveis com melhor **custo-benefício**.

---

## Antes de começar

Você precisa ter o **Python** instalado no computador (versão 3.10 ou mais nova).

- Baixe em: https://www.python.org/downloads/
- **No Windows**, durante a instalação, marque a caixinha **"Add Python to PATH"**.

Para checar se já tem o Python, abra o terminal e digite:

- **Windows** (abra o "PowerShell"): `python --version`
- **Mac** (abra o "Terminal"): `python3 --version`

Se aparecer um número de versão (ex.: `Python 3.13.1`), está instalado.

---

## Como baixar e instalar

Abra o terminal **dentro da pasta do projeto** e rode os comandos abaixo, na ordem.
Você só precisa fazer isso **uma vez**.

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Mac (Terminal)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

O que esses comandos fazem, em resumo: criam um "ambiente isolado" só para este projeto
(`.venv`), instalam as bibliotecas necessárias e baixam o navegador que o programa usa
para buscar os imóveis.

> **Observação (Mac):** se o `pip install` der erro, pode ser por causa do Python 3.14.
> Instale o **Python 3.13** e refaça os passos. (Alternativa avançada: usar a ferramenta
> `uv` no lugar do `venv`/`pip`.)

---

## Como usar

Sempre que for usar o programa, primeiro **ative o ambiente** (o mesmo comando de ativação
da instalação): `.venv\Scripts\activate` no Windows ou `source .venv/bin/activate` no Mac.

São só dois passos no dia a dia:

**1. Buscar os imóveis** (atualiza os preços):

```
python collect.py
```

Ele vai na internet, busca os apartamentos e guarda tudo. Um navegador (Chrome) vai abrir
sozinho durante a busca — **isso é normal**, é o programa trabalhando. Rode este comando
sempre que quiser atualizar os dados (por exemplo, uma vez por semana).

**2. Ver o relatório** (a parte interativa, com mapa e estrelas):

```
python app.py
```

Depois abra o navegador e acesse: **http://localhost:8765**

> Por que essa "porta" 8765? É só um número de endereço interno do seu computador.
> Usamos um número incomum para não conflitar com outros programas.

Para parar o relatório, volte ao terminal e aperte **Ctrl + C**.

> Existe ainda um comando extra, opcional: `python ranking.py` mostra o ranking direto no
> terminal (sem mapa). Para o uso normal, **`python app.py` é o principal**.

---

## Como funciona o score (a nota de custo-benefício)

Cada imóvel ganha uma **nota de 0 a 100** — quanto **maior, melhor**. O programa calcula
essa nota juntando 7 características, cada uma com um peso:

| Peso | Característica | O que pontua mais |
|-----:|----------------|-------------------|
| **34%** | Preço total (aluguel + condomínio + IPTU) | mais barato |
| **25%** | Distância até o shopping | mais perto |
| **15%** | Sua nota de estrelas | mais estrelas |
| **9%** | É mobiliado? | se for mobiliado |
| **9%** | Tem vaga de garagem? | se tiver vaga |
| **4%** | Fica no 4º andar ou acima? | se for andar alto |
| **4%** | NÃO aceita pet? | se não aceitar pet |

> Os pesos podem ser alterados no arquivo `ranking.py`, caso você queira valorizar mais
> o preço, a distância, etc.

---

## Como funciona a pontuação de estrelas

No relatório, a **primeira coluna** de cada imóvel tem 5 estrelas. Você usa para registrar
sua opinião pessoal sobre cada apartamento:

- **Clique numa estrela** → dá sua nota de **1 a 5**. Clicar de novo na mesma estrela
  **apaga** a nota. Sua nota entra no cálculo do score (vale 15%). Imóveis com nota **4 ou
  5** ficam **destacados** (linha amarela e pin dourado no mapa).

- **Clique com o botão direito** numa estrela → marca um **traço (–)**. Serve para dizer
  "já olhei este, mas não me interessou a ponto de dar estrela". É **apenas uma marcação**
  e **não muda o score**. Clicar com o botão direito de novo remove o traço.
  *(Se o imóvel já tiver estrelas, o botão direito é ignorado.)*

- **Botão ✕** (na última coluna) → **esconde** o anúncio, que some do relatório.

> Suas notas e marcações ficam salvas no banco de dados — não se perdem ao fechar o
> relatório ou ao rodar a busca de novo.

---

## Como ajustar a busca

Quase tudo o que dá para mudar fica no arquivo **`config.py`** (abra com qualquer editor
de texto):

- **Faixa de preço e tamanho**: `FILTROS_ALUGUEL` (vai na busca do site) e os limites
  `PRECO_MIN` / `PRECO_MAX` / `AREA_MIN` / `AREA_MAX`. *Mantenha os dois em sintonia —
  se mudar o preço no filtro, ajuste também os limites.*
- **Distância máxima** mostrada no relatório: `DISTANCIA_MAX_KM`.
- **Outra região / outro ponto de referência**: troque `SHOPPING_NOME`, `SHOPPING_LAT` e
  `SHOPPING_LON` (as coordenadas do lugar de referência).

Os **bairros** pesquisados ficam guardados no banco de dados (não no `config.py`), e cada
um pode ser ligado ou desligado.

---

## O que tem em cada arquivo

- `config.py` — as configurações (faixa de preço, distância, ponto de referência)
- `collect.py` — comando que faz a busca dos imóveis na internet
- `app.py` — comando que abre o relatório interativo no navegador
- `report.html` — a página do relatório (mapa + tabela); usada pelo `app.py`
- `ranking.py` — mostra o ranking no terminal (e contém o cálculo do score)
- `scraper.py` — a parte que lê os anúncios do site QuintoAndar
- `geo.py` — descobre as coordenadas dos endereços e calcula a distância
- `database.py` — cuida do banco de dados (o arquivo `moradia.db`)
