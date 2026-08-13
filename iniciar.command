#!/bin/bash
# Atalho clicável (Finder) para usar o Moradia sem digitar comandos.
# Toda a lógica (criar ambiente, instalar, menu) está em start.py; aqui só achamos o Python.

cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python não encontrado neste computador."
  echo "Baixe em https://www.python.org/downloads/ e clique neste atalho de novo."
  read -r -p "Aperte Enter para fechar."
  exit 1
fi

python3 start.py
