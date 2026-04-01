# scripts/run_mcp_server.ps1
param(
  [switch]$DryRun,
  [string]$PythonExe = ".\.venv\Scripts\python.exe",
  [string]$AppFactory = "mcp_server.main:create_app",
  [int]$Port = 3000,
  [string]$LogPath = ".\mcp_server.log",
  [int]$RotateSizeMB = 50,
  [int]$StartupTimeoutSec = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Ensure log directory exists
$logFile = Resolve-Path -LiteralPath $LogPath -ErrorAction SilentlyContinue
if (-not $logFile) {
    $dir = Split-Path -Parent $LogPath
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    # Create an empty file atomically
    New-Item -Path $LogPath -ItemType File -Force | Out-Null
}

# Ensure writable
try {
    $stream = [System.IO.File]::Open($LogPath, 'Open', 'Write', 'Read')
    $stream.Close()
} catch {
    Write-Error "Log file '$LogPath' is not writable: $_"
    exit 2
}

# Rotate if too large
try {
    $fi = Get-Item -LiteralPath $LogPath -ErrorAction Stop
    if ($fi.Length -gt ($RotateSizeMB * 1MB)) {
        $ts = Get-Date -Format "yyyyMMdd_HHmmss"
        $rot = "$LogPath.$ts"
        Move-Item -LiteralPath $LogPath -Destination $rot -Force
        New-Item -Path $LogPath -ItemType File -Force | Out-Null
        Write-Host "Rotated log to $rot"
    }
} catch {
    # ignore rotation errors but warn
    Write-Warning "Log rotate check failed: $_"
}

# Prevent duplicate server instances (simple check)
$existing = Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%$AppFactory%'" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Warning "Found existing MCP server process; skipping start. Existing PIDs: $($existing.ProcessId -join ',')"
    exit 0
}

if ($DryRun) {
    Write-Host "[DryRun] Would start: $PythonExe -m uvicorn `"$AppFactory`" --factory --host 0.0.0.0 --port $Port --log-level debug"
    exit 0
}

# Start uvicorn and redirect output to log (Start-Process with -NoNewWindow won't detach reliably; use Start-Process so we can capture PID)
$uvicornArgs = "-m uvicorn `"$AppFactory`" --factory --host 0.0.0.0 --port $Port --log-level debug"
$startInfo = @{
    FilePath = $PythonExe
    ArgumentList = $uvicornArgs
    RedirectStandardOutput = $true
    RedirectStandardError  = $true
    WindowStyle = 'Hidden'
    NoNewWindow = $false
}
# Start-Process doesn't support both RedirectStandardOutput and -NoNewWindow well in PS, so use a background job wrapper:
$cmd = "& `"$PythonExe`" $uvicornArgs 1>> `"$LogPath`" 2>&1"
$job = Start-Job -ScriptBlock { param($c) Invoke-Expression $c } -ArgumentList $cmd

Write-Host "Started MCP server job id=$($job.Id). Waiting up to $StartupTimeoutSec seconds for /health..."

# Wait and poll for health endpoint
$started = $false
$end = (Get-Date).AddSeconds($StartupTimeoutSec)
while ((Get-Date) -lt $end) {
    Start-Sleep -Seconds 1
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:$Port/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($resp -and $resp.status) {
            Write-Host "MCP /health: $($resp | ConvertTo-Json -Depth 2)"
            $started = $true
            break
        }
    } catch {
        # not up yet
    }
}

if (-not $started) {
    Write-Warning "MCP server did not report healthy within $StartupTimeoutSec seconds. See log: $LogPath"
    # Stream tail to help debug
    Get-Content -Path $LogPath -Tail 200 -Wait -ErrorAction SilentlyContinue
    exit 3
}

Write-Host "MCP appears healthy. Streaming log (press Ctrl+C to stop):"
Get-Content -Path $LogPath -Tail 200 -Wait
