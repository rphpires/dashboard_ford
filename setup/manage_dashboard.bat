@echo off
REM Script para gerenciar o Dashboard Ford

SETLOCAL EnableDelayedExpansion

echo ===================================================
echo  GERENCIAMENTO DO DASHBOARD FORD
echo ===================================================
echo.

REM Verifica se Docker está instalado
docker --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Docker nao esta instalado. Por favor, instale o Docker Desktop primeiro.
    echo Visite: https://docs.docker.com/desktop/windows/install/
    pause
    exit /b 1
)

:MENU
echo Escolha uma opcao:
echo 1. Iniciar Dashboard
echo 2. Parar Dashboard
echo 3. Configurar Conexao com Banco de Dados
echo 4. Ver Logs
echo 5. Reiniciar Dashboard
echo 6. Sair
echo.

set /p opcao="Digite o numero da opcao desejada: "

if "%opcao%"=="1" goto INICIAR
if "%opcao%"=="2" goto PARAR
if "%opcao%"=="3" goto CONFIGURAR_BD
if "%opcao%"=="4" goto VER_LOGS
if "%opcao%"=="5" goto REINICIAR
if "%opcao%"=="6" goto SAIR

echo Opcao invalida!
goto MENU

:INICIAR
echo.
echo Iniciando o Dashboard Ford...
docker-compose -f setup/docker-compose.yml up -d
echo.
echo Dashboard iniciado! Acesse em http://localhost:8050
echo.
pause
goto MENU

:PARAR
echo.
echo Parando o Dashboard Ford...
docker-compose -f setup/docker-compose.yml down
echo.
echo Dashboard parado.
echo.
pause
goto MENU

:CONFIGURAR_BD
echo.
echo ===== CONFIGURACAO DO BANCO DE DADOS =====
echo.
set /p servidor="Servidor (ex: localhost): "
set /p banco="Nome do Banco de Dados: "
set /p usuario="Usuario: "
set /p senha="Senha: "

REM Confirmar as configurações
echo.
echo Configuracoes:
echo Servidor: %servidor%
echo Banco: %banco%
echo Usuario: %usuario%
echo.
set /p confirma="Confirmar estas configuracoes? (S/N): "

if /i "%confirma%"=="S" (
    echo.
    echo Aplicando configuracoes...
    
    REM Atualizar arquivo .env ou criar se não existir
    echo DB_SERVER=%servidor%> .env
    echo DB_DATABASE=%banco%>> .env
    echo DB_USERNAME=%usuario%>> .env
    echo DB_PASSWORD=%senha%>> .env
    echo DB_PORT=1433>> .env    
    echo.
    echo Configuracoes salvas. Reiniciando o Dashboard...
    
    docker-compose -f setup/docker-compose.yml down
    docker-compose -f setup/docker-compose.yml up -d
    
    echo.
    echo Dashboard reiniciado com novas configuracoes.
) else (
    echo.
    echo Configuracoes canceladas.
)

echo.
pause
goto MENU

:VER_LOGS
echo.
echo Exibindo logs do Dashboard (pressione Ctrl+C para sair)...
echo.
docker-compose -f setup/docker-compose.yml logs -f
goto MENU

:REINICIAR
echo.
echo Reiniciando o Dashboard Ford...
docker-compose -f setup/docker-compose.yml restart
echo.
echo Dashboard reiniciado.
echo.
pause
goto MENU

:SAIR
echo.
echo Saindo do gerenciador...
exit /b 0