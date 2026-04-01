# Quick fixes for Repository Coordinator errors

Write-Host "🔧 Fixing Repository Coordinator errors..." -ForegroundColor Yellow

# Fix 1: Update setup script
$setupFile = ".\setup-coordinator.ps1"
if (Test-Path $setupFile) {
    $content = Get-Content $setupFile -Raw
    $content = $content -replace "pip install hashlib pathlib datetime", "# Built-in modules - no installation needed"
    $content | Out-File $setupFile -Encoding UTF8
    Write-Host "✅ Fixed setup script" -ForegroundColor Green
}

# Fix 2: Create missing directories
$requiredDirs = @(".\src\core", ".\data\logs", ".\data\backups")
foreach ($dir in $requiredDirs) {
    if (!(Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force
        Write-Host "✅ Created missing directory: $dir" -ForegroundColor Green
    }
}

# Fix 3: Test Python file syntax
Write-Host "🔍 Testing Python syntax..." -ForegroundColor Cyan
if (Test-Path ".\src\core\RepositoryCoordinator.py") {
    $syntaxTest = python -m py_compile ".\src\core\RepositoryCoordinator.py" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python syntax OK" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Python syntax errors found: $syntaxTest" -ForegroundColor Red
    }
}

# Fix 4: Test PowerShell syntax
Write-Host "🔍 Testing PowerShell syntax..." -ForegroundColor Cyan
if (Test-Path ".\src\core\RepositoryCoordinator.ps1") {
    try {
        $null = Get-Command ".\src\core\RepositoryCoordinator.ps1" -Syntax -ErrorAction Stop
        Write-Host "✅ PowerShell syntax OK" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ PowerShell syntax error: $_" -ForegroundColor Red
    }
}

Write-Host "🎯 Error fixes complete!" -ForegroundColor Green
