#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Weekly Adoption Metrics Runner for Windows Task Scheduler

.DESCRIPTION
    Runs orphan symbol adoption metrics and saves results to timestamped JSON file.
    Designed for Windows Task Scheduler automation (weekly Monday 9am).

.EXAMPLE
    .\run_weekly_adoption_metrics.ps1
    
.NOTES
    Author: NuSyQ Development Team
    Date: 2026-02-17
    Schedule: Weekly (Monday 9:00 AM)
#>

[CmdletBinding()]
param()

# Configuration
$projectRoot = Split-Path -Parent $PSScriptRoot
$reportsDir = Join-Path $projectRoot "reports"
$date = Get-Date -Format "yyyyMMdd"
$outputFile = Join-Path $reportsDir "adoption_$date.json"

# Ensure reports directory exists
if (-not (Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null
    Write-Output "📁 Created reports directory: $reportsDir"
}

# Change to project root
Push-Location $projectRoot

try {
    Write-Output "=" * 70
    Write-Output "📊 Weekly Adoption Metrics Tracker"
    Write-Output "=" * 70
    Write-Output "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Output "Output: $outputFile"
    Write-Output ""

    # Run adoption metrics
    Write-Output "🔍 Running adoption metrics analysis..."
    python scripts/orphan_adoption_metrics.py --json --save $outputFile

    if ($LASTEXITCODE -eq 0) {
        Write-Output ""
        Write-Output "✅ Adoption metrics saved successfully"
        Write-Output "📄 File: $outputFile"
        
        # Display file size
        $fileSize = (Get-Item $outputFile).Length
        Write-Output "📦 Size: $fileSize bytes"
        
        # Quick summary
        $metrics = Get-Content $outputFile | ConvertFrom-Json
        Write-Output ""
        Write-Output "📈 Quick Summary:"
        Write-Output "  Total Symbols:     $($metrics.total_symbols)"
        Write-Output "  Adoption Rate:     $($metrics.adoption_rate)%"
        Write-Output "  CLI Invocations:   $($metrics.cli_invocations)"
        
        # Archive old reports (keep last 12 weeks)
        $oldReports = Get-ChildItem -Path $reportsDir -Filter "adoption_*.json" | 
                      Sort-Object LastWriteTime -Descending | 
                      Select-Object -Skip 12
        
        if ($oldReports) {
            Write-Output ""
            Write-Output "🗑️  Archiving old reports (keeping last 12 weeks)..."
            $archiveDir = Join-Path $reportsDir "archive"
            if (-not (Test-Path $archiveDir)) {
                New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
            }
            
            foreach ($report in $oldReports) {
                Move-Item -Path $report.FullName -Destination $archiveDir -Force
                Write-Output "  Archived: $($report.Name)"
            }
        }
        
        exit 0
    } else {
        Write-Error "❌ Adoption metrics script failed with exit code $LASTEXITCODE"
        exit 1
    }
} catch {
    Write-Error "❌ Error running adoption metrics: $_"
    Write-Error $_.Exception.Message
    exit 1
} finally {
    Pop-Location
}
