param(
    [string]$Task = 'help'
)

switch ($Task.ToLower()) {
    'install' { Write-Host 'Create venv manually and run: pip install -r requirements.txt' }
    'install-dev' { pip install -e "[dev]" }
    'lint' { ruff .; black --check . }
    'test' { pytest -q }
    'scan' { python -m src.tools.maze_solver . --max-depth 6 --progress }
    'orchestrator' { $env:PYTHONPATH = Convert-Path .; python -u scripts/start_multi_ai_orchestrator.py }
    'smoke' { $env:PYTHONPATH = Convert-Path .; python -u scripts/submit_orchestrator_test_task.py }
    default { Write-Host "Usage: .\scripts\dev.ps1 <install|install-dev|lint|test|scan|orchestrator|smoke>" }
}
