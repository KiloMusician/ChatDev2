@echo off
setlocal
set "SCRIPT=%~dp0compact-docker-vhd.ps1"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath powershell.exe -Verb RunAs -WorkingDirectory '%~dp0' -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-File','%SCRIPT%')"
endlocal
