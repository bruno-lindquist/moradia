@echo off
REM Atalho clicavel (Explorer) para usar o Moradia sem digitar comandos.
REM Toda a logica (criar ambiente, instalar, menu) esta em start.py; aqui so achamos o Python.
REM
REM Este arquivo fica sem acento e com quebra de linha CRLF de proposito: o cmd.exe le o
REM arquivo por posicao de byte e se perde com quebra de linha de Mac/Linux (LF), e os
REM acentos dependem da configuracao do terminal. As mensagens do programa, que estao no
REM start.py, saem acentuadas normalmente.

cd /d "%~dp0"

REM 'py' e o lancador oficial do Python. Ele vem antes de 'python' porque, no Windows,
REM 'python' sozinho pode ser o atalho falso da Microsoft Store, que abre a loja em vez
REM de rodar o programa.
where /q py
if %errorlevel%==0 goto use_py

where /q python
if %errorlevel%==0 goto use_python

echo.
echo Python nao encontrado neste computador.
echo Baixe em https://www.python.org/downloads/ e clique neste atalho de novo.
echo Durante a instalacao, marque a caixinha "Add Python to PATH".
echo.
pause
goto end

:use_py
py -3 start.py
goto end

:use_python
python start.py

:end
