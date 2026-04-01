# ACTION: CREATE
# filepath: c:\Users\malik\Documents\GitHub\KILO-FOOLISH\tools\ImportHealthCheck.ps1
# LOCATION: PowerShell automation wrapper

param(
    [switch]$Fix,
    [switch]$DryRun,
    [switch]$GenerateRequirements,
    [string]$OutputDir = ".",
    [switch]$Verbose
)

Write-Host "🔍 KILO-FOOLISH Import Health Checker" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Gray

# Ensure we're in the repository root
$repoRoot = "c:\Users\malik\Documents\GitHub\KILO-FOOLISH"
Set-Location $repoRoot

# Create tools directory if it doesn't exist
if (!(Test-Path "tools")) {
    New-Item -ItemType Directory -Path "tools" -Force
    Write-Host "✅ Created tools directory" -ForegroundColor Green
}

# Run the Python import checker
$pythonArgs = @("tools\import_health_checker.py", "--repository", $repoRoot)

if ($Fix) { $pythonArgs += "--fix" }
if ($DryRun) { $pythonArgs += "--dry-run" }
if ($GenerateRequirements) { $pythonArgs += "--generate-requirements" }
if ($OutputDir -ne ".") { $pythonArgs += @("--output-dir", $OutputDir) }

Write-Host "🚀 Running import health check..." -ForegroundColor Yellow

try {
    & python @pythonArgs

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Import health check completed successfully" -ForegroundColor Green

        # Show generated files
        if (Test-Path "import_health_report.json") {
            Write-Host "📊 Report generated: import_health_report.json" -ForegroundColor Cyan
        }

        if ($GenerateRequirements -and (Test-Path "requirements_missing.txt")) {
            Write-Host "📦 Missing packages file: requirements_missing.txt" -ForegroundColor Yellow

            # Show missing packages
            $missingPackages = Get-Content "requirements_missing.txt"
            if ($missingPackages) {
                Write-Host "`n🚫 Missing packages found:" -ForegroundColor Red
                foreach ($package in $missingPackages) {
                    Write-Host "  - $package" -ForegroundColor White
                }

                Write-Host "`n💡 To install missing packages, run:" -ForegroundColor Cyan
                Write-Host "pip install -r requirements_missing.txt" -ForegroundColor White
            }
        }
    }
    else {
        Write-Host "❌ Import health check failed" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error running import health checker: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "="*80 -ForegroundColor Gray
