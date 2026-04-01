# KILO-FOOLISH Auto-Setup Script
Write-Host "🧙‍♂️ KILO-FOOLISH Auto-Setup Starting..." -ForegroundColor Magenta

# Check if virtual environment is active
if (-not C:\Users\malik\Documents\GitHub\KILO-FOOLISH\ΞNuSyQ₁-Hub₁\.venv) {
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Cyan
    & "ΞNuSyQ₁-Hub₁\.venv\Scripts\Activate.ps1"
}

# Check if Ollama is running
try {
     = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Starting Ollama..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep 3
}

# Install required packages
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
pip install rich pandas requests ollama-python jupyter-client

Write-Host "🎉 Setup complete! Choose your adventure:" -ForegroundColor Green
Write-Host "1. Enhanced Wizard Navigator: python src\interface\Enhanced-Wizard-Navigator.py" -ForegroundColor Yellow
Write-Host "2. ChatDev Party System: python ΞNuSyQ₁-Hub₁\ChatDev-Party-System.py" -ForegroundColor Yellow
Write-Host "3. Original Wizard Navigator: python src\interface\wizard_navigator.py" -ForegroundColor Yellow
