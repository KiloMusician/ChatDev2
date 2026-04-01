# KILO-FOOLISH System Information & Configuration

## 📊 Hardware Requirements & Recommendations

### Minimum System Requirements
- **OS**: Windows 10 (version 1903+) or Windows 11
- **RAM**: 8GB (16GB recommended for AI/ML tasks)
- **Storage**: 20GB free space (SSD recommended)
- **CPU**: Multi-core processor (Intel i5/AMD Ryzen 5 or better)
- **GPU**: Optional but recommended for ML workloads (NVIDIA RTX series)

### Recommended Development Setup
- **RAM**: 32GB for large AI model training
- **Storage**: NVMe SSD with 100GB+ free space
- **CPU**: Intel i7/i9 or AMD Ryzen 7/9 (8+ cores)
- **GPU**: NVIDIA RTX 3070+ or RTX 4060+ for CUDA support

## 🛤️ Repository Paths & Structure

### Important Path Variables
```powershell
# Repository Root
$REPO_ROOT = "C:\Users\malik\Documents\GitHub\KILO-FOOLISH"

# Python Virtual Environment
$VENV_PATH = "$REPO_ROOT\venv_kilo"

# Documentation Hub
$DOCS_PATH = "$REPO_ROOT\ΞNuSyQ₁-Hub₁"

# Archive & Legacy Files
$ARCHIVE_PATH = "$REPO_ROOT\Archive"
```

### Key Configuration Files
- **`requirements.txt`**: Python dependencies
- **`KILO-FOOLISH.code-workspace`**: VS Code workspace configuration
- **`.gitignore`**: Git ignore patterns
- **`.env`**: Environment variables (create if needed)

## 🔧 Environment Setup Checklist

### ✅ Pre-Installation Checklist
- [ ] Windows 10/11 with latest updates
- [ ] Administrator access to PowerShell
- [ ] Stable internet connection
- [ ] At least 20GB free disk space

### ✅ Installation Progress Tracker
- [ ] WinGet package manager installed
- [ ] PowerShell 7+ installed
- [ ] Python 3.11+ installed
- [ ] Pip upgraded to latest version
- [ ] VS Code installed
- [ ] GitHub Desktop installed
- [ ] WSL installed (optional but recommended)
- [ ] Docker Desktop installed (for containerization)

### ✅ Python Environment Setup
- [ ] Virtual environment created (`venv_kilo`)
- [ ] Virtual environment activated
- [ ] Requirements.txt dependencies installed
- [ ] Python path configured correctly
- [ ] Pip working in virtual environment

### ✅ VS Code Configuration
- [ ] Workspace file configured
- [ ] Recommended extensions installed
- [ ] Python interpreter set to virtual environment
- [ ] PowerShell as default terminal
- [ ] Git integration working

## 🧪 System Verification Commands

### Test Python Setup
```powershell
# Check Python installation
python --version
pip --version
where python
where pip

# Test virtual environment
.\venv_kilo\Scripts\Activate.ps1
python -c "import sys; print(f'Python: {sys.version}'); print(f'Location: {sys.executable}')"
pip list
```

### Test AI/ML Dependencies
```powershell
# Test core packages (after requirements.txt installation)
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import ollama; print('Ollama: OK')"
python -c "import numpy as np; print(f'NumPy: {np.__version__}')"
```

### System Information
```powershell
# Get system info
systeminfo | findstr /C:"OS Name" /C:"OS Version" /C:"System Type" /C:"Total Physical Memory"

# Get Python environment info
python -c "
import platform
import sys
import os
print(f'Platform: {platform.platform()}')
print(f'Python Version: {sys.version}')
print(f'Python Executable: {sys.executable}')
print(f'Current Working Directory: {os.getcwd()}')
print(f'Environment PATH: {os.environ.get(\"PATH\", \"Not Found\")[:100]}...')
"
```

## 🗃️ Directory Structure Validation

### Required Directories
```
KILO-FOOLISH/
├── venv_kilo/                 # Python virtual environment
├── src/                       # Source code (to be created)
├── tests/                     # Unit tests (to be created)
├── docs/                      # Generated documentation (to be created)
├── config/                    # Configuration files (to be created)
├── data/                      # Data files (to be created)
├── logs/                      # Log files (to be created)
└── .vscode/                   # VS Code settings (auto-generated)
```

### Create Missing Directories
```powershell
# Navigate to repository root
cd "C:\Users\malik\Documents\GitHub\KILO-FOOLISH"

# Create development directories
New-Item -ItemType Directory -Force -Path "src"
New-Item -ItemType Directory -Force -Path "tests"
New-Item -ItemType Directory -Force -Path "docs"
New-Item -ItemType Directory -Force -Path "config"
New-Item -ItemType Directory -Force -Path "data"
New-Item -ItemType Directory -Force -Path "logs"
New-Item -ItemType Directory -Force -Path ".vscode"
```

## 🔐 Security & Environment Variables

### Create .env file (if needed)
```powershell
# Create environment variables file
@"
# KILO-FOOLISH Environment Configuration
REPO_ROOT=C:\Users\malik\Documents\GitHub\KILO-FOOLISH
PYTHON_ENV=venv_kilo
LOG_LEVEL=INFO
DEVELOPMENT_MODE=true

# AI API Keys (replace with actual keys when available)
OPENAI_API_KEY=your_openai_key_here
OLLAMA_HOST=http://localhost:11434

# Database Configuration (if needed)
DATABASE_URL=sqlite:///./data/kilo_foolish.db
"@ | Out-File -FilePath ".env" -Encoding UTF8
```

## 📈 Performance Monitoring

### Monitor System Resources
```powershell
# Check system performance
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
```

## 🚨 Troubleshooting

### Common Issues & Solutions

**Python not found:**
```powershell
# Add Python to PATH manually
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311"
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts"
```

**Pip not working:**
```powershell
# Reinstall pip
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

**Virtual environment issues:**
```powershell
# Recreate virtual environment
Remove-Item -Recurse -Force venv_kilo
python -m venv venv_kilo
.\venv_kilo\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Permission errors:**
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

**Last Updated**: July 8, 2025
**System**: Windows-based development environment
**Purpose**: KILO-FOOLISH ΞNuSyQ₁ Quantum Development Framework
