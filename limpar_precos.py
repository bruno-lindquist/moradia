# Script de uso unico: enxuga o historico da tabela 'precos', deixando so os pontos de
# mudanca de preco. Antes desta limpeza, cada execucao de collect/fix_coords gravava um
# snapshot mesmo quando o valor nao mudava, inchando a tabela com duplicatas.
#
# Regra (por imovel, ordenado por id, que segue a ordem temporal): mantem a linha se ela
# for a PRIMEIRA, a ULTIMA, ou um PONTO DE MUDANCA (valor ou valor_total difere da linha
# anterior). Apaga as duplicatas consecutivas do meio. Isso preserva o preco atual e a
# funcao price_change (que compara o 1o com o ultimo snapshot) sem alterar o relatorio.
#
# Seguranca: faz backup do .db antes de apagar e so toca a tabela 'precos'.
# Uso:  python limpar_precos.py [caminho_do_banco]   (sem argumento -> config.DB_PATH)

import shutil
import sqlite3
import sys
from datetime import datetime

import config

# ids a manter: primeira/ultima/ponto-de-mudanca de cada imovel. LAG le a linha anterior;
# ROW_NUMBER da a posicao (1 = primeira) e COUNT total (rn == total => ultima).
KEEP_IDS_QUERY = """
WITH seq AS (
    SELECT id,
           valor,
           valor_total,
           LAG(valor)       OVER janela AS valor_anterior,
           LAG(valor_total) OVER janela AS valor_total_anterior,
           ROW_NUMBER()     OVER janela AS posicao,
           COUNT(*)         OVER (PARTITION BY imovel_id) AS total
    FROM precos
    WINDOW janela AS (PARTITION BY imovel_id ORDER BY id)
)
SELECT id FROM seq
WHERE posicao = 1
   OR posicao = total
   OR valor IS NOT valor_anterior
   OR IFNULL(valor_total, -1) <> IFNULL(valor_total_anterior, -1)
"""


def backup_database(db_path):
    # Copia o banco para um arquivo com timestamp antes de qualquer escrita.
    # Retorna o caminho do backup. Levanta excecao se a copia falhar.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = f"{db_path}.bak-{stamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def main(db_path):
    print(f"Banco alvo: {db_path}")
    backup_path = backup_database(db_path)
    print(f"Backup criado: {backup_path}")

    connection = sqlite3.connect(db_path)
    try:
        total_before = connection.execute("SELECT COUNT(*) FROM precos").fetchone()[0]
        keep_ids = [row[0] for row in connection.execute(KEEP_IDS_QUERY).fetchall()]
        to_delete = total_before - len(keep_ids)
        print(f"Linhas antes:    {total_before}")
        print(f"Linhas a manter: {len(keep_ids)}")
        print(f"Linhas a apagar: {to_delete}")

        if to_delete <= 0:
            print("Nada a apagar. Encerrando.")
            return

        # Tabela temporaria com os ids a manter: evita um IN gigante com milhares de '?'.
        connection.execute("CREATE TEMP TABLE ids_a_manter (id INTEGER PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO ids_a_manter VALUES (?)", [(keep_id,) for keep_id in keep_ids]
        )
        connection.execute(
            "DELETE FROM precos WHERE id NOT IN (SELECT id FROM ids_a_manter)"
        )
        connection.commit()
        connection.execute("VACUUM")  # recupera o espaco em disco das linhas apagadas

        total_after = connection.execute("SELECT COUNT(*) FROM precos").fetchone()[0]
        print(f"Linhas depois:   {total_after}")
        print(f"Pronto. Backup em: {backup_path}")
    finally:
        connection.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else config.DB_PATH
    main(db_path)
