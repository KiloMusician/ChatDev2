$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $scriptDir
$logDir = Join-Path $scriptDir 'logs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir 'orchestrator.log'
# Start the orchestrator with stdout/stderr redirected to log file
$python = 'python'
# Pass arguments as an array: first element is '-c', second element is the code string
$code = 'from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator; MultiAIOrchestrator().start_orchestration()'
Start-Process -FilePath $python -ArgumentList '-c', $code -WorkingDirectory $scriptDir -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru | Out-Null
Write-Host "Orchestrator start initiated, logging to $logFile"
