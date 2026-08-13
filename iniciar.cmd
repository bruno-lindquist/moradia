@echo off
REM Atalho clicavel (Explorer) para usar o Moradia sem digitar comandos.
REM Toda a logica (criar ambiente, instalar, menu) esta em start.py; aqui so achamos o Python.

REM Faz o terminal do Windows entender acentos nas mensagens abaixo.
chcp 65001 >nul

cd /d "%~dp0"

REM 'py' e o lancador oficial do Python. Ele vem antes de 'python' porque, no Windows,
REM 'python' sozinho pode ser o atalho falso da Microsoft Store, que abre a loja em vez
REM de rodar o programa.
where /q py
if %errorlevel%==0 (
  py -3 start.py
  goto end
)

where /q python
if %errorlevel%==0 (
  python start.py
  goto end
)

echo.
echo Python não encontrado neste computador.
echo Baixe em https://www.python.org/downloads/ e clique neste atalho de novo.
echo Durante a instalação, marque a caixinha "Add Python to PATH".
echo.
pause

:end
