# Enhanced Context Browser Desktop App Launcher
# Launches the app in a dedicated window with app-like behavior

Write-Host "🚀 Enhanced Context Browser Desktop App" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

$AppPath = Join-Path $PSScriptRoot "Enhanced-Interactive-Context-Browser-Fixed.py"
$Port = 8501

Write-Host "📍 Starting Enhanced Context Browser..." -ForegroundColor Yellow

# Kill any existing Streamlit processes
Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force

# Start Streamlit with app-optimized settings
$StreamlitArgs = @(
    "run"
    $AppPath
    "--server.headless=false"
    "--server.runOnSave=true"
    "--browser.gatherUsageStats=false"
    "--theme.base=dark"
    "--server.address=localhost"
    "--server.port=$Port"
    "--global.developmentMode=false"
    "--server.maxUploadSize=200"
)

Write-Host "🔧 Launching with optimized settings..." -ForegroundColor Green

try {
    # Start Streamlit in background
    $Process = Start-Process -FilePath "streamlit" -ArgumentList $StreamlitArgs -PassThru -WindowStyle Hidden

    # Wait a moment for startup
    Start-Sleep -Seconds 3

    # Open in default browser (will feel more app-like)
    $Url = "http://localhost:$Port"
    Write-Host "🌐 Opening app at: $Url" -ForegroundColor Green
    Start-Process $Url

    Write-Host "✅ Enhanced Context Browser is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎮 App Features Available:" -ForegroundColor Cyan
    Write-Host "  📊 Dashboard - Repository overview and metrics"
    Write-Host "  🔍 Deep Analysis - Detailed file analysis"
    Write-Host "  🕸️ Relationships - Dependency mapping"
    Write-Host "  🏷️ Tag Explorer - Intelligent tagging system"
    Write-Host "  📈 Metrics & Trends - Data visualization"
    Write-Host "  🔧 System Health - Component monitoring"
    Write-Host "  🎮 Interactive - AI assistant and custom queries"
    Write-Host "  📜 Logs - Real-time log viewing"
    Write-Host ""
    Write-Host "🛑 Press Ctrl+C to stop the app" -ForegroundColor Red

    # Keep the script running until user stops it
    try {
        while ($Process -and !$Process.HasExited) {
            Start-Sleep -Seconds 1
        }
    }
    catch {
        Write-Host "🛑 Stopping Enhanced Context Browser..." -ForegroundColor Yellow
    }
    finally {
        if ($Process -and !$Process.HasExited) {
            $Process.Kill()
        }
        Write-Host "✅ App stopped successfully" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Error launching app: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Make sure Streamlit is installed: pip install streamlit" -ForegroundColor Yellow
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
