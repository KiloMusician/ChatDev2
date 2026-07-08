#requires -Version 5.1
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("doctor", "local-proof", "local-start", "local-stop", "local-status", "bootstrap", "smoke", "latest", "latest-full", "status", "status-full", "status-compact")]
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
$DoctorPy = Join-Path $ScriptDir "chatdev_colony_doctor.py"
$LocalApp = Join-Path $ScriptDir "local_devall_app.py"
$Bootstrapper = Join-Path $ScriptDir "bootstrap_gamedev_env.ps1"
$Smoke = Join-Path $ScriptDir "run_gamedev_mechanic_smoke.ps1"
$Latest = Join-Path $ScriptDir "latest_smoke_receipt.py"
$Status = Join-Path $ScriptDir "chatdev_gamedev_status.py"
$DefaultSmokeRepoRoot = "C:\dev\_sandboxes\chatdev-factory-prototype-smoke"
$DefaultSmokeSessionName = "gamedev_mechanic_smoke_repo_gamedev_local"
$DefaultReceiptDir = Join-Path $DefaultSmokeRepoRoot "WareHouse\_smoke_receipts"

switch ($Action) {
    "doctor" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($DoctorPy, "--timeout", ([string]$Timeout))
        if ($Json) {
            $argsList += "--json"
        }
        & $Python @argsList
    }
    "local-proof" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($DoctorPy, "--timeout", ([string]$Timeout), "--local-proof")
        if ($Json) {
            $argsList += "--json"
        }
        & $Python @argsList
    }
    "local-start" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        & $Python $LocalApp start --timeout ([string]([Math]::Max($Timeout, 20.0)))
    }
    "local-stop" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        & $Python $LocalApp stop --timeout ([string]([Math]::Max($Timeout, 10.0)))
    }
    "local-status" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        & $Python $LocalApp status
    }
    "bootstrap" {
        powershell -NoProfile -ExecutionPolicy Bypass -File $Bootstrapper
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

        $argsList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $Smoke, "-Prompt", $Prompt)
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
    "latest-full" {
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
        & $Python @argsList
    }
    "status" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($Status, "--timeout", ([string]$Timeout))
        $EffectiveReceiptDir = $ReceiptDir
        if ([string]::IsNullOrWhiteSpace($EffectiveReceiptDir)) {
            $EffectiveReceiptDir = $DefaultReceiptDir
        }
        $argsList += @("--receipt-dir", $EffectiveReceiptDir)
        if ($Json) {
            $argsList += "--json"
        }
        & $Python @argsList
    }
    "status-full" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($Status, "--timeout", ([string]$Timeout), "--json")
        $EffectiveReceiptDir = $ReceiptDir
        if ([string]::IsNullOrWhiteSpace($EffectiveReceiptDir)) {
            $EffectiveReceiptDir = $DefaultReceiptDir
        }
        $argsList += @("--receipt-dir", $EffectiveReceiptDir)
        & $Python @argsList
    }
    "status-compact" {
        $Python = Join-Path (Split-Path -Parent $ScriptDir) ".venv-gamedev313\Scripts\python.exe"
        if (-not (Test-Path $Python)) {
            $Python = "python"
        }
        $argsList = @($Status, "--timeout", ([string]$Timeout), "--automation-summary-only")
        $EffectiveReceiptDir = $ReceiptDir
        if ([string]::IsNullOrWhiteSpace($EffectiveReceiptDir)) {
            $EffectiveReceiptDir = $DefaultReceiptDir
        }
        $argsList += @("--receipt-dir", $EffectiveReceiptDir)
        & $Python @argsList
    }
}
