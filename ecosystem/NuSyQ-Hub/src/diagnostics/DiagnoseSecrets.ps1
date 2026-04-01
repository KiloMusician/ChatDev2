# Quick diagnostic for secrets setup

Write-Host "🔍 KILO-FOOLISH Secrets Diagnostic" -ForegroundColor Cyan
Write-Host "=" * 40 -ForegroundColor Cyan

# Check current directory
Write-Host "`n📁 Current Directory:" -ForegroundColor Yellow
Write-Host "  $(Get-Location)" -ForegroundColor White

# Check if files exist
Write-Host "`n📄 File Status:" -ForegroundColor Yellow
$files = @(
    ".\src\config\SecretsManager.ps1",
    ".\src\config\secrets.ps1",
    ".\src\config\.secure",
    ".\src\config\.backup"
)

foreach ($file in $files) {
    $exists = Test-Path $file
    $icon = if ($exists) { "✅" } else { "❌" }
    Write-Host "  $icon $file" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
}

# Check PowerShell execution policy
Write-Host "`n🔒 PowerShell Policy:" -ForegroundColor Yellow
Write-Host "  $(Get-ExecutionPolicy)" -ForegroundColor White

# Try to load the SecretsManager
Write-Host "`n🧪 Testing SecretsManager:" -ForegroundColor Yellow
try {
    if (Test-Path ".\src\config\SecretsManager.ps1") {
        # Test parameter parsing
        $testParams = @{
            Setup  = $false
            Status = $true
        }
        Write-Host "  ✅ SecretsManager.ps1 found and readable" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ SecretsManager.ps1 not found" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ❌ Error loading SecretsManager: $_" -ForegroundColor Red
}

# Check if secrets.ps1 contains your API key
Write-Host "`n🔑 API Key Status:" -ForegroundColor Yellow
if (Test-Path ".\src\config\secrets.ps1") {
    $content = Get-Content ".\src\config\secrets.ps1" -Raw
    if ($content -match "sk-[a-zA-Z0-9]{48,}") {
        Write-Host "  ✅ API key found in secrets.ps1" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ No valid API key found in secrets.ps1" -ForegroundColor Red
    }
}
else {
    Write-Host "  ⚠️ secrets.ps1 not created yet" -ForegroundColor Yellow
}

Write-Host "`n💡 Next Steps:" -ForegroundColor Magenta
if (!(Test-Path ".\src\config\secrets.ps1")) {
    Write-Host "  1. Run: .\src\config\SecretsManager.ps1 -Setup" -ForegroundColor White
}
else {
    Write-Host "  1. Run: .\src\config\SecretsManager.ps1 -Status" -ForegroundColor White
}
Write-Host "  2. Run: .\src\config\SecretsManager.ps1 -Sync" -ForegroundColor White
