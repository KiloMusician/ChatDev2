#requires -Version 5.1
param(
    [string]$Prompt = "Create the smallest possible playable pygame square-move demo. Keep it to one file.",
    [string]$RepoRoot = "C:\dev\_sandboxes\chatdev-factory-prototype-smoke",
    [string]$SessionName = "",
    [string]$ResultJson = "",
    [double]$TimeoutSeconds = 240,
    [double]$PollInterval = 2,
    [double]$GraceSeconds = 20,
    [double]$PythonRunTimeoutSeconds = 5
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoPath = Split-Path -Parent $ScriptDir
$SmokeRunner = Join-Path $ScriptDir "workflow_smoke_runner.py"
$Bootstrapper = Join-Path $ScriptDir "bootstrap_gamedev_env.ps1"
$RuntimePython = Join-Path $RepoPath ".venv-gamedev313\Scripts\python.exe"
$YamlFile = Join-Path $RepoPath "yaml_instance\GameDev_mechanic_smoke.yaml"

if (-not (Test-Path $RuntimePython)) {
    Write-Output "Missing repo-local GameDev env; bootstrapping .venv-gamedev313..."
    powershell -ExecutionPolicy Bypass -File $Bootstrapper
}

if (-not (Test-Path $RuntimePython)) {
    throw "Expected GameDev runtime not found after bootstrap: $RuntimePython"
}

if ([string]::IsNullOrWhiteSpace($SessionName)) {
    $SessionName = "gamedev_mechanic_smoke_repo_gamedev_local"
}

if ([string]::IsNullOrWhiteSpace($ResultJson)) {
    $ReceiptDir = Join-Path $RepoRoot "WareHouse\_smoke_receipts"
    $ResultJson = Join-Path $ReceiptDir ($SessionName + ".json")
}

& $RuntimePython $SmokeRunner `
    --repo-root $RepoRoot `
    --source-root $RepoPath `
    --yaml-file $YamlFile `
    --task-prompt $Prompt `
    --session-name $SessionName `
    --timeout-seconds $TimeoutSeconds `
    --poll-interval $PollInterval `
    --grace-seconds $GraceSeconds `
    --stop-on-first-artifact `
    --validate-python-artifacts `
    --run-python-artifacts `
    --result-json $ResultJson `
    --runtime-python $RuntimePython `
    --python-run-timeout-seconds $PythonRunTimeoutSeconds
