# ENTRYPOINT 3: gera uma pagina HTML (relatorio.html) com MAPA + tabela a partir do banco.
# Rode com:  python relatorio.py
# Depois o arquivo abre sozinho no navegador.
#
# Reaproveita a logica de score e variacao do analisar.py (nao duplica calculo).
# A pagina mostra os imoveis de aluguel num mapa + tabela ordenavel.
# Mapa: Leaflet + OpenStreetMap (gratuito, sem chave de API).

import json
import webbrowser
from pathlib import Path

import analisar
import config
import db

ARQUIVO_SAIDA = "relatorio.html"


def _coletar_dados(conexao, operacao):
    # Monta a lista de imoveis (com score e variacao) pronta para virar JSON.
    # Ja vem ordenada por score. Descarta o que esta alem do raio (config.DISTANCIA_MAX_KM).
    imoveis = analisar._calcular_scores(analisar._carregar(conexao, operacao))
    imoveis = [i for i in imoveis if i["distancia_km"] <= config.DISTANCIA_MAX_KM]
    return [
        {
            "id": imovel["id"],
            "nota": imovel.get("nota", 0),
            "score": imovel["score"],
            "valor": imovel["valor"],
            "valor_total": imovel.get("valor_total"),
            "preco_m2": round(imovel["preco_m2"]),
            "distancia_km": imovel["distancia_km"],
            "quartos": imovel["quartos"],
            "area_m2": round(imovel["area_m2"]),
            "vagas": imovel.get("vagas") or 0,
            "mobiliado": imovel.get("mobiliado"),
            "andar": imovel.get("andar"),
            "aceita_pet": imovel.get("aceita_pet"),
            "endereco": imovel["endereco"] or "",
            "url": (imovel["url"] or "").split("?")[0],
            "lat": imovel["latitude"],
            "lon": imovel["longitude"],
            "variacao": analisar._variacao(conexao, imovel["id"]),
        }
        for imovel in imoveis
    ]


def gerar_html(conexao):
    dados = {
        "aluguel": _coletar_dados(conexao, "aluguel"),
        "shopping": {
            "nome": config.SHOPPING_NOME,
            "lat": config.SHOPPING_LAT,
            "lon": config.SHOPPING_LON,
        },
    }
    # json.dumps com ensure_ascii=False preserva acentos no HTML
    pagina = _PAGINA.replace("{{DADOS}}", json.dumps(dados, ensure_ascii=False))
    return pagina.replace("{{NOTA_DESTAQUE}}", str(analisar.NOTA_DESTAQUE))


def main():
    conexao = db.conectar()
    db.criar_tabelas(conexao)
    pagina = gerar_html(conexao)
    conexao.close()

    Path(ARQUIVO_SAIDA).write_text(pagina, encoding="utf-8")
    caminho = Path(ARQUIVO_SAIDA).resolve()
    print(f"Relatorio gerado: {caminho}")
    webbrowser.open(caminho.as_uri())


_PAGINA = """<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Moradia perto do Shopping Morumbi</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
          integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <style>
    /* Tema escuro */
    body { font-family: -apple-system, Arial, sans-serif; margin: 24px;
           color: #e6e6e6; background: #1a1d21; }
    h1 { font-size: 22px; }
    .controles { margin: 16px 0; }
    select { font-size: 15px; padding: 6px 10px; background: #2a2e34; color: #e6e6e6;
             border: 1px solid #444; border-radius: 4px; }
    /* O wrapper e sticky (o Leaflet sobrescreve o position do #mapa interno, por isso
       prendemos o container externo). O mapa "gruda" no topo ao rolar a lista. */
    .mapa-wrap { position: sticky; top: 0; z-index: 500;
                 background: #1a1d21; padding-bottom: 12px; margin-bottom: 12px; }
    #mapa { height: 360px; border-radius: 8px; }
    table { border-collapse: collapse; width: 100%; font-size: 14px; }
    th, td { padding: 8px 18px; border-bottom: 1px solid #333; text-align: left; }
    /* thead sticky logo abaixo do mapa (360px), para os titulos seguirem visiveis */
    thead th { position: sticky; top: 360px; z-index: 400; }
    th { background: #2a2e34; cursor: pointer; user-select: none; white-space: nowrap; }
    th:hover { background: #353a42; }
    tbody tr:hover { background: #23272e; }
    a { color: #5aa9ff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .caiu { color: #4cd07d; font-weight: bold; }
    .subiu { color: #ff6b5e; font-weight: bold; }
    .estavel, .novo { color: #888; }
    .desativar { border: none; background: none; color: #ff6b5e; cursor: pointer;
                 font-size: 15px; padding: 2px 6px; border-radius: 4px; }
    .desativar:hover { background: #3a2422; }
    /* 5 estrelas de nota: cinza apagado por padrao, dourada quando preenchida */
    .estrelas { white-space: nowrap; }
    .estrela { color: #555; cursor: pointer; font-size: 16px; line-height: 1; }
    .estrela.on { color: #ffc83d; }
    .estrela:hover { color: #ffe08a; }
    /* "visto" (botao direito): um traco no lugar das estrelas, so para marcar
       que o imovel ja foi olhado, sem dar nota. Nao entra no score. */
    .visto { color: #888; cursor: pointer; font-size: 16px; line-height: 1; }
    .visto:hover { color: #bbb; }
    /* linha de imovel bem avaliado (nota alta): fundo amarelo escuro */
    tr.linha-nota-alta td { background: #332f1a; }
    .contagem { font-size: 13px; font-weight: normal; color: #999; }
    .rodape { margin-top: 28px; font-size: 12px; color: #888; }
    .pin-num { background: #2a2e34; color: #e6e6e6; border: 2px solid #888; border-radius: 50%;
               width: 26px; height: 26px; line-height: 22px; text-align: center;
               font-weight: bold; font-size: 12px; }
    .pin-nota-alta { border-width: 3px; box-shadow: 0 0 0 2px #ffc83d; }
  </style>
</head>
<body>
  <h1>🏠 Moradia perto do Shopping Morumbi</h1>

  <div class="controles">
    <strong>Aluguel</strong> (filtros aplicados na busca)
    <span class="contagem" id="resumo"></span>
  </div>

  <div class="mapa-wrap">
    <div id="mapa"></div>
  </div>

  <table id="tabela">
    <thead>
      <tr>
        <th></th><th>#</th><th>Score</th><th>Total</th><th>Distância</th>
        <th>Quartos</th><th>Área</th><th>Vagas</th><th>Mobiliado</th><th>Andar</th><th>Pet</th><th>Variação</th><th>Endereço</th><th>Cód.</th><th></th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>

  <p class="rodape">
    Ordenado por custo-benefício (60% preço/m² + 40% distância). Clique num cabeçalho para reordenar.
    Imóveis sem coordenada não aparecem no mapa, mas continuam na tabela.
    Gerado de moradia.db — rode <code>python coletar.py</code> para atualizar.
  </p>

  <script>
    const DADOS = {{DADOS}};
    const SHOPPING = DADOS.shopping;
    const NOTA_DESTAQUE = {{NOTA_DESTAQUE}};  // nota a partir da qual destaca linha/pin

    // Cor do pin conforme o score: verde (bom) -> amarelo -> vermelho (ruim)
    function corPorScore(score) {
      if (score >= 66) return '#1a8a3a';
      if (score >= 33) return '#e0a800';
      return '#c0392b';
    }

    function classeVariacao(texto) {
      if (texto.startsWith('caiu')) return 'caiu';
      if (texto.startsWith('subiu')) return 'subiu';
      if (texto === 'novo') return 'novo';
      return 'estavel';
    }

    // Cria um <td> com texto seguro (textContent). 'ordenavel' vai em data-valor
    // para a ordenacao usar o numero. 'tag' opcional embrulha o texto (ex.: strong).
    function celula(texto, ordenavel, tag) {
      const td = document.createElement('td');
      if (ordenavel !== undefined) td.dataset.valor = ordenavel;
      if (tag) {
        const elemento = document.createElement(tag);
        elemento.textContent = texto;
        td.appendChild(elemento);
      } else {
        td.textContent = texto;
      }
      return td;
    }

    // --- Mapa ---
    const mapa = L.map('mapa').setView([SHOPPING.lat, SHOPPING.lon], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap', maxZoom: 19
    }).addTo(mapa);

    // Pin do shopping (estrela vermelha grande)
    L.marker([SHOPPING.lat, SHOPPING.lon], {
      icon: L.divIcon({ html: '⭐', className: '', iconSize: [30, 30] })
    }).addTo(mapa).bindPopup('<b>' + SHOPPING.nome + '</b>');

    let camadaPins = L.layerGroup().addTo(mapa);
    let marcadores = {};   // indice da linha -> marcador, para o hover da tabela

    // Escapa texto antes de injetar em HTML (defesa contra XSS no balao do mapa)
    function esc(texto) {
      const div = document.createElement('div');
      div.textContent = texto;
      return div.innerHTML;
    }

    function balao(imovel, posicao) {
      const total = imovel.valor_total != null
        ? 'R$ ' + imovel.valor_total.toLocaleString('pt-BR') + ' total'
        : 'R$ ' + imovel.valor.toLocaleString('pt-BR') + ' aluguel';
      const mob = imovel.mobiliado === 1 ? ' · mobiliado'
                : imovel.mobiliado === 0 ? ' · sem mobília' : '';
      const andar = imovel.andar != null ? ' · ' + imovel.andar + 'º andar' : '';
      const pet = imovel.aceita_pet === 0 ? ' · não aceita pet'
                : imovel.aceita_pet === 1 ? ' · aceita pet' : '';
      return '<b>#' + posicao + ' — score ' + imovel.score + '</b><br>' +
             total + ' (' + imovel.preco_m2 + '/m²)<br>' +
             imovel.quartos + ' quarto(s), ' + imovel.area_m2 + ' m², ' + imovel.vagas + ' vaga(s)' + mob + '<br>' +
             imovel.distancia_km + ' km do shopping' + andar + pet + '<br>' +
             '<a href="' + esc(imovel.url) + '" target="_blank">ver anúncio ↗</a>';
    }

    // --- Renderizacao (mapa + tabela) para a operacao escolhida ---
    function renderizar(operacao) {
      const lista = DADOS[operacao];
      camadaPins.clearLayers();
      marcadores = {};

      // Pins no mapa (so quem tem coordenada)
      const pontos = [[SHOPPING.lat, SHOPPING.lon]];
      lista.forEach(function (imovel, indice) {
        if (imovel.lat == null || imovel.lon == null) return;
        const posicao = indice + 1;
        const notaAlta = (imovel.nota || 0) >= NOTA_DESTAQUE;
        const corPin = notaAlta ? '#f5a623' : corPorScore(imovel.score);
        const classePin = 'pin-num' + (notaAlta ? ' pin-nota-alta' : '');
        const marcador = L.marker([imovel.lat, imovel.lon], {
          icon: L.divIcon({
            className: '',
            html: '<div class="' + classePin + '" style="border-color:' + corPin + '">' + posicao + '</div>',
            iconSize: [26, 26]
          })
        }).bindPopup(balao(imovel, posicao));
        camadaPins.addLayer(marcador);
        marcadores[indice] = marcador;
        pontos.push([imovel.lat, imovel.lon]);
      });
      // Enquadra o mapa em todos os pontos
      if (pontos.length > 1) mapa.fitBounds(pontos, { padding: [40, 40] });

      // Tabela. Usamos textContent (nao innerHTML) para evitar XSS: assim,
      // qualquer "<" vindo do endereco do site vira texto, nunca codigo executavel.
      const corpo = document.querySelector('#tabela tbody');
      corpo.replaceChildren();
      lista.forEach(function (imovel, indice) {
        const posicao = indice + 1;
        const tr = document.createElement('tr');

        // Linha destacada se a nota for alta
        if ((imovel.nota || 0) >= NOTA_DESTAQUE) tr.classList.add('linha-nota-alta');

        // 1a coluna: 5 estrelas de nota. Clicar na estrela N da nota N; clicar na
        // estrela igual a nota atual zera (tira a nota).
        const tdEstrelas = document.createElement('td');
        tdEstrelas.className = 'estrelas';
        montarEstrelas(tdEstrelas, imovel, tr);
        tr.appendChild(tdEstrelas);

        tr.appendChild(celula(posicao, posicao));
        tr.appendChild(celula(imovel.score, imovel.score, 'strong'));
        // Total (valor cheio). Aluguel e R$/m2 nao sao mais exibidos.
        const textoTotal = imovel.valor_total != null
          ? 'R$ ' + imovel.valor_total.toLocaleString('pt-BR') : '—';
        tr.appendChild(celula(textoTotal, imovel.valor_total != null ? imovel.valor_total : 0));
        tr.appendChild(celula(imovel.distancia_km + ' km', imovel.distancia_km));
        tr.appendChild(celula(imovel.quartos, imovel.quartos));
        tr.appendChild(celula(imovel.area_m2 + ' m²', imovel.area_m2));
        // vaga: so mostra se tiver 1+ (0 -> vazio)
        tr.appendChild(celula(imovel.vagas >= 1 ? imovel.vagas : '', imovel.vagas));
        // mobiliado: so mostra "Sim" (positivo); nao/desconhecido -> vazio
        tr.appendChild(celula(imovel.mobiliado === 1 ? 'Sim' : '', imovel.mobiliado === 1 ? 1 : 0));
        // andar: so mostra se for 4o ou acima (positivo); abaixo/desconhecido -> vazio
        const andarBom = imovel.andar != null && imovel.andar >= 4;
        tr.appendChild(celula(andarBom ? imovel.andar + 'º' : '', imovel.andar != null ? imovel.andar : -1));
        // pet: so mostra "Não" (positivo p/ o usuario); sim/desconhecido -> vazio
        tr.appendChild(celula(imovel.aceita_pet === 0 ? 'Não' : '', imovel.aceita_pet === 0 ? 1 : 0));
        // variacao: so mostra se mudou (subiu/caiu); estavel/novo -> vazio
        const mudou = imovel.variacao.startsWith('subiu') || imovel.variacao.startsWith('caiu');
        const tdVar = celula(mudou ? imovel.variacao : '');
        if (mudou) tdVar.className = classeVariacao(imovel.variacao);
        tr.appendChild(tdVar);

        const tdEnd = document.createElement('td');
        const link = document.createElement('a');
        link.href = imovel.url;
        link.target = '_blank';
        link.textContent = imovel.endereco;   // sem seta; textContent evita XSS
        tdEnd.appendChild(link);
        tr.appendChild(tdEnd);

        // Codigo do imovel (ID do QuintoAndar), como link para o anuncio
        const tdCod = document.createElement('td');
        const linkCod = document.createElement('a');
        linkCod.href = imovel.url;
        linkCod.target = '_blank';
        linkCod.textContent = imovel.id;   // textContent evita XSS
        tdCod.appendChild(linkCod);
        tr.appendChild(tdCod);

        // Ultima coluna: botao de desativar (esconder). textContent evita XSS.
        const tdBotao = document.createElement('td');
        const botao = document.createElement('button');
        botao.className = 'desativar';
        botao.textContent = '✕';
        botao.title = 'Não tenho interesse — esconder este anúncio';
        botao.addEventListener('click', function () {
          desativar(imovel.id, tr, marcadores[indice]);
        });
        tdBotao.appendChild(botao);
        tr.appendChild(tdBotao);

        // Hover na linha destaca o pin correspondente
        tr.addEventListener('mouseenter', function () {
          if (marcadores[indice]) marcadores[indice].openPopup();
        });
        corpo.appendChild(tr);
      });

      const semCoord = lista.filter(function (i) { return i.lat == null; }).length;
      document.getElementById('resumo').textContent =
        lista.length + ' imóveis' + (semCoord ? ' (' + semCoord + ' sem coordenada, fora do mapa)' : '');
    }

    // --- Ordenacao por coluna ---
    document.querySelectorAll('#tabela th').forEach(function (cabecalho, indice) {
      cabecalho.addEventListener('click', function () {
        const corpo = document.querySelector('#tabela tbody');
        const linhas = Array.from(corpo.querySelectorAll('tr'));
        const crescente = cabecalho.dataset.ordem !== 'asc';
        cabecalho.dataset.ordem = crescente ? 'asc' : 'desc';
        linhas.sort(function (a, b) {
          const va = a.children[indice].dataset.valor;
          const vb = b.children[indice].dataset.valor;
          let cmp = (va !== undefined && vb !== undefined)
            ? parseFloat(va) - parseFloat(vb)
            : a.children[indice].textContent.localeCompare(b.children[indice].textContent);
          return crescente ? cmp : -cmp;
        });
        linhas.forEach(function (linha) { corpo.appendChild(linha); });
      });
    });

    // Desativa um anuncio: avisa o servidor (grava ativo=0) e some com a linha + pin.
    function desativar(id, tr, marcador) {
      fetch('/desativar/' + id, { method: 'POST' })
        .then(function (resposta) {
          if (!resposta.ok) throw new Error('falha');
          tr.remove();
          if (marcador) camadaPins.removeLayer(marcador);
        })
        .catch(function () {
          alert('Nao foi possivel desativar. O servidor (app.py) esta rodando?');
        });
    }

    // Desenha as estrelas (ou o traco de "visto") refletindo imovel.nota e liga os cliques.
    // nota -1 = visto (traco); 0 = sem nada; 1..5 = estrelas.
    function montarEstrelas(td, imovel, tr) {
      td.replaceChildren();

      // Estado "visto": mostra so um traco. Botao direito de novo volta ao vazio.
      if (imovel.nota === -1) {
        const traco = document.createElement('span');
        traco.className = 'visto';
        traco.textContent = '–';
        traco.title = 'Visto (sem nota). Botão direito para desmarcar.';
        traco.addEventListener('contextmenu', function (e) {
          e.preventDefault();
          darNota(imovel, 0, td, tr);  // desmarca: volta ao vazio
        });
        td.appendChild(traco);
        return;
      }

      for (let n = 1; n <= 5; n++) {
        const estrela = document.createElement('span');
        estrela.className = 'estrela' + (n <= (imovel.nota || 0) ? ' on' : '');
        estrela.textContent = n <= (imovel.nota || 0) ? '★' : '☆';
        estrela.title = 'Dar nota ' + n + ' (botão direito = marcar como visto)';
        estrela.addEventListener('click', function () {
          // clicar na estrela igual a nota atual zera; senao, vira a nota clicada
          const novaNota = imovel.nota === n ? 0 : n;
          darNota(imovel, novaNota, td, tr);
        });
        // Botao direito marca "visto" -- mas so quando ainda nao tem nota (regra 3b).
        estrela.addEventListener('contextmenu', function (e) {
          e.preventDefault();
          if (!imovel.nota) darNota(imovel, -1, td, tr);
        });
        td.appendChild(estrela);
      }
    }

    // Grava a nota no servidor e atualiza estrelas + destaque da linha.
    function darNota(imovel, nota, td, tr) {
      fetch('/nota/' + imovel.id + '/' + nota, { method: 'POST' })
        .then(function (resposta) {
          if (!resposta.ok) throw new Error('falha');
          return resposta.json();
        })
        .then(function (dados) {
          imovel.nota = dados.nota;
          montarEstrelas(td, imovel, tr);
          tr.classList.toggle('linha-nota-alta', imovel.nota >= NOTA_DESTAQUE);
        })
        .catch(function () {
          alert('Nao foi possivel salvar a nota. O servidor (app.py) esta rodando?');
        });
    }

    renderizar('aluguel');
  </script>
</body>
</html>"""


if __name__ == "__main__":
    main()
