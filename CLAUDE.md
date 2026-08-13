# moradia — instruções para o Claude

**Projeto concluído.** MVP pessoal: busca imóveis para alugar perto do MASP
(ponto de referência em `config.py`), salva num SQLite local (`moradia.db`) e mostra
um relatório com mapa e ranking de custo-benefício. Rodando só no Mac do usuário.

Não proponha refatoração, nova feature ou "melhoria" por conta própria — o escopo
está fechado. Só mexa no código quando eu pedir uma mudança específica (bug, ajuste
pontual, ou uso contínuo do dia a dia como coletar/atualizar dados).

## Stack e como rodar

- Python 3.10+, `venv` + `pip` (ou `uv`). Dependências: `requirements.txt` (playwright, geopy, flask).
- `python -m playwright install chromium` na primeira vez.
- Banco: SQLite, arquivo único `moradia.db` (schema em `database.py`).
- Entrypoints:
  - `python collect.py` — busca/atualiza imóveis (scraper QuintoAndar).
  - `python ranking.py` — recalcula score e mostra ranking no terminal.
  - `python app.py` — servidor Flask local (`localhost:8765`) com o relatório interativo (`report.html`, mapa + tabela, permite dar nota e desativar anúncio — precisa do Flask porque grava no banco).
- Atalhos clicáveis: `iniciar.command` (Mac) / `iniciar.cmd` (Windows). Ambos só chamam
  `start.py`, que é a fonte única: cria o `.venv`, instala as dependências na primeira vez
  (marcador `.venv/setup-fingerprint.txt`), pergunta A/B e chama `collect.py` / `app.py`.
  Mudança no fluxo dos atalhos vai em `start.py`, nunca duplicada nos dois lançadores.

## Regras deste projeto

1. **Código e nomes de arquivo em inglês.** Comentários em pt-br, explicativos, objetivos, não redundantes.
2. **Estrutura enxuta**: tudo na raiz, sem pastas tipo `templates/`. Juntar arquivos pequenos e relacionados em vez de fragmentar.
3. **Nunca usar a janela de perguntas (AskUserQuestion)** — sempre perguntas numeradas no texto, opções em letras.
4. **Nunca apagar ou sobrescrever `moradia.db` sem autorização explícita por escrito na conversa** — já aconteceu aqui (bairros apagados sem querer). Para testar mudanças no banco, usar cópia com outro nome. Ver também a regra global equivalente.
5. **`amenities.AMENITIES` é a fonte única** dos pontos de cada amenidade (piscina, academia, sauna etc.) — nunca duplicar esses valores em outro arquivo.

## Score de custo-benefício (`ranking.py`) — cuidado ao mexer

- Soma de pontos com **faixas fixas** (não relativas aos outros imóveis do momento — isso é proposital, permite comparar ranking de dias diferentes).
- Pesos atuais: preço 35, distância 35, mobiliado 10, vaga 6, andar 4º+ 3, nota manual 5, + pontos de amenidades (fonte única `amenities.py`).
- Preço mais baixo = pontuação melhor (inverso). Distância menor = pontuação melhor (inverso).
- Imóveis ativos fora da faixa de preço/distância são **eliminados** do ranking; imóveis ocultos continuam sendo pontuados (a eliminação/filtro é feita por quem chama, não aqui).
- `pet` e `bicicletário` são só exibidos na tabela, **não** entram no score.
- Antes de mudar um peso, pergunte — já mudou de opinião sobre a fórmula mais de uma vez nas sessões anteriores.

## Erros já cometidos aqui (evite repetir)

- Apagar dados do banco sem autorização (bairros sumiram numa sessão). Regra 4 existe por causa disso.
- Amenidades marcadas manualmente não sendo salvas — checar se o commit no banco está de fato acontecendo (não só em memória) sempre que mexer em `amenities.py`/`database.py`.
- Atualização de preço alterando a localização do imóvel por engano — `fix_coords.py`/o fluxo de atualização de preço devem tocar **só** preço, nunca lat/lon.
- Depois de atualizar dados, a página não refletir a mudança sem reiniciar o servidor Flask — se isso acontecer de novo, é sinal de cache/estado não invalidado, não "reiniciar o banco".
- Paginação do scraper quebrando ao mudar filtros na URL (`?pagina=2` + faixa de preço/área) — testar a URL manualmente antes de assumir que está ok.
