# KILO-FOOLISH Intelligent Commentary System - PowerShell Interface

param(
    [switch]$Start,
    [switch]$Session,
    [switch]$Status,
    [switch]$Stop,
    [int]$Interval = 5,
    [string]$Target
)

function Write-CommentaryLog {
    param([string]$Message, [string]$Level = "INFO")

    $colors = @{
        "ERROR" = "Red"; "WARNING" = "Yellow"; "SUCCESS" = "Green"
        "INFO" = "Cyan"; "COMMENTARY" = "Magenta"
    }

    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] [COMMENTARY] $Message" -ForegroundColor $colors[$Level]
}

function Start-IntelligentCommentary {
    param([bool]$Continuous = $false)

    Write-CommentaryLog "🧠 Starting KILO-FOOLISH Intelligent Commentary..." "COMMENTARY"

    try {
        if ($Continuous) {
            # Start continuous commentary
            $pythonArgs = @("--continuous")
            Write-CommentaryLog "Starting continuous commentary (Ctrl+C to stop)..." "INFO"
            python ".\src\core\IntelligentCommentary.py" @pythonArgs
        }
        else {
            # Run single session
            $result = python ".\src\core\IntelligentCommentary.py" --session 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-CommentaryLog "Commentary session completed successfully" "SUCCESS"
                Write-Host $result
            }
            else {
                Write-CommentaryLog "Commentary session failed: $result" "ERROR"
            }
        }
    }
    catch {
        Write-CommentaryLog "Error during commentary: $_" "ERROR"
    }
}

function Show-CommentaryStatus {
    Write-CommentaryLog "📊 KILO-FOOLISH Commentary System Status" "COMMENTARY"

    # Check if commentary system is set up
    if (!(Test-Path ".\src\core\IntelligentCommentary.py")) {
        Write-CommentaryLog "❌ Intelligent Commentary system not found" "ERROR"
        return
    }

    Write-CommentaryLog "✅ Intelligent Commentary system ready" "SUCCESS"

    # Check for commentary intelligence data
    if (Test-Path ".\src\core\commentary_intelligence.json") {
        try {
            $data = Get-Content ".\src\core\commentary_intelligence.json" | ConvertFrom-Json
            $historyCount = $data.comment_history.PSObject.Properties.Count
            $rulesCount = $data.commentary_rules.PSObject.Properties.Count

            Write-CommentaryLog "🧠 $historyCount comments in history, $rulesCount active rules" "INFO"

            if ($data.timestamp) {
                $lastRun = [DateTime]::Parse($data.timestamp)
                $timeSince = (Get-Date) - $lastRun
                Write-CommentaryLog "⏰ Last activity: $($timeSince.Hours) hours ago" "INFO"
            }
        }
        catch {
            Write-CommentaryLog "⚠️ Commentary intelligence data exists but couldn't be read" "WARNING"
        }
    }
    else {
        Write-CommentaryLog "📝 No commentary history found (will be created)" "INFO"
    }

    # Check commentary log
    $logFile = ".\data\logs\commentary.log"
    if (Test-Path $logFile) {
        $recentLines = Get-Content $logFile -Tail 3
        Write-CommentaryLog "📋 Recent activity:" "INFO"
        foreach ($line in $recentLines) {
            Write-Host "  $line" -ForegroundColor Gray
        }
    }
}

function Stop-CommentaryProcess {
    Write-CommentaryLog "🛑 Stopping commentary processes..." "WARNING"

    # Find and stop commentary processes
    $processes = Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*IntelligentCommentary*" }

    if ($processes) {
        foreach ($proc in $processes) {
            try {
                $proc.Kill()
                Write-CommentaryLog "Stopped commentary process (PID: $($proc.Id))" "SUCCESS"
            }
            catch {
                Write-CommentaryLog "Could not stop process $($proc.Id): $_" "WARNING"
            }
        }
    }
    else {
        Write-CommentaryLog "No active commentary processes found" "INFO"
    }
}

function New-CommentaryService {
    Write-CommentaryLog "⚙️ Setting up Commentary as Windows Service..." "INFO"

    # Create service wrapper script
    $serviceScript = @"
# KILO-FOOLISH Commentary Service Wrapper
Set-Location "$((Get-Location).Path)"

while (`$true) {
    try {
        python ".\src\core\IntelligentCommentary.py" --session
        Start-Sleep -Seconds 300  # 5 minutes
    }
    catch {
        Write-Host "Commentary service error: `$_"
        Start-Sleep -Seconds 60   # Wait 1 minute on error
    }
}
"@

    $serviceScript | Out-File ".\CommentaryService.ps1" -Encoding UTF8
    Write-CommentaryLog "✅ Service wrapper created: CommentaryService.ps1" "SUCCESS"
    Write-CommentaryLog "💡 Run as background job: Start-Job { .\CommentaryService.ps1 }" "INFO"
}

function Start-CommentaryJob {
    Write-CommentaryLog "🚀 Starting Commentary as background job..." "INFO"

    $jobScript = {
        param($WorkingDir)
        Set-Location $WorkingDir

        while ($true) {
            try {
                python ".\src\core\IntelligentCommentary.py" --session
                Start-Sleep -Seconds 300  # 5 minutes
            }
            catch {
                Write-Host "Commentary job error: $_"
                Start-Sleep -Seconds 60
            }
        }
    }

    $job = Start-Job -ScriptBlock $jobScript -ArgumentList (Get-Location).Path -Name "KILO-Commentary"

    if ($job) {
        Write-CommentaryLog "✅ Commentary job started (ID: $($job.Id))" "SUCCESS"
        Write-CommentaryLog "💡 Check status: Get-Job -Name 'KILO-Commentary'" "INFO"
        Write-CommentaryLog "💡 Stop job: Stop-Job -Name 'KILO-Commentary'" "INFO"
    }
    else {
        Write-CommentaryLog "❌ Failed to start commentary job" "ERROR"
    }
}

function Show-CommentaryJobs {
    Write-CommentaryLog "📋 Active Commentary Jobs:" "INFO"

    $jobs = Get-Job -Name "*Commentary*" -ErrorAction SilentlyContinue

    if ($jobs) {
        foreach ($job in $jobs) {
            $status = $job.State
            $statusColor = switch ($status) {
                "Running" { "Green" }
                "Completed" { "Yellow" }
                "Failed" { "Red" }
                default { "Gray" }
            }
            Write-Host "  Job $($job.Id): $($job.Name) - $status" -ForegroundColor $statusColor
        }
    }
    else {
        Write-CommentaryLog "No active commentary jobs found" "INFO"
    }
}

# Main execution
Write-Host "`n🧠 KILO-FOOLISH Intelligent Commentary System" -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Magenta

if ($Start) {
    Start-IntelligentCommentary -Continuous $true
}
elseif ($Session) {
    Start-IntelligentCommentary -Continuous $false
}
elseif ($Status) {
    Show-CommentaryStatus
    Show-CommentaryJobs
}
elseif ($Stop) {
    Stop-CommentaryProcess

    # Also stop background jobs
    $jobs = Get-Job -Name "*Commentary*" -ErrorAction SilentlyContinue
    if ($jobs) {
        Stop-Job -Name "*Commentary*"
        Remove-Job -Name "*Commentary*" -Force
        Write-CommentaryLog "Stopped and removed commentary jobs" "SUCCESS"
    }
}
else {
    Write-CommentaryLog "Available commands:" "INFO"
    Write-CommentaryLog "  -Start     : Start continuous commentary (5-minute intervals)" "INFO"
    Write-CommentaryLog "  -Session   : Run single commentary session" "INFO"
    Write-CommentaryLog "  -Status    : Show system status and recent activity" "INFO"
    Write-CommentaryLog "  -Stop      : Stop all commentary processes" "INFO"

    Write-Host "`n🚀 Quick actions:" -ForegroundColor Yellow
    Write-Host "  .\src\core\IntelligentCommentary.ps1 -Session" -ForegroundColor White
    Write-Host "  .\src\core\IntelligentCommentary.ps1 -Start" -ForegroundColor White

    Write-Host "`n💡 Background operation:" -ForegroundColor Cyan
    Write-Host "  Start-CommentaryJob      # Run as PowerShell background job" -ForegroundColor White
    Write-Host "  Get-Job -Name '*Commentary*'    # Check job status" -ForegroundColor White
}
