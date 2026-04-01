@echo off
setlocal
set "ROOT=%~dp0.."
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" doctor -AudioTriage %*
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$f = Get-ChildItem '%ROOT%\incidents\*.html' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($f) { Start-Process $f.FullName }"
pause
endlocal
