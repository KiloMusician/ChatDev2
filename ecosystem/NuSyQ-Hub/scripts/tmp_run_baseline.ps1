$NusyqRoot = $env:NUSYQ_ROOT_PATH
if (-not $NusyqRoot) {
    $NusyqRoot = Join-Path $env:USERPROFILE "NuSyQ"
}
$env:CHATDEV_PATH = Join-Path $NusyqRoot "ChatDev"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:GITHUB_COPILOT_API_KEY = "dummy"
$env:MCP_SERVER_URL = "http://localhost:8081"
$env:NU_SYG_QUICK_CHECK = "1"
$env:PYTHONPATH = "."
Set-Location -LiteralPath $PSScriptRoot
python -m scripts.check_env | Tee-Object -FilePath baseline_check_env.txt
python -m src.diagnostics.quick_system_analyzer | Tee-Object -FilePath baseline_quick_system_analysis.txt
python scripts/comprehensive_modernization_audit.py > baseline_modernization_audit.json 2>&1
Write-Host 'Baseline run complete.'
