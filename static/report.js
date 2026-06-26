// Dados injetados pelo servidor (app.py) num bloco inline do report.html, em window.REPORT.
// Manter este arquivo 100% estatico: nada de Jinja2 aqui, so leitura de REPORT.
const DATA = REPORT.data;
const REFERENCE = DATA.reference;
const HIGHLIGHT_RATING = REPORT.highlight_rating;  // nota a partir da qual destaca linha/pin
// Amenidades exibidas (key/icon/label), na ordem da fonte unica (amenities.py do back).
// Usadas para montar as colunas da tabela, suas celulas e a lista do popup.
const AMENITIES = REPORT.amenities;
const LAST_CLICKED_KEY = 'moradia-ultima-linha-clicada';  // id salvo no localStorage
const MAX_SCORE = REPORT.max_score;  // score maximo possivel (calculado no back, ranking.py)

// Cor do pin conforme o score: verde (bom) -> ambar -> vermelho (ruim).
// Mesmas cores de acento da paleta (verde/ambar/vermelho do tema).
// Cortes nos tercos da escala (derivados de MAX_SCORE, nunca desencontram).
function colorByScore(score) {
  if (score >= MAX_SCORE * 2 / 3) return '#3fc97e';
  if (score >= MAX_SCORE / 3) return '#e0a92e';
  return '#e0625a';
}

function changeClass(text) {
  if (text.startsWith('caiu')) return 'down';
  if (text.startsWith('subiu')) return 'up';
  if (text === 'novo') return 'new';
  return 'stable';
}

// Mostra um aviso curto que some sozinho depois de ~2s
let toastTimer = null;
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 2000);
}

// Cria um <td> com texto seguro (textContent). 'sortable' vai em data-value
// para a ordenacao usar o numero. 'tag' opcional embrulha o texto (ex.: strong).
function cell(text, sortable, tag) {
  const td = document.createElement('td');
  if (sortable !== undefined) td.dataset.value = sortable;
  if (tag) {
    const element = document.createElement(tag);
    element.textContent = text;
    td.appendChild(element);
  } else {
    td.textContent = text;
  }
  return td;
}

// --- Mapa ---
const map = L.map('map').setView([REFERENCE.lat, REFERENCE.lon], 14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap', maxZoom: 19
}).addTo(map);

// Pin do trabalho/shopping (ponto de referencia). O font-size controla o tamanho
// visual do emoji; iconSize e so a caixa. iconAnchor centra a ponta do pin no ponto.
L.marker([REFERENCE.lat, REFERENCE.lon], {
  icon: L.divIcon({
    html: '<div style="font-size: 44px; line-height: 48px; text-align: center;">📍</div>',
    className: '',
    iconSize: [48, 48],
    iconAnchor: [24, 46]
  })
}).addTo(map).bindPopup('<b>' + REFERENCE.name + '</b>');

// Rede de metro/CPTM (transit.json): traçados coloridos das linhas + estacoes.
// Vai num pane proprio abaixo dos pins de imoveis para nao atrapalhar o clique.
// Carrega via fetch porque o arquivo e grande (~300 KB) e nao muda.
map.createPane('transitLines');
map.getPane('transitLines').style.zIndex = 350;  // acima do tile (200), abaixo dos marcadores (600)
fetch('/transit.json')
  .then(function (response) { return response.json(); })
  .then(function (transit) {
    transit.lines.forEach(function (line) {
      line.paths.forEach(function (path) {
        L.polyline(path, {
          color: line.colour, weight: 4, opacity: 0.75, pane: 'transitLines'
        }).addTo(map).bindPopup('<b>' + line.name + '</b>');
      });
    });
    // Ⓜ️ = metro, 🔶 = trem (CPTM). Menores que o pin do shopping.
    transit.stations.forEach(function (station) {
      const emoji = station.type === 'metro' ? 'Ⓜ️' : '🔶';
      L.marker([station.lat, station.lon], {
        icon: L.divIcon({
          html: '<div style="font-size: 16px; line-height: 18px; text-align: center;">' + emoji + '</div>',
          className: '',
          iconSize: [18, 18],
          iconAnchor: [9, 9]
        })
      }).addTo(map).bindPopup('<b>' + station.name + '</b>');
    });
  });

// markerClusterGroup agrupa pins proximos (resolve o amontoado do Brooklin/Campo Belo)
let pinLayer = L.markerClusterGroup({ maxClusterRadius: 45 }).addTo(map);
let markers = {};   // indice da linha -> marcador, para o hover da tabela

// Escapa texto antes de injetar em HTML (defesa contra XSS no balao do mapa)
function esc(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function popup(property, position) {
  const total = property.total_price != null
    ? 'R$ ' + property.total_price.toLocaleString('pt-BR') + ' total'
    : 'R$ ' + property.price.toLocaleString('pt-BR') + ' aluguel';
  const furnished = property.furnished === 1 ? ' · mobiliado'
                  : property.furnished === 0 ? ' · sem mobília' : '';
  const floor = property.floor != null ? ' · ' + property.floor + 'º andar' : '';
  // amenidades presentes (so as marcadas como "tem" = 1), derivadas da fonte unica
  const present = AMENITIES
    .filter(function (amenity) { return property[amenity.key] === 1; })
    .map(function (amenity) { return amenity.icon + ' ' + amenity.label.toLowerCase(); });
  const amenityLine = present.length ? present.join(' · ') + '<br>' : '';
  return '<b>#' + position + ' — score ' + property.score + '</b><br>' +
         total + ' (' + property.price_per_m2 + '/m²)<br>' +
         property.bedrooms + ' quarto(s), ' + property.area_m2 + ' m², ' + property.parking + ' vaga(s)' + furnished + '<br>' +
         property.distance_km + ' km do shopping' + floor + '<br>' +
         amenityLine +
         '<a href="' + esc(property.url) + '" target="_blank">ver anúncio ↗</a>';
}

// Abrevia logradouros no endereco EXIBIDO (nao altera o dado). Palavra inteira (\b),
// sem acento na chave porque os enderecos do site ja vem sem acento (ex.: "Avenida").
function shortAddress(address) {
  return (address || '')
    .replace(/\bAvenida\b/gi, 'Av')
    .replace(/\bRua\b/gi, 'R')
    .replace(/\bJardim\b/gi, 'Jd')

    .replace(/\bSanto\b/gi, 'St')
    .replace(/\bJúnior\b/gi, 'Jr')
    .replace(/\bDoutor\b/gi, 'Dr')
    .replace(/\bProfessor\b/gi, 'Prof')

    .replace(/\bVila\b/gi, 'Vl');
}

// Celula de tempo ate o shopping: "19′ · 6′" (a pe · bike). Vazia quando ainda
// nao calculado (commute.py nao rodou para este imovel). Ordena pelo tempo a pe;
// nao calculados (Infinity) vao para o fim ao ordenar.
function commuteCell(walkMin, bikeMin) {
  const td = document.createElement('td');
  td.className = 'extras';
  if (walkMin != null) {
    td.textContent = walkMin + '′ · ' + (bikeMin != null ? bikeMin + '′' : '–');
    td.title = 'A pé ' + walkMin + ' min · de bike ' + (bikeMin != null ? bikeMin + ' min' : '?');
  }
  td.dataset.value = walkMin != null ? walkMin : Infinity;
  return td;
}

// Celula de "extra": mostra o icone so quando positivo (senao fica vazia).
// 'sortValue' (0/1 ou o numero) permite ordenar a coluna pelo cabecalho.
function extraCell(icon, title, positive, sortValue) {
  const td = document.createElement('td');
  td.className = 'extras';
  if (positive) {
    const span = document.createElement('span');
    span.textContent = icon;
    span.title = title;
    td.appendChild(span);
  }
  td.dataset.value = sortValue;
  return td;
}

// Celula de amenidade manual (piscina/academia/bicicletario/sauna). Botao direito alterna
// 3 estados: nao verificado (null) -> tem (1) -> nao tem (0) -> null. So "tem" pontua.
// Cria o <td> e desenha o estado inicial via drawAmenity.
function amenityCell(property, key, icon, label) {
  const td = document.createElement('td');
  td.className = 'extras amenity';
  td.title = label + ' (botão direito para marcar)';
  td.addEventListener('contextmenu', function (e) {
    e.preventDefault();  // nao abre o menu do navegador
    // ciclo: null -> 1 -> 0 -> null
    const current = property[key];
    const next = current == null ? 1 : current === 1 ? 0 : null;
    setAmenity(property, key, next, td, icon);
  });
  drawAmenity(td, property[key], icon);
  return td;
}

// Desenha o icone da amenidade: aceso (tem), riscado/apagado (nao tem) ou vazio (null).
// Tambem grava data-value para a ordenacao da coluna (1 / 0 / -1).
function drawAmenity(td, value, icon) {
  td.replaceChildren();
  if (value === 1) {
    const span = document.createElement('span');
    span.className = 'amenity-on';
    span.textContent = icon;
    td.appendChild(span);
  } else if (value === 0) {
    const span = document.createElement('span');
    span.className = 'amenity-off';
    span.textContent = icon;
    td.appendChild(span);
  }
  // value null: deixa a celula vazia (mas clicavel)
  td.dataset.value = value === 1 ? 1 : value === 0 ? 0 : -1;
}

// Minusculas e sem acento, para comparar texto de forma tolerante.
// normalize('NFD') separa a letra do acento; o replace apaga so os acentos.
function normalize(text) {
  return (text || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
}

// Aplica os filtros (checkboxes) sobre a lista completa. Retorna so o que passa.
function getFiltered() {
  const onlyParking = document.getElementById('f-parking').checked;
  const onlyFurnished = document.getElementById('f-furnished').checked;
  const onlyRated = document.getElementById('f-rated').checked;
  const hideSeen = document.getElementById('f-hide-seen').checked;
  // Campos numericos vazios viram NaN: tratamos como "sem teto" (Infinity)
  const maxDistance = parseFloat(document.getElementById('f-max-distance').value);
  const maxTotal = parseFloat(document.getElementById('f-max-total').value);
  const distanceLimit = isNaN(maxDistance) ? Infinity : maxDistance;
  const totalLimit = isNaN(maxTotal) ? Infinity : maxTotal;
  // Filtro por endereco: texto vazio = sem filtro. Compara normalizado (sem acento/caixa).
  const addressQuery = normalize(document.getElementById('f-address').value);
  // Toggle "Só ocultos": ligado mostra apenas os ocultos (active 0); desligado, so os ativos.
  const onlyHidden = document.getElementById('f-hidden-toggle').classList.contains('on');
  const nearCheap = document.getElementById('f-near-cheap').checked;
  const filtered = DATA.rentals.filter(function (property) {
    const isHidden = property.active === 0;
    if (onlyHidden ? !isHidden : isHidden) return false;
    if (onlyParking && !(property.parking >= 1)) return false;
    if (onlyFurnished && property.furnished !== 1) return false;
    if (onlyRated && !(property.rating >= 1)) return false;
    if (hideSeen && property.rating === -1) return false;
    if (property.distance_km > distanceLimit) return false;
    // total_price ausente (null): so passa quando nao ha teto de valor
    if (totalLimit !== Infinity && (property.total_price == null || property.total_price > totalLimit)) return false;
    if (addressQuery && !normalize(property.address).includes(addressQuery)) return false;
    return true;
  });
  // "Perto + barato": ordena por distancia (em faixas de 0,5 km) e, dentro da mesma
  // faixa, pelo total mais barato. Faixas porque distancias quase nunca sao iguais
  // (0,93 vs 0,94 km), entao agrupamos antes de comparar preco. Total ausente vai pro fim.
  if (nearCheap) {
    const DISTANCE_BAND_KM = 0.5;
    filtered.sort(function (a, b) {
      const bandA = Math.floor(a.distance_km / DISTANCE_BAND_KM);
      const bandB = Math.floor(b.distance_km / DISTANCE_BAND_KM);
      if (bandA !== bandB) return bandA - bandB;
      const priceA = a.total_price != null ? a.total_price : Infinity;
      const priceB = b.total_price != null ? b.total_price : Infinity;
      return priceA - priceB;
    });
  }
  return filtered;
}

// --- Renderizacao (mapa + tabela) a partir da lista filtrada ---
function render() {
  const list = getFiltered();
  const lastClicked = localStorage.getItem(LAST_CLICKED_KEY);
  pinLayer.clearLayers();
  markers = {};

  // Pins no mapa: so quem tem coordenada E nao esta marcado como "visto" (rating -1),
  // que sai do mapa mas continua na tabela.
  const points = [[REFERENCE.lat, REFERENCE.lon]];
  list.forEach(function (property, index) {
    if (property.lat == null || property.lon == null) return;
    if (property.rating === -1) return;  // "visto" nao aparece no mapa
    const position = index + 1;
    const highRating = (property.rating || 0) >= HIGHLIGHT_RATING;
    const pinColor = highRating ? '#ffcf4d' : colorByScore(property.score);
    const pinClass = 'pin-num' + (highRating ? ' pin-high-rating' : '');
    const marker = L.marker([property.lat, property.lon], {
      icon: L.divIcon({
        className: '',
        html: '<div class="' + pinClass + '" style="border-color:' + pinColor + '">' + position + '</div>',
        iconSize: [26, 26]
      })
    }).bindPopup(popup(property, position));
    // Clicar no pin rola ate a linha correspondente na tabela e a faz piscar.
    marker.on('click', function () { goToRow(index); });
    pinLayer.addLayer(marker);
    markers[index] = marker;
    points.push([property.lat, property.lon]);
  });
  // Enquadra o mapa em todos os pontos
  if (points.length > 1) map.fitBounds(points, { padding: [40, 40] });

  // Tabela. Usamos textContent (nao innerHTML) para evitar XSS: assim,
  // qualquer "<" vindo do endereco do site vira texto, nunca codigo executavel.
  const body = document.querySelector('#table tbody');
  body.replaceChildren();
  list.forEach(function (property, index) {
    const position = index + 1;
    const tr = document.createElement('tr');

    // Linha destacada se a nota for alta
    if ((property.rating || 0) >= HIGHLIGHT_RATING) tr.classList.add('high-rating');
    // Marca a ultima linha cujo link foi clicado (persistida no localStorage)
    if (lastClicked && property.id === lastClicked) tr.classList.add('last-clicked');

    // 1a coluna: 5 estrelas de nota. Clicar na estrela N da nota N; clicar na
    // estrela igual a nota atual zera (tira a nota).
    const tdStars = document.createElement('td');
    tdStars.className = 'stars';
    buildStars(tdStars, property, tr);
    tr.appendChild(tdStars);

    tr.appendChild(cell(position, position));
    tr.appendChild(cell(property.score, property.score, 'strong'));
    // Total (valor cheio).
    const totalText = property.total_price != null
      ? 'R$ ' + property.total_price.toLocaleString('pt-BR') : '—';
    tr.appendChild(cell(totalText, property.total_price != null ? property.total_price : 0));
    tr.appendChild(cell(property.distance_km + ' km', property.distance_km));
    tr.appendChild(commuteCell(property.walk_min, property.bike_min));
    tr.appendChild(cell(property.bedrooms, property.bedrooms));
    tr.appendChild(cell(property.area_m2 + ' m²', property.area_m2));
    // Extras em colunas separadas (sem titulo no cabecalho), so o icone quando positivo
    tr.appendChild(extraCell('🅿️', property.parking + ' vaga(s)', property.parking >= 1, property.parking));
    // Mobiliado: marcavel manualmente (botao direito), igual as amenidades
    tr.appendChild(amenityCell(property, 'furnished', '🛋️', 'Mobiliado'));
    const goodFloor = property.floor != null && property.floor >= 4;
    tr.appendChild(extraCell('↑' + property.floor, 'Andar ' + property.floor + 'º', goodFloor, property.floor != null ? property.floor : -1));
    // Amenidades manuais (clicaveis): derivadas da fonte unica (mesma ordem do cabecalho).
    AMENITIES.forEach(function (amenity) {
      tr.appendChild(amenityCell(property, amenity.key, amenity.icon, amenity.label));
    });
    // variacao: seta + valor (↓ caiu / ↑ subiu); estavel/novo -> vazio
    const changed = property.change.startsWith('subiu') || property.change.startsWith('caiu');
    const arrow = property.change.startsWith('caiu') ? '↓' : '↑';
    const value = property.change.replace(/^(caiu|subiu)\s*/, '');  // "caiu R$ 250" -> "R$ 250"
    const tdChange = cell(changed ? arrow + ' ' + value : '');
    if (changed) tdChange.className = changeClass(property.change);
    tr.appendChild(tdChange);

    const tdAddress = document.createElement('td');
    const link = document.createElement('a');
    link.href = property.url;
    link.target = '_blank';
    link.textContent = shortAddress(property.address);   // abrevia; textContent evita XSS
    link.addEventListener('click', function () { markClicked(property.id); });
    tdAddress.appendChild(link);
    tr.appendChild(tdAddress);

    // Codigo do imovel (ID do QuintoAndar), como link para o anuncio
    const tdCode = document.createElement('td');
    const codeLink = document.createElement('a');
    codeLink.href = property.url;
    codeLink.target = '_blank';
    codeLink.textContent = property.id;   // textContent evita XSS
    codeLink.addEventListener('click', function () { markClicked(property.id); });
    tdCode.appendChild(codeLink);
    tr.appendChild(tdCode);

    // Ultima coluna: ✕ esconde (ativo) ou ↩ restaura (oculto). textContent evita XSS.
    const tdButton = document.createElement('td');
    const button = document.createElement('button');
    if (property.active === 0) {
      button.className = 'restore';
      button.textContent = '↩';
      button.title = 'Restaurar — voltar a mostrar este anúncio';
      button.addEventListener('click', function () {
        reactivate(property.id);
      });
    } else {
      button.className = 'deactivate';
      button.textContent = '✕';
      button.title = 'Não tenho interesse — esconder este anúncio';
      button.addEventListener('click', function () {
        deactivate(property.id, tr, markers[index]);
      });
    }
    tdButton.appendChild(button);
    tr.appendChild(tdButton);

    // Hover na linha destaca o pin correspondente no mapa (cresce + anel azul)
    tr.addEventListener('mouseenter', function () { highlightPin(index, true); });
    tr.addEventListener('mouseleave', function () { highlightPin(index, false); });
    body.appendChild(tr);
  });

  // Total = universo coerente com o modo atual: ocultos quando o toggle "Só ocultos"
  // esta ligado, senao os ativos. Assim o "de N" nao soma os ocultos no modo normal.
  const onlyHidden = document.getElementById('f-hidden-toggle').classList.contains('on');
  const total = DATA.rentals.filter(function (p) {
    return onlyHidden ? p.active === 0 : p.active !== 0;
  }).length;
  const visible = list.length;
  const withoutCoord = list.filter(function (p) { return p.lat == null; }).length;
  let summary = visible === total
    ? visible + ' imóveis'
    : visible + ' de ' + total + ' imóveis';
  if (withoutCoord) summary += ' (' + withoutCoord + ' sem coordenada, fora do mapa)';
  document.getElementById('summary').textContent = summary;

  // Reaplica a ordenacao escolhida pelo usuario (se houver), para nao perde-la ao re-renderizar.
  applySort();
}

// Marca a linha clicada (salva o id; re-renderiza para mover a marca)
function markClicked(id) {
  localStorage.setItem(LAST_CLICKED_KEY, id);
  render();
}

// Liga/desliga o destaque visual de um pin ao passar o mouse na linha da tabela.
// Se o pin estiver agrupado num cluster, destaca o proprio cluster (getVisibleParent),
// pois o pin individual nao esta renderizado nesse caso.
function highlightPin(index, on) {
  const marker = markers[index];
  if (!marker) return;  // imovel "visto" ou sem coordenada: nao tem pin
  const visible = pinLayer.getVisibleParent(marker);  // o proprio marker, ou o cluster que o contem
  const element = visible ? visible.getElement() : null;
  if (!element) return;  // ainda nao renderizado (fora da area visivel do mapa)
  // pino individual usa .pin-num; o cluster usa o div padrao do markercluster
  const target = element.querySelector('.pin-num') || element;
  target.classList.toggle('pin-hover', on);
}

// Rola ate a linha 'index' na tabela e a faz piscar (chamado ao clicar no pin).
function goToRow(index) {
  const rows = document.querySelectorAll('#table tbody tr');
  const row = rows[index];
  if (!row) return;
  row.scrollIntoView({ behavior: 'smooth', block: 'start' });
  // reinicia a animacao mesmo se a linha ja tinha a classe
  row.classList.remove('flash');
  void row.offsetWidth;  // forca reflow para a animacao rodar de novo
  row.classList.add('flash');
}

// --- Ordenacao por coluna ---
// Guarda a ultima ordenacao escolhida para REAPLICAR depois de cada render()
// (senao clicar num link chama render() e a tabela volta a ordem original por score).
let sortState = null;  // { index, ascending } ou null = ordem original (por score)

// Reordena as linhas atuais da tabela conforme sortState. Sem efeito se for null.
function applySort() {
  // "Perto + barato" ja ordenou a lista (tabela e pins juntos): nao deixa a
  // ordenacao por clique no cabecalho sobrescrever.
  if (document.getElementById('f-near-cheap').checked) return;
  if (!sortState) return;
  const body = document.querySelector('#table tbody');
  const rows = Array.from(body.querySelectorAll('tr'));
  rows.sort(function (a, b) {
    const va = a.children[sortState.index].dataset.value;
    const vb = b.children[sortState.index].dataset.value;
    let cmp = (va !== undefined && vb !== undefined)
      ? parseFloat(va) - parseFloat(vb)
      : a.children[sortState.index].textContent.localeCompare(b.children[sortState.index].textContent);
    return sortState.ascending ? cmp : -cmp;
  });
  rows.forEach(function (row) { body.appendChild(row); });
}

document.querySelectorAll('#table th').forEach(function (header, index) {
  header.addEventListener('click', function () {
    const ascending = header.dataset.order !== 'asc';
    header.dataset.order = ascending ? 'asc' : 'desc';
    sortState = { index: index, ascending: ascending };  // memoriza a escolha
    applySort();
  });
});

// Filtros: ao mudar qualquer controle, re-renderiza tudo.
// 'input' cobre tanto os checkboxes quanto a digitacao nos campos numericos.
document.querySelectorAll('.filters input').forEach(function (input) {
  input.addEventListener('input', render);
});

// Toggle "Só ocultos": liga/desliga a classe .on e re-renderiza
document.getElementById('f-hidden-toggle').addEventListener('click', function () {
  this.classList.toggle('on');
  render();
});

// POST padrao para o servidor (app.py): trata o erro de forma uniforme. Chama onOk
// com o JSON da resposta (ou null em 204 sem corpo). Mostra um alerta unico em falha.
function postAction(url, onOk) {
  fetch(url, { method: 'POST' })
    .then(function (response) {
      if (!response.ok) throw new Error('falha');
      return response.status === 204 ? null : response.json();
    })
    .then(onOk)
    .catch(function () {
      alert('Não foi possível salvar. O servidor (app.py) está rodando?');
    });
}

// Desativa um anuncio: avisa o servidor (grava ativo=0) e some com a linha + pin.
function deactivate(id, tr, marker) {
  postAction('/deactivate/' + id, function () {
    const property = DATA.rentals.find(function (p) { return p.id === id; });
    if (property) property.active = 0;  // mantem o DATA coerente para o toggle "Só ocultos"
    tr.remove();
    if (marker) pinLayer.removeLayer(marker);
    showToast('Anúncio escondido');
  });
}

// Restaura um anuncio oculto: avisa o servidor (grava ativo=1), atualiza o DATA
// e re-renderiza (a linha sai da lista "só ocultos").
function reactivate(id) {
  postAction('/reactivate/' + id, function () {
    const property = DATA.rentals.find(function (p) { return p.id === id; });
    if (property) property.active = 1;
    render();
    showToast('Anúncio restaurado');
  });
}

// Desenha as estrelas (ou o traco de "visto") refletindo property.rating e liga os cliques.
// rating -1 = visto (traco); 0 = sem nada; 1..5 = estrelas.
function buildStars(td, property, tr) {
  td.replaceChildren();

  // Estado "visto": mostra so um traco. Botao direito de novo volta ao vazio.
  if (property.rating === -1) {
    const dash = document.createElement('span');
    dash.className = 'seen';
    dash.textContent = '–';
    dash.title = 'Visto (sem nota). Botão direito para desmarcar.';
    dash.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      setRating(property, 0, td, tr);  // desmarca: volta ao vazio
    });
    td.appendChild(dash);
    return;
  }

  for (let n = 1; n <= 5; n++) {
    const star = document.createElement('span');
    star.className = 'star' + (n <= (property.rating || 0) ? ' on' : '');
    star.textContent = n <= (property.rating || 0) ? '★' : '☆';
    star.title = 'Dar nota ' + n + ' (botão direito = marcar como visto)';
    star.addEventListener('click', function () {
      // clicar na estrela igual a nota atual zera; senao, vira a nota clicada
      const newRating = property.rating === n ? 0 : n;
      setRating(property, newRating, td, tr);
    });
    // Botao direito marca "visto" -- mas so quando ainda nao tem nota (regra 3b).
    star.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      if (!property.rating) setRating(property, -1, td, tr);
    });
    td.appendChild(star);
  }
}

// Grava a nota no servidor e atualiza estrelas + destaque da linha.
function setRating(property, rating, td, tr) {
  postAction('/rate/' + property.id + '/' + rating, function (result) {
    property.rating = result.rating;
    buildStars(td, property, tr);
    tr.classList.toggle('high-rating', property.rating >= HIGHLIGHT_RATING);
    showToast('Nota salva');
  });
}

// Grava a amenidade no servidor (1/0/null) e redesenha o icone.
function setAmenity(property, key, value, td, icon) {
  const param = value == null ? 'null' : value;  // null vira texto "null" na URL
  postAction('/amenity/' + property.id + '/' + key + '/' + param, function (result) {
    property[key] = result.value;
    drawAmenity(td, property[key], icon);
    showToast('Amenidade salva');
  });
}

render();

// O mapa fica num wrapper sticky e pode nascer com tamanho errado (largura 0) antes do
// layout assentar, fazendo o fitBounds degenerar (zoom maximo, sem pins). Esperamos 2
// frames para o layout assentar, recalculamos o tamanho do mapa e re-renderizamos para
// enquadrar os pins corretamente.
requestAnimationFrame(function () {
  requestAnimationFrame(function () {
    map.invalidateSize();
    render();
  });
});
