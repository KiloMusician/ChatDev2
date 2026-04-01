Param(
  [string]$AdminToken = $env:ADMIN_TOKEN,
  [string]$BaseUrl = $env:BASE_URL
)

# Helper: run the trigger -> verify -> harness sequence in PowerShell
Write-Host "Running local rehydration harness sequence..."

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$simPath = Join-Path $root '..' | Resolve-Path | Select-Object -ExpandProperty Path
Set-Location $simPath

if (-Not (Test-Path package.json)) {
  Write-Host "No package.json found in $simPath; please run this from the repository root where SimulatedVerse folder exists." -ForegroundColor Yellow
  exit 1
}

# Ensure state directory exists
if (-Not (Test-Path .\state)) { New-Item -ItemType Directory -Path .\state | Out-Null }

Write-Host "Installing dependencies (will run npm install if package-lock.json missing)..."
if (Test-Path package-lock.json) {
  npm ci
} else {
  npm install
}

Write-Host "Triggering sanitized circuit dump via reportError()..."
npx --yes tsx server/utils/trigger_dump_via_report.ts

if ($AdminToken) { $env:ADMIN_TOKEN = $AdminToken }
if ($BaseUrl) { $env:BASE_URL = $BaseUrl }

Write-Host "Verifying verbosity endpoint (best-effort)..."
npx --yes tsx server/utils/verify_verbosity_endpoint.ts

Write-Host "Running deterministic rehydration harness..."
npm run rehydrate:harness

Write-Host "--- Results ---"
if (Test-Path .\state\rehydration_harness_result.json) { Get-Content .\state\rehydration_harness_result.json -Raw } else { Write-Host "Result file missing" -ForegroundColor Red }
if (Test-Path .\state\rehydration_harness_error.json) { Get-Content .\state\rehydration_harness_error.json -Raw }

Write-Host "Local harness run complete."
