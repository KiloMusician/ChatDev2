@echo off
setlocal
set "ROOT=%~dp0.."
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\tools\Launch-KeeperShell.ps1" -PreferWebFallback %*
endlocal
