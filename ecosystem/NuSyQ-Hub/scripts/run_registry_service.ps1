# Start the Model Registry API as a background process on Windows
# Usage: .\scripts\run_registry_service.ps1
$python = (Get-Command python).Source
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path "$root\..")
$log = "state\registry_api.log"
if (!(Test-Path -Path (Split-Path $log))) { New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null }
# Start in a detached process
Start-Process -FilePath $python -ArgumentList "-m", "src.registry.run_api" -RedirectStandardOutput $log -RedirectStandardError $log -WindowStyle Hidden
Write-Host "Model Registry API started (detached). Logs: $log"
