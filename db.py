# Camada de banco de dados (SQLite puro, sem ORM).
# Duas tabelas: imoveis (dados estaveis) e precos (um snapshot por execucao).

import sqlite3
from datetime import datetime

import config


def conectar():
    # row_factory=Row permite acessar colunas pelo nome (linha["preco"]) em vez de indice
    conexao = sqlite3.connect(config.DB_PATH)
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_tabelas(conexao):
    conexao.executescript(
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
            andar         INTEGER,
            aceita_pet    INTEGER,
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
    _semear_bairros(conexao)
    _migrar_colunas_imoveis(conexao)
    conexao.commit()


def _migrar_colunas_imoveis(conexao):
    # Bancos criados antes destas colunas nao as tem. ALTER TABLE so adiciona a coluna
    # (nao apaga nada). Idempotente: so age se a coluna ainda nao existir.
    colunas = [linha["name"] for linha in conexao.execute("PRAGMA table_info(imoveis)")]
    if "ativo" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
    if "preferido" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN preferido INTEGER NOT NULL DEFAULT 0")
    if "mobiliado" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN mobiliado INTEGER")
    if "andar" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN andar INTEGER")
    if "aceita_pet" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN aceita_pet INTEGER")
    if "detalhado" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN detalhado INTEGER NOT NULL DEFAULT 0")
    if "nota" not in colunas:
        conexao.execute("ALTER TABLE imoveis ADD COLUMN nota INTEGER NOT NULL DEFAULT 0")
        # converte preferidos existentes em nota 5 (nao perde as escolhas ja feitas)
        conexao.execute("UPDATE imoveis SET nota = 5 WHERE preferido = 1")


def desativar_imovel(conexao, imovel_id):
    # Marca o imovel como inativo (some do relatorio). Nao apaga nada.
    conexao.execute("UPDATE imoveis SET ativo = 0 WHERE id = ?", (imovel_id,))
    conexao.commit()


def definir_nota(conexao, imovel_id, nota):
    # Define a nota do imovel. Valores: -1 = "visto" (so um traco, sem estrela),
    # 0 = sem nota nenhuma, 1 a 5 = estrelas. Retorna a nota gravada.
    nota = max(-1, min(5, int(nota)))  # garante -1..5
    conexao.execute("UPDATE imoveis SET nota = ? WHERE id = ?", (nota, imovel_id))
    conexao.commit()
    return nota


# Bairros iniciais (regiao do Brooklin/Campo Belo + vizinhos). Sao repostos se o banco
# for recriado. Para adicionar mais, inclua aqui (e/ou faca INSERT direto na tabela).
_BAIRROS_INICIAIS = [
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


def _semear_bairros(conexao):
    # So insere se a tabela estiver vazia (nao sobrescreve ajustes seus depois).
    vazia = conexao.execute("SELECT COUNT(*) FROM bairros").fetchone()[0] == 0
    if vazia:
        conexao.executemany(
            "INSERT INTO bairros (slug, nome) VALUES (?, ?)", _BAIRROS_INICIAIS
        )


def ids_detalhados(conexao):
    # Conjunto de IDs cujos detalhes (mobilia/andar/pet/vagas) ja foram capturados.
    # O scraper usa isso para nao reabrir a pagina desses imoveis.
    linhas = conexao.execute("SELECT id FROM imoveis WHERE detalhado = 1").fetchall()
    return {linha["id"] for linha in linhas}


def bairros_ativos(conexao):
    # Retorna lista de (slug, nome) dos bairros marcados como ativos.
    linhas = conexao.execute(
        "SELECT slug, nome FROM bairros WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return [(linha["slug"], linha["nome"]) for linha in linhas]


def salvar_imovel(conexao, imovel, agora):
    # Upsert: insere o imovel; se ja existir, atualiza os dados que podem ter mudado.
    # primeira_vez so e gravado na 1a vez (ON CONFLICT preserva o valor antigo).
    conexao.execute(
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
            mobiliado = COALESCE(excluded.mobiliado, imoveis.mobiliado),
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
            "id": imovel["id"],
            "operacao": imovel["operacao"],
            "titulo": imovel.get("titulo"),
            "endereco": imovel.get("endereco"),
            "area_m2": imovel.get("area_m2"),
            "quartos": imovel.get("quartos"),
            "vagas": imovel.get("vagas"),
            "url": imovel.get("url"),
            "latitude": imovel.get("latitude"),
            "longitude": imovel.get("longitude"),
            "distancia_km": imovel.get("distancia_km"),
            "mobiliado": imovel.get("mobiliado"),
            "andar": imovel.get("andar"),
            "aceita_pet": imovel.get("aceita_pet"),
            "detalhado": 1 if imovel.get("detalhado") else 0,
            "primeira_vez": agora,
        },
    )


def salvar_preco(conexao, imovel_id, valor, valor_total, agora):
    # Sempre INSERT: cada execucao deixa um snapshot, formando o historico.
    conexao.execute(
        "INSERT INTO precos (imovel_id, valor, valor_total, coletado_em) VALUES (?, ?, ?, ?)",
        (imovel_id, valor, valor_total, agora),
    )


def imovel_ja_existe(conexao, imovel_id):
    cursor = conexao.execute("SELECT 1 FROM imoveis WHERE id = ?", (imovel_id,))
    return cursor.fetchone() is not None


def agora_iso():
    return datetime.now().isoformat(timespec="seconds")
