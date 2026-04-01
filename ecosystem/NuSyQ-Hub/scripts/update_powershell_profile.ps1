#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Updates PowerShell Profile with VS Code Shell Integration and KILO-FOOLISH Development Utilities

.DESCRIPTION
    This script adds VS Code shell integration and useful development shortcuts
    to your PowerShell profile for enhanced KILO-FOOLISH development workflow.

.EXAMPLE
    .\update_powershell_profile.ps1
#>

# Get the PowerShell profile path
$ProfilePath = $PROFILE

# Create profile directory if it doesn't exist
$ProfileDir = Split-Path $ProfilePath -Parent
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force
    Write-Host "✅ Created PowerShell profile directory: $ProfileDir" -ForegroundColor Green
}

# Profile content with VS Code integration and KILO-FOOLISH utilities
$ProfileContent = @'
# VS Code Shell Integration
if ($env:TERM_PROGRAM -eq "vscode") { . "$(code --locate-shell-integration-path pwsh)" }

# KILO-FOOLISH Development Environment Setup
# ===========================================

# Quick navigation aliases
Set-Alias -Name kilo -Value "Set-Location 'C:\Users\malik\Documents\GitHub\KILO-FOOLISH'"
Set-Alias -Name nusyq -Value "Set-Location 'C:\Users\malik\Desktop\NuSyQ-Hub'"

# Development shortcuts
function Start-KiloWatch { python "./src/core/ArchitectureWatcher.py" }
function Update-KiloArch { python "./src/core/ArchitectureScanner.py" }
function Test-KiloSystem { python "C:\Users\malik\Desktop\NuSyQ-Hub\test_github_validation.py" }

# Enhanced directory listing with colors
function ll { Get-ChildItem -Force | Format-Table -AutoSize }
function la { Get-ChildItem -Hidden -Force }

# Git shortcuts
function gs { git status }
function ga { git add . }
function gc { param($message) git commit -m $message }
function gp { git push }

# Python environment helpers
function Activate-Venv {
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & ".venv\Scripts\Activate.ps1"
    } elseif (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    } else {
        Write-Host "No virtual environment found in current directory" -ForegroundColor Red
    }
}

# ZETA Development Pipeline Shortcuts
function Start-ZetaSession {
    Write-Host "🚀 Starting ZETA Development Session..." -ForegroundColor Cyan
    nusyq
    Activate-Venv
}

function Run-ZetaTests {
    Write-Host "🧪 Running ZETA test suite..." -ForegroundColor Yellow
    python -m pytest tests/ -v
}

# Quantum Development Helpers
function Start-QuantumAnalysis {
    Write-Host "🌌 Starting Quantum Analysis..." -ForegroundColor Magenta
    python "./src/diagnostics/comprehensive_quantum_analysis.py"
}

# Repository Analysis Shortcuts
function Quick-SystemAnalysis {
    Write-Host "📊 Running Quick System Analysis..." -ForegroundColor Blue
    python "./src/diagnostics/quick_system_analyzer.py"
}

# Welcome message for KILO-FOOLISH development
Write-Host "🎯 KILO-FOOLISH Development Environment Ready!" -ForegroundColor Cyan
Write-Host "📁 Quick navigation: " -NoNewline -ForegroundColor Yellow
Write-Host "kilo" -NoNewline -ForegroundColor Green
Write-Host " | " -NoNewline -ForegroundColor Yellow
Write-Host "nusyq" -ForegroundColor Green
Write-Host "🚀 Development tools: " -NoNewline -ForegroundColor Yellow
Write-Host "Start-ZetaSession" -NoNewline -ForegroundColor Green
Write-Host " | " -NoNewline -ForegroundColor Yellow
Write-Host "Run-ZetaTests" -ForegroundColor Green
Write-Host "🌌 Quantum tools: " -NoNewline -ForegroundColor Yellow
Write-Host "Start-QuantumAnalysis" -NoNewline -ForegroundColor Magenta
Write-Host " | " -NoNewline -ForegroundColor Yellow
Write-Host "Quick-SystemAnalysis" -ForegroundColor Blue
'@

# Write the profile content
try {
    $ProfileContent | Out-File -FilePath $ProfilePath -Encoding UTF8 -Force
    Write-Host "✅ PowerShell profile updated successfully!" -ForegroundColor Green
    Write-Host "📍 Profile location: $ProfilePath" -ForegroundColor Cyan

    # Reload the profile in current session
    Write-Host "🔄 Reloading profile..." -ForegroundColor Yellow
    . $ProfilePath

    Write-Host ""
    Write-Host "🎉 VS Code shell integration and KILO-FOOLISH utilities are now active!" -ForegroundColor Green
    Write-Host "💡 Restart VS Code terminals to see the full integration effects." -ForegroundColor Yellow

} catch {
    Write-Error "❌ Failed to update PowerShell profile: $($_.Exception.Message)"
}
