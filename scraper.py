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


def _pausa_humana(minimo=1.5, maximo=4.0):
    # Espera um tempo aleatorio (anti-deteccao): navegacao humana nao tem ritmo fixo.
    time.sleep(random.uniform(minimo, maximo))


def _scroll_humano(pagina):
    # Rola a pagina em alguns passos com pausas curtas, imitando leitura humana.
    for _ in range(random.randint(2, 4)):
        pagina.mouse.wheel(0, random.randint(600, 1400))
        time.sleep(random.uniform(0.4, 1.2))


def _coletar_pagina(pagina, operacao, url):
    # Abre uma URL de busca e extrai os cards. Reusa a 'pagina' (navegador ja aberto).
    imoveis = []
    pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(config.PAUSA_SEGUNDOS)

    # O QuintoAndar mostra so 12 imoveis por vez; o resto carrega clicando em "Ver mais".
    # (Nao funciona por URL ?pagina=N nem por scroll simples.) Clicamos ate o botao sumir.
    _clicar_ver_mais(pagina)

    # Cada imovel e um link para /imovel/<id>/... ; pegamos todos esses cards.
    cards = pagina.query_selector_all('a[href*="/imovel/"]')
    vistos = set()
    for card in cards:
        href = card.get_attribute("href") or ""
        imovel_id = _extrair_id(href)
        if not imovel_id or imovel_id in vistos:
            continue
        vistos.add(imovel_id)

        texto = card.inner_text()
        imovel = {
            "id": imovel_id,
            "operacao": operacao,
            "url": _url_absoluta(href),
            "titulo": _primeira_linha(texto),
            "endereco": _extrair_endereco(texto),
            "area_m2": _extrair_numero(texto, r"(\d+)\s*m"),
            "quartos": _extrair_inteiro(texto, r"(\d+)\s*quart"),
            "vagas": _extrair_inteiro(texto, r"(\d+)\s*vaga"),
            "valor": _extrair_valor(texto),
            "valor_total": _extrair_valor_total(texto),
        }
        if _dentro_dos_filtros(imovel):
            imoveis.append(imovel)
    return imoveis


def _detalhar_imovel(pagina, imovel):
    # Abre a pagina individual do imovel e extrai dados estruturados do bloco
    # 'house-main-info': se e mobiliado e quantas vagas. Anti-deteccao: tempo
    # aleatorio na pagina + scroll. Em caso de falha, deixa os campos como None.
    try:
        pagina.goto(imovel["url"], wait_until="domcontentloaded", timeout=60000)
        _pausa_humana()        # tempo aleatorio simulando leitura
        _scroll_humano(pagina) # rolagem humana
        bloco = pagina.query_selector('[data-testid="house-main-info"]')
        if not bloco:
            return
        itens = [p.inner_text().strip() for p in bloco.query_selector_all("p")]
        imovel["mobiliado"] = _interpretar_mobilia(itens)
        imovel["andar"] = _interpretar_andar(itens)
        imovel["aceita_pet"] = _interpretar_pet(itens)
        vagas = _interpretar_vagas(itens)
        if vagas is not None:
            imovel["vagas"] = vagas
        imovel["detalhado"] = 1  # sucesso: nao precisa reabrir a pagina deste imovel
    except Exception:
        pass  # deixa os campos como estao; nao marca detalhado -> tenta de novo na proxima


def _interpretar_mobilia(itens):
    # Procura o item de mobilia: "Mobiliado"/"Semimobiliado" -> 1, "Sem mobilia" -> 0.
    for texto in itens:
        baixo = texto.lower()
        if "sem mob" in baixo:        # "Sem mobília"
            return 0
        if "mobiliad" in baixo:       # "Mobiliado" / "Semimobiliado"
            return 1
    return None


def _interpretar_andar(itens):
    # O andar vem como faixa: "8° a 11° andar", "Até 3° andar", "12° a 15° andar".
    # Guardamos o MENOR numero da faixa (conservador para a regra "4o ou acima").
    for texto in itens:
        if "andar" not in texto.lower():
            continue
        numeros = re.findall(r"(\d+)", texto)
        if numeros:
            return min(int(n) for n in numeros)
    return None


def _interpretar_pet(itens):
    # "Aceita pet" -> 1 ; "Nao aceita" -> 0. (O usuario prefere quem NAO aceita,
    # mas guardamos o fato cru; a preferencia entra no score.)
    for texto in itens:
        baixo = texto.lower()
        if "não aceita" in baixo or "nao aceita" in baixo:
            return 0
        if "aceita pet" in baixo:
            return 1
    return None


def _interpretar_vagas(itens):
    # O item de vaga e "-" (sem vaga) ou um numero. Procuramos pelo formato.
    for texto in itens:
        if texto.strip() == "-":
            return 0
        achado = re.match(r"^(\d+)\s*vaga", texto, re.IGNORECASE)
        if achado:
            return int(achado.group(1))
    return None


@contextmanager
def abrir_navegador():
    # Abre o navegador uma vez e o mantem aberto para varios bairros.
    # Use com 'with abrir_navegador() as pagina:'. Fecha tudo ao sair do bloco.
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch(headless=config.HEADLESS)
        pagina = navegador.new_page()
        try:
            yield pagina
        finally:
            navegador.close()


def coletar_bairro(pagina, slug, nome, ja_detalhados=frozenset()):
    # Coleta UM bairro por completo: lista (com "Ver mais") + detalhe de cada imovel.
    # ja_detalhados: IDs cujos detalhes ja foram capturados -> nao reabre a pagina deles.
    # Retorna a lista de imoveis desse bairro. O chamador (coletar.py) salva no banco
    # antes de ir para o proximo bairro, para nao perder tudo se algo falhar no meio.
    url = config.URL_ALUGUEL_MOLDE.format(slug=slug)
    print(f"  buscando aluguel em {nome}...")
    imoveis = _coletar_pagina(pagina, "aluguel", url)

    a_detalhar = [im for im in imoveis if im["id"] not in ja_detalhados]
    pulados = len(imoveis) - len(a_detalhar)
    print(f"    detalhando {len(a_detalhar)} imoveis de {nome} ({pulados} ja detalhados, pulados)...")
    for imovel in a_detalhar:
        _detalhar_imovel(pagina, imovel)
    return imoveis


def _clicar_ver_mais(pagina):
    # Clica no botao "Ver mais" ate ele sumir (ou atingir o limite de seguranca).
    # Cada clique carrega mais ~12 imoveis na mesma pagina.
    for _ in range(config.MAX_VER_MAIS):
        try:
            botao = pagina.get_by_text(re.compile(r"ver mais", re.IGNORECASE)).first
            if not botao.is_visible():
                break
            botao.scroll_into_view_if_needed()
            time.sleep(0.5)
            botao.click()
            time.sleep(config.PAUSA_SEGUNDOS)
        except Exception:
            break  # botao sumiu ou nao e mais clicavel -> acabou a paginacao


def _dentro_dos_filtros(imovel):
    # O QuintoAndar mistura imoveis "recomendados" fora do filtro quando a busca e
    # restritiva. Descartamos o que esta fora da faixa de preco/area (config.py).
    valor = imovel.get("valor")
    area = imovel.get("area_m2")
    if valor is None or not (config.PRECO_MIN <= valor <= config.PRECO_MAX):
        return False
    if area is None or not (config.AREA_MIN <= area <= config.AREA_MAX):
        return False
    return True


# --- Funcoes auxiliares de extracao (toleram campo ausente: retornam None) ---

def _extrair_id(href):
    achado = re.search(r"/imovel/(\d+)", href)
    return achado.group(1) if achado else None


def _url_absoluta(href):
    if href.startswith("http"):
        return href
    return "https://www.quintoandar.com.br" + href


def _primeira_linha(texto):
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    return linhas[0] if linhas else None


def _extrair_endereco(texto):
    # Heuristica: a linha que comeca com tipo de logradouro costuma ser o endereco.
    # Mantemos so ate o " · " (separador do QuintoAndar) e cortamos numero/complemento
    # longos, que atrapalham a geocodificacao.
    for linha in texto.splitlines():
        linha = linha.strip()
        if re.match(r"(Rua|Avenida|Av\.|Alameda|Travessa|Praca|Estrada)\b", linha, re.IGNORECASE):
            return linha.split("·")[0].strip()
    return None


def _extrair_numero(texto, padrao):
    achado = re.search(padrao, texto, re.IGNORECASE)
    return float(achado.group(1)) if achado else None


def _extrair_inteiro(texto, padrao):
    achado = re.search(padrao, texto, re.IGNORECASE)
    return int(achado.group(1)) if achado else None


def _para_reais(trecho):
    # "R$ 2.500" -> 2500.0 ; remove pontos de milhar
    digitos = re.sub(r"[^\d]", "", trecho)
    return float(digitos) if digitos else None


def _extrair_valor(texto):
    # O 1o "R$ ..." costuma ser o valor principal (aluguel mensal ou preco de venda)
    achado = re.search(r"R\$\s*[\d.]+", texto)
    return _para_reais(achado.group(0)) if achado else None


def _extrair_valor_total(texto):
    # Procura um valor rotulado como "total" (aluguel + condominio + IPTU)
    achado = re.search(r"R\$\s*[\d.]+\s*(?:total|no total)", texto, re.IGNORECASE)
    return _para_reais(achado.group(0)) if achado else None
