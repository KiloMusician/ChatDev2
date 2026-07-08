#requires -Version 5.1
param(
    [switch]$Json,
    [double]$Timeout = 2.0
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Doctor = Join-Path $ScriptDir "chatdev_colony_doctor.py"
$Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$argsList = @($Doctor, "--timeout", ([string]$Timeout))
if ($Json) {
    $argsList += "--json"
}

& $Python @argsList
