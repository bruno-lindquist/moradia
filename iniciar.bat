@echo off
REM Atalho clicavel (Explorer) para usar o Moradia sem digitar comandos.
REM Pergunta se voce quer (A) buscar imoveis ou (B) so ver o relatorio, e abre
REM o relatorio no navegador. O servidor fica rodando nesta janela ate voce
REM apertar Ctrl+C (ou fechar a janela).

REM Vai para a pasta do projeto (onde este arquivo esta), nao importa de onde foi aberto
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"
set "URL=http://localhost:8765"

REM Confere se o ambiente foi instalado (veja o README para a instalacao inicial)
if not exist "%PYTHON%" (
  echo Ambiente nao encontrado (.venv^).
  echo Faca a instalacao uma vez seguindo o README.md e tente de novo.
  pause
  exit /b 1
)

echo Moradia perto do Shopping Morumbi
echo.
echo O que voce quer fazer?
echo   A^) Buscar imoveis (atualiza os precos na internet e depois abre o relatorio^)
echo   B^) Ver o relatorio (abre direto, com os dados que ja tem^)
echo.
set /p "escolha=Digite A ou B e aperte Enter: "

REM Normaliza a resposta para maiuscula (aceita 'a' ou 'A')
if /i "%escolha%"=="A" (
  echo.
  echo Buscando imoveis... um navegador (Chrome^) vai abrir sozinho durante a busca.
  "%PYTHON%" collect.py
) else (
  if /i not "%escolha%"=="B" (
    echo Opcao invalida. Abrindo o relatorio mesmo assim...
  )
)

echo.
echo Abrindo o relatorio em %URL%
echo Para parar o servidor, volte a esta janela e aperte Ctrl+C.

REM Abre o navegador alguns segundos depois (tempo do servidor subir), em segundo plano,
REM enquanto o servidor roda em primeiro plano segurando esta janela.
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start "" "%URL%""

"%PYTHON%" app.py
