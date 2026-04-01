param(
    [switch]$Recreate
)

Write-Host "== venv-repair.ps1 =="
$venvPath = Join-Path -Path $PSScriptRoot -ChildPath "..\.venv" | Resolve-Path -ErrorAction SilentlyContinue
if (-not $venvPath) { $venvPath = Join-Path -Path (Get-Location) -ChildPath "..\.venv" }
$venvPath = (Resolve-Path -Path $venvPath).Path

if ($Recreate -and (Test-Path $venvPath)) {
    Write-Host "Removing existing venv at $venvPath"
    Remove-Item -Recurse -Force -LiteralPath $venvPath
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv at $venvPath"
    python -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python not found in venv: $python"
    exit 2
}

Write-Host "Upgrading pip, setuptools, wheel"
& $python -m pip install --upgrade pip setuptools wheel

Write-Host "Installing core packages: PyYAML, fastapi, uvicorn, aiohttp, requests"
& $python -m pip install PyYAML fastapi uvicorn aiohttp requests

Write-Host "Done. Use `& $python -m pip freeze` to inspect installed packages."
