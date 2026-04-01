# KILO-FOOLISH Setup Script
# PowerShell script to automate development environment setup

param(
    [switch]$SkipPython,
    [switch]$SkipVSCode,
    [switch]$SkipDocker,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "ðŸš€ KILO-FOOLISH Development Environment Setup" -ForegroundColor Cyan
Write-Host "==============================================`n" -ForegroundColor Cyan

# --- Real-time terminal output logging ---
$terminalLogPath = ".\logs\terminal_output.log"
if (!(Test-Path ".\logs")) { New-Item -ItemType Directory -Path ".\logs" -Force | Out-Null }
if (!(Test-Path $terminalLogPath)) { New-Item -ItemType File -Path $terminalLogPath -Force | Out-Null }

# Start transcript for full session logging
try {
    if ($null -eq $global:TranscriptStarted) {
        Start-Transcript -Path $terminalLogPath -Append
        $global:TranscriptStarted = $true
        Write-Host "[INFO] Terminal output is being logged to $terminalLogPath" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[WARNING] Could not start transcript: $_" -ForegroundColor Yellow
}

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to log messages
function Write-SetupLog {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }

    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color

    # Also log to file
    $logPath = ".\logs\setup.log"
    if (!(Test-Path ".\logs")) { New-Item -ItemType Directory -Path ".\logs" -Force | Out-Null }
    "[$timestamp] [$Level] $Message" | Add-Content -Path $logPath
}

# Check administrator privileges
if (!(Test-Administrator)) {
    Write-SetupLog "This script requires administrator privileges. Please run PowerShell as Administrator." "ERROR"
    Write-SetupLog "Right-click PowerShell and select 'Run as Administrator'" "ERROR"
    exit 1
}

Write-SetupLog "Running with administrator privileges âœ“" "SUCCESS"

# Check PowerShell version
$psVersion = $PSVersionTable.PSVersion
Write-SetupLog "PowerShell Version: $psVersion" "INFO"

if ($psVersion.Major -lt 5) {
    Write-SetupLog "PowerShell 5.0 or higher is required. Please upgrade PowerShell." "ERROR"
    exit 1
}

# Set execution policy
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-SetupLog "Execution policy set to RemoteSigned âœ“" "SUCCESS"
catch {
    Write-SetupLog "Failed to set execution policy: $_" "ERROR"
}

# Function to install package via WinGet
function Install-WinGetPackage {
    param(
        [string]$PackageId,
        [string]$Name
    )

    Write-SetupLog "Installing $Name..." "INFO"
    try {
        winget install --id $PackageId --accept-package-agreements --accept-source-agreements --silent
        Write-SetupLog "$Name installed successfully ✅" "SUCCESS"
    }
    catch {
        Write-SetupLog ("Failed to install {0}: {1}" -f $Name, $_) "WARNING"
        Write-SetupLog "You may need to install $Name manually" "INFO"
    }
}

# Check and install WinGet
Write-SetupLog "Checking WinGet installation..." "INFO"
try {
    $wingetVersion = winget --version
    Write-SetupLog "WinGet version: $wingetVersion ✅" "SUCCESS"
}
catch {
    Write-SetupLog "WinGet not found. Installing WinGet..." "WARNING"
    try {
        # Install WinGet via Microsoft Store or GitHub
        Invoke-WebRequest -Uri "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle" -OutFile "$env:TEMP\winget.msixbundle"
        Add-AppxPackage -Path "$env:TEMP\winget.msixbundle"
        Write-SetupLog "WinGet installed successfully âœ“" "SUCCESS"
    }
    catch {
        Write-SetupLog "Failed to install WinGet: $_" "ERROR"
        Write-SetupLog "Please install WinGet manually from Microsoft Store" "WARNING"
        }
}

# Install core tools
$packages = @(
    @{Id = "Microsoft.PowerShell"; Name = "PowerShell 7+"; Skip = $false },
    @{Id = "Python.Python.3.11"; Name = "Python 3.11"; Skip = $SkipPython },
    @{Id = "Microsoft.VisualStudioCode"; Name = "Visual Studio Code"; Skip = $SkipVSCode },
    @{Id = "GitHub.GitHubDesktop"; Name = "GitHub Desktop"; Skip = $false },
    @{Id = "OpenJS.NodeJS"; Name = "Node.js"; Skip = $false },
    @{Id = "Docker.DockerDesktop"; Name = "Docker Desktop"; Skip = $SkipDocker },
    @{Id = "Ollama.Ollama"; Name = "Ollama"; Skip = $false }
)

foreach ($package in $packages) {
    if (!$package.Skip) {
        Install-WinGetPackage -PackageId $package.Id -Name $package.Name
        Start-Sleep -Seconds 2
    }
    else {
        Write-SetupLog "Skipping $($package.Name) installation" "INFO"
            }
}

# Install WSL
Write-SetupLog "Installing Windows Subsystem for Linux (WSL)..." "INFO"
try {
    wsl --install --no-distribution
    Write-SetupLog "WSL installed successfully âœ“" "SUCCESS"
        Write-SetupLog "Note: WSL may require a system restart to complete installation" "WARNING"
    }
    catch {
        Write-SetupLog "Failed to install WSL: $_" "WARNING"
        Write-SetupLog "Try running: wsl --install manually" "INFO"
    }

    # Refresh environment variables
    Write-SetupLog "Refreshing environment variables..." "INFO"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

    # Verify Python installation
    if (!$SkipPython) {
        Write-SetupLog "Verifying Python installation..." "INFO"
        Start-Sleep -Seconds 5  # Wait for installation to complete

        try {
            $pythonVersion = python --version 2>&1
            Write-SetupLog "Python version: $pythonVersion âœ“" "SUCCESS"

        # Check pip
        $pipVersion = pip --version 2>&1
        Write-SetupLog "Pip version: $pipVersion âœ“" "SUCCESS"

            # Upgrade pip
            Write-SetupLog "Upgrading pip..." "INFO"
            python -m pip install --upgrade pip
            Write-SetupLog "Pip upgraded successfully âœ“" "SUCCESS"

    }
    catch {
        Write-SetupLog "Python verification failed: $_" "ERROR"
        Write-SetupLog "You may need to restart your terminal or add Python to PATH manually" "WARNING"
    }
}

# Create project structure
Write-SetupLog "Creating project directory structure..." "INFO"
$directories = @("src", "tests", "docs", "config", "data", "logs", ".vscode")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        Write-SetupLog "Created directory: $dir âœ“" "SUCCESS"
        }
        else {
            Write-SetupLog "Directory already exists: $dir" "INFO"
        }
    }
    catch {
        Write-SetupLog "Error creating directory: $_" "ERROR"
    }
}

# Create Python virtual environment
if (!$SkipPython) {
    Write-SetupLog "Creating Python virtual environment..." "INFO"
    try {
        if (Test-Path "venv_kilo") {
            @"
                    }
                    else {
                        Write-SetupLog "requirements.txt not found, skipping dependency installation" "WARNING"
                $pipConfig = @"
                    }

                }
                catch {
                    Write-SetupLog "Failed to create virtual environment: $_" "ERROR"
                }
            }
        }

        # Install VS Code Extensions
    }
Write-SetupLog ".env file created ✓" "SUCCESS"
        Write-SetupLog "Setting up VS Code extensions..." "INFO"
        $installExtensions = Read-Host "Install VS Code extensions? (Essential/AI/All/Skip) [Essential]"
        if ($installExtensions -eq "" -or $installExtensions.ToLower() -eq "essential") {
            . ".\setup\InstallVSCodeExtensions.ps1" -Essential -AI
        }
        elseif ($installExtensions.ToLower() -eq "ai") {
            . ".\setup\InstallVSCodeExtensions.ps1" -Essential -AI -Debug
        }
        elseif ($installExtensions.ToLower() -eq "all") {
            . ".\setup\InstallVSCodeExtensions.ps1" -All
        }

        Write-SetupLog "VS Code setup completed âœ“" "SUCCESS"

# Create .env file if it doesn't exist
if (!(Test-Path ".env")) {
    Write-SetupLog "Creating .env configuration file..." "INFO"
    @"
        # KILO-FOOLISH Environment Configuration
        REPO_ROOT=$PWD
        PYTHON_ENV=venv_kilo
        LOG_LEVEL=INFO
        DEVELOPMENT_MODE=true

        # AI API Keys (replace with actual keys when available)
        OPENAI_API_KEY=your_openai_key_here
        OLLAMA_HOST=http://localhost:11434

        # Database Configuration (if needed)
        DATABASE_URL=sqlite:///./data/kilo_foolish.db
    "@ | Out-File -FilePath ".env" -Encoding UTF8
Write-SetupLog ".env file created ✓" "SUCCESS"

# Load project configuration
try {
    . ".\config\project.ps1"
    $ProjectName = Get-ProjectName
    $ProjectVersion = Get-ProjectVersion
    Write-SetupLog "Loaded $ProjectName v$ProjectVersion configuration âœ“" "SUCCESS"
    }
    catch {
        # Fallback
        $ProjectName = "KILO-FOOLISH"
        $ProjectVersion = "1.0.0"
        Write-SetupLog "Using fallback configuration for $ProjectName" "WARNING"
    }

    # Security setup
    Write-SetupLog "Setting up secure configuration..." "INFO"

    # Create secrets template if it doesn't exist
    $secretsTemplate = ".\config\secrets.template.ps1"
    $secretsFile = ".\config\secrets.ps1"

    if (!(Test-Path $secretsTemplate)) {
        Write-SetupLog "Creating secrets template..." "INFO"
        # Copy the template content we created above
        # ... (template content) ...
        Write-SetupLog "Secrets template created: $secretsTemplate âœ“" "SUCCESS"
}

if (!(Test-Path $secretsFile)) {
    Write-SetupLog "Creating your secrets file..." "INFO"
    Copy-Item $secretsTemplate $secretsFile
    Write-SetupLog "âš ï¸  IMPORTANT: Edit $secretsFile with your actual API keys!" "WARNING"
    Write-SetupLog "âš ï¸  NEVER commit $secretsFile to version control!" "WARNING"
}

## .env file creation already handled above; remove duplicate block if present
    Write-SetupLog "Creating secure .env configuration file..." "INFO"
    @"
        # KILO-FOOLISH Environment Configuration
        # Safe for version control (no secrets here!)

        ENVIRONMENT=development
        REPO_ROOT=$PWD
        PYTHON_ENV=venv_kilo
        LOG_LEVEL=INFO
        DEVELOPMENT_MODE=true

        # Service URLs (no secrets)
        OLLAMA_HOST=http://localhost:11434
        DATABASE_URL=sqlite:///./data/kilo_foolish.db

        CACHE_ENABLED=false
        RATE_LIMIT_ENABLED=false
        DEBUG_MODE=true

        # File Paths
        LOG_FILE=./logs/storage/kilo_foolish.log
        DATA_DIR=./data
        CONFIG_DIR=./config
        "@ | Out-File -FilePath ".env" -Encoding UTF8
Write-SetupLog ".env file created (safe for version control) ✓" "SUCCESS"
## Remove stray closing brace after .env creation

# Test environment setup
Write-SetupLog "Testing environment configuration..." "INFO"
try {
    . ".\config\environment.ps1" -Environment "development"
    $issues = Test-EnvironmentSetup

try {
    if ($issues.Count -eq 0) {
        Write-SetupLog "Environment configuration valid âœ“" "SUCCESS"
    }
    else {
        Write-SetupLog "Environment issues found:" "WARNING"
        foreach ($issue in $issues) {
            Write-SetupLog "  - $issue" "WARNING"
        }
    }

    Write-Host "ðŸš€ $ProjectName Development Environment Setup v$ProjectVersion" -ForegroundColor Cyan

    # Now you can use $ProjectName throughout your script
    Write-SetupLog "Setting up $ProjectName development environment..." "INFO"

    # Final verification


    # Function to check and install pip
    function Install-PipIfNeeded {
        Write-SetupLog "Checking pip installation..." "INFO"

        try {
            # Check if pip is available
            $pipVersion = pip --version 2>$null
            if ($pipVersion) {
                Write-SetupLog "Pip is already installed: $pipVersion âœ“" "SUCCESS"
            return $true
        }
    }
    catch {
        Write-SetupLog "Pip command not found, checking Python installation..." "WARNING"
    }

    # Check if Python is installed
    try {
        $pythonVersion = python --version 2>$null
        if (!$pythonVersion) {
        @"

                try {
                    # Method 2: Download and install pip manually
                    Write-SetupLog "Downloading get-pip.py..." "INFO"
                    $pipInstaller = "get-pip.py"
                    $pipUrl = "https://bootstrap.pypa.io/get-pip.py"

                    Invoke-WebRequest -Uri $pipUrl -OutFile $pipInstaller
                    Write-SetupLog "Downloaded get-pip.py âœ“" "SUCCESS"

            # Install pip
            python $pipInstaller
            Write-SetupLog "Pip installed via get-pip.py âœ“" "SUCCESS"

                    # Clean up
                    Remove-Item $pipInstaller -Force
                }
                catch {
                    Write-SetupLog "Failed to install pip manually: $_" "ERROR"
                    return $false
                }
            }

    }
Write-SetupLog ".env file created (safe for version control) ✓" "SUCCESS"
            # Verify pip installation
            try {
                $pipVersion = pip --version
                Write-SetupLog "Pip verification successful: $pipVersion âœ“" "SUCCESS"

        # Upgrade pip to latest version
        Write-SetupLog "Upgrading pip to latest version..." "INFO"
        python -m pip install --upgrade pip

        $newPipVersion = pip --version
        Write-SetupLog "Pip upgraded: $newPipVersion âœ“" "SUCCESS"

                return $true
            }
            catch {
                Write-SetupLog "Pip verification failed: $_" "ERROR"
                return $false
            }
        }
        catch {
            Write-SetupLog "Error in previous block: $_" "ERROR"
        }

    }

    # Function to validate pip and Python environment
    function Test-PythonEnvironment {
        Write-SetupLog "Validating Python environment..." "INFO"

        $issues = @()

        # Check Python version
        try {
            $pythonVersion = python --version
            $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)"
            if ($versionMatch) {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
                    $issues += "Python version $pythonVersion is too old. Python 3.8+ recommended."
                }
                else {
                    Write-SetupLog "Python version check passed: $pythonVersion ✓" "SUCCESS"
                }
            }
        }
        catch {
            $issues += "Python not found in PATH"
        }

        # Check pip functionality
        try {
            $pipList = pip list --format=json | ConvertFrom-Json
            Write-SetupLog "Pip is functional, found $($pipList.Count) packages ✓" "SUCCESS"
        }
        catch {
            $issues += "Pip is not functional"
        }

        # Check if pip can install packages (test with a small package)
        try {
            Write-SetupLog "Testing pip package installation capability..." "INFO"
            pip install --dry-run setuptools >$null 2>&1
            Write-SetupLog "Pip can install packages ✓" "SUCCESS"
        }
        catch {
            $issues += "Pip cannot install packages (network/permission issue)"
        }
        return $issues
    }

    # Function to setup Python virtual environment
    function Setup-PythonVirtualEnvironment {
        param(
            [string]$VenvName = "venv_kilo"
        )
        Write-SetupLog "Setting up Python virtual environment..." "INFO"
        try {
            if (Test-Path $VenvName) {
                Write-SetupLog "Virtual environment already exists: $VenvName" "INFO"
                return $true
            }
            python -m venv $VenvName
            Write-SetupLog "Virtual environment created: $VenvName" "SUCCESS"
            return $true
        }
        catch {
            Write-SetupLog "Failed to create virtual environment: $_" "ERROR"
            return $false
        }
    }

    # Main pip installation workflow
    Write-SetupLog "Starting Python and pip setup..." "INFO"

    # Step 1: Install pip if needed
    $pipInstalled = Install-PipIfNeeded
    if (!$pipInstalled) {
        Write-SetupLog "Failed to install pip. Cannot continue with Python setup." "ERROR"
        exit 1
    }

    # Step 2: Validate Python environment
    $pythonIssues = Test-PythonEnvironment
    if ($pythonIssues.Count -gt 0) {
        Write-SetupLog "Python environment issues found:" "WARNING"
        foreach ($issue in $pythonIssues) {
            Write-SetupLog "  - $issue" "WARNING"
        }

        # Ask user if they want to continue
        $continue = Read-Host "Continue with setup despite issues? (y/N)"
        if ($continue.ToLower() -ne 'y') {
            Write-SetupLog "Setup cancelled by user" "WARNING"
            exit 0
        }
    }

    # Step 3: Setup virtual environment
    $venvSetup = Setup-PythonVirtualEnvironment -VenvName "venv_kilo"
    if (!$venvSetup) {
        Write-SetupLog "Failed to setup virtual environment" "ERROR"
        exit 1
    }

    # Step 4: Install project dependencies
    Write-SetupLog "Installing project dependencies..." "INFO"
    if (Test-Path "requirements.txt") {
        try {
            Start-Process -NoNewWindow -Wait -FilePath ".\venv_kilo\Scripts\pip.exe" -ArgumentList "install", "-r", "requirements.txt"
            Write-SetupLog "Project dependencies installed âœ“" "SUCCESS"
                }
                catch {
                    Write-SetupLog "Failed to install some dependencies: $_" "WARNING"
                }
            }
            else {
                Write-SetupLog "No requirements.txt found, skipping dependency installation" "WARNING"
            }

            # Step 5: Final validation
            Write-SetupLog "Final Python environment validation..." "INFO"
            try {
                $finalPython = (Start-Process -NoNewWindow -Wait -FilePath ".\venv_kilo\Scripts\python.exe" -ArgumentList "--version" -PassThru)
                $finalPip = (Start-Process -NoNewWindow -Wait -FilePath ".\venv_kilo\Scripts\pip.exe" -ArgumentList "--version" -PassThru)
                $installedPackages = (Start-Process -NoNewWindow -Wait -FilePath ".\venv_kilo\Scripts\pip.exe" -ArgumentList "list", "--format=freeze" -PassThru)

                Write-SetupLog "âœ“ Python: $finalPython" "SUCCESS"
            Write-SetupLog "âœ“ Pip: $finalPip" "SUCCESS"
                Write-SetupLog "âœ“ Installed packages: $($installedPackages.Count) packages" "SUCCESS"
        }
        catch {
            Write-SetupLog "Final validation failed: $_" "ERROR"
        }

        Write-SetupLog "Python and pip setup completed!" "SUCCESS"

        # Function to check for common pip issues and fix them
        function Repair-PipInstallation {
            Write-SetupLog "Checking for common pip issues..." "INFO"

            # Issue 1: PATH problems
            $pythonPaths = @()
            $pipPaths = @()

            # Find Python installations
            Get-Command python -All -ErrorAction SilentlyContinue | ForEach-Object {
                $pythonPaths += $_.Source
            }

            # Find pip installations
            Get-Command pip -All -ErrorAction SilentlyContinue | ForEach-Object {
                $pipPaths += $_.Source
            }

            Write-SetupLog "Found Python installations: $($pythonPaths -join ', ')" "INFO"
            Write-SetupLog "Found pip installations: $($pipPaths -join ', ')" "INFO"

            # Issue 2: Certificate problems
            try {
                pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --dry-run setuptools >$null 2>&1
                Write-SetupLog "SSL certificates are working âœ“" "SUCCESS"
            }
            catch {
                Write-SetupLog "SSL certificate issues detected, adding trusted hosts..." "WARNING"
                # This will be handled in individual pip commands
            }

            # Issue 3: Permissions
            try {
                $tempFile = [System.IO.Path]::GetTempFileName()
                pip freeze > $tempFile
                Remove-Item $tempFile
                Write-SetupLog "Pip permissions are working âœ“" "SUCCESS"
            }
            catch {
                Write-SetupLog "Pip permission issues detected" "WARNING"
            }
        }

        # Function to create a pip configuration file for better reliability
        function New-PipConfig {
            $pipConfigDir = "$env:APPDATA\pip"
            $pipConfigFile = "$pipConfigDir\pip.ini"

            if (!(Test-Path $pipConfigDir)) {
                New-Item -Path $pipConfigDir -ItemType Directory -Force
                Write-SetupLog "Created pip config directory: $pipConfigDir" "SUCCESS"
            }

            if (!(Test-Path $pipConfigFile)) {
                $pipConfig = @"
[global]
timeout = 60
trusted-host = pypi.org
pypi.python.org
files.pythonhosted.org

[install]
upgrade-strategy = only-if-needed
"@
            $pipConfig | Out-File -FilePath $pipConfigFile -Encoding UTF8
            Write-SetupLog "Created pip configuration file: $pipConfigFile ✓" "SUCCESS"
        }
        catch {
            Write-SetupLog "Error creating pip config: $_" "ERROR"
        }
    }
}
}
}
}

# Run self-diagnostics at the end
Write-SetupLog "Running self-diagnostics..." "INFO"
try {
    . ".\src\diagnostics\ErrorDetector.ps1" -AutoFix -Verbose
    Write-SetupLog "Self-diagnostics completed âœ“" "SUCCESS"
}
catch {
    Write-SetupLog "Self-diagnostics failed: $_" "WARNING"
}

    }
}
# Launch AI Roadmap Assistant
Write-SetupLog "Launching AI Roadmap Assistant..." "INFO"
try {
    . ".\src\ai\RoadmapAssistant.ps1" -Mode "interactive" -Context "development"
    Write-SetupLog "AI Assistant analysis completed âœ“" "SUCCESS"
}
catch {
    Write-SetupLog "AI Assistant failed: $_" "WARNING"
}

# Setup Ollama integration
Write-SetupLog "Setting up Ollama integration..." "INFO"
try {
    . ".\src\ai\OllamaSetup.ps1" -Install -Configure -Models @("llama2:7b", "codellama:7b")
    Write-SetupLog "Ollama integration completed âœ“" "SUCCESS"
}
catch {
    Write-SetupLog "Ollama setup failed: $_" "WARNING"
}

# Setup AI Coordination Layer
Write-SetupLog "Setting up AI Coordination Layer..." "INFO"
try {
    . ".\src\ai\AICoordinatorSetup.ps1" -Test
    Write-SetupLog "AI Coordinator setup completed âœ“" "SUCCESS"
}
catch {
    Write-SetupLog "AI Coordinator setup failed: $_" "WARNING"
}

# Setup RPG Inventory System
Write-SetupLog "Setting up RPG Inventory System..." "INFO"
try {
    . ".\src\system\RPGInventorySetup.ps1" -Install -Start
    Write-SetupLog "RPG Inventory System setup completed âœ“" "SUCCESS"
        }
        catch {
            Write-SetupLog "RPG Inventory setup failed: $_" "WARNING"
        }

# Launch RPG Dashboard (optional)
$launchDashboard = Read-Host "Launch RPG Dashboard now? (y/N)"
try {
    if ($launchDashboard.ToLower() -eq 'y') {
        Write-SetupLog "Launching RPG Dashboard..." "INFO"
        . "./src/system/RPGInventorySetup.ps1" -Dashboard
    }
    Write-SetupLog "Starting RPG Inventory monitoring..." "INFO"
    . "./src/system/RPGInventorySetup.ps1" -Install -Start
    Write-SetupLog "Launching real-time RPG Dashboard..." "INFO"
    . "./src/system/RPGInventorySetup.ps1" -Dashboard
    Write-SetupLog "Performing quick RPG status check..." "INFO"
    . "./src/system/RPGInventorySetup.ps1" -Status
}
catch {
    Write-SetupLog "RPG Dashboard or Inventory setup failed: $($_)" "ERROR"
}
