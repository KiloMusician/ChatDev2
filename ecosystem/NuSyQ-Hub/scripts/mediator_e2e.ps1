<#
Mediator end-to-end test helper
- Starts mediator via the repository's start script
- Waits for mediator.http.port file to appear
- GET /status, then POST /stop-child
- Verifies that child.pid / mediator.pid are removed
#>
param(
  [string]$WorkspaceRoot = "$(Resolve-Path ..)"
)

$mediatorDir = Join-Path $WorkspaceRoot '.vscode\mediator'
$startScript = Join-Path $WorkspaceRoot 'scripts\start_powershell_mediator.ps1'
$httpPortFile = Join-Path $mediatorDir 'mediator.http.port'
$pidFile = Join-Path $mediatorDir 'mediator.pid'
$childPidFile = Join-Path $mediatorDir 'child.pid'

if (-not (Test-Path $startScript)) {
  Write-Error "start_powershell_mediator.ps1 not found at $startScript"
  exit 2
}

Write-Host "Starting mediator (background via start script)..."
# Start mediator
pwsh -NoProfile -File $startScript

# Wait for port file
$maxWait = 20
$waited = 0
while (-not (Test-Path $httpPortFile) -and $waited -lt $maxWait) {
  Start-Sleep -Seconds 1
  $waited += 1
}

if (-not (Test-Path $httpPortFile)) {
  Write-Error "mediator.http.port did not appear after $maxWait seconds"
  exit 3
}

$port = Get-Content $httpPortFile | ForEach-Object { $_.Trim() }
Write-Host "Mediator HTTP port: $port"

# Check /status
$statusUrl = "http://127.0.0.1:$port/status"
try {
  $s = Invoke-RestMethod -Method Get -Uri $statusUrl -TimeoutSec 5
  Write-Host "Status response:`n" ($s | ConvertTo-Json -Depth 3)
} catch {
  Write-Error "Failed to GET /status: $_"
}

# Call /stop-child
$stopUrl = "http://127.0.0.1:$port/stop-child"
try {
  $r = Invoke-RestMethod -Method Post -Uri $stopUrl -TimeoutSec 5
  Write-Host "Stop response:`n" ($r | ConvertTo-Json -Depth 3)
} catch {
  Write-Error "Failed to POST /stop-child: $_"
}

# Wait for child.pid removal
$waitChild = 15
$elapsed = 0
while (Test-Path $childPidFile -and $elapsed -lt $waitChild) {
  Start-Sleep -Seconds 1
  $elapsed += 1
}

if (Test-Path $childPidFile) { Write-Error "child.pid still present after stop" } else { Write-Host "child.pid removed" }

# Wait for mediator.pid removal
$waitMed = 10
$elapsed = 0
while (Test-Path $pidFile -and $elapsed -lt $waitMed) {
  Start-Sleep -Seconds 1
  $elapsed += 1
}
if (Test-Path $pidFile) { Write-Error "mediator.pid still present after stop" } else { Write-Host "mediator.pid removed" }

Write-Host "Mediator E2E test finished."
