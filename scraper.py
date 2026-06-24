# Scraper do QuintoAndar usando Playwright (Chrome real automatizado).
# Percorre cada bairro ativo (tabela 'bairros' do banco) buscando aluguel,
# rola a pagina para carregar mais cards e extrai os dados de cada imovel.
#
# AVISO: o QuintoAndar nao tem API publica e pode mudar o HTML a qualquer momento.
# Se parar de coletar, os seletores abaixo (CSS/regex) sao o primeiro lugar a revisar.

import random
import re
import time
from contextlib import contextmanager

from playwright.sync_api import sync_playwright

import config


def _human_pause(minimum=1.5, maximum=4.0):
    # Espera um tempo aleatorio (anti-deteccao): navegacao humana nao tem ritmo fixo.
    time.sleep(random.uniform(minimum, maximum))


def _human_scroll(page):
    # Rola a pagina em alguns passos com pausas curtas, imitando leitura humana.
    for _ in range(random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(600, 1400))
        time.sleep(random.uniform(0.4, 1.2))


def _scrape_listing(page, operation, url):
    # Abre uma URL de busca e extrai os cards. Reusa a 'page' (navegador ja aberto).
    properties = []
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(config.PAUSE_SECONDS)

    # O QuintoAndar mostra so 12 imoveis por vez; o resto carrega clicando em "Ver mais".
    # (Nao funciona por URL ?pagina=N nem por scroll simples.) Clicamos ate o botao sumir.
    _click_load_more(page)

    # Cada imovel e um link para /imovel/<id>/... ; pegamos todos esses cards.
    cards = page.query_selector_all('a[href*="/imovel/"]')
    seen = set()
    for card in cards:
        href = card.get_attribute("href") or ""
        property_id = _parse_id(href)
        if not property_id or property_id in seen:
            continue
        seen.add(property_id)

        text = card.inner_text()
        property = {
            "id": property_id,
            "operation": operation,
            "url": _absolute_url(href),
            "title": _first_line(text),
            "address": _parse_address(text),
            "area_m2": _parse_number(text, r"(\d+)\s*m"),
            "bedrooms": _parse_integer(text, r"(\d+)\s*quart"),
            "parking": _parse_integer(text, r"(\d+)\s*vaga"),
            "price": _parse_price(text),
            "total_price": _parse_total_price(text),
        }
        if _within_filters(property):
            properties.append(property)
    return properties


def _scrape_details(page, property):
    # Abre a pagina individual do imovel e extrai dados estruturados do bloco
    # 'house-main-info': se e mobiliado e quantas vagas. Anti-deteccao: tempo
    # aleatorio na pagina + scroll. Em caso de falha, deixa os campos como None.
    try:
        page.goto(property["url"], wait_until="domcontentloaded", timeout=60000)
        _human_pause()        # tempo aleatorio simulando leitura
        _human_scroll(page)   # rolagem humana
        block = page.query_selector('[data-testid="house-main-info"]')
        if not block:
            return
        items = [p.inner_text().strip() for p in block.query_selector_all("p")]
        property["furnished"] = _parse_furnished(items)
        property["floor"] = _parse_floor(items)
        property["accepts_pet"] = _parse_pet(items)
        parking = _parse_parking(items)
        if parking is not None:
            property["parking"] = parking
        # Coordenada exata do imovel, fornecida pelo proprio QuintoAndar na pagina.
        # E muito mais precisa que geocodificar pelo nome da rua (ruas longas geram
        # erro de ate ~1 km). geo() so e usado como fallback quando isto vem vazio.
        latitude, longitude = _parse_coordinates(page)
        if latitude is not None:
            property["latitude"] = latitude
            property["longitude"] = longitude
        property["detailed"] = 1  # sucesso: nao precisa reabrir a pagina deste imovel
    except Exception:
        pass  # deixa os campos como estao; nao marca detailed -> tenta de novo na proxima


def _parse_coordinates(page):
    # Le a coordenada do imovel do JSON __NEXT_DATA__ embutido na pagina.
    # Retorna (latitude, longitude) ou (None, None) se nao encontrar.
    try:
        block = page.query_selector("#__NEXT_DATA__")
        if not block:
            return None, None
        text = block.inner_text()
        latitude = re.search(r'"lat"\s*:\s*(-?\d+\.\d+)', text)
        longitude = re.search(r'"lng"\s*:\s*(-?\d+\.\d+)', text)
        if latitude and longitude:
            return float(latitude.group(1)), float(longitude.group(1))
    except Exception:
        pass
    return None, None


def _parse_furnished(items):
    # Procura o item de mobilia: "Mobiliado"/"Semimobiliado" -> 1, "Sem mobilia" -> 0.
    for text in items:
        lower = text.lower()
        if "sem mob" in lower:        # "Sem mobília"
            return 0
        if "mobiliad" in lower:       # "Mobiliado" / "Semimobiliado"
            return 1
    return None


def _parse_floor(items):
    # O andar vem como faixa: "8° a 11° andar", "Até 3° andar", "12° a 15° andar".
    # Guardamos o MENOR numero da faixa (conservador para a regra "4o ou acima").
    for text in items:
        if "andar" not in text.lower():
            continue
        numbers = re.findall(r"(\d+)", text)
        if numbers:
            return min(int(n) for n in numbers)
    return None


def _parse_pet(items):
    # "Aceita pet" -> 1 ; "Nao aceita" -> 0. (O usuario prefere quem NAO aceita,
    # mas guardamos o fato cru; a preferencia entra no score.)
    for text in items:
        lower = text.lower()
        if "não aceita" in lower or "nao aceita" in lower:
            return 0
        if "aceita pet" in lower:
            return 1
    return None


def _parse_parking(items):
    # O item de vaga e "-" (sem vaga) ou um numero. Procuramos pelo formato.
    for text in items:
        if text.strip() == "-":
            return 0
        match = re.match(r"^(\d+)\s*vaga", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


@contextmanager
def open_browser():
    # Abre o navegador uma vez e o mantem aberto para varios bairros.
    # Use com 'with open_browser() as page:'. Fecha tudo ao sair do bloco.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=config.HEADLESS)
        page = browser.new_page()
        try:
            yield page
        finally:
            browser.close()


def scrape_neighborhood(page, slug, name, already_detailed=frozenset()):
    # Coleta UM bairro por completo: lista (com "Ver mais") + detalhe de cada imovel.
    # already_detailed: IDs cujos detalhes ja foram capturados -> nao reabre a pagina deles.
    # Retorna a lista de imoveis desse bairro. O chamador (collect.py) salva no banco
    # antes de ir para o proximo bairro, para nao perder tudo se algo falhar no meio.
    url = config.RENT_URL_TEMPLATE.format(slug=slug)
    print(f"  buscando aluguel em {name}...")
    properties = _scrape_listing(page, "aluguel", url)

    to_detail = [p for p in properties if p["id"] not in already_detailed]
    skipped = len(properties) - len(to_detail)
    print(f"    detalhando {len(to_detail)} imoveis de {name} ({skipped} ja detalhados, pulados)...")
    for property in to_detail:
        _scrape_details(page, property)
    return properties


def _click_load_more(page):
    # Clica no botao "Ver mais" ate ele sumir (ou atingir o limite de seguranca).
    # Cada clique carrega mais ~12 imoveis na mesma pagina.
    for _ in range(config.MAX_LOAD_MORE_CLICKS):
        try:
            button = page.get_by_text(re.compile(r"ver mais", re.IGNORECASE)).first
            if not button.is_visible():
                break
            button.scroll_into_view_if_needed()
            time.sleep(0.5)
            button.click()
            time.sleep(config.PAUSE_SECONDS)
        except Exception:
            break  # botao sumiu ou nao e mais clicavel -> acabou a paginacao


def _within_filters(property):
    # O QuintoAndar mistura imoveis "recomendados" fora do filtro quando a busca e
    # restritiva. Descartamos o que esta fora da faixa de preco/area (config.py).
    price = property.get("price")
    area = property.get("area_m2")
    if price is None or not (config.PRICE_MIN <= price <= config.PRICE_MAX):
        return False
    if area is None or not (config.AREA_MIN <= area <= config.AREA_MAX):
        return False
    return True


# --- Funcoes auxiliares de extracao (toleram campo ausente: retornam None) ---

def _parse_id(href):
    match = re.search(r"/imovel/(\d+)", href)
    return match.group(1) if match else None


def _absolute_url(href):
    if href.startswith("http"):
        return href
    return "https://www.quintoandar.com.br" + href


def _first_line(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[0] if lines else None


def _parse_address(text):
    # Heuristica: a linha que comeca com tipo de logradouro costuma ser o endereco.
    # Mantemos so ate o " · " (separador do QuintoAndar) e cortamos numero/complemento
    # longos, que atrapalham a geocodificacao.
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"(Rua|Avenida|Av\.|Alameda|Travessa|Praca|Estrada)\b", line, re.IGNORECASE):
            return line.split("·")[0].strip()
    return None


def _parse_number(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def _parse_integer(text, pattern):
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def _to_reais(snippet):
    # "R$ 2.500" -> 2500.0 ; remove pontos de milhar
    digits = re.sub(r"[^\d]", "", snippet)
    return float(digits) if digits else None


def _parse_price(text):
    # O 1o "R$ ..." costuma ser o valor principal (aluguel mensal ou preco de venda)
    match = re.search(r"R\$\s*[\d.]+", text)
    return _to_reais(match.group(0)) if match else None


def _parse_total_price(text):
    # Procura um valor rotulado como "total" (aluguel + condominio + IPTU)
    match = re.search(r"R\$\s*[\d.]+\s*(?:total|no total)", text, re.IGNORECASE)
    return _to_reais(match.group(0)) if match else None
