# 🏠 Moradia perto do MASP

Um programa que procura apartamentos para **alugar** em São Paulo, guarda tudo num banco
de dados no seu computador e mostra um **relatório com mapa e tabela**, já ordenado por
**custo-benefício** (quanto mais barato e mais perto do metrô, melhor).

O ponto de referência é o **MASP** (Avenida Paulista, 1578). O programa roda inteiro na
sua máquina: nada é enviado para a internet além das buscas nos sites de mapas e de
imóveis.

---

## Índice

1. [Baixar o programa](#1-baixar-o-programa)
2. [Instalar o Python](#2-instalar-o-python)
3. [Usar (duplo-clique)](#3-usar-duplo-clique)
4. [Se alguma coisa der errado](#4-se-alguma-coisa-der-errado)
5. [Como usar o relatório](#5-como-usar-o-relatório)
6. [A nota de custo-benefício (score)](#6-a-nota-de-custo-benefício-score)
7. [Manutenção: comandos extras](#7-manutenção-comandos-extras)
8. [Como ajustar a busca](#8-como-ajustar-a-busca)
9. [Usando pelo terminal (alternativa ao atalho)](#9-usando-pelo-terminal-alternativa-ao-atalho)
10. [O que tem em cada arquivo](#10-o-que-tem-em-cada-arquivo)
11. [Cuidados](#11-cuidados)
12. [**Cola: todos os comandos**](#12-cola-todos-os-comandos)

---

## 1. Baixar o programa

O projeto fica no GitHub: **https://github.com/bruno-lindquist/moradia**

1. Abra o endereço acima no navegador.
2. Clique no botão verde **`Code`** e depois em **`Download ZIP`**.
3. Ache o arquivo baixado (normalmente na pasta **Downloads**) e **descompacte**:
   - **Mac**: duplo-clique no `.zip`.
   - **Windows**: botão direito no `.zip` → **Extrair tudo**.
4. Você vai ficar com uma pasta chamada `moradia-main` (ou `moradia`). **Mova essa pasta
   para um lugar fixo**, por exemplo a Área de Trabalho ou a pasta Documentos. É de dentro
   dela que tudo acontece, e o banco de dados com suas notas fica lá dentro.

> **Não trabalhe com a pasta ainda dentro do `.zip`.** No Mac e no Windows, dar duplo-clique
> em algo que está dentro do zip roda numa pasta temporária e você perde as alterações.

> **Quem usa Git** pode simplesmente rodar `git clone https://github.com/bruno-lindquist/moradia.git`.

O banco de dados (`moradia.db`) vem junto no download, já com os imóveis, os bairros e as
notas registradas até agora.

---

## 2. Instalar o Python

O programa é escrito em Python, então o Python precisa estar instalado no computador.

- Baixe em: **https://www.python.org/downloads/**
- Versão: **3.10, 3.11, 3.12 ou 3.13**. A **3.14 ainda não serve** (quebra a instalação das
  bibliotecas). Se a página oferecer a 3.14, procure a 3.13 na lista de versões mais abaixo.
- **No Windows**, durante a instalação, marque a caixinha **"Add Python to PATH"** na
  primeira tela. Sem ela, o computador não acha o Python depois.
- **No Mac**, é só abrir o instalador e ir clicando em continuar.

Se você já tem Python instalado, não precisa fazer nada: o programa procura sozinho uma
versão compatível entre as que existirem na máquina.

---

## 3. Usar (duplo-clique)

Dentro da pasta do projeto, dê **duplo-clique** no atalho do seu sistema:

- **Mac**: `iniciar.command`
- **Windows**: `iniciar.cmd`

Uma janela preta (o terminal) vai abrir. **Não feche essa janela**: é ela que mostra o que
está acontecendo.

**Na primeira vez**, o atalho prepara tudo sozinho: cria o ambiente isolado do projeto,
instala as bibliotecas e baixa o navegador usado na busca. Isso leva alguns minutos e
baixa cerca de **150 MB**. Nas vezes seguintes ele abre em segundos, porque só repete a
instalação quando a lista de bibliotecas muda.

Depois ele pergunta o que você quer fazer:

- **A) Buscar imóveis**: vai na internet, atualiza os anúncios e os preços, e depois abre
  o relatório. Um navegador (Chrome) vai abrir e navegar sozinho durante a busca: **isso é
  normal**, é o programa trabalhando. Pode demorar bastante, dependendo de quantos bairros
  estão ativos.
- **B) Ver o relatório**: abre direto, com os dados que já estão salvos. É a opção do dia a dia.

O navegador abre sozinho no relatório (`http://localhost:8765`). Para parar, volte à janela
preta e aperte **Ctrl + C**, ou simplesmente feche a janela.

> ⚠️ **Depois de cada busca (opção A), vale rodar `python commute.py`.** Esse comando
> calcula o tempo a pé até o metrô, que sozinho vale 35 dos 139 pontos do ranking. Sem ele,
> os imóveis recém-encontrados aparecem lá embaixo mesmo sendo bons. Como fazer:
> [seção 12, a cola dos comandos](#12-cola-todos-os-comandos).

> Clicar no atalho de novo com o relatório já aberto não estraga nada: ele percebe que já
> está no ar e só traz a página de volta ao navegador.

> **O mapa precisa de internet** para carregar as imagens do mapa e a biblioteca que o
> desenha. Sem conexão, a tabela funciona, mas o mapa fica em branco.

---

## 4. Se alguma coisa der errado

**"Python não encontrado"**
Instale pelo passo 2 e clique no atalho de novo. No Windows, o motivo mais comum é ter
esquecido a caixinha **"Add Python to PATH"**: se foi isso, desinstale e instale de novo
marcando a caixinha.

**Mac: o sistema barra o duplo-clique ("não pode ser aberto porque é de um desenvolvedor
não identificado")**
Na primeira vez, clique no arquivo `iniciar.command` com o **botão direito → Abrir**, e
confirme. Depois disso o duplo-clique passa a funcionar normalmente.

**Mac: o atalho abre num editor de texto em vez de rodar**
Acontece quando o projeto chegou dentro de um `.zip`, que apaga a permissão de execução.
Abra o app **Terminal**, digite `chmod +x ` (com espaço no fim), **arraste o arquivo
`iniciar.command` para dentro da janela do Terminal** e aperte Enter. Depois disso, o
duplo-clique funciona.

**A busca não acha nada / o navegador abre e fecha sem coletar**
O QuintoAndar muda o site de tempos em tempos e isso quebra a leitura dos anúncios. Não
tem solução pelo atalho: é preciso ajustar o arquivo `scraper.py`.

**A janela fecha sozinha antes de eu conseguir ler**
Não deveria: todo erro do programa termina com "Aperte Enter para fechar". Se fechar mesmo
assim, abra o atalho pelo terminal para a mensagem ficar na tela.

**Mudei os dados e o relatório continua igual**
O relatório é montado quando a página carrega. Atualize a página (F5). Se ainda assim não
mudar, pare o servidor (Ctrl + C) e abra de novo.

---

## 5. Como usar o relatório

O relatório tem duas partes: o **mapa** em cima e a **tabela** embaixo. Tudo que você marca
é salvo no banco na hora e não se perde ao fechar.

### O mapa

- Cada imóvel é um **pin numerado** com a posição dele na lista.
- A **cor** vem da nota de custo-benefício: verde (bom), âmbar (médio), vermelho (ruim).
- Imóveis com **nota 4 ou 5 estrelas** ficam com o pin **dourado**.
- O pin 📍 grande marca o **MASP**.
- As **linhas coloridas** são o metrô e a CPTM; os símbolos Ⓜ️ (metrô) e 🔶 (trem) são as
  estações. Clique numa linha ou numa estação para ver o nome.
- Pins muito próximos se **agrupam** num círculo com a contagem. Aproxime o zoom para separá-los.
- **Clique num pin** para rolar até a linha correspondente da tabela (ela pisca).
- **Passe o mouse numa linha** da tabela para o pin dela se destacar no mapa.

### As estrelas (sua opinião sobre o imóvel)

Primeira coluna da tabela:

- **Clique numa estrela** → dá a nota de **1 a 5**. Clicar de novo na mesma estrela **apaga**
  a nota. A nota entra no cálculo do score (vale até 5 pontos).
- **Clique com o botão direito** numa estrela → marca um **traço (–)**, que significa "já
  olhei, não me interessou". É só uma marcação: **não muda o score**. Imóveis marcados
  assim **somem do mapa**, mas continuam na tabela. Botão direito no traço desmarca.
  *(Se o imóvel já tiver estrelas, o botão direito é ignorado.)*

### Os outros botões e colunas

| Coluna | O que é |
|---|---|
| **#** | posição no ranking |
| **Score** | a nota de custo-benefício (ver seção 6) |
| **Total** | aluguel + condomínio + IPTU. Mostra um tracinho quando o site não informou |
| **🚇** | minutos **a pé** até a estação de metrô/trem mais próxima. Passe o mouse para ver o nome da estação. Vazio = ainda não calculado |
| **Qt.** | número de quartos |
| **Área** | metros quadrados |
| **🛋️ ↑** | mobiliado e andar (o `↑4` aparece só a partir do 4º andar) |
| **ícones** | as amenidades (ver abaixo) |
| **↓ ↑ R$** | variação de preço desde o primeiro registro |
| **Endereço** | link para o anúncio. A última linha clicada fica marcada |
| **Cód.** | o código do imóvel no QuintoAndar, também com link |
| **✕** | esconde o anúncio (ele some da lista) |
| **↩** | aparece no modo "Só ocultos": traz o anúncio de volta |

**Clique no cabeçalho de qualquer coluna** para ordenar por ela; clique de novo para
inverter a ordem.

### Marcar amenidades à mão

O site não informa se tem piscina, fogão, cama etc. Você marca à mão: **clique com o botão
direito** na célula do ícone. Cada botão direito avança um estado:

**vazio (não verifiquei) → ícone aceso (tem) → ícone apagado (não tem) → vazio**

Só o estado **"tem"** soma pontos no score. O mesmo vale para a coluna **🛋️ mobiliado**,
com um detalhe: marcar mobiliado à mão **protege** esse valor, ou seja, a próxima busca não
sobrescreve o que você decidiu.

Amenidades disponíveis e quanto valem:

| Ícone | Amenidade | Pontos |
|:---:|---|---:|
| 🔥 | Fogão | 5 |
| ❄️ | Geladeira | 5 |
| 📡 | Micro-ondas | 5 |
| 🥂 | Armário de cozinha | 5 |
| 🛌🏻 | Cama | 5 |
| 👕 | Guarda-roupas | 5 |
| 𖣘 | Ar-condicionado | 5 |
| 💻 | Workspace | 5 |
| 🏊 | Piscina | 5 |
| 🏋️ | Academia | 3 |
| 🧖 | Sauna | 3 (não tem coluna na tabela, só pontua) |
| 🚲 | Bicicletário | 0 (aparece, mas não pontua) |

### Os filtros (no topo)

Funcionam na hora, sem recarregar a página, e valem para a tabela **e** para os pins.

- **Só mobiliado** / **Só com nota**: mostra apenas esses.
- **Esconder vistos**: some com os marcados com o traço.
- **Perto + barato**: reordena por proximidade em faixas de 500 m e, dentro da mesma faixa,
  do mais barato para o mais caro. Enquanto estiver ligado, clicar no cabeçalho não reordena.
- **Distância … km**: teto de distância em linha reta até o MASP.
- **Total R$**: teto de valor total. Imóveis sem valor total informado saem quando há teto.
- **End.**: busca por trecho do endereço (ignora acento e maiúscula).
- **Só ocultos**: mostra apenas os anúncios escondidos com o ✕, para você revê-los e
  restaurá-los com o ↩.

À direita fica a contagem: quantos imóveis estão aparecendo, de quantos no total.

---

## 6. A nota de custo-benefício (score)

Cada imóvel ganha uma **nota em pontos**: quanto **maior, melhor**. O máximo possível hoje é
**139 pontos**. As faixas são **fixas** (não dependem dos outros imóveis da lista), então a
nota de um apartamento não muda quando outro entra ou sai, e dá para comparar rankings de
dias diferentes.

| Pontos | Critério | O que dá a pontuação cheia |
|---:|---|---|
| **35** | Valor total mensal (aluguel + condomínio + IPTU) | R$ 1.800 ou menos. Em R$ 3.000 zera |
| **35** | Tempo **a pé** até a estação de metrô/trem mais próxima | 5 minutos ou menos. Em 25 minutos zera |
| **10** | É mobiliado | se for mobiliado |
| **5** | Sua nota de estrelas | proporcional às estrelas (5 estrelas = 5 pontos) |
| **3** | Fica no 4º andar ou acima | se for andar alto |
| **51** | Amenidades marcadas à mão | soma dos pontos de cada uma (tabela da seção 5) |

Detalhes que valem saber:

- **Quem fica de fora do relatório**: imóveis com valor total **acima de R$ 3.000** ou
  **abaixo de R$ 1.800**, e imóveis a **mais de 25 minutos a pé** da estação. Imóveis cujo
  tempo até a estação ainda não foi calculado **não** são eliminados.
- Se o site não informar o valor total, o programa usa o **aluguel** como aproximação.
- O tempo até a estação só existe depois que o `commute.py` roda (veja a seção 7). Sem ele,
  o imóvel fica com **zero** nos 35 pontos do metrô, o que joga o score para baixo.
- **Vaga de garagem** e **aceita pet** são coletados e guardados, mas **não entram no score**.
- Anúncios escondidos com o ✕ continuam sendo pontuados: eles só somem da tela.

> Os pesos e as faixas ficam no arquivo `ranking.py` (`POINTS_PRICE`, `POINTS_STATION`,
> `POINTS_FURNISHED`, `POINTS_FLOOR`, `POINTS_RATING`, `PRICE_MIN`, `PRICE_MAX`,
> `STATION_MIN_MINUTES`, `STATION_MAX_MINUTES`). Os pontos de cada amenidade ficam na tabela
> `amenidades`, dentro do banco.

---

## 7. Manutenção: comandos extras

Estes comandos **não** têm atalho clicável: rodam pelo terminal, com o ambiente do projeto
ativado (veja a seção 9). Nenhum é obrigatório para o uso normal, mas o primeiro faz
diferença grande no ranking.

### Calcular o tempo até o metrô (o mais importante)

```bash
python commute.py
```

Calcula o tempo **a pé até a estação** de metrô/trem mais próxima de cada imóvel e grava no
banco. **Vale muito rodar depois de cada busca**, porque esse tempo é 35 dos 139 pontos do
score: sem ele, um imóvel ótimo aparece lá embaixo no ranking. Ele pula quem já tem o tempo
calculado e agrupa imóveis no mesmo endereço numa consulta só, então é rápido a partir da
segunda vez.

### Corrigir a localização e checar seus favoritos

```bash
python fix_coords.py
```

Reabre a página de cada imóvel **que tem nota de estrelas**, do maior score para o menor, e:
corrige a localização exata no mapa (o endereço do site não tem número, então a posição
inicial é aproximada), registra o preço atual e **detecta anúncios que saíram do ar** (que
passam a ficar ocultos). Bom rodar de vez em quando nos seus favoritos.

Para testar antes, dá para limitar a quantidade. Este processa só o primeiro colocado:

```bash
python fix_coords.py 1
```

### Ver o ranking sem abrir o navegador

```bash
python ranking.py
```

Mostra o ranking direto no terminal, sem mapa, com a variação de preço de cada imóvel.

### Enxugar o histórico de preços (raro)

```bash
python limpar_precos.py
```

Manutenção rara: deixa no histórico só os pontos em que o preço de fato mudou. Faz um
backup do banco antes de apagar qualquer coisa.

---

## 8. Como ajustar a busca

### No arquivo `config.py` (abra com qualquer editor de texto)

- **Faixa de preço e de tamanho da busca**: `PRICE_MIN`, `PRICE_MAX`, `AREA_MIN`, `AREA_MAX`.
  Esses valores montam o filtro que vai na URL do QuintoAndar (`RENT_FILTERS`) e também
  descartam o que o site insiste em mostrar fora do filtro. *Atenção: essa faixa é a da
  busca; a faixa que pontua e elimina no ranking é outra, e fica no `ranking.py`.*
- **Outro ponto de referência**: `REFERENCE_NAME`, `REFERENCE_LAT` e `REFERENCE_LON`.
- **Ver ou não o navegador durante a busca**: `HEADLESS = False` abre o Chrome visível
  (padrão, bom para acompanhar); `True` roda escondido.
- **Quantidade de imóveis por bairro**: `MAX_LOAD_MORE_CLICKS` (cada clique em "Ver mais"
  traz cerca de 12 imóveis).

### No arquivo `ranking.py`

Os **pesos** do score e as **faixas** de preço e de tempo até a estação (veja a seção 6).

### Os bairros pesquisados

Ficam **no banco de dados**, na tabela `bairros`, não em arquivo de texto. Cada bairro tem um
`slug` (o nome como aparece na URL do QuintoAndar) e um campo `ativo`: só os ativos entram na
busca. Hoje são 10 cadastrados, 9 ativos. Há um levantamento de bairros candidatos, com
distância até o MASP e quantidade de imóveis, em `docs/bairros-candidatos.md`.

---

## 9. Usando pelo terminal (alternativa ao atalho)

O atalho já faz tudo isso sozinho. Os comandos abaixo servem para quem quer rodar à mão ou
precisa dos comandos extras da seção 7.

**Preparar o ambiente (uma vez só)**, dentro da pasta do projeto:

```bash
# Mac (Terminal). No Windows (PowerShell), troque "python3" por "python"
# e "source .venv/bin/activate" por ".venv\Scripts\activate"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

> Se o `pip install` der erro, provavelmente o `python3` da sua máquina é a versão 3.14, que
> ainda não funciona aqui. Instale o **Python 3.13** e refaça usando `python3.13 -m venv .venv`.

**No dia a dia**, com o ambiente ativado:

```bash
python collect.py   # busca e atualiza os imóveis na internet
python commute.py   # calcula o tempo a pé até a estação (rode depois do collect)
python app.py       # abre o relatório em http://localhost:8765
```

Para parar o relatório, aperte **Ctrl + C** no terminal.

> **Por que a porta 8765?** É só um número de endereço interno do seu computador. Um número
> incomum evita conflito com outros programas (a 5000 é usada pelo AirPlay do Mac, a 8000
> pelo Docker).

---

## 10. O que tem em cada arquivo

**Atalhos e preparação**

- `iniciar.command` / `iniciar.cmd`: os atalhos clicáveis (Mac / Windows). Só acham o
  Python e chamam o `start.py`.
- `start.py`: toda a lógica dos atalhos (cria o ambiente, instala as bibliotecas, mostra o
  menu A/B e chama `collect.py` / `app.py`).
- `requirements.txt`: a lista de bibliotecas (playwright, geopy, flask).

**Os comandos**

- `collect.py`: busca os imóveis na internet e grava no banco.
- `app.py`: servidor local que abre o relatório interativo no navegador.
- `commute.py`: calcula o tempo a pé até a estação mais próxima.
- `fix_coords.py`: corrige a localização, atualiza o preço e detecta anúncios fora do ar.
- `ranking.py`: mostra o ranking no terminal **e** contém o cálculo do score.
- `limpar_precos.py`: manutenção rara do histórico de preços.

**As peças internas**

- `config.py`: as configurações (faixa de busca, ponto de referência, pausas).
- `scraper.py`: lê os anúncios do QuintoAndar (a parte que quebra quando o site muda).
- `geo.py`: descobre as coordenadas dos endereços e calcula a distância até a referência.
- `database.py`: a camada de acesso ao banco.
- `amenities.py`: carrega a lista de amenidades (definida na tabela `amenidades` do banco).

**A interface e os dados**

- `report.html`: a estrutura da página do relatório.
- `static/report.css`: a aparência do relatório.
- `static/report.js`: o que torna o relatório interativo (mapa, filtros, estrelas).
- `moradia.db`: **o banco de dados**, com imóveis, preços, bairros, amenidades e suas notas.
- `transit.json`: as linhas e estações de metrô/CPTM desenhadas no mapa.
- `docs/bairros-candidatos.md`: levantamento de bairros para eventualmente incluir na busca.

---

## 11. Cuidados

- **`moradia.db` é o arquivo mais importante.** Ele guarda suas notas, os anúncios escondidos
  e as amenidades marcadas. Faça uma cópia dele de vez em quando (basta copiar e colar o
  arquivo). Se apagar, perde tudo isso.
- **Não mova arquivos soltos para fora da pasta**: o programa espera todos juntos, na mesma
  pasta.
- **A busca é lenta de propósito.** O programa espera alguns segundos entre as ações para não
  parecer um robô e acabar bloqueado pelo site. Buscar em muitos bairros leva bastante tempo.
- **O QuintoAndar pode mudar o site a qualquer momento** e isso quebra a coleta. Não é erro
  de instalação: é o site que mudou, e o `scraper.py` precisa ser ajustado.
- **A pasta `.venv`** é o ambiente criado na primeira execução. Se algo der muito errado na
  instalação, apagar essa pasta e clicar no atalho de novo refaz tudo do zero, sem tocar nos
  seus dados.

---

## 12. Cola: todos os comandos

Para o uso normal você **não precisa de nenhum comando**: é só o duplo-clique no
`iniciar.command` (Mac) ou `iniciar.cmd` (Windows). Esta lista é para quando precisar.

### O básico

| O que eu quero | Como faço |
|---|---|
| Abrir o programa | duplo-clique em **`iniciar.command`** (Mac) ou **`iniciar.cmd`** (Windows) |
| Ver o relatório no navegador | **http://localhost:8765** |
| Parar o programa | **Ctrl + C** na janela preta, ou fechar a janela |
| Atualizar a página do relatório | **F5** |

### Pelo terminal

Antes de qualquer comando, entre na pasta do projeto e **ative o ambiente**:

```bash
# Mac
cd caminho/da/pasta/moradia
source .venv/bin/activate
```

```powershell
# Windows (PowerShell)
cd caminho\da\pasta\moradia
.venv\Scripts\activate
```

Depois, o comando que você quiser:

```bash
python collect.py        # busca e atualiza os imóveis na internet
python commute.py        # calcula o tempo a pé até a estação (rode depois do collect)
python app.py            # abre o relatório em http://localhost:8765
python ranking.py        # mostra o ranking no terminal, sem mapa
python fix_coords.py     # corrige a localização e o preço dos imóveis com nota
python limpar_precos.py  # enxuga o histórico de preços (raro)
```

Se for a primeira vez naquele computador e o ambiente ainda não existir, veja a
[seção 9](#9-usando-pelo-terminal-alternativa-ao-atalho).
