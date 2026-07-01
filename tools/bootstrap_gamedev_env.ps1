param(
    [string]$TargetPath = ".venv-gamedev313",
    [string]$PythonCommand = "python",
    [switch]$ForceRecreate
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ResolvedTarget = if ([System.IO.Path]::IsPathRooted($TargetPath)) {
    $TargetPath
} else {
    Join-Path $RepoRoot $TargetPath
}

if (Test-Path $ResolvedTarget) {
    if (-not $ForceRecreate) {
        Write-Output "Target already exists: $ResolvedTarget"
        Write-Output "Use -ForceRecreate to rebuild it."
        exit 0
    }
    Remove-Item -LiteralPath $ResolvedTarget -Recurse -Force
}

$ProbeScript = @'
import importlib.util
import platform
import sys
print(sys.executable)
print(platform.python_version())
print(importlib.util.find_spec('pygame') is not None)
'@

Write-Output "Bootstrapping GameDev env at: $ResolvedTarget"
Write-Output "Using Python command: $PythonCommand"
& $PythonCommand -c $ProbeScript

& $PythonCommand -m venv $ResolvedTarget

$EnvPython = Join-Path $ResolvedTarget "Scripts\python.exe"
if (-not (Test-Path $EnvPython)) {
    throw "Expected venv interpreter not found: $EnvPython"
}

& $EnvPython -m pip install --upgrade pip
& $EnvPython -m pip install -r (Join-Path $RepoRoot "requirements.txt")

Write-Output "Verifying pygame in bootstrapped env..."
& $EnvPython -c $ProbeScript
