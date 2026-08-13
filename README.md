# 🏠 Moradia perto do MASP

Um programa que procura apartamentos para **alugar** perto do MASP (Avenida Paulista, São Paulo),
organiza tudo num banco de dados e mostra um **relatório com mapa**, já indicando os
imóveis com melhor **custo-benefício**.

---

## Como usar (é só dar duplo-clique)

Não é preciso digitar comandos nem instalar nada à mão. São dois passos.

**1. Tenha o Python no computador** (versão 3.10 ou mais nova; a 3.14 ainda não serve).

- Baixe em: https://www.python.org/downloads/
- **No Windows**, durante a instalação, marque a caixinha **"Add Python to PATH"**.

**2. Dê duplo-clique no atalho**, dentro da pasta do projeto:

- **Mac**: `iniciar.command` (no Finder)
- **Windows**: `iniciar.cmd` (no Explorer)

Na **primeira vez**, o atalho prepara tudo sozinho: cria o ambiente isolado do projeto,
instala as bibliotecas e baixa o navegador usado na busca. Isso leva alguns minutos e
baixa cerca de 150 MB, então **não feche a janela** enquanto estiver acontecendo. Nas
vezes seguintes ele abre em segundos, porque só repete a instalação se a lista de
bibliotecas mudar.

Em seguida ele pergunta o que você quer fazer:

- **A) Buscar imóveis**: atualiza os preços na internet e depois abre o relatório.
- **B) Ver o relatório**: abre direto, com os dados que já tem.

O navegador abre sozinho com o relatório. Para parar, volte à janela preta (terminal) que
ficou aberta e aperte **Ctrl + C** (ou simplesmente feche a janela).

> Clicar no atalho de novo com o relatório já aberto não estraga nada: ele percebe que já
> está no ar e só traz a página de volta ao navegador.

### Se o atalho não abrir

- **Mac, na primeira vez**: por segurança, o sistema pode barrar o duplo-clique. Clique no
  arquivo com o **botão direito → Abrir** uma vez; depois passa a funcionar normalmente.
- **Mac, se ele abrir num editor de texto**: acontece quando o projeto chegou dentro de um
  `.zip`, que apaga a permissão de execução do arquivo. Abra o Terminal na pasta do projeto
  e rode uma vez: `chmod +x iniciar.command`.
- **"Python não encontrado"**: instale pelo link do passo 1 e clique no atalho de novo.
  No Windows, o mais comum é ter esquecido a caixinha "Add Python to PATH".

---

## Usando pelos comandos (alternativa ao atalho)

### Instalação manual (só se você não quiser usar o atalho)

O atalho já faz isso sozinho. Os comandos equivalentes, rodados **uma vez** dentro da
pasta do projeto, são:

```bash
# Mac (Terminal). No Windows (PowerShell), troque "python3" por "python"
# e "source .venv/bin/activate" por ".venv\Scripts\activate"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

Eles criam o ambiente isolado (`.venv`), instalam as bibliotecas e baixam o navegador
usado na busca.

> Se o `pip install` der erro, provavelmente o `python3` da sua máquina é a versão 3.14,
> que ainda não funciona aqui. Instale o **Python 3.13** e refaça os passos usando
> `python3.13 -m venv .venv`. (O atalho já resolve isso sozinho: ele procura uma versão
> compatível entre as instaladas.)

### No dia a dia

Com o ambiente **ativado** (`source .venv/bin/activate` no Mac, `.venv\Scripts\activate`
no Windows), são dois passos:

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

### Comandos extras (opcionais)

- `python commute.py` — calcula, para os imóveis **com nota**, o tempo **a pé** e **de
  bicicleta** até o shopping e o tempo **a pé até a estação** de metrô/trem mais próxima.
  Esses tempos aparecem no relatório (colunas 🚶🚴 e 🚇).
- `python fix_coords.py` — reabre a página de cada imóvel **com nota** para: corrigir a
  localização exata no mapa, registrar o preço atual e **detectar anúncios que saíram do
  ar** (some do relatório). Útil rodar de vez em quando para manter os dados precisos.
- `python ranking.py` — mostra o ranking direto no terminal (sem mapa).

> Para o uso normal, **o atalho clicável (ou `python app.py`) é o principal**. Os comandos
> acima são refinamentos opcionais.

---

## Como funciona o score (a nota de custo-benefício)

Cada imóvel ganha uma **nota em pontos** — quanto **maior, melhor**. O programa soma os
pontos de várias características. As faixas são **fixas** (não dependem dos outros imóveis),
então a nota de um apartamento não muda quando outro entra ou sai da lista.

| Pontos | Característica | O que pontua mais |
|-------:|----------------|-------------------|
| **35** | Preço total (aluguel + condomínio + IPTU) | mais barato (R$ 1.800 = cheio; R$ 3.200 = zero) |
| **35** | Distância até o shopping | mais perto (0,3 km = cheio; 3 km = zero) |
| **10** | É mobiliado? | se for mobiliado |
| **6**  | Tem vaga de garagem? | se tiver 1+ vaga |
| **5**  | Sua nota de estrelas | proporcional a quantas estrelas (1 a 5) |
| **3**  | Fica no 4º andar ou acima? | se for andar alto |
| **+**  | Amenidades marcadas à mão | cada amenidade soma seus pontos (piscina, academia, etc.) |

Imóveis **fora da faixa** de preço (acima de R$ 3.200) ou de distância (acima de 3 km) são
**eliminados** do ranking. O campo "aceita pet" é apenas **exibido** — não entra no score.

> Os pesos e as faixas ficam no arquivo `ranking.py` (variáveis `POINTS_*`, `PRICE_MIN`,
> `PRICE_MAX`, `DISTANCE_MIN`, `DISTANCE_MAX`). Os pontos de cada amenidade ficam na tabela
> `amenidades` do banco.

---

## Como funciona a pontuação de estrelas

No relatório, a **primeira coluna** de cada imóvel tem 5 estrelas. Você usa para registrar
sua opinião pessoal sobre cada apartamento:

- **Clique numa estrela** → dá sua nota de **1 a 5**. Clicar de novo na mesma estrela
  **apaga** a nota. Sua nota entra no cálculo do score (vale 5 pontos). Imóveis com nota
  **4 ou 5** ficam **destacados** (linha amarela e pin dourado no mapa).

- **Clique com o botão direito** numa estrela → marca um **traço (–)**. Serve para dizer
  "já olhei este, mas não me interessou a ponto de dar estrela". É **apenas uma marcação**
  e **não muda o score**. Clicar com o botão direito de novo remove o traço.
  *(Se o imóvel já tiver estrelas, o botão direito é ignorado.)*

- **Botão ✕** (na última coluna) → **esconde** o anúncio, que some do relatório.

> Suas notas e marcações ficam salvas no banco de dados — não se perdem ao fechar o
> relatório ou ao rodar a busca de novo.

---

## O relatório por dentro (mapa, filtros e amenidades)

- **Mapa** — cada imóvel é um pin colorido pela sua nota de custo-benefício (verde = bom,
  âmbar = médio, vermelho = ruim). Pins próximos se agrupam num círculo com a contagem; o
  pin do shopping marca o ponto de referência.

- **Filtros** (no topo, sem recarregar a página) — estreitam a lista e os pins: com vaga,
  só mobiliado, só com nota, esconder vistos, distância máxima, valor total máximo, busca
  por endereço e um botão "Só ocultos" (para rever e restaurar anúncios escondidos).

- **Amenidades** — colunas de ícone (🅿️ vaga, 🛋️ mobiliado, ↑ andar 4º+, piscina,
  academia, etc.). Você pode marcar à mão se um imóvel **tem** ou **não tem** cada
  amenidade; as marcadas como "tem" somam pontos no score. Marcar "mobiliado" à mão
  **protege** esse valor de ser sobrescrito na próxima busca.

- **Tempos de deslocamento** — colunas 🚶🚴 (a pé e de bike até o shopping) e 🚇 (a pé até
  a estação mais próxima). Só aparecem depois de rodar `python commute.py`.

- **Reordenar** — clique no cabeçalho de qualquer coluna para ordenar por ela.

---

## Como ajustar a busca

Quase tudo o que dá para mudar fica no arquivo **`config.py`** (abra com qualquer editor
de texto):

- **Faixa de preço e tamanho**: a string `RENT_FILTERS` (vai na busca do site) e os limites
  `PRICE_MIN` / `PRICE_MAX` / `AREA_MIN` / `AREA_MAX`. *Mantenha os dois em sintonia — se
  mudar o preço no filtro, ajuste também os limites.*
- **Outra região / outro ponto de referência**: troque `REFERENCE_NAME`, `REFERENCE_LAT` e
  `REFERENCE_LON` (as coordenadas do lugar de referência).

A **distância máxima** que entra no ranking fica em **`ranking.py`** (`DISTANCE_MAX`),
junto com os pesos do score.

Os **bairros** pesquisados ficam guardados no banco de dados (não no `config.py`), e cada
um pode ser ligado ou desligado.

---

## O que tem em cada arquivo

- `config.py` — as configurações (faixa de preço, ponto de referência, filtros da busca)
- `collect.py` — comando que faz a busca dos imóveis na internet
- `app.py` — comando que abre o relatório interativo no navegador (servidor Flask)
- `commute.py` — comando que calcula os tempos a pé/bike até o shopping e a pé até a estação
- `fix_coords.py` — comando que corrige coordenadas e detecta anúncios fora do ar
- `ranking.py` — mostra o ranking no terminal (e contém o cálculo do score)
- `report.html` — a página do relatório (estrutura HTML); usada pelo `app.py`
- `static/report.css` — a aparência do relatório
- `static/report.js` — o que torna o relatório interativo (mapa, filtros, estrelas)
- `scraper.py` — a parte que lê os anúncios do site QuintoAndar
- `geo.py` — descobre as coordenadas dos endereços e calcula a distância
- `amenities.py` — carrega a lista de amenidades (definida na tabela `amenidades` do banco)
- `database.py` — cuida do banco de dados (o arquivo `moradia.db`)
- `start.py` — o que o atalho executa: prepara o ambiente na primeira vez, pergunta A ou B
  e chama `collect.py` / `app.py`
- `iniciar.command` / `iniciar.cmd` — atalhos clicáveis (Mac / Windows); ambos apenas
  chamam o `start.py`
