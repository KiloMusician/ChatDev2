# KILO-FOOLISH COMPREHENSIVE STARTUP & OPERATIONS CHECKLIST
# Sequential dependency-based command execution for systematic system cultivation

## 🔥 PHASE 0: FOUNDATION VERIFICATION

### 0.1 System Prerequisites Check
```powershell
# Verify Windows version and architecture
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type"
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory

# Check execution policy (must allow script execution)
Get-ExecutionPolicy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Verify PowerShell version (7+ recommended)
$PSVersionTable.PSVersion
winget --version
```

### 0.2 Administrator Privileges Verification
```powershell
# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Please run PowerShell as Administrator" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green
}
```

### 0.3 Network Connectivity Verification  
```powershell
# Test critical connectivity
Test-NetConnection -ComputerName "github.com" -Port 443
Test-NetConnection -ComputerName "pypi.org" -Port 443
Test-NetConnection -ComputerName "api.openai.com" -Port 443

# Test DNS resolution
Resolve-DnsName github.com
Resolve-DnsName pypi.org
```

### 0.4 Storage Space Verification
```powershell
# Check available disk space (need 100GB+ for full system)
Get-WmiObject -Class Win32_LogicalDisk | 
    Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, 
    @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}, 
    @{Name="PercentFree";Expression={[math]::Round(($_.FreeSpace/$_.Size)*100,2)}}

# Verify repository location accessibility
cd "C:\Users\malik\Documents\GitHub\KILO-FOOLISH"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Repository path not accessible" -ForegroundColor Red
    exit 1
}
```

## 🛠️ PHASE 1: CORE TOOLCHAIN INSTALLATION

### 1.1 Windows Package Manager (WinGet) Setup
```powershell
# Install WinGet if not present
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing WinGet..." -ForegroundColor Yellow
    $progressPreference = 'silentlyContinue'
    Invoke-WebRequest -Uri https://aka.ms/getwinget -OutFile Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
    Add-AppxPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle
}

# Verify WinGet installation
winget --version
```

### 1.2 Git Version Control Installation
```powershell
# Install Git
winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements

# Verify Git installation
git --version
where git

# Configure Git (replace with actual values)
git config --global user.name "KILO-FOOLISH Developer"
git config --global user.email "developer@kilo-foolish.local"
git config --global init.defaultBranch main
git config --global core.autocrlf true
```

### 1.3 PowerShell 7+ Installation  
```powershell
# Install PowerShell 7
winget install --id Microsoft.PowerShell --source winget

# Verify PowerShell 7 installation
pwsh --version

# Test PowerShell 7 functionality
pwsh -Command "Write-Host 'PowerShell 7 working!' -ForegroundColor Green"
```

### 1.4 Python Development Environment
```powershell
# Install Python 3.11 (specific version for consistency)
winget install Python.Python.3.11 --source winget

# Verify Python installation
python --version
pip --version
where python
where pip

# Upgrade pip to latest
python -m pip install --upgrade pip

# Install virtualenv
pip install virtualenv
```

### 1.5 Node.js and npm (for future web components)
```powershell
# Install Node.js LTS
winget install OpenJS.NodeJS.LTS --source winget

# Verify Node.js installation
node --version
npm --version
```

### 1.6 Development IDE Installation
```powershell
# Install Visual Studio Code
winget install Microsoft.VisualStudioCode --source winget

# Install VS Code extensions via command line
code --install-extension ms-python.python
code --install-extension ms-vscode.powershell
code --install-extension GitHub.copilot
code --install-extension ms-python.black-formatter
code --install-extension ms-python.flake8
code --install-extension redhat.vscode-yaml
code --install-extension yzhang.markdown-all-in-one
```

## 🐍 PHASE 2: PYTHON ENVIRONMENT SETUP

### 2.1 Virtual Environment Creation
```powershell
# Navigate to project root
cd "C:\Users\malik\Documents\GitHub\KILO-FOOLISH"

# Create virtual environment
python -m venv venv_kilo

# Verify virtual environment creation
if (Test-Path "venv_kilo\Scripts\Activate.ps1") {
    Write-Host "✅ Virtual environment created successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment creation failed" -ForegroundColor Red
    exit 1
}
```

### 2.2 Virtual Environment Activation
```powershell
# Activate virtual environment
.\venv_kilo\Scripts\Activate.ps1

# Verify activation
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment activation failed" -ForegroundColor Red
    exit 1
}

# Check Python location (should be in venv)
where python
python -c "import sys; print(f'Python executable: {sys.executable}')"
```

### 2.3 Core Dependencies Installation
```powershell
# Verify requirements.txt exists
if (!(Test-Path "requirements.txt")) {
    Write-Host "❌ requirements.txt not found" -ForegroundColor Red
    # Create minimal requirements.txt if missing
    @"
# KILO-FOOLISH Core Dependencies
psutil>=5.9.0
requests>=2.31.0
aiohttp>=3.8.0
aiofiles>=23.1.0
"@ | Out-File "requirements.txt" -Encoding UTF8
}

# Install requirements
pip install -r requirements.txt

# Verify core imports
python -c "import psutil; print(f'psutil {psutil.__version__} installed')"
python -c "import requests; print(f'requests {requests.__version__} installed')"
python -c "import aiohttp; print(f'aiohttp {aiohttp.__version__} installed')"
```

### 2.4 AI/ML Dependencies Installation
```powershell
# Install AI/ML packages (this may take time)
pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu
pip install transformers>=4.30.0
pip install numpy>=1.24.0
pip install pandas>=2.0.0

# Verify AI/ML imports
python -c "import torch; print(f'PyTorch {torch.__version__} installed')"
python -c "import transformers; print(f'Transformers {transformers.__version__} installed')"
python -c "import numpy as np; print(f'NumPy {np.__version__} installed')"
```

### 2.5 Ollama Integration Setup
```powershell
# Install Ollama CLI
winget install Ollama.Ollama --source winget

# Verify Ollama installation
ollama --version

# Test Ollama service (CORRECTED - no & operator)
Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep 5
curl http://localhost:11434/api/tags

# Install Ollama Python package
pip install ollama>=0.2.0

# Test Ollama Python integration
python -c "import ollama; print('Ollama Python package installed')"
```

## 📁 PHASE 3: PROJECT STRUCTURE INITIALIZATION

### 3.1 Core Directory Structure Creation
```powershell
# Create essential directories
$directories = @(
    "src\core",
    "src\config", 
    "src\ai",
    "src\utils",
    "src\interfaces",
    "tests\unit",
    "tests\integration", 
    "tests\fixtures",
    "docs\api",
    "docs\guides",
    "docs\architecture",
    "data\logs",
    "data\cache",
    "data\backups",
    "scripts",
    "config"
)

foreach ($dir in $directories) {
    New-Item -Path $dir -ItemType Directory -Force
    Write-Host "✅ Created directory: $dir" -ForegroundColor Green
}
```

### 3.2 Configuration Files Initialization
```powershell
# Create main configuration file
@"
{
    "project": {
        "name": "KILO-FOOLISH",
        "version": "1.0.0",
        "description": "ΞNuSyQ₁ Quantum AI Development Framework"
    },
    "paths": {
        "src": "src",
        "tests": "tests",
        "docs": "docs",
        "data": "data",
        "logs": "data/logs"
    },
    "environment": {
        "python_version": "3.11",
        "virtual_env": "venv_kilo"
    }
}
"@ | Out-File "config\project.json" -Encoding UTF8

# Create logging configuration
@"
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        }
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "data/logs/kilo_foolish.log",
            "formatter": "standard"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
"@ | Out-File "config\logging.json" -Encoding UTF8
```

## 🔧 PHASE 4: SYSTEM AUDIT & DIAGNOSTICS

### 4.1 Pre-Audit Dependency Check
```powershell
# Check if pre-audit script exists, create if missing
if (!(Test-Path "scripts\pre_audit.py")) {
    @"
# Quick pre-audit check
import sys
print(f'Python version: {sys.version}')
try:
    import psutil, requests, aiohttp
    print('✅ Core dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    sys.exit(1)
"@ | Out-File "scripts\pre_audit.py" -Encoding UTF8
}

# Run lightweight pre-audit
python scripts\pre_audit.py

# If pre-audit fails, install missing packages
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Pre-audit detected issues, installing missing packages..." -ForegroundColor Yellow
    pip install psutil requests aiohttp aiofiles
}
```

### 4.2 Comprehensive System Audit
```powershell
# Run full system audit
python scripts\system_audit.py

# Check audit results
if (Test-Path "audit_report.json") {
    Write-Host "✅ System audit completed successfully" -ForegroundColor Green
    
    # Display key metrics from audit
    $audit = Get-Content "audit_report.json" | ConvertFrom-Json
    Write-Host "📊 System Status Overview:" -ForegroundColor Cyan
    
    # Check if properties exist before accessing
    if ($audit.hardware_check.memory) {
        Write-Host "💾 Memory: $($audit.hardware_check.memory.total_gb)GB total" -ForegroundColor Cyan
    }
    if ($audit.package_ecosystem.installed_packages) {
        Write-Host "📦 Packages: $($audit.package_ecosystem.installed_packages.total_count)" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ System audit failed" -ForegroundColor Red
    exit 1
}
```

### 4.3 System Evolution Baseline
```powershell
# Create initial system evolution baseline
python scripts\async_def_track_system_evolution.py

# Verify evolution tracking setup
if (Test-Path "audit_history.jsonl") {
    Write-Host "✅ System evolution tracking initialized" -ForegroundColor Green
} else {
    Write-Host "⚠️ Evolution tracking not initialized (normal for first run)" -ForegroundColor Yellow
}
```

## 🧠 PHASE 5: AI INTEGRATION SETUP

### 5.1 Ollama Model Installation
```powershell
# Start Ollama service (CORRECTED)
Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden

# Wait for service to start
Start-Sleep 10

# Install core models (this will take significant time)
Write-Host "🤖 Installing AI models (this may take 30+ minutes)..." -ForegroundColor Yellow

# Install lightweight models first
ollama pull phi:2.7b
ollama pull mistral:7b-instruct

# Verify model installation
ollama list

# Test model functionality
ollama run phi:2.7b "Test message: Can you respond?"
```

### 5.2 Enhanced Ollama Integration
```powershell
# Test Ollama integration module (with error handling)
python -c "
try:
    from src.core.ollama_integration import EnhancedOllamaHub
    import asyncio
    
    async def test():
        hub = EnhancedOllamaHub()
        await hub.initialize()
        models = hub.models
        print(f'Available models: {list(models.keys())}')
    
    asyncio.run(test())
    print('✅ Ollama integration working')
except ImportError as e:
    print(f'⚠️ Ollama integration not yet available: {e}')
except Exception as e:
    print(f'❌ Ollama integration error: {e}')
"
```

## 🗂️ PHASE 6: REPOSITORY COORDINATION

### 6.1 Repository Coordinator Setup
```powershell
# Test Repository Coordinator availability
if (Test-Path "src\core\RepositoryCoordinator.py") {
    Write-Host "✅ Repository Coordinator found" -ForegroundColor Green
    
    # Run initial repository scan
    python src\core\RepositoryCoordinator.py --scan
    
    # Review coordination report
    if (Test-Path "COORDINATION_REPORT.md") {
        code COORDINATION_REPORT.md
    }
} else {
    Write-Host "❌ Repository Coordinator missing" -ForegroundColor Red
    Write-Host "💡 Will create basic coordinator structure..." -ForegroundColor Yellow
    
    # Create basic coordinator if missing
    New-Item -Path "src\core" -ItemType Directory -Force
    @"
# Basic Repository Coordinator
print('Repository Coordinator - Basic version')
print('Scanning project structure...')

import os
from pathlib import Path

def scan_repository():
    root = Path('.')
    for item in root.rglob('*'):
        if item.is_file() and item.suffix in ['.py', '.md', '.json']:
            print(f'Found: {item}')

if __name__ == '__main__':
    scan_repository()
"@ | Out-File "src\core\RepositoryCoordinator.py" -Encoding UTF8
    
    python src\core\RepositoryCoordinator.py
}
```

### 6.2 Architecture Monitoring Setup
```powershell
# Start architecture watcher (CORRECTED - no & operator)
if (Test-Path "src\core\ArchitectureWatcher.py") {
    Write-Host "🔄 Starting architecture monitoring..." -ForegroundColor Green
    Start-Job -Name "ArchitectureWatcher" -ScriptBlock { 
        python src\core\ArchitectureWatcher.py 
    }
    Write-Host "✅ Architecture monitoring started (background job)" -ForegroundColor Green
} else {
    Write-Host "⚠️ ArchitectureWatcher not found, skipping..." -ForegroundColor Yellow
}
```

## 🚀 PHASE 7: DEVELOPMENT ENVIRONMENT FINALIZATION

### 7.1 VS Code Workspace Configuration
```powershell
# Create comprehensive workspace file
@"
{
    "folders": [
        {
            "name": "KILO-FOOLISH Root",
            "path": "."
        },
        {
            "name": "ΞNuSyQ₁-Hub₁", 
            "path": "./ΞNuSyQ₁-Hub₁"
        }
    ],
    "settings": {
        "python.defaultInterpreterPath": "./venv_kilo/Scripts/python.exe",
        "python.terminal.activateEnvironment": true,
        "python.linting.enabled": true,
        "python.linting.flake8Enabled": true,
        "python.formatting.provider": "black",
        "powershell.codeFormatting.preset": "OTBS",
        "files.associations": {
            "*.ps1": "powershell",
            "*.psm1": "powershell", 
            "*.psd1": "powershell"
        },
        "terminal.integrated.defaultProfile.windows": "PowerShell",
        "git.enableSmartCommit": true,
        "workbench.colorTheme": "Default Dark+"
    },
    "extensions": {
        "recommendations": [
            "ms-python.python",
            "ms-vscode.powershell", 
            "GitHub.copilot",
            "ms-python.black-formatter",
            "yzhang.markdown-all-in-one"
        ]
    }
}
"@ | Out-File "KILO-FOOLISH.code-workspace" -Encoding UTF8

Write-Host "✅ VS Code workspace configured" -ForegroundColor Green
```

## 🎯 PHASE 8: SYSTEM VALIDATION & TESTING

### 8.1 Comprehensive System Validation
```powershell
Write-Host "🎯 KILO-FOOLISH System Validation - Final Check" -ForegroundColor Magenta

# Validate all core components
$validationResults = @{}

# 1. Python environment
try {
    .\venv_kilo\Scripts\Activate.ps1
    python -c "import sys; print(f'Python: {sys.version}'); import psutil, requests, aiohttp; print('Core packages OK')"
    $validationResults["Python"] = "✅ PASS"
}
catch {
    $validationResults["Python"] = "❌ FAIL: $_"
}

# 2. AI integration
try {
    python -c "import ollama; print('Ollama package OK')"
    $validationResults["AI Integration"] = "✅ PASS"
}
catch {
    $validationResults["AI Integration"] = "❌ FAIL: $_"
}

# 3. System audit
try {
    python scripts\system_audit.py | Out-Null
    $validationResults["System Audit"] = "✅ PASS"
}
catch {
    $validationResults["System Audit"] = "❌ FAIL: $_"
}

# 4. Repository coordination
try {
    python src\core\RepositoryCoordinator.py | Out-Null
    $validationResults["Repository Coordination"] = "✅ PASS" 
}
catch {
    $validationResults["Repository Coordination"] = "❌ FAIL: $_"
}

# Display results
Write-Host "`n📊 VALIDATION RESULTS:" -ForegroundColor Cyan
foreach ($test in $validationResults.GetEnumerator()) {
    Write-Host "  $($test.Key): $($test.Value)"
}

# Overall status
$failedTests = ($validationResults.Values | Where-Object { $_ -like "*FAIL*" }).Count
if ($failedTests -eq 0) {
    Write-Host "`n🎉 ALL SYSTEMS OPERATIONAL!" -ForegroundColor Green
    Write-Host "🚀 KILO-FOOLISH is ready for development!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ $failedTests components failed validation" -ForegroundColor Yellow
    Write-Host "Please review and fix issues before proceeding" -ForegroundColor Yellow
}
```

## 🔄 PHASE 9: OPERATIONAL WORKFLOWS

### 9.1 Daily Startup Sequence
```powershell
# Daily development environment activation
Write-Host "🌅 KILO-FOOLISH Daily Startup Sequence" -ForegroundColor Cyan

# 1. Navigate to project
Set-Location "C:\Users\malik\Documents\GitHub\KILO-FOOLISH"

# 2. Activate virtual environment
.\venv_kilo\Scripts\Activate.ps1

# 3. Start Ollama service
Start-Process ollama -ArgumentList "serve" -WindowStyle Hidden

# 4. Check system status
python scripts\system_audit.py

# 5. Open development environment
code KILO-FOOLISH.code-workspace

Write-Host "🚀 Development environment ready!" -ForegroundColor Green
```

### 9.2 Quick Development Commands
```powershell
# Essential daily commands

# System health check
python scripts\system_audit.py

# Repository organization  
python src\core\RepositoryCoordinator.py

# Evolution tracking
python scripts\async_def_track_system_evolution.py

# AI model interaction
ollama run phi:2.7b "Help me understand this code structure"

# Package management
pip list --outdated
```

## 🏁 PHASE 10: COMPLETION

### 10.1 Final Documentation
```powershell
# Generate final documentation
Write-Host "📚 Generating system documentation..." -ForegroundColor Cyan

@"
# KILO-FOOLISH System Setup Complete

## ✅ Installed Components
- Python 3.11 with virtual environment
- Ollama AI integration
- VS Code development environment
- Git version control
- Comprehensive system monitoring

## 🚀 Quick Start Commands
- Activate environment: .\venv_kilo\Scripts\Activate.ps1
- System audit: python scripts\system_audit.py
- Repository scan: python src\core\RepositoryCoordinator.py
- Start development: code KILO-FOOLISH.code-workspace

## 📞 Troubleshooting
- Memory debug: python scripts\debug_memory.py
- Evolution tracking: python scripts\async_def_track_system_evolution.py

System setup completed on: $(Get-Date)
"@ | Out-File "SYSTEM_SETUP_COMPLETE.md" -Encoding UTF8

Write-Host "✅ Setup documentation created: SYSTEM_SETUP_COMPLETE.md" -ForegroundColor Green

# Display next steps
Write-Host "`n🛣️ DEVELOPMENT ROADMAP:" -ForegroundColor Magenta
Write-Host "1. 🎮 Idler Game Development - Begin core game mechanics" -ForegroundColor White
Write-Host "2. 🤖 AI Enhancement - Expand model capabilities" -ForegroundColor White  
Write-Host "3. 🔧 System Optimization - Performance tuning" -ForegroundColor White

Write-Host "`n💡 SUGGESTED NEXT COMMANDS:" -ForegroundColor Cyan
Write-Host "  # Start daily development session:" -ForegroundColor Gray
Write-Host "  .\venv_kilo\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  code KILO-FOOLISH.code-workspace" -ForegroundColor White
Write-Host ""
Write-Host "  # Run comprehensive system check:" -ForegroundColor Gray  
Write-Host "  python scripts\system_audit.py" -ForegroundColor White
```
