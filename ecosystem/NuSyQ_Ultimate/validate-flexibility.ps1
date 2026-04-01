# NuSyQ Flexibility Validation Script
# ===================================

Write-Host "🔍 NuSyQ Flexibility Validation" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

$validationResults = @{
    "GitHub Authentication" = $false
    "Python Path Flexibility" = $false
    "Environment Configuration" = $false
    "VS Code Extension Auth" = $false
    "Docker Integration" = $false
    "Kubernetes Configuration" = $false
    "Brittleness Fixes" = @{}
}

# 1. Check GitHub Authentication
Write-Host "1. Validating GitHub Authentication..." -ForegroundColor Yellow
try {
    $authStatus = gh auth status 2>&1
    if ($authStatus -match "KiloMusician") {
        Write-Host "   ✅ Authenticated as KiloMusician" -ForegroundColor Green
        $validationResults["GitHub Authentication"] = $true
    } else {
        Write-Host "   ⚠️ GitHub authentication found but not for KiloMusician" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ GitHub authentication not configured" -ForegroundColor Red
}

# 2. Check Python Path Flexibility
Write-Host "2. Validating Python Path Flexibility..." -ForegroundColor Yellow
$envConfigPath = "config\environment.json"
if (Test-Path $envConfigPath) {
    $envConfig = Get-Content $envConfigPath -Raw | ConvertFrom-Json
    if ($envConfig.PYTHON_PATH -and (Test-Path $envConfig.PYTHON_PATH)) {
        Write-Host "   ✅ Python path configured and accessible" -ForegroundColor Green
        $validationResults["Python Path Flexibility"] = $true
    } else {
        Write-Host "   ⚠️ Python path configured but not accessible" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Environment configuration not found" -ForegroundColor Red
}

# 3. Check Environment Configuration
Write-Host "3. Validating Environment Configuration..." -ForegroundColor Yellow
if (Test-Path $envConfigPath) {
    $envConfig = Get-Content $envConfigPath -Raw | ConvertFrom-Json
    $requiredFields = @("GITHUB_USER", "NUSYQ_ROOT", "PYTHON_PATH")
    $missingFields = @()

    foreach ($field in $requiredFields) {
        if (-not $envConfig.$field) {
            $missingFields += $field
        }
    }

    if ($missingFields.Count -eq 0) {
        Write-Host "   ✅ All required environment fields present" -ForegroundColor Green
        $validationResults["Environment Configuration"] = $true
    } else {
        Write-Host "   ⚠️ Missing fields: $($missingFields -join ', ')" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Environment configuration file missing" -ForegroundColor Red
}

# 4. Check VS Code Extension Authentication
Write-Host "4. Validating VS Code Extension Authentication..." -ForegroundColor Yellow
$vscodeSettingsPath = ".vscode\settings.json"
if (Test-Path $vscodeSettingsPath) {
    $vscodeSettings = Get-Content $vscodeSettingsPath -Raw | ConvertFrom-Json
    if ($vscodeSettings."github.username" -eq "KiloMusician") {
        Write-Host "   ✅ VS Code configured for KiloMusician" -ForegroundColor Green
        $validationResults["VS Code Extension Auth"] = $true
    } else {
        Write-Host "   ⚠️ VS Code not configured for KiloMusician" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ VS Code settings not found" -ForegroundColor Red
}

# 5. Check Docker Integration
Write-Host "5. Validating Docker Integration..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "   ✅ Docker is available" -ForegroundColor Green
    $validationResults["Docker Integration"] = $true
} catch {
    Write-Host "   ⚠️ Docker not available (optional)" -ForegroundColor Yellow
}

# 6. Check Kubernetes Configuration
Write-Host "6. Validating Kubernetes Configuration..." -ForegroundColor Yellow
$kubeconfigPath = "$env:USERPROFILE\.kube\config"
if (Test-Path $kubeconfigPath) {
    Write-Host "   ✅ Kubeconfig exists" -ForegroundColor Green
    $validationResults["Kubernetes Configuration"] = $true
} else {
    Write-Host "   ❌ Kubeconfig not found" -ForegroundColor Red
}

# 7. Check for Brittleness Fixes
Write-Host "7. Validating Brittleness Fixes..." -ForegroundColor Yellow

# Check orchestrator script for flexible paths
$orchestratorPath = "NuSyQ.Orchestrator.ps1"
if (Test-Path $orchestratorPath) {
    $orchestratorContent = Get-Content $orchestratorPath -Raw

    # Check for flexible Python path function
    if ($orchestratorContent -match "Get-FlexiblePythonPath") {
        Write-Host "   ✅ Orchestrator uses flexible Python paths" -ForegroundColor Green
        $validationResults["Brittleness Fixes"]["Orchestrator Python Path"] = $true
    } else {
        Write-Host "   ⚠️ Orchestrator still uses hardcoded Python paths" -ForegroundColor Yellow
        $validationResults["Brittleness Fixes"]["Orchestrator Python Path"] = $false
    }

    # Check for environment config loading
    if ($orchestratorContent -match "environment\.json") {
        Write-Host "   ✅ Orchestrator loads environment configuration" -ForegroundColor Green
        $validationResults["Brittleness Fixes"]["Environment Config Loading"] = $true
    } else {
        Write-Host "   ⚠️ Orchestrator doesn't load environment config" -ForegroundColor Yellow
        $validationResults["Brittleness Fixes"]["Environment Config Loading"] = $false
    }
}

# Check ChatDev configurations for hardcoded paths
$chatdevConfigPath = "ChatDev\ecl\config.yaml"
if (Test-Path $chatdevConfigPath) {
    $chatdevConfig = Get-Content $chatdevConfigPath -Raw
    if ($chatdevConfig -match "C:\\|C:/") {
        Write-Host "   ⚠️ ChatDev config contains hardcoded paths" -ForegroundColor Yellow
        $validationResults["Brittleness Fixes"]["ChatDev Paths"] = $false
    } else {
        Write-Host "   ✅ ChatDev config appears flexible" -ForegroundColor Green
        $validationResults["Brittleness Fixes"]["ChatDev Paths"] = $true
    }
}

# Summary
Write-Host ""
Write-Host "📊 Validation Summary" -ForegroundColor Green
Write-Host "====================" -ForegroundColor Green

$totalChecks = 0
$passedChecks = 0

foreach ($check in $validationResults.Keys) {
    if ($check -ne "Brittleness Fixes") {
        $totalChecks++
        if ($validationResults[$check]) {
            $passedChecks++
            Write-Host "✅ $check" -ForegroundColor Green
        } else {
            Write-Host "❌ $check" -ForegroundColor Red
        }
    }
}

# Brittleness fixes summary
Write-Host ""
Write-Host "🔧 Brittleness Fixes:" -ForegroundColor Cyan
foreach ($fix in $validationResults["Brittleness Fixes"].Keys) {
    $totalChecks++
    if ($validationResults["Brittleness Fixes"][$fix]) {
        $passedChecks++
        Write-Host "   ✅ $fix" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $fix" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📈 Overall Score: $passedChecks/$totalChecks ($([math]::Round(($passedChecks/$totalChecks)*100, 1))%)" -ForegroundColor Cyan

if ($passedChecks -eq $totalChecks) {
    Write-Host "🎉 All flexibility validations passed!" -ForegroundColor Green
} elseif ($passedChecks / $totalChecks -gt 0.8) {
    Write-Host "✅ Good flexibility setup with minor issues" -ForegroundColor Yellow
} else {
    Write-Host "⚠️ Flexibility setup needs improvement" -ForegroundColor Red
}

# Save validation results
$validationResults | ConvertTo-Json -Depth 3 | Out-File -FilePath "Reports\flexibility-validation.json" -Encoding UTF8
Write-Host ""
Write-Host "📄 Detailed results saved to Reports\flexibility-validation.json" -ForegroundColor Cyan
