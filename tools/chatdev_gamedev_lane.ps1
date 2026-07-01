#requires -Version 5.1
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("doctor", "bootstrap", "smoke", "latest")]
    [string]$Action,
    [string]$SessionName = "",
    [string]$ResultJson = "",
    [string]$Prompt = "Create the smallest possible playable pygame square-move demo. Keep it to one file.",
    [switch]$Json,
    [double]$Timeout = 2.0
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Doctor = Join-Path $ScriptDir "chatdev_colony_doctor.ps1"
$Bootstrapper = Join-Path $ScriptDir "bootstrap_gamedev_env.ps1"
$Smoke = Join-Path $ScriptDir "run_gamedev_mechanic_smoke.ps1"
$Latest = Join-Path $ScriptDir "latest_smoke_receipt.py"

switch ($Action) {
    "doctor" {
        $argsList = @("-ExecutionPolicy", "Bypass", "-File", $Doctor, "-Timeout", ([string]$Timeout))
        if ($Json) {
            $argsList += "-Json"
        }
        powershell @argsList
    }
    "bootstrap" {
        powershell -ExecutionPolicy Bypass -File $Bootstrapper
    }
    "smoke" {
        $argsList = @("-ExecutionPolicy", "Bypass", "-File", $Smoke, "-Prompt", $Prompt)
        if (-not [string]::IsNullOrWhiteSpace($SessionName)) {
            $argsList += @("-SessionName", $SessionName)
        }
        if (-not [string]::IsNullOrWhiteSpace($ResultJson)) {
            $argsList += @("-ResultJson", $ResultJson)
        }
        powershell @argsList
    }
    "latest" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($Latest)
        if (-not $Json) {
            $argsList += "--summary"
        }
        & $Python @argsList
    }
}
