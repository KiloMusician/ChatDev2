@echo off
setlocal
set "ROOT=%~dp0.."
echo Starting Keeper Steam game-watcher. Press Ctrl+C to stop.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" listen %*
pause
endlocal
