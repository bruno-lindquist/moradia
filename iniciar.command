#!/bin/bash
# Atalho clicavel (Finder) para usar o Moradia sem digitar comandos.
# Pergunta se voce quer (A) buscar imoveis ou (B) so ver o relatorio, e abre
# o relatorio no navegador. O servidor fica rodando nesta janela ate voce
# apertar Ctrl+C (ou fechar a janela).

# Vai para a pasta do projeto (onde este arquivo esta), nao importa de onde foi aberto
cd "$(dirname "$0")" || exit 1

PYTHON=".venv/bin/python"
URL="http://localhost:8765"

# Confere se o ambiente foi instalado (veja o README para a instalacao inicial)
if [ ! -x "$PYTHON" ]; then
  echo "Ambiente nao encontrado (.venv)."
  echo "Faca a instalacao uma vez seguindo o README.md e tente de novo."
  read -r -p "Pressione Enter para fechar."
  exit 1
fi

echo "🏠 Moradia perto do Shopping Morumbi"
echo ""
echo "O que voce quer fazer?"
echo "  A) Buscar imoveis (atualiza os precos na internet e depois abre o relatorio)"
echo "  B) Ver o relatorio (abre direto, com os dados que ja tem)"
echo ""
read -r -p "Digite A ou B e aperte Enter: " escolha

# Normaliza a resposta para maiuscula (aceita 'a' ou 'A')
escolha=$(echo "$escolha" | tr '[:lower:]' '[:upper:]')

if [ "$escolha" = "A" ]; then
  echo ""
  echo "Buscando imoveis... um navegador (Chrome) vai abrir sozinho durante a busca."
  "$PYTHON" collect.py
elif [ "$escolha" != "B" ]; then
  echo "Opcao invalida. Abrindo o relatorio mesmo assim..."
fi

echo ""
echo "Abrindo o relatorio em $URL"
echo "Para parar o servidor, volte a esta janela e aperte Ctrl+C."

# Abre o navegador alguns segundos depois (tempo do servidor subir), em segundo plano,
# enquanto o servidor roda em primeiro plano segurando esta janela.
( sleep 2 && open "$URL" ) &

"$PYTHON" app.py
