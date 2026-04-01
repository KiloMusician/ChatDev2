# KILO-FOOLISH Repository Coordinator - PowerShell Interface

param(
    [switch]$Scan,
    [switch]$Organize,
    [switch]$Report,
    [switch]$AutoFix,
    [switch]$DryRun,    # This was missing the proper handling
    [switch]$Status
)

function Write-CoordinatorLog {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = Get-Date -Format "HH:mm:ss"
    $colors = @{
        "ERROR" = "Red"; "WARNING" = "Yellow"; "SUCCESS" = "Green"
        "INFO" = "Cyan"; "COORDINATOR" = "Magenta"
    }

    Write-Host "[$timestamp] [COORDINATOR] $Message" -ForegroundColor $colors[$Level]
}

# Fix the function parameter types

function Start-RepositoryCoordination {
    param(
        [bool]$AutoFix = $false,
        [bool]$DryRun = $true
    )

    Write-CoordinatorLog "🧭 Starting KILO-FOOLISH Repository Coordination..." "COORDINATOR"

    try {
        # Fix: Properly construct arguments array
        $pythonArgs = @()
        if ($AutoFix) { $pythonArgs += "--auto-fix" }
        if (!$DryRun) { $pythonArgs += "--no-dry-run" }  # Fix: Use negative logic

        if ($pythonArgs.Count -gt 0) {
            $result = python ".\src\core\RepositoryCoordinator.py" @pythonArgs 2>&1
        }
        else {
            $result = python ".\src\core\RepositoryCoordinator.py" 2>&1
        }

        if ($LASTEXITCODE -eq 0) {
            Write-CoordinatorLog "✅ Coordination completed successfully" "SUCCESS"

            # Display summary
            if (Test-Path ".\COORDINATION_REPORT.md") {
                Write-CoordinatorLog "📄 Report generated: COORDINATION_REPORT.md" "SUCCESS"

                # Show quick summary
                $reportContent = Get-Content ".\COORDINATION_REPORT.md" -Raw
                if ($reportContent -match "Organization Score\*\*:\s*(\d+)") {
                    $score = $matches[1]
                    $scoreColor = if ($score -gt 80) { "Green" } elseif ($score -gt 60) { "Yellow" } else { "Red" }
                    Write-Host "🎯 Organization Score: $score/100" -ForegroundColor $scoreColor
                }
            }
        }
        else {
            Write-CoordinatorLog "❌ Coordination failed: $result" "ERROR"
        }
    }
    catch {
        Write-CoordinatorLog "❌ Error during coordination: $_" "ERROR"
    }
}

function Show-CoordinationStatus {
    Write-CoordinatorLog "📊 KILO-FOOLISH Repository Status" "INFO"

    # Check if coordinator is set up
    if (!(Test-Path ".\src\core\RepositoryCoordinator.py")) {
        Write-CoordinatorLog "❌ Repository Coordinator not found" "ERROR"
        return
    }

    # Check configuration files
    $configFiles = @(
        ".\src\core\coordinator_config.json",
        ".\src\core\organization_rules.json"
    )

    foreach ($file in $configFiles) {
        if (Test-Path $file) {
            Write-CoordinatorLog "✅ $file exists" "SUCCESS"
        }
        else {
            Write-CoordinatorLog "⚠️ $file missing (will be created)" "WARNING"
        }
    }

    # Show recent coordination activity
    $logFile = ".\data\logs\coordinator.log"
    if (Test-Path $logFile) {
        Write-CoordinatorLog "📋 Recent Activity:" "INFO"
        $recentLogs = Get-Content $logFile -Tail 5
        foreach ($log in $recentLogs) {
            Write-Host "  $log" -ForegroundColor Gray
        }
    }

    # Check if report exists
    if (Test-Path ".\COORDINATION_REPORT.md") {
        $reportAge = (Get-Date) - (Get-Item ".\COORDINATION_REPORT.md").LastWriteTime
        Write-CoordinatorLog "📄 Last report: $($reportAge.Hours) hours ago" "INFO"
    }
    else {
        Write-CoordinatorLog "📄 No coordination report found" "WARNING"
    }
}

function Start-AutomaticCoordination {
    Write-CoordinatorLog "🤖 Starting automatic coordination mode..." "COORDINATOR"

    # Create VS Code task for continuous monitoring
    $taskContent = @{
        version = "2.0.0"
        tasks   = @(
            @{
                label        = "KILO Repository Coordinator"
                type         = "shell"
                command      = "python"
                args         = @("src/core/RepositoryCoordinator.py", "--continuous")
                group        = "build"
                presentation = @{
                    echo   = $true
                    reveal = "always"
                    focus  = $false
                    panel  = "new"
                }
                runOptions   = @{
                    runOn = "folderOpen"
                }
            }
        )
    }

    $vscodeDir = ".\.vscode"
    if (!(Test-Path $vscodeDir)) {
        New-Item -Path $vscodeDir -ItemType Directory -Force
    }

    $taskFile = "$vscodeDir\tasks.json"
    $taskContent | ConvertTo-Json -Depth 10 | Out-File $taskFile -Encoding UTF8

    Write-CoordinatorLog "✅ Automatic coordination configured" "SUCCESS"
    Write-CoordinatorLog "🎯 Run 'Tasks: Run Task' > 'KILO Repository Coordinator' in VS Code" "INFO"
}

# Main execution
Write-Host "`n🧭 KILO-FOOLISH Repository Coordinator" -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Magenta

if ($Scan) {
    Start-RepositoryCoordination -DryRun $true -AutoFix $false
}
elseif ($Organize) {
    if ($AutoFix) {
        Write-CoordinatorLog "⚠️ Auto-fix mode enabled - files will be moved!" "WARNING"
        $confirm = Read-Host "Continue? (y/N)"
        if ($confirm -eq 'y' -or $confirm -eq 'Y') {
            Start-RepositoryCoordination -DryRun $false -AutoFix $true
        }
        else {
            Write-CoordinatorLog "🚫 Operation cancelled" "WARNING"
        }
    }
    else {
        # Fix: Use $DryRun parameter properly
        $isDryRun = if ($DryRun) { $false } else { $true }
        Start-RepositoryCoordination -DryRun $isDryRun -AutoFix $false
    }
}
elseif ($Report) {
    if (Test-Path ".\COORDINATION_REPORT.md") {
        Write-CoordinatorLog "📖 Opening coordination report..." "INFO"
        code ".\COORDINATION_REPORT.md"
    }
    else {
        Write-CoordinatorLog "📄 No report found, running coordination first..." "WARNING"
        Start-RepositoryCoordination -DryRun $true -AutoFix $false
    }
}
elseif ($Status) {
    Show-CoordinationStatus
}
else {
    Write-CoordinatorLog "Available commands:" "INFO"
    Write-CoordinatorLog "  -Scan      : Scan repository and generate report" "INFO"
    Write-CoordinatorLog "  -Organize  : Organize files (add -AutoFix to actually move)" "INFO"
    Write-CoordinatorLog "  -Report    : View coordination report" "INFO"
    Write-CoordinatorLog "  -Status    : Show coordination status" "INFO"
    Write-CoordinatorLog "  -AutoFix   : Enable automatic file organization" "INFO"

    Write-Host "`n🚀 Quick start:" -ForegroundColor Yellow
    Write-Host "  .\src\core\RepositoryCoordinator.ps1 -Scan" -ForegroundColor White
}
