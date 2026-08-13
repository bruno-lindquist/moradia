# ENTRYPOINT 0: prepara o ambiente e mostra o menu do dia a dia. É o que os atalhos
# clicáveis (iniciar.command / iniciar.cmd) chamam.
#
# Por que existe: quem usa o programa não precisa saber criar venv nem rodar pip. Este
# arquivo cria o ambiente, instala as bibliotecas e só então chama collect.py / app.py.
# Por isso ele usa SOMENTE a biblioteca padrão: é ele quem instala o resto, então não
# pode depender do que ainda não existe (e precisa rodar até em Python antigo, para
# conseguir avisar que a versão não serve em vez de quebrar com erro técnico).
#
# Toda a lógica dos atalhos mora aqui; os dois lançadores apenas chamam este arquivo.

import hashlib
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"
# Guarda a "impressão digital" do requirements.txt já instalado. Se não mudou, o atalho
# pula pip e playwright e abre em segundos em vez de conferir tudo de novo.
SETUP_MARKER = VENV_DIR / "setup-fingerprint.txt"

PORT = 8765  # mesma porta do app.py
URL = f"http://localhost:{PORT}"
DOWNLOAD_PAGE = "https://www.python.org/downloads/"

# 3.10 é o mínimo exigido pelo projeto. A 3.14 fica de fora porque quebra a instalação
# das dependências (pip); quando isso for resolvido, é só subir o limite.
MIN_VERSION = (3, 10)
MAX_VERSION_EXCLUSIVE = (3, 14)


def ask(prompt):
    # Sem terminal interativo (janela fechada, saída redirecionada), input() levanta
    # EOFError. Aqui isso vira resposta vazia, em vez de um erro técnico na tela.
    try:
        return input(prompt)
    except EOFError:
        print()
        return ""


def fail(message):
    # Erro sempre termina assim: mensagem em português e uma pausa, senão a janela fecha
    # sozinha antes de a pessoa conseguir ler o que aconteceu.
    print()
    print(message)
    print()
    ask("Aperte Enter para fechar.")
    sys.exit(1)


def run(command, error_message):
    # Roda um comando mostrando a saída ao vivo, para a pessoa acompanhar o progresso.
    try:
        result = subprocess.run([str(part) for part in command])
    except FileNotFoundError:
        fail(error_message)
    if result.returncode != 0:
        fail(error_message)


def venv_python():
    # O Windows guarda os executáveis do venv em Scripts/; Mac e Linux, em bin/.
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def is_supported(version):
    return MIN_VERSION <= (version[0], version[1]) < MAX_VERSION_EXCLUSIVE


def find_compatible_python():
    # Devolve o comando de um Python compatível (lista de argumentos) ou None.
    # O atalho chama o Python padrão do sistema, que pode estar fora da faixa suportada
    # mesmo havendo outra versão instalada ao lado; aqui procuramos essa outra.
    if is_supported(sys.version_info):
        return [sys.executable]
    for minor in range(MAX_VERSION_EXCLUSIVE[1] - 1, MIN_VERSION[1] - 1, -1):
        candidates = []
        if os.name == "nt":
            candidates.append(["py", f"-3.{minor}"])  # lançador oficial do Windows
        found = shutil.which(f"python3.{minor}")
        if found:
            candidates.append([found])
        for command in candidates:
            try:
                probe = subprocess.run(command + ["--version"], capture_output=True)
            except OSError:
                continue
            if probe.returncode == 0:
                return command
    return None


def ensure_launcher_executable():
    # Baixar o projeto como .zip tira a permissão de execução do iniciar.command e o
    # duplo-clique para de funcionar. Restaura para as próximas vezes.
    if os.name == "nt":
        return
    launcher = PROJECT_DIR / "iniciar.command"
    if launcher.exists() and not os.access(launcher, os.X_OK):
        launcher.chmod(0o755)


def ensure_venv():
    # Cria o ambiente isolado (.venv) na primeira vez.
    if venv_python().exists():
        return
    python = find_compatible_python()
    if python is None:
        webbrowser.open(DOWNLOAD_PAGE)
        fail(
            f"Este programa precisa do Python {MIN_VERSION[0]}.{MIN_VERSION[1]} ou mais novo "
            f"(e ainda não funciona na versão {MAX_VERSION_EXCLUSIVE[0]}.{MAX_VERSION_EXCLUSIVE[1]}).\n"
            f"Abri a página de download no navegador: {DOWNLOAD_PAGE}\n"
            'No Windows, marque a caixinha "Add Python to PATH" durante a instalação.\n'
            "Depois de instalar, clique no atalho de novo."
        )
    print("Preparando o ambiente pela primeira vez...")
    run(
        python + ["-m", "venv", str(VENV_DIR)],
        "Não consegui criar o ambiente (.venv). Apague a pasta .venv, se ela existir, "
        "e tente de novo.",
    )


def ensure_pip():
    # Ambiente criado com a ferramenta uv vem sem pip. O ensurepip, da biblioteca padrão,
    # instala o pip dentro do ambiente sem precisar refazê-lo do zero.
    probe = subprocess.run([str(venv_python()), "-m", "pip", "--version"], capture_output=True)
    if probe.returncode == 0:
        return
    run(
        [venv_python(), "-m", "ensurepip", "--upgrade"],
        "Não consegui preparar o instalador de bibliotecas (pip) no ambiente. "
        "Apague a pasta .venv e clique no atalho de novo.",
    )


def ensure_dependencies():
    # Instala as bibliotecas e o navegador da busca. Só roda quando o requirements.txt
    # mudou (ou na primeira vez), para o atalho abrir rápido no uso normal.
    fingerprint = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    if SETUP_MARKER.exists() and SETUP_MARKER.read_text() == fingerprint:
        return

    ensure_pip()
    print()
    print("Instalando o que o programa precisa. Isso demora alguns minutos na primeira")
    print("vez (baixa cerca de 150 MB) e não se repete depois. Não feche esta janela.")
    print()
    run(
        [venv_python(), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        "Não consegui instalar as bibliotecas. Confira se você está conectado à internet "
        "e clique no atalho de novo.",
    )
    print()
    print("Baixando o navegador usado na busca...")
    run(
        [venv_python(), "-m", "playwright", "install", "chromium"],
        "Não consegui baixar o navegador da busca. Confira a conexão com a internet "
        "e clique no atalho de novo.",
    )
    # Marcador escrito só no fim: instalação interrompida no meio recomeça na próxima vez.
    SETUP_MARKER.write_text(fingerprint)


def port_in_use():
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", PORT)) == 0


def open_browser_when_ready():
    # Espera o servidor responder antes de abrir o navegador: em máquina lenta, abrir
    # cedo demais mostra "não foi possível acessar o site".
    for _ in range(60):
        if port_in_use():
            webbrowser.open(URL)
            return
        time.sleep(0.5)


def ask_choice():
    print("O que você quer fazer?")
    print("  A) Buscar imóveis (atualiza os preços na internet e depois abre o relatório)")
    print("  B) Ver o relatório (abre direto, com os dados que já tem)")
    print()
    choice = ask("Digite A ou B e aperte Enter: ").strip().upper()
    if choice not in ("A", "B"):
        print("Opção inválida. Abrindo o relatório mesmo assim...")
        return "B"
    return choice


def main():
    # O duplo-clique pode abrir o terminal em outra pasta; tudo aqui depende da pasta do projeto.
    os.chdir(PROJECT_DIR)

    print("Moradia perto do MASP")
    print()

    if port_in_use():
        # Segundo clique no atalho com o relatório já aberto: sem isso, o servidor
        # falharia com "porta em uso".
        print("O relatório já está aberto. Trazendo a janela do navegador...")
        webbrowser.open(URL)
        return

    ensure_launcher_executable()
    ensure_venv()
    ensure_dependencies()

    if ask_choice() == "A":
        print()
        print("Buscando imóveis... um navegador (Chrome) vai abrir sozinho durante a busca.")
        run(
            [venv_python(), "collect.py"],
            "A busca não terminou. Confira a conexão com a internet e tente de novo.",
        )

    print()
    print(f"Abrindo o relatório em {URL}")
    print("Para parar, volte a esta janela e aperte Ctrl+C.")
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    run(
        [venv_python(), "app.py"],
        "O relatório não conseguiu abrir. Feche outros programas que possam estar usando "
        f"a porta {PORT} e tente de novo.",
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("Encerrado.")
