#requires -Version 5.1
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("doctor", "bootstrap", "smoke", "latest")]
    [string]$Action,
    [string]$SessionName = "",
    [string]$ResultJson = "",
    [string]$ReceiptDir = "",
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
$DefaultSmokeRepoRoot = "C:\dev\_sandboxes\chatdev-factory-prototype-smoke"
$DefaultSmokeSessionName = "gamedev_mechanic_smoke_repo_gamedev_local"
$DefaultReceiptDir = Join-Path $DefaultSmokeRepoRoot "WareHouse\_smoke_receipts"

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
        $EffectiveSessionName = $SessionName
        if ([string]::IsNullOrWhiteSpace($EffectiveSessionName)) {
            $EffectiveSessionName = $DefaultSmokeSessionName
        }
        $EffectiveReceiptDir = $ReceiptDir
        if ([string]::IsNullOrWhiteSpace($EffectiveReceiptDir)) {
            $EffectiveReceiptDir = $DefaultReceiptDir
        }
        $EffectiveResultJson = $ResultJson
        if ([string]::IsNullOrWhiteSpace($EffectiveResultJson)) {
            $EffectiveResultJson = Join-Path $EffectiveReceiptDir ($EffectiveSessionName + ".json")
        }

        $argsList = @("-ExecutionPolicy", "Bypass", "-File", $Smoke, "-Prompt", $Prompt)
        if (-not [string]::IsNullOrWhiteSpace($SessionName)) {
            $argsList += @("-SessionName", $SessionName)
        }
        if (-not [string]::IsNullOrWhiteSpace($EffectiveResultJson)) {
            $argsList += @("-ResultJson", $EffectiveResultJson)
        }
        if ($Json) {
            & powershell @argsList *> $null
            $exitCode = $LASTEXITCODE
            if (Test-Path $EffectiveResultJson) {
                Get-Content -Path $EffectiveResultJson
            }
            exit $exitCode
        }
        powershell @argsList
    }
    "latest" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($Latest)
        $EffectiveReceiptDir = $ReceiptDir
        if ([string]::IsNullOrWhiteSpace($EffectiveReceiptDir)) {
            $EffectiveReceiptDir = $DefaultReceiptDir
        }
        $argsList += @("--receipt-dir", $EffectiveReceiptDir)
        if (-not $Json) {
            $argsList += "--summary"
        }
        & $Python @argsList
    }
}
