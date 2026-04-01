@echo off
:: td.cmd — Terminal Depths Universal Launcher (Windows Command Prompt)
:: Works in: cmd.exe · Windows Command Prompt
:: Run: td [subcommand] [args...]
::
:: For PowerShell, use td.ps1 instead.
:: For bash/git-bash/wsl, use td (no extension).
:: ---------------------------------------------------------------
setlocal

:: Resolve repo root from this script's directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if exist "%SCRIPT_DIR%\scripts\td.py" (
    set "TD_PY=%SCRIPT_DIR%\scripts\td.py"
) else if exist "%SCRIPT_DIR%\..\scripts\td.py" (
    pushd "%SCRIPT_DIR%\.."
    set "TD_PY=%CD%\scripts\td.py"
    popd
) else (
    if exist "%SCRIPT_DIR%\.td_repo" (
        set /p TD_REPO=<"%SCRIPT_DIR%\.td_repo"
        set "TD_PY=%TD_REPO%\scripts\td.py"
    ) else (
        echo [td] ERROR: Cannot locate DevMentor repo. Set TD_REPO env var. >&2
        exit /b 1
    )
)

where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 "%TD_PY%" %*
) else (
    python "%TD_PY%" %*
)
endlocal
