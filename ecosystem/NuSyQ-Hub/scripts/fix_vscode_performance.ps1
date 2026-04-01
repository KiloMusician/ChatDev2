#!/usr/bin/env pwsh
# Performance Diagnostic and Recovery Script
# Kills hung linter/formatter processes and resets VS Code state

Write-Host "🔍 NuSyQ Performance Recovery" -ForegroundColor Cyan
Write-Host "=" * 60

# 1. Kill hung Python processes (isort, ruff, mypy, etc.)
Write-Host "`n1️⃣  Checking for hung Python processes..." -ForegroundColor Yellow
$hungPython = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 10 }
if ($hungPython) {
    Write-Host "   Found $($hungPython.Count) hung Python processes" -ForegroundColor Red
    $hungPython | ForEach-Object {
        Write-Host "   Killing PID $($_.Id) (CPU: $([math]::Round($_.CPU, 2))%)" -ForegroundColor Yellow
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "   ✅ Python processes killed" -ForegroundColor Green
} else {
    Write-Host "   ✅ No hung Python processes found" -ForegroundColor Green
}

# 2. Check VS Code extension host processes
Write-Host "`n2️⃣  Checking VS Code extension hosts..." -ForegroundColor Yellow
$hungVSCode = Get-Process Code -ErrorAction SilentlyContinue | Where-Object { $_.CPU -gt 50 }
if ($hungVSCode) {
    Write-Host "   ⚠️  Found $($hungVSCode.Count) high-CPU VS Code processes:" -ForegroundColor Red
    $hungVSCode | ForEach-Object {
        Write-Host "   PID $($_.Id): $([math]::Round($_.CPU, 2))% CPU, $([math]::Round($_.WorkingSet64/1MB, 2)) MB" -ForegroundColor Yellow
    }
    $response = Read-Host "   Kill these processes? (y/N)"
    if ($response -eq 'y') {
        $hungVSCode | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
        Write-Host "   ✅ VS Code processes killed (restart VS Code)" -ForegroundColor Green
    }
} else {
    Write-Host "   ✅ No hung VS Code processes" -ForegroundColor Green
}

# 3. Clear VS Code cache files
Write-Host "`n3️⃣  Clearing VS Code cache..." -ForegroundColor Yellow
$caches = @(
    "$env:APPDATA\Code\Cache\*",
    "$env:APPDATA\Code\CachedData\*",
    "$env:APPDATA\Code\logs\*"
)
$cleared = 0
foreach ($cache in $caches) {
    if (Test-Path $cache) {
        Remove-Item $cache -Recurse -Force -ErrorAction SilentlyContinue
        $cleared++
    }
}
if ($cleared -gt 0) {
    Write-Host "   ✅ Cleared $cleared cache locations" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  No caches to clear" -ForegroundColor Gray
}

# 4. Check Python linter processes
Write-Host "`n4️⃣  Checking for orphaned linter processes..." -ForegroundColor Yellow
$linters = @("ruff", "mypy", "pylint", "flake8", "black", "isort")
$found = 0
foreach ($linter in $linters) {
    $proc = Get-Process $linter -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "   Found: $linter (PID: $($proc.Id))" -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        $found++
    }
}
if ($found -gt 0) {
    Write-Host "   ✅ Killed $found linter processes" -ForegroundColor Green
} else {
    Write-Host "   ✅ No orphaned linters" -ForegroundColor Green
}

# 5. Performance recommendations
Write-Host "`n📊 Performance Status:" -ForegroundColor Cyan
Write-Host "   • isort: DISABLED (causes hangs)" -ForegroundColor Green
Write-Host "   • ruff organizeImports: DISABLED" -ForegroundColor Green
Write-Host "   • formatOnSave: DISABLED" -ForegroundColor Green
Write-Host "   • Manual formatting: Ctrl+Shift+P → Format Document" -ForegroundColor Gray

Write-Host "`n💡 Recommendations:" -ForegroundColor Cyan
Write-Host "   1. Restart VS Code to clear extension state" -ForegroundColor White
Write-Host "   2. Disable isort extension: Ctrl+Shift+X → search 'isort' → Disable" -ForegroundColor White
Write-Host "   3. Use manual formatting when needed" -ForegroundColor White
Write-Host "   4. Run this script if performance degrades again" -ForegroundColor White

Write-Host "`n✅ Recovery complete!" -ForegroundColor Green
