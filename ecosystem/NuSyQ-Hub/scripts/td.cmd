@echo off
REM Terminal Depths Universal Command for Command Prompt
REM Installation: Add this directory to PATH

setlocal enabledelayedexpansion

REM Find NuSyQ root
set "NUSYQ_ROOT=%~dp0.."
if not exist "%NUSYQ_ROOT%\scripts\terminal_depths_launcher.py" (
    echo Error: Terminal Depths launcher not found at %NUSYQ_ROOT%
    exit /b 1
)

REM Parse arguments
set "MODE=cli"
set "SURFACE=terminal"
set "PORT=7777"
set "AGENT="
set "NO_COLOR="

:parse_args
if "%~1"=="" goto run
if "%~1"=="--mode" (
    set "MODE=%~2"
    shift & shift
    goto parse_args
)
if "%~1"=="--surface" (
    set "SURFACE=%~2"
    shift & shift
    goto parse_args
)
if "%~1"=="--port" (
    set "PORT=%~2"
    shift & shift
    goto parse_args
)
if "%~1"=="--agent" (
    set "AGENT=--agent %~2"
    shift & shift
    goto parse_args
)
if "%~1"=="--no-color" (
    set "NO_COLOR=--no-color"
    shift
    goto parse_args
)
shift
goto parse_args

:run
cd /d "%NUSYQ_ROOT%"
python -m scripts.terminal_depths_launcher ^
    --mode %MODE% ^
    --surface %SURFACE% ^
    --port %PORT% ^
    %AGENT% %NO_COLOR%

endlocal
