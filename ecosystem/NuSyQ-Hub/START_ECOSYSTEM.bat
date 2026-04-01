@echo off
REM ========================================
REM NuSyQ Ecosystem Quick Start
REM ========================================
REM Double-click this file to start:
REM - Docker Desktop
REM - Ollama service
REM - Then check status
REM ========================================

echo.
echo ========================================
echo    STARTING NUSYQ ECOSYSTEM
echo ========================================
echo.

REM Start Docker Desktop
echo [1/3] Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if errorlevel 1 (
    echo WARNING: Docker Desktop not found at default location
    echo Please start Docker Desktop manually
    pause
)

REM Wait for Docker to initialize
echo [2/3] Waiting 30 seconds for Docker to start...
timeout /t 30 /nobreak

REM Start Ollama in a new window
echo [3/3] Starting Ollama service...
start "Ollama Service" cmd /k "echo Ollama Service Running - DO NOT CLOSE THIS WINDOW && ollama serve"
if errorlevel 1 (
    echo WARNING: Ollama not found
    echo Install from: https://ollama.ai
    pause
)

REM Wait a moment for Ollama to start
echo Waiting 10 seconds for Ollama to initialize...
timeout /t 10 /nobreak

REM Check status
echo.
echo ========================================
echo    CHECKING SERVICE STATUS
echo ========================================
echo.

python scripts\startup_ecosystem.py

echo.
echo ========================================
echo    STARTUP COMPLETE
echo ========================================
echo.
echo Docker Desktop should be running (whale icon in system tray)
echo Ollama service is running in a separate window
echo.
echo Press any key to close this window...
pause > nul
