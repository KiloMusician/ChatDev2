#!/usr/bin/env pwsh
<#
Attempts to activate common virtual environments and checks for semgrep.
Run this from the repository root (NuSyQ-Hub).
#>
Set-StrictMode -Version Latest

$candidates = @(
  'C:\Users\keath\NuSyQ\\.venv\\Scripts\\Activate.ps1',
  '${env:USERPROFILE}\\.venv\\Scripts\\Activate.ps1',
  '${PWD}\\.venv\\Scripts\\Activate.ps1',
  'C:\Users\keath\\Desktop\\Legacy\\NuSyQ-Hub\\.venv\\Scripts\\Activate.ps1'
)

Write-Host "Checking semgrep availability and trying common venv activations...`n"

foreach ($act in $candidates) {
  $expanded = (Invoke-Expression """$act""" ) 2>$null
}

# More reliable: test known python interpreters directly
$pyCandidates = @(
  'C:\Users\keath\NuSyQ\\.venv\\Scripts\\python.exe',
  'C:\Users\keath\\NuSyQ-Hub\\.venv\\Scripts\\python.exe',
  'C:\Program Files\Python310\\python.exe'
)

foreach ($py in $pyCandidates) {
  Write-Host "\n--- Checking interpreter: $py ---"
  if (Test-Path $py) {
    try {
      & $py -m semgrep --version
      Write-Host "semgrep available via $py"
    } catch {
      Write-Host "semgrep not available via $py"
      try { & $py -m pip show semgrep } catch {}
    }
  } else {
    Write-Host "Interpreter not found: $py"
  }
}

Write-Host "\nAlso check system PATH:"
try { Get-Command semgrep -ErrorAction SilentlyContinue | Format-List } catch {}
try { & where.exe semgrep } catch { Write-Host 'where semgrep: none' }

Write-Host "\nIf you have a specific venv to activate, run:`n& 'C:\path\to\venv\Scripts\Activate.ps1'`nThen run `semgrep --version` or `python -m semgrep --version`."
