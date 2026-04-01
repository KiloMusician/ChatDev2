@echo off
REM DevMentor / Terminal Depths — Windows CMD Launcher
REM Usage: devmentor.bat [serve|play|docker|stop|mcp|help]

setlocal
set MODE=%1
if "%MODE%"=="" set MODE=serve

if "%MODE%"=="serve" goto :serve
if "%MODE%"=="s"     goto :serve
if "%MODE%"=="play"  goto :play
if "%MODE%"=="p"     goto :play
if "%MODE%"=="docker" goto :docker
if "%MODE%"=="d"      goto :docker
if "%MODE%"=="stop"  goto :stop
if "%MODE%"=="status" goto :status
if "%MODE%"=="mcp"   goto :mcp
if "%MODE%"=="help"  goto :help
goto :help

:serve
echo [DevMentor] Starting API server...
python -m cli.devmentor serve --host 0.0.0.0 --port 7337
goto :end

:play
set SESSION=%2
if "%SESSION%"=="" set SESSION=player-%USERNAME%
echo [DevMentor] Interactive REPL (session: %SESSION%)
python -m cli.devmentor play --session-id %SESSION%
goto :end

:docker
echo [DevMentor] Starting Docker stack...
docker compose -f docker-compose.yml up -d
echo API: http://localhost:7337
goto :end

:stop
docker compose -f docker-compose.yml down
docker compose -f docker-compose.full.yml down
goto :end

:status
python -m cli.devmentor status
goto :end

:mcp
echo [DevMentor] MCP server (stdio)...
python mcp/server.py
goto :end

:help
echo.
echo Usage: devmentor.bat [mode] [args]
echo.
echo   serve (s)     Start API server (default)
echo   play  (p)     Interactive REPL
echo   docker (d)    Docker Compose
echo   stop          Stop containers
echo   status        System status
echo   mcp           MCP stdio server
echo   help          This message
echo.

:end
endlocal
