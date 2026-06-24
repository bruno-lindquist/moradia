# Camada de banco de dados (SQLite puro, sem ORM).
# Duas tabelas: imoveis (dados estaveis) e precos (um snapshot por execucao).
#
# Convencao de idioma: os identificadores SQL (tabelas/colunas) estao em portugues
# porque vivem dentro do banco real (moradia.db). O codigo Python em volta esta em
# ingles. A traducao ingles->portugues acontece so na fronteira com o SQL.

import sqlite3
from datetime import datetime

import amenities
import config


def connect():
    # row_factory=Row permite acessar colunas pelo nome (row["preco"]) em vez de indice
    connection = sqlite3.connect(config.DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS imoveis (
            id            TEXT PRIMARY KEY,
            operacao      TEXT NOT NULL,
            titulo        TEXT,
            endereco      TEXT,
            area_m2       REAL,
            quartos       INTEGER,
            vagas         INTEGER,
            url           TEXT,
            latitude      REAL,
            longitude     REAL,
            distancia_km  REAL,
            primeira_vez  TEXT,
            ativo         INTEGER NOT NULL DEFAULT 1,
            preferido     INTEGER NOT NULL DEFAULT 0,
            nota          INTEGER NOT NULL DEFAULT 0,
            mobiliado     INTEGER,
            mobiliado_manual INTEGER NOT NULL DEFAULT 0,
            andar         INTEGER,
            aceita_pet    INTEGER,
            academia      INTEGER,
            piscina       INTEGER,
            bicicletario  INTEGER,
            sauna         INTEGER,
            cama            INTEGER,
            fogao           INTEGER,
            geladeira       INTEGER,
            guarda_roupa    INTEGER,
            armario_cozinha INTEGER,
            ar_condicionado INTEGER,
            microondas      INTEGER,
            airfryer        INTEGER,
            workspace       INTEGER,
            detalhado     INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS precos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            imovel_id     TEXT NOT NULL REFERENCES imoveis(id),
            valor         REAL NOT NULL,
            valor_total   REAL,
            coletado_em   TEXT NOT NULL
        );

        -- Cache de geocodificacao: evita pedir o mesmo endereco varias vezes ao Nominatim
        CREATE TABLE IF NOT EXISTS geocache (
            endereco   TEXT PRIMARY KEY,
            latitude   REAL,
            longitude  REAL
        );

        -- Bairros a buscar. 'slug' vai na URL do QuintoAndar; 'ativo' liga/desliga.
        CREATE TABLE IF NOT EXISTS bairros (
            slug   TEXT PRIMARY KEY,
            nome   TEXT NOT NULL,
            ativo  INTEGER NOT NULL DEFAULT 1
        );
        """
    )
    _seed_neighborhoods(connection)
    _migrate_property_columns(connection)
    connection.commit()


def _migrate_property_columns(connection):
    # Bancos criados antes destas colunas nao as tem. ALTER TABLE so adiciona a coluna
    # (nao apaga nada). Idempotente: so age se a coluna ainda nao existir.
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(imoveis)")}

    # Colunas que nao sao amenidades genericas (tem regra/default proprio).
    base_columns = [
        ("ativo", "INTEGER NOT NULL DEFAULT 1"),
        ("preferido", "INTEGER NOT NULL DEFAULT 0"),
        ("mobiliado", "INTEGER"),
        # flag: mobiliado foi definido manualmente no relatorio? (1 = scraping nao sobrescreve)
        ("mobiliado_manual", "INTEGER NOT NULL DEFAULT 0"),
        ("andar", "INTEGER"),
        ("aceita_pet", "INTEGER"),
        ("detalhado", "INTEGER NOT NULL DEFAULT 0"),
        # Tempo de deslocamento ate a referencia (Shopping Morumbi), em segundos, calculado
        # via OSRM por commute.py. NULL = ainda nao calculado.
        ("walk_seconds", "INTEGER"),
        ("bike_seconds", "INTEGER"),
    ]
    # Amenidades manuais (1=tem, 0=nao tem, NULL=nao verificado): derivadas da fonte unica.
    amenity_columns = [(amenity["column"], "INTEGER") for amenity in amenities.AMENITIES]

    for name, definition in base_columns + amenity_columns:
        if name not in columns:
            connection.execute(f"ALTER TABLE imoveis ADD COLUMN {name} {definition}")

    # 'nota' fica fora do loop por causa do efeito colateral: ao cria-la pela 1a vez,
    # converte preferidos existentes em nota 5 (nao perde as escolhas ja feitas).
    if "nota" not in columns:
        connection.execute("ALTER TABLE imoveis ADD COLUMN nota INTEGER NOT NULL DEFAULT 0")
        connection.execute("UPDATE imoveis SET nota = 5 WHERE preferido = 1")


def deactivate_property(connection, property_id):
    # Marca o imovel como inativo (some do relatorio). Nao apaga nada.
    connection.execute("UPDATE imoveis SET ativo = 0 WHERE id = ?", (property_id,))
    connection.commit()


def reactivate_property(connection, property_id):
    # Volta o imovel para ativo (desfaz o "esconder"). Nao apaga nada.
    connection.execute("UPDATE imoveis SET ativo = 1 WHERE id = ?", (property_id,))
    connection.commit()


def set_rating(connection, property_id, rating):
    # Define a nota do imovel. Valores: -1 = "visto" (so um traco, sem estrela),
    # 0 = sem nota nenhuma, 1 a 5 = estrelas. Retorna a nota gravada.
    rating = max(-1, min(5, int(rating)))  # garante -1..5
    connection.execute("UPDATE imoveis SET nota = ? WHERE id = ?", (rating, property_id))
    connection.commit()
    return rating


# Colunas marcaveis manualmente no relatorio. Allowlist tambem protege contra SQL
# injection: o nome da coluna nao pode vir como '?', entao validamos antes de interpolar.
# Derivada da fonte unica (amenities.py) + 'mobiliado' (tem regra propria, ver set_amenity):
# tambem vem do scraping; ao marca-lo aqui, ligamos a flag mobiliado_manual.
AMENITY_COLUMNS = {amenity["column"] for amenity in amenities.AMENITIES} | {"mobiliado"}


def set_amenity(connection, property_id, amenity, value):
    # Marca uma coluna do imovel. value: 1 = tem, 0 = nao tem, None = nao verificado.
    # Retorna o valor gravado. Levanta ValueError se a coluna nao for da allowlist.
    if amenity not in AMENITY_COLUMNS:
        raise ValueError(f"coluna invalida: {amenity}")
    value = None if value is None else (1 if int(value) == 1 else 0)
    connection.execute(
        f"UPDATE imoveis SET {amenity} = ? WHERE id = ?", (value, property_id)
    )
    # Mobiliado definido manualmente passa a ser "protegido": flag liga quando ha valor
    # (1/0) e desliga ao voltar para "nao verificado" (None), devolvendo ao scraping.
    if amenity == "mobiliado":
        manual = 0 if value is None else 1
        connection.execute(
            "UPDATE imoveis SET mobiliado_manual = ? WHERE id = ?", (manual, property_id)
        )
    connection.commit()
    return value


# Bairros iniciais (regiao do Brooklin/Campo Belo + vizinhos). Sao repostos se o banco
# for recriado. Para adicionar mais, inclua aqui (e/ou faca INSERT direto na tabela).
_INITIAL_NEIGHBORHOODS = [
    ("jardim-das-acacias", "Jardim das Acácias"),
    ("brooklin", "Brooklin"),
    ("campo-belo", "Campo Belo"),
    ("granja-julieta", "Granja Julieta"),
    ("vila-sao-francisco", "Vila São Francisco"),
    ("vila-cordeiro", "Vila Cordeiro"),
    ("alto-da-boa-vista", "Alto da Boa Vista"),
    ("jardim-heliomar", "Jardim Heliomar"),
    ("brooklin-novo", "Brooklin Novo"),
    ("chacara-santo-antonio", "Chácara Santo Antônio"),
    ("brooklin-velho", "Brooklin Velho"),
    ("jardim-petropolis", "Jardim Petrópolis"),
]


def _seed_neighborhoods(connection):
    # So insere se a tabela estiver vazia (nao sobrescreve ajustes seus depois).
    is_empty = connection.execute("SELECT COUNT(*) FROM bairros").fetchone()[0] == 0
    if is_empty:
        connection.executemany(
            "INSERT INTO bairros (slug, nome) VALUES (?, ?)", _INITIAL_NEIGHBORHOODS
        )


def detailed_ids(connection):
    # Conjunto de IDs cujos detalhes (mobilia/andar/pet/vagas) ja foram capturados.
    # O scraper usa isso para nao reabrir a pagina desses imoveis.
    rows = connection.execute("SELECT id FROM imoveis WHERE detalhado = 1").fetchall()
    return {row["id"] for row in rows}


def active_neighborhoods(connection):
    # Retorna lista de (slug, nome) dos bairros marcados como ativos.
    rows = connection.execute(
        "SELECT slug, nome FROM bairros WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return [(row["slug"], row["nome"]) for row in rows]


def save_property(connection, property, now):
    # Upsert: insere o imovel; se ja existir, atualiza os dados que podem ter mudado.
    # primeira_vez so e gravado na 1a vez (ON CONFLICT preserva o valor antigo).
    # As chaves do dict 'property' estao em ingles; o mapeamento abaixo faz a ponte
    # ingles->portugues para os parametros nomeados do SQL.
    connection.execute(
        """
        INSERT INTO imoveis (id, operacao, titulo, endereco, area_m2,
                             quartos, vagas, url, latitude, longitude, distancia_km,
                             mobiliado, andar, aceita_pet, detalhado, primeira_vez)
        VALUES (:id, :operacao, :titulo, :endereco, :area_m2,
                :quartos, :vagas, :url, :latitude, :longitude, :distancia_km,
                :mobiliado, :andar, :aceita_pet, :detalhado, :primeira_vez)
        ON CONFLICT(id) DO UPDATE SET
            titulo = excluded.titulo,
            endereco = excluded.endereco,
            area_m2 = excluded.area_m2,
            quartos = excluded.quartos,
            -- estes vem da pagina de detalhe; se vier NULL (falhou), mantem o antigo
            vagas = COALESCE(excluded.vagas, imoveis.vagas),
            -- mobiliado: se foi marcado manualmente (flag=1), preserva o valor manual;
            -- senao, comporta como os demais (usa o novo do scraping ou mantem o antigo).
            mobiliado = CASE WHEN imoveis.mobiliado_manual = 1 THEN imoveis.mobiliado
                             ELSE COALESCE(excluded.mobiliado, imoveis.mobiliado) END,
            andar = COALESCE(excluded.andar, imoveis.andar),
            aceita_pet = COALESCE(excluded.aceita_pet, imoveis.aceita_pet),
            -- detalhado so "sobe" para 1; uma vez detalhado, continua detalhado
            detalhado = MAX(excluded.detalhado, imoveis.detalhado),
            url = excluded.url,
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            distancia_km = excluded.distancia_km
        """,
        {
            "id": property["id"],
            "operacao": property["operation"],
            "titulo": property.get("title"),
            "endereco": property.get("address"),
            "area_m2": property.get("area_m2"),
            "quartos": property.get("bedrooms"),
            "vagas": property.get("parking"),
            "url": property.get("url"),
            "latitude": property.get("latitude"),
            "longitude": property.get("longitude"),
            "distancia_km": property.get("distance_km"),
            "mobiliado": property.get("furnished"),
            "andar": property.get("floor"),
            "aceita_pet": property.get("accepts_pet"),
            "detalhado": 1 if property.get("detailed") else 0,
            "primeira_vez": now,
        },
    )


def save_price(connection, property_id, value, total_value, now):
    # Sempre INSERT: cada execucao deixa um snapshot, formando o historico.
    connection.execute(
        "INSERT INTO precos (imovel_id, valor, valor_total, coletado_em) VALUES (?, ?, ?, ?)",
        (property_id, value, total_value, now),
    )


def property_exists(connection, property_id):
    cursor = connection.execute("SELECT 1 FROM imoveis WHERE id = ?", (property_id,))
    return cursor.fetchone() is not None


def now_iso():
    return datetime.now().isoformat(timespec="seconds")
