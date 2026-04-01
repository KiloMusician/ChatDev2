# td.ps1 — Terminal Depths Universal Launcher (PowerShell 5.1 + PowerShell 7)
# Works in: PowerShell 5.1 · PowerShell Core (pwsh) · Windows · Linux · macOS
#
# Usage: .\td.ps1 [subcommand] [args...]
#   .\td.ps1              — enter Terminal Depths (auto interface)
#   .\td.ps1 play         — terminal REPL
#   .\td.ps1 open         — open in browser
#   .\td.ps1 status       — server health
#   .\td.ps1 install      — install 'td' globally
#   .\td.ps1 surfaces     — map all detected surfaces
# ------------------------------------------------------------------
param(
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$TDArgs
)

# Resolve repo root from this script's location
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe  = "python"

# Search for scripts/td.py relative to this file
if (Test-Path "$ScriptDir\scripts\td.py") {
    $TDPy = "$ScriptDir\scripts\td.py"
} elseif (Test-Path "$ScriptDir\..\scripts\td.py") {
    $TDPy = (Resolve-Path "$ScriptDir\..\scripts\td.py").Path
} else {
    $TDRepoFile = Join-Path $ScriptDir ".td_repo"
    if (Test-Path $TDRepoFile) {
        $TDRepo = Get-Content $TDRepoFile -Raw
        $TDPy = "$($TDRepo.Trim())\scripts\td.py"
    } else {
        Write-Error "[td] Cannot locate DevMentor repo. Set TD_REPO env var."
        exit 1
    }
}

# Prefer python3 if available, fall back to python
if (Get-Command "python3" -ErrorAction SilentlyContinue) {
    $PythonExe = "python3"
}

& $PythonExe $TDPy @TDArgs
exit $LASTEXITCODE
