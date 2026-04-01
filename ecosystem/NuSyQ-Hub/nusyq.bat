@echo off
REM NuSyQ-Hub Windows Launcher
REM ==========================
REM One-command entrypoint for factory/orchestration workflows.

setlocal enabledelayedexpansion

set "NUSYQ_ROOT=%~dp0"
cd /d "%NUSYQ_ROOT%"

REM Activate local venv when present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Python command detection
set "PYTHON_EXE=python"
set "PYTHON_ARGS="
where python >nul 2>&1
if errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
)

set "CMD=%~1"
if "%CMD%"=="" set "CMD=help"

if /i "%CMD%"=="help" goto :help
if /i "%CMD%"=="run" goto :run
if /i "%CMD%"=="cycle" goto :cycle
if /i "%CMD%"=="auto" goto :auto
if /i "%CMD%"=="test" goto :test
if /i "%CMD%"=="status" goto :status
if /i "%CMD%"=="generate" goto :generate
if /i "%CMD%"=="doctor" goto :doctor
if /i "%CMD%"=="doctorfix" goto :doctorfix
if /i "%CMD%"=="autopilot" goto :autopilot
if /i "%CMD%"=="cigate" goto :cigate
if /i "%CMD%"=="refill" goto :refill
if /i "%CMD%"=="autosvc-start" goto :autosvc_start
if /i "%CMD%"=="autosvc-stop" goto :autosvc_stop
if /i "%CMD%"=="autosvc-status" goto :autosvc_status
if /i "%CMD%"=="autosvc-restart" goto :autosvc_restart
if /i "%CMD%"=="chatdev" goto :chatdev

echo Unknown command: %CMD%
goto :help

:help
echo.
echo NuSyQ-Hub Command Line Interface
echo =================================
echo.
echo Usage: nusyq.bat [command] [options]
echo.
echo Core:
echo   run         Run the main CLI (nq)
echo   cycle       Run one autonomous cycle
echo   auto        Start autonomous loop (run_autonomous.py)
echo   autosvc-start   Start persistent autonomous monitor service
echo   autosvc-stop    Stop autonomous monitor service
echo   autosvc-status  Show autonomous monitor service status
echo   autosvc-restart Restart autonomous monitor service
echo   refill      Refill PU queue from autonomous audit pass
echo   status      Show generators and PU queue status
echo   test        Run quick test check
echo.
echo Factory:
echo   generate    nq factory generate ...
echo   doctor      nq factory doctor --strict-hooks --workspace-integrity
echo   doctorfix   nq factory doctor --fix --strict-hooks --workspace-integrity
echo   autopilot   nq factory autopilot --strict-hooks
echo   cigate      nq factory ci-gate
echo.
echo AI:
echo   chatdev     Run ChatDev task against local Ollama
echo.
echo Examples:
echo   nusyq.bat auto --hours 1 --tasks 5 --doctor-preflight
echo   nusyq.bat doctor --json
echo   nusyq.bat autopilot --fix --json
echo   nusyq.bat chatdev "Create a CLI todo app"
echo.
goto :end

:run
shift
%PYTHON_EXE% %PYTHON_ARGS% nq %*
goto :end

:cycle
%PYTHON_EXE% %PYTHON_ARGS% -c "from src.automation.autonomous_loop import AutonomousLoop; loop=AutonomousLoop(max_cycles=1); loop.run_cycle()"
goto :end

:auto
shift
%PYTHON_EXE% %PYTHON_ARGS% run_autonomous.py %*
goto :end

:test
%PYTHON_EXE% %PYTHON_ARGS% tests/quick_check.py
goto :end

:status
%PYTHON_EXE% %PYTHON_ARGS% -c "from src.factories.generators.registry import GeneratorRegistry; r=GeneratorRegistry(); print('Generators:', r.list_available())"
%PYTHON_EXE% %PYTHON_ARGS% -c "import json, pathlib; p=pathlib.Path('data/unified_pu_queue.json'); q=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []; pending=sum(1 for x in q if x.get('status') in {'approved','queued','pending'}); completed=sum(1 for x in q if x.get('status')=='completed'); failed=sum(1 for x in q if x.get('status')=='failed'); print(f'PU Queue: total={len(q)} pending={pending} completed={completed} failed={failed}')"
goto :end

:generate
shift
%PYTHON_EXE% %PYTHON_ARGS% nq factory generate %*
goto :end

:doctor
shift
%PYTHON_EXE% %PYTHON_ARGS% nq factory doctor --strict-hooks --workspace-integrity %*
goto :end

:doctorfix
shift
%PYTHON_EXE% %PYTHON_ARGS% nq factory doctor --fix --strict-hooks --workspace-integrity %*
goto :end

:autopilot
shift
%PYTHON_EXE% %PYTHON_ARGS% nq factory autopilot --strict-hooks %*
goto :end

:cigate
shift
%PYTHON_EXE% %PYTHON_ARGS% nq factory ci-gate %*
goto :end

:refill
%PYTHON_EXE% %PYTHON_ARGS% -c "from src.automation.autonomous_loop import AutonomousLoop; loop=AutonomousLoop(interval_minutes=5, max_tasks_per_cycle=0, max_cycles=1); print(loop._run_audit())"
goto :end

:autosvc_start
shift
%PYTHON_EXE% %PYTHON_ARGS% scripts/start_autonomous_service.py %*
goto :end

:autosvc_stop
%PYTHON_EXE% %PYTHON_ARGS% scripts/start_autonomous_service.py --stop
goto :end

:autosvc_status
%PYTHON_EXE% %PYTHON_ARGS% scripts/start_autonomous_service.py --status
goto :end

:autosvc_restart
shift
%PYTHON_EXE% %PYTHON_ARGS% scripts/start_autonomous_service.py --restart %*
goto :end

:chatdev
shift
set "TASK=%*"
if "%TASK%"=="" (
    echo Usage: nusyq.bat chatdev "Your task description"
    goto :end
)

set "CHATDEV_DIR="
if defined CHATDEV_PATH set "CHATDEV_DIR=%CHATDEV_PATH%"
if not defined CHATDEV_DIR if exist "C:\Users\keath\NuSyQ\ChatDev\run_ollama.py" set "CHATDEV_DIR=C:\Users\keath\NuSyQ\ChatDev"
if not defined CHATDEV_DIR if exist "C:\Users\keath\NuSyQ\ChatDev\run.py" set "CHATDEV_DIR=C:\Users\keath\NuSyQ\ChatDev"
if not defined CHATDEV_DIR if exist "C:\Users\keath\Desktop\Legacy\ChatDev_CORE\ChatDev-main\run_ollama.py" set "CHATDEV_DIR=C:\Users\keath\Desktop\Legacy\ChatDev_CORE\ChatDev-main"
if not defined CHATDEV_DIR if exist "C:\Users\keath\Desktop\Legacy\ChatDev_CORE\ChatDev-main\run.py" set "CHATDEV_DIR=C:\Users\keath\Desktop\Legacy\ChatDev_CORE\ChatDev-main"

if not defined CHATDEV_DIR (
    echo ChatDev path not found. Set CHATDEV_PATH or install ChatDev in known locations.
    goto :end
)

if "%OLLAMA_BASE_URL%"=="" set "OLLAMA_BASE_URL=http://localhost:11434/v1"
set "OPENAI_API_KEY=ollama-local"
set "BASE_URL=%OLLAMA_BASE_URL%"
set "OPENAI_BASE_URL=%OLLAMA_BASE_URL%"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddHHmmss"') do set "STAMP=%%I"
if not defined STAMP set "STAMP=manual"

cd /d "%CHATDEV_DIR%"
if exist "run_ollama.py" (
    %PYTHON_EXE% %PYTHON_ARGS% run_ollama.py --task "%TASK%" --name "NuSyQGen_%STAMP%" --org "NuSyQ" --model "qwen2.5-coder:14b"
) else (
    %PYTHON_EXE% %PYTHON_ARGS% run.py --task "%TASK%" --name "NuSyQGen_%STAMP%" --org "NuSyQ" --model "GPT_3_5_TURBO"
)
goto :end

:end
endlocal
