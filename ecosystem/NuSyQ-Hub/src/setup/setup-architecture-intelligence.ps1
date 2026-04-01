# KILO-FOOLISH Architecture Intelligence Setup

Write-Host "🏗️ Setting up KILO-FOOLISH Architecture Intelligence System..." -ForegroundColor Magenta

# Install required Python packages
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install watchdog psutil requests

# Create directory structure
$directories = @(
    ".\src\core",
    ".\docs\architecture",
    ".\data\logs"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force
        Write-Host "✅ Created: $dir" -ForegroundColor Green
    }
}

# Run initial architecture scan
Write-Host "🔍 Running initial architecture scan..." -ForegroundColor Cyan
python ".\src\core\ArchitectureScanner.py"

# Generate AI context
Write-Host "🧠 Generating AI context..." -ForegroundColor Cyan
.\src\core\AIContextGenerator.ps1 -Generate

# Create VS Code task for real-time monitoring
$vscodeTasks = @{
    version = "2.0.0"
    tasks   = @(
        @{
            label          = "Start Architecture Watcher"
            type           = "shell"
            command        = "python"
            args           = @("src/core/ArchitectureWatcher.py")
            group          = "build"
            presentation   = @{
                echo   = $true
                reveal = "always"
                focus  = $false
                panel  = "new"
            }
            problemMatcher = @()
        },
        @{
            label        = "Update Architecture"
            type         = "shell"
            command      = "python"
            args         = @("src/core/ArchitectureScanner.py")
            group        = "build"
            presentation = @{
                echo   = $true
                reveal = "always"
                focus  = $false
            }
        },
        @{
            label        = "Serve AI Context"
            type         = "shell"
            command      = "powershell"
            args         = @("-File", "src/core/AIContextGenerator.ps1", "-Serve")
            group        = "build"
            presentation = @{
                echo   = $true
                reveal = "always"
                focus  = $false
                panel  = "new"
            }
        }
    )
}

$vscodeDir = ".\.vscode"
if (!(Test-Path $vscodeDir)) {
    New-Item -Path $vscodeDir -ItemType Directory -Force
}

$tasksFile = "$vscodeDir\tasks.json"
$vscodeTasks | ConvertTo-Json -Depth 10 | Out-File $tasksFile -Encoding UTF8

Write-Host "✅ Architecture Intelligence System setup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "🎯 What's now available:" -ForegroundColor Cyan
Write-Host "  📄 ARCHITECTURE.md - Real-time repository map" -ForegroundColor White
Write-Host "  🤖 ai_context.json - AI system context" -ForegroundColor White
Write-Host "  🛣️ roadmap.json - Development roadmap" -ForegroundColor White
Write-Host "  👁️ Real-time monitoring system" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "🚀 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: Ctrl+Shift+P > 'Tasks: Run Task' > 'Start Architecture Watcher'" -ForegroundColor White
Write-Host "  2. Check ARCHITECTURE.md for your live repository map" -ForegroundColor White
Write-Host "  3. Use ai_context.json to inform AI systems" -ForegroundColor White
