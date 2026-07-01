#requires -Version 5.1
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("doctor", "bootstrap", "smoke")]
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
}
