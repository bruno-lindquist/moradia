# ENTRYPOINT 4: servidor web local que serve o relatorio COM o botao de desativar anuncios.
# Rode com:  python app.py   (depois abra http://localhost:5000 no navegador)
#
# Por que existe: o relatorio.html sozinho e um arquivo estatico e nao consegue gravar
# no banco. Este servidor pequeno (Flask) permite que o botao "x" desative o anuncio.

from flask import Flask, abort

import db
import relatorio

app = Flask(__name__)


@app.route("/")
def pagina():
    # Gera o HTML na hora, ja sem os anuncios desativados.
    conexao = db.conectar()
    db.criar_tabelas(conexao)
    html = relatorio.gerar_html(conexao)
    conexao.close()
    return html


@app.route("/desativar/<imovel_id>", methods=["POST"])
def desativar(imovel_id):
    conexao = db.conectar()
    db.criar_tabelas(conexao)
    existe = conexao.execute("SELECT 1 FROM imoveis WHERE id = ?", (imovel_id,)).fetchone()
    if not existe:
        conexao.close()
        abort(404)
    db.desativar_imovel(conexao, imovel_id)
    conexao.close()
    return "", 204  # 204 = sucesso, sem conteudo


@app.route("/nota/<imovel_id>/<valor>", methods=["POST"])
def nota(imovel_id, valor):
    # valor vem como texto porque o conversor <int:> do Flask nao aceita negativos.
    # Aceitamos -1 ("visto", so um traco), 0 (sem nota) e 1 a 5 (estrelas).
    try:
        valor = int(valor)
    except ValueError:
        abort(400)
    conexao = db.conectar()
    db.criar_tabelas(conexao)
    existe = conexao.execute("SELECT 1 FROM imoveis WHERE id = ?", (imovel_id,)).fetchone()
    if not existe:
        conexao.close()
        abort(404)
    nova_nota = db.definir_nota(conexao, imovel_id, valor)
    conexao.close()
    return {"nota": nova_nota}  # devolve a nota gravada para o JS atualizar as estrelas


if __name__ == "__main__":
    # Porta 8765: a 5000 e usada pelo AirPlay do macOS e a 8000 pelo Docker.
    # Esta e incomum, entao dificilmente conflita.
    PORTA = 8765
    print(f"Servidor em http://localhost:{PORTA}  (Ctrl+C para parar)")
    app.run(port=PORTA, debug=False)
