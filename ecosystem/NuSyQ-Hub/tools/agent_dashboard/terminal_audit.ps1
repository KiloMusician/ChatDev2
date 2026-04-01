#!/usr/bin/env pwsh
<#
Simple terminal/process audit for NuSyQ agent dashboard.
Generates tools/agent_dashboard/status.json summarizing matching agent processes,
optional quests from tools/agent_dashboard/quests.json, and recent errors.
#>

Set-StrictMode -Version Latest

$outDir = Join-Path -Path $PSScriptRoot -ChildPath '.'
$statusPath = Join-Path $outDir 'status.json'

# collect processes
$procs = Get-CimInstance Win32_Process | Select-Object ProcessId, Name, CommandLine, CreationDate

$agentPatterns = 'copilot|claude|codex|chatdev|nusyq|nuSyQ|simulatedverse|python|node|powershell|pwsh|code'

$agents = @()
foreach ($p in $procs) {
  $cmd = ($p.CommandLine -join '')
  if ($cmd -and ($cmd -match $agentPatterns -or $p.Name -match $agentPatterns)) {
    $agents += [PSCustomObject]@{
      name = $p.Name
      pid  = $p.ProcessId
      command = $p.CommandLine
      created = $p.CreationDate
    }
  }
}

# read quests if present
$questsPath = Join-Path $outDir 'quests.json'
$quests = @()
if (Test-Path $questsPath) {
  try { $quests = Get-Content $questsPath -Raw | ConvertFrom-Json } catch { $quests = @() }
}

# collect recent errors from errors/*.log
$errors = @()
$errDir = Join-Path $outDir 'errors'
if (Test-Path $errDir) {
  Get-ChildItem -Path $errDir -Filter '*.log' -File -ErrorAction SilentlyContinue | ForEach-Object {
    $tail = Get-Content -Path $_.FullName -Tail 20 -ErrorAction SilentlyContinue -Raw
    $errors += [PSCustomObject]@{ file = $_.Name; tail = $tail }
  }
}

$status = [PSCustomObject]@{
  generated = (Get-Date).ToString('o')
  agents = $agents
  quests = $quests
  errors = $errors
}

$scans = @{}
# try run semgrep if available
try {
  $semgrepOutput = Join-Path $outDir 'semgrep_output.json'
  $semgrepCmd = 'semgrep'
  $haveSemgrep = $false
  try { & $semgrepCmd --version > $null 2>&1; $haveSemgrep = $true } catch { $haveSemgrep = $false }
  if (-not $haveSemgrep) {
    # try common venv location (NuSyQ)
    $py = 'C:\Users\keath\NuSyQ\\.venv\\Scripts\\python.exe'
    if (Test-Path $py) {
      try { & $py -m semgrep --version > $null 2>&1; $haveSemgrep = $true; $semgrepCmd = "$py -m semgrep" } catch { $haveSemgrep = $false }
    }
  }

  if ($haveSemgrep) {
    # run a quick semgrep scan (auto config) and write JSON
    try {
      if ($semgrepCmd -like '* -m semgrep') {
        & $py -m semgrep --config auto --json --output $semgrepOutput . > $null 2>&1
      } else {
        & $semgrepCmd --config auto --json --output $semgrepOutput . > $null 2>&1
      }
      if (Test-Path $semgrepOutput) {
        $scans.semgrep = Get-Content $semgrepOutput -Raw | ConvertFrom-Json
      }
    } catch {
      $scans.semgrep_error = $_.Exception.Message
    }
  } else {
    $scans.semgrep = 'not available'
  }
} catch {
  $scans.semgrep_error = $_.Exception.Message
}

$status = [PSCustomObject]@{
  generated = (Get-Date).ToString('o')
  agents = $agents
  quests = $quests
  errors = $errors
  scans = $scans
}

$json = $status | ConvertTo-Json -Depth 10
Set-Content -Path $statusPath -Value $json -Encoding UTF8
Write-Output "Wrote status to $statusPath"
