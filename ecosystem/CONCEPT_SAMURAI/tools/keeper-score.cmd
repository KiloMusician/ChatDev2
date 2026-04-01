@echo off
setlocal
set "ROOT=%~dp0.."
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" score %*
pause
endlocal
