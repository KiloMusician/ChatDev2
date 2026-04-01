# KILO-FOOLISH Error Detection | Start-Process -NoNewWindow -Wait Self-Healing Module
# Identifies issues and provides actionable solutions

param(
    [switch]$AutoFix,
    [switch]$Verbose,
    [string]$LogLevel = "INFO"
)

# Load project configuration
try {
    . ".\config\project.ps1"
    $ProjectName = Get-ProjectName
}
catch {
    $ProjectName = "KILO-FOOLISH"
}

# Diagnostic results container
$script:DiagnosticResults = @{
    Errors      = @()
    Warnings    = @()
    Fixes       = @()
    Suggestions = @()
}

function Write-DiagnosticLog {
    param([string]$Message, [string]$Level = "INFO", [string]$Component = "DIAG")

    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        "FIX" { "Cyan" }
        default { "White" }
    }

    if ($Verbose -or $Level -in @("ERROR", "WARNING", "FIX")) {
        Write-Host "[$timestamp] [$Component] $Message" -ForegroundColor $color
    }
}

# Function to detect Python/pip issues
function Test-PythonEnvironment {
    Write-DiagnosticLog "Analyzing Python environment..." "INFO"

    $issues = @()
    $fixes = @()

    # Check 1: Python installation
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]

            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
                $issues += @{
                    Type        = "ERROR"
                    Component   = "Python"
                    Issue       = "Python version $pythonVersion is outdated"
                    Impact      = "Some packages may not work correctly"
                    Fix         = "winget install Python.Python.3.11"
                    AutoFixable = $true
                }
            }
            else {
                Write-DiagnosticLog "Python version OK: $pythonVersion" "SUCCESS"
            }
        }
    }
    catch {
        $issues += @{
            Type        = "ERROR"
            Component   = "Python"
            Issue       = "Python not found in PATH"
            Impact      = "Cannot run Python scripts"
            Fix         = "Add Python to PATH or reinstall Python"
            AutoFixable = $false
        }
    }

    # Check 2: Pip functionality
    try {
        $pipVersion = pip --version 2>&1
        if ($pipVersion) {
            Write-DiagnosticLog "Pip version OK: $pipVersion" "SUCCESS"

            # Test pip install capability
            try {
                pip install --dry-run setuptools 2>&1 | Out-Null
                Write-DiagnosticLog "Pip install capability: OK" "SUCCESS"
            }
            catch {
                $issues += @{
                    Type        = "WARNING"
                    Component   = "Pip"
                    Issue       = "Pip cannot install packages (network/SSL issue)"
                    Impact      = "Package installation will fail"
                    Fix         = "Create pip.ini with trusted hosts"
                    AutoFixable = $true
                }
            }
        }
    }
    catch {
        $issues += @{
            Type        = "ERROR"
            Component   = "Pip"
            Issue       = "Pip not available"
            Impact      = "Cannot install Python packages"
            Fix         = "python -m ensurepip --upgrade"
            AutoFixable = $true
        }
    }

    # Check 3: Virtual environment
    if (Test-Path "venv_kilo") {
        try {
            $venvPython = &  -NoNewWindow -Wait ".\venv_kilo\Scripts\python.exe" --version 2>&1
            Write-DiagnosticLog "Virtual environment: OK ($venvPython)" "SUCCESS"
        }
        catch {
            $issues += @{
                Type        = "WARNING"
                Component   = "VirtualEnv"
                Issue       = "Virtual environment corrupted"
                Impact      = "Cannot use isolated Python environment"
                Fix         = "Remove and recreate: Remove-Item venv_kilo -Recurse; python -m venv venv_kilo"
                AutoFixable = $true
            }
        }
    }
    else {
        $issues += @{
            Type        = "WARNING"
            Component   = "VirtualEnv"
            Issue       = "Virtual environment missing"
            Impact      = "No isolated Python environment"
            Fix         = "python -m venv venv_kilo"
            AutoFixable = $true
        }
    }

    return $issues
}

# Function to detect VS Code issues
function Test-VSCodeEnvironment {
    Write-DiagnosticLog "Analyzing VS Code environment..." "INFO"

    $issues = @()

    # Check VS Code installation
    try {
        $codeVersion = code --version 2>&1
        Write-DiagnosticLog "VS Code: OK" "SUCCESS"

        # Check essential extensions
        $requiredExtensions = @(
            "ms-python.python",
            "ms-vscode.powershell"
        )

        $installedExtensions = code --list-extensions 2>&1

        foreach ($ext in $requiredExtensions) {
            if ($installedExtensions -notcontains $ext) {
                $issues += @{
                    Type        = "WARNING"
                    Component   = "VSCode"
                    Issue       = "Missing essential extension: $ext"
                    Impact      = "Reduced development experience"
                    Fix         = "code --install-extension $ext"
                    AutoFixable = $true
                }
            }
        }
    }
    catch {
        $issues += @{
            Type        = "WARNING"
            Component   = "VSCode"
            Issue       = "VS Code not found or not in PATH"
            Impact      = "Cannot use VS Code from command line"
            Fix         = "Add VS Code to PATH or reinstall"
            AutoFixable = $false
        }
    }

    return $issues
}

# Function to detect configuration issues
function Test-ProjectConfiguration {
    Write-DiagnosticLog "Analyzing project configuration..." "INFO"

    $issues = @()

    # Check essential files
    $essentialFiles = @{
        "requirements.txt"   = "Python dependencies not defined"
        "config\project.ps1" = "Project configuration missing"
        ".gitignore"         = "Git ignore rules missing"
        ".env"               = "Environment configuration missing"
    }

    foreach ($file in $essentialFiles.Keys) {
        if (!(Test-Path $file)) {
            $issues += @{
                Type        = "WARNING"
                Component   = "Config"
                Issue       = "Missing file: $file"
                Impact      = $essentialFiles[$file]
                Fix         = "Create $file with appropriate content"
                AutoFixable = $true
            }
        }
    }

    # Check for exposed secrets
    $secretPatterns = @(
        "sk-[a-zA-Z0-9]{32,}",  # OpenAI API keys
        "ghp_[a-zA-Z0-9]{36}",   # GitHub tokens
        "AKIA[0-9A-Z]{16}",      # AWS access keys
        "[0-9a-f]{32}"           # Generic 32-char hashes
    )

    Get-ChildItem -Recurse -Include "*.ps1", "*.py", "*.txt", "*.md" | ForEach-Object {
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($content) {
            foreach ($pattern in $secretPatterns) {
                if ($content -match $pattern) {
                    $issues += @{
                        Type        = "ERROR"
                        Component   = "Security"
                        Issue       = "Potential exposed secret in $($_.Name)"
                        Impact      = "Security vulnerability"
                        Fix         = "Move secrets to config\secrets.ps1 and add to .gitignore"
                        AutoFixable = $false
                    }
                    break
                }
            }
        }
    }

    return $issues
}

# Function to apply automatic fixes
function Invoke-AutoFix {
    param([array]$Issues)

    Write-DiagnosticLog "Applying automatic fixes..." "FIX"

    foreach ($issue in $Issues) {
        if ($issue.AutoFixable) {
            Write-DiagnosticLog "Fixing: $($issue.Issue)" "FIX"

            try {
                switch ($issue.Component) {
                    "Pip" {
                        if ($issue.Fix -like "*ensurepip*") {
                            Invoke-Expression $issue.Fix
                        }
                        elseif ($issue.Fix -like "*pip.ini*") {
                            Create-PipConfig
                        }
                    }
                    "VirtualEnv" {
                        if ($issue.Fix -like "*Remove-Item*") {
                            if (Test-Path "venv_kilo") {
                                Remove-Item "venv_kilo" -Recurse -Force
                            }
                            python -m venv venv_kilo
                        }
                        elseif ($issue.Fix -like "*python -m venv*") {
                            python -m venv venv_kilo
                        }
                    }
                    "VSCode" {
                        if ($issue.Fix -like "*--install-extension*") {
                            Invoke-Expression $issue.Fix
                        }
                    }
                    "Config" {
                        Create-MissingConfigFiles -FileName $issue.Fix
                    }
                }

                Write-DiagnosticLog "Fixed: $($issue.Issue)" "SUCCESS"
                $script:DiagnosticResults.Fixes += $issue
            }
            catch {
                Write-DiagnosticLog "Failed to fix: $($issue.Issue) - $_" "ERROR"
            }
        }
    }
}

# Function to create missing configuration files
function Create-MissingConfigFiles {
    param([string]$FileName)

    switch ($FileName) {
        "requirements.txt" {
            @"
# KILO-FOOLISH Python Dependencies
# Core packages
pip>=23.0.0
setuptools>=65.0.0
wheel>=0.38.0

# AI/ML packages
openai>=1.0.0
ollama>=0.1.0
transformers>=4.30.0

# Utility packages
python-dotenv>=1.0.0
pyyaml>=6.0
rich>=13.0.0
typer[all]>=0.9.0
requests>=2.31.0

# Development packages
pytest>=7.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
        }

        ".env" {
            @"
# KILO-FOOLISH Environment Configuration
ENVIRONMENT=development
PROJECT_NAME=KILO-FOOLISH
LOG_LEVEL=INFO
DEBUG_MODE=true

# Service URLs
OLLAMA_HOST=http://localhost:11434
DATABASE_URL=sqlite:///./data/kilo_foolish.db

# Paths
DATA_DIR=./data
LOG_DIR=./logs
CONFIG_DIR=./config
"@ | Out-File -FilePath ".env" -Encoding UTF8
        }
    }
}

# Function to generate improvement suggestions
function Get-ImprovementSuggestions {
    param([array]$Issues)

    $suggestions = @()

    # Analyze patterns in issues
    $componentCounts = $Issues | Group-Object Component | Sort-Object Count -Descending

    if ($componentCounts[0].Count -gt 2) {
        $suggestions += "ðŸ” Focus on $($componentCounts[0].Name) issues first - they have the most problems"
    }

    # Security suggestions
    $securityIssues = $Issues | Where-Object { $_.Component -eq "Security" }
    if ($securityIssues.Count -gt 0) {
        $suggestions += "ðŸ”’ Priority: Address security issues immediately"
        $suggestions += "ðŸ’¡ Consider implementing pre-commit hooks to prevent secret commits"
    }

    # Development workflow suggestions
    if ($Issues | Where-Object { $_.Component -in @("Python", "Pip", "VirtualEnv") }) {
        $suggestions += "ðŸ Consider using conda instead of pip for better dependency management"
        $suggestions += "ðŸ”„ Set up automated testing to catch these issues early"
    }

    # VS Code workflow suggestions
    if ($Issues | Where-Object { $_.Component -eq "VSCode" }) {
        $suggestions += "ðŸ’» Create a .vscode/extensions.json file to auto-suggest extensions"
        $suggestions += "âš™ï¸ Set up workspace settings for consistent development experience"
    }

    return $suggestions
}

# Main diagnostic function
function Start-Diagnostics {
    Write-Host "`nðŸ” $ProjectName Self-Diagnostic System" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan

    # Run all diagnostic tests
    $allIssues = @()
    $allIssues += Test-PythonEnvironment
    $allIssues += Test-VSCodeEnvironment
    $allIssues += Test-ProjectConfiguration

    # Categorize issues
    $errors = $allIssues | Where-Object { $_.Type -eq "ERROR" }
    $warnings = $allIssues | Where-Object { $_.Type -eq "WARNING" }

    # Store results
    $script:DiagnosticResults.Errors = $errors
    $script:DiagnosticResults.Warnings = $warnings

    # Display summary
    Write-Host "`nðŸ“Š Diagnostic Summary:" -ForegroundColor Yellow
    Write-Host "  Errors: $($errors.Count)" -ForegroundColor Red
    Write-Host "  Warnings: $($warnings.Count)" -ForegroundColor Yellow
    Write-Host "  Auto-fixable: $(($allIssues | Where-Object AutoFixable).Count)" -ForegroundColor Green

    # Display issues
    if ($errors.Count -gt 0) {
        Write-Host "`nâŒ ERRORS (require immediate attention):" -ForegroundColor Red
        $errors | ForEach-Object {
            Write-Host "  â€¢ [$($_.Component)] $($_.Issue)" -ForegroundColor Red
            Write-Host "    Impact: $($_.Impact)" -ForegroundColor Gray
            Write-Host "    Fix: $($_.Fix)" -ForegroundColor Cyan
        }
    }

    if ($warnings.Count -gt 0) {
        Write-Host "`nâš ï¸  WARNINGS (should be addressed):" -ForegroundColor Yellow
        $warnings | ForEach-Object {
            Write-Host "  â€¢ [$($_.Component)] $($_.Issue)" -ForegroundColor Yellow
            Write-Host "    Fix: $($_.Fix)" -ForegroundColor Cyan
        }
    }

    # Auto-fix if requested
    if ($AutoFix -and $allIssues.Count -gt 0) {
        Write-Host "`nðŸ”§ Applying automatic fixes..." -ForegroundColor Cyan
        Invoke-AutoFix -Issues $allIssues
    }

    # Generate suggestions
    $suggestions = Get-ImprovementSuggestions -Issues $allIssues
    if ($suggestions.Count -gt 0) {
        Write-Host "`nðŸ’¡ Improvement Suggestions:" -ForegroundColor Green
        $suggestions | ForEach-Object {
            Write-Host "  $($_)" -ForegroundColor Green
        }
    }

    # Final status
    if ($allIssues.Count -eq 0) {
        Write-Host "`nâœ… All systems healthy! Your $ProjectName environment is optimized." -ForegroundColor Green
    }
    else {
        Write-Host "`nðŸŽ¯ Next steps: Address the issues above to optimize your development environment." -ForegroundColor Cyan
    }

    return $script:DiagnosticResults
}

# Run diagnostics if script is executed directly
if ($MyInvocation.InvocationName -ne '.if ($MyInvocation.InvocationName -ne '.') { Start-Diagnostics }
