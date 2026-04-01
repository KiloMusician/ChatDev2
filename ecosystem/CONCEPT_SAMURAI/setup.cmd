@echo off
echo Installing Keeper desktop and Start Menu shortcuts...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-shortcuts.ps1"
pause
