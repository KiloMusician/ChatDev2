# KILO-FOOLISH VS Code Extension Installer

param(
    [switch]$Essential,
    [switch]$AI,
    [switch]$Debug,
    [switch]$Productivity,
    [switch]$All,
    [switch]$Verbose
)

function Write-ExtensionLog {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = Get-Date -Format "HH:mm:ss"
    $colors = @{
        "ERROR" = "Red"; "WARNING" = "Yellow"; "SUCCESS" = "Green"
        "INFO" = "White"; "EXTENSION" = "Blue"
    }

    Write-Host "[$timestamp] [EXTENSION] $Message" -ForegroundColor $colors[$Level]
}

# Extension categories
$ExtensionSets = @{
    Essential    = @(
        "ms-python.python",
        "ms-python.black-formatter",
        "ms-python.isort",
        "ms-python.flake8",
        "ms-vscode.powershell",
        "streetsidesoftware.code-spell-checker",
        "ms-vscode.vscode-json",
        "redhat.vscode-yaml",
        "davidanson.vscode-markdownlint"
    )

    AI           = @(
        "github.copilot",
        "github.copilot-chat",
        "continue.continue",
        "tabnine.tabnine-vscode",
        "rubberduck.rubberduck-vscode",
        "appland.appmap"
    )

    Debug        = @(
        "wallabyjs.console-ninja",
        "yoavbls.pretty-ts-errors",
        "ubaid.varlens",
        "ms-vscode.vscode-js-debug",
        "formulahendry.code-runner",
        "ms-python.debugpy"
    )

    Productivity = @(
        "alefragnani.bookmarks",
        "aaron-bond.better-comments",
        "formulahendry.auto-rename-tag",
        "christian-kohler.path-intellisense",
        "adpyke.codesnap",
        "pkief.material-icon-theme",
        "zhuangtongfa.material-theme",
        "oderwat.indent-rainbow",
        "coenraads.bracket-pair-colorizer-2",
        "ritwickdey.liveserver",
        "ms-vscode.live-server"
    )

    Advanced     = @(
        "ms-vscode.remote-wsl",
        "ms-vscode.remote-containers",
        "ms-azuretools.vscode-docker",
        "ms-vscode.vscode-ai-toolkit",
        "ms-toolsai.jupyter",
        "ms-python.vscode-pylance",
        "bradlc.vscode-tailwindcss",
        "esbenp.prettier-vscode"
    )
}

function Test-VSCodeInstalled {
    try {
        $result = code --version 2>$null
        return $null -ne $result
    }
    catch {
        return $false
    }
}

function Install-ExtensionSet {
    param([string]$SetName, [string[]]$Extensions)

    Write-ExtensionLog "Installing $SetName extension set..." "EXTENSION"

    $installed = 0
    $failed = 0

    foreach ($extension in $Extensions) {
        try {
            Write-ExtensionLog "Installing $extension..." "INFO"

            $result = code --install-extension $extension --force 2>&1

            if ($global:LASTEXITCODE -eq 0) {
                Write-ExtensionLog "✓ $extension installed" "SUCCESS"
                $installed++
            }
            else {
                Write-ExtensionLog "✗ Failed to install $extension" "ERROR"
                $failed++
                if ($Verbose) {
                    Write-ExtensionLog "Error: $result" "ERROR"
                }
            }
        }
        catch {
            Write-ExtensionLog "✗ Exception installing $extension: $($_.Exception.Message)" "ERROR"
            $failed++
        }

        Start-Sleep -Milliseconds 500  # Prevent rate limiting
    }

    Write-ExtensionLog "$SetName set complete: $installed installed, $failed failed" "INFO"
    return @{ Installed = $installed; Failed = $failed }
}

function New-VSCodeSettings {
    Write-ExtensionLog "Creating optimized VS Code settings..." "EXTENSION"

    $settingsDir = "$env:APPDATA\Code\User"
    $settingsFile = "$settingsDir\settings.json"

    if (!(Test-Path $settingsDir)) {
        New-Item -Path $settingsDir -ItemType Directory -Force
    }

    $optimizedSettings = @{
        # Python configuration
        "python.defaultInterpreterPath"              = ".\venv_kilo\Scripts\python.exe"
        "python.formatting.provider"                 = "black"
        "python.linting.enabled"                     = $true
        "python.linting.flake8Enabled"               = $true
        "python.analysis.typeCheckingMode"           = "basic"

        # PowerShell configuration
        "powershell.powerShellDefaultVersion"        = "Windows PowerShell (x86)"
        "powershell.integratedConsole.showOnStartup" = $false

        # AI assistance
        "github.copilot.enable"                      = @{
            "*"         = $true
            "yaml"      = $false
            "plaintext" = $false
        }
        "continue.telemetryEnabled"                  = $false

        # Editor enhancements
        "editor.suggestOnTriggerCharacters"          = $true
        "editor.quickSuggestions"                    = @{
            "other"    = $true
            "comments" = $false
            "strings"  = $true
        }
        "editor.bracketPairColorization.enabled"     = $true
        "editor.guides.bracketPairs"                 = "active"
        "editor.minimap.enabled"                     = $true
        "editor.wordWrap"                            = "on"
        "editor.formatOnSave"                        = $true
        "editor.codeActionsOnSave"                   = @{
            "source.organizeImports" = $true
        }

        # File associations for KILO-FOOLISH
        "files.associations"                         = @{
            "*.ps1"             = "powershell"
            "*.psd1"            = "powershell"
            "*.psm1"            = "powershell"
            "requirements*.txt" = "pip-requirements"
        }

        # Theme and appearance
        "workbench.colorTheme"                       = "Material Theme Ocean High Contrast"
        "workbench.iconTheme"                        = "material-icon-theme"
        "workbench.startupEditor"                    = "readme"

        # Terminal configuration
        "terminal.integrated.defaultProfile.windows" = "PowerShell"
        "terminal.integrated.profiles.windows"       = @{
            "PowerShell"     = @{
                "source" = "PowerShell"
                "icon"   = "terminal-powershell"
            }
            "Command Prompt" = @{
                "path" = @(
                    "${env:windir}\Sysnative\cmd.exe",
                    "${env:windir}\System32\cmd.exe"
                )
                "args" = @()
                "icon" = "terminal-cmd"
            }
        }

        # Code runner configuration
        "code-runner.executorMap"                    = @{
            "python"     = ".\venv_kilo\Scripts\python.exe"
            "powershell" = "powershell -ExecutionPolicy Bypass -File"
        }
        "code-runner.runInTerminal"                  = $true
        "code-runner.preserveFocus"                  = $false

        # Live server
        "liveServer.settings.donotShowInfoMsg"       = $true
        "liveServer.settings.donotVerifyTags"        = $true

        # Spell checker
        "cSpell.words"                               = @(
            "KILO",
            "FOOLISH",
            "ΞNuSyQ",
            "Ollama",
            "venv",
            "psutil",
            "asyncio",
            "dataclass",
            "subprocess"
        )

        # Auto-save
        "files.autoSave"                             = "afterDelay"
        "files.autoSaveDelay"                        = 1000

        # Git integration
        "git.enableSmartCommit"                      = $true
        "git.confirmSync"                            = $false
        "git.autofetch"                              = $true
    }

    try {
        $settingsJson = $optimizedSettings | ConvertTo-Json -Depth 10
        $settingsJson | Out-File -FilePath $settingsFile -Encoding UTF8 -Force
        Write-ExtensionLog "VS Code settings configured ✓" "SUCCESS"
        return $true
    }
    catch {
        Write-ExtensionLog "Failed to create settings: $_" "ERROR"
        return $false
    }
}

function New-VSCodeWorkspace {
    Write-ExtensionLog "Creating KILO-FOOLISH workspace file..." "EXTENSION"

    $workspaceConfig = @{
        folders    = @(
            @{ path = "." }
        )
        settings   = @{
            "python.defaultInterpreterPath" = ".\venv_kilo\Scripts\python.exe"
            "terminal.integrated.cwd"       = "${workspaceFolder}"
        }
        extensions = @{
            recommendations = @(
                "ms-python.python",
                "github.copilot",
                "ms-vscode.powershell",
                "wallabyjs.console-ninja",
                "continue.continue"
            )
        }
        tasks      = @{
            version = "2.0.0"
            tasks   = @(
                @{
                    label        = "Setup KILO-FOOLISH"
                    type         = "shell"
                    command      = ".\setup.ps1"
                    group        = "build"
                    presentation = @{
                        echo   = $true
                        reveal = "always"
                        focus  = $false
                        panel  = "shared"
                    }
                },
                @{
                    label   = "Start RPG Dashboard"
                    type    = "shell"
                    command = ".\src\system\RPGInventorySetup.ps1"
                    args    = @("-Dashboard")
                    group   = "test"
                },
                @{
                    label   = "Test AI Coordinator"
                    type    = "shell"
                    command = ".\src\ai\AICoordinatorSetup.ps1"
                    args    = @("-Test", "-Interactive")
                    group   = "test"
                }
            )
        }
        launch     = @{
            version        = "0.2.0"
            configurations = @(
                @{
                    name    = "Python: Current File"
                    type    = "python"
                    request = "launch"
                    program = "${file}"
                    console = "integratedTerminal"
                    python  = ".\venv_kilo\Scripts\python.exe"
                },
                @{
                    name    = "PowerShell: Current File"
                    type    = "PowerShell"
                    request = "launch"
                    script  = "${file}"
                    cwd     = "${workspaceFolder}"
                }
            )
        }
    }

    try {
        $workspaceJson = $workspaceConfig | ConvertTo-Json -Depth 10
        $workspaceJson | Out-File -FilePath "KILO-FOOLISH.code-workspace" -Encoding UTF8 -Force
        Write-ExtensionLog "Workspace file created ✓" "SUCCESS"
        return $true
    }
    catch {
        Write-ExtensionLog "Failed to create workspace: $_" "ERROR"
        return $false
    }
}

# Main execution
Write-Host "`n💎 KILO-FOOLISH VS Code Extension Installer" -ForegroundColor Blue
Write-Host "=" * 50 -ForegroundColor Blue

# Check if VS Code is installed
if (!(Test-VSCodeInstalled)) {
    Write-ExtensionLog "VS Code not found or not in PATH" "ERROR"
    Write-ExtensionLog "Please install VS Code and ensure 'code' command is available" "ERROR"
    exit 1
}

$totalStats = @{ Installed = 0; Failed = 0 }

# Install extension sets based on parameters
if ($Essential -or $All) {
    $result = Install-ExtensionSet -SetName "Essential" -Extensions $ExtensionSets.Essential
    $totalStats.Installed += $result.Installed
    $totalStats.Failed += $result.Failed
}

if ($AI -or $All) {
    $result = Install-ExtensionSet -SetName "AI" -Extensions $ExtensionSets.AI
    $totalStats.Installed += $result.Installed
    $totalStats.Failed += $result.Failed
}

if ($Debug -or $All) {
    $result = Install-ExtensionSet -SetName "Debug" -Extensions $ExtensionSets.Debug
    $totalStats.Installed += $result.Installed
    $totalStats.Failed += $result.Failed
}

if ($Productivity -or $All) {
    $result = Install-ExtensionSet -SetName "Productivity" -Extensions $ExtensionSets.Productivity
    $totalStats.Installed += $result.Installed
    $totalStats.Failed += $result.Failed
}

if ($All) {
    $result = Install-ExtensionSet -SetName "Advanced" -Extensions $ExtensionSets.Advanced
    $totalStats.Installed += $result.Installed
    $totalStats.Failed += $result.Failed
}

# Create optimized settings and workspace
if ($totalStats.Installed -gt 0) {
    Write-ExtensionLog "Configuring VS Code for KILO-FOOLISH..." "EXTENSION"

    New-VSCodeSettings
    New-VSCodeWorkspace

    Write-ExtensionLog "Configuration complete! Restart VS Code to apply changes." "SUCCESS"
}

# Summary
Write-Host "`n📊 Installation Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Extensions installed: $($totalStats.Installed)" -ForegroundColor Green
Write-Host "  ❌ Extensions failed: $($totalStats.Failed)" -ForegroundColor Red

if ($totalStats.Failed -eq 0 -and $totalStats.Installed -gt 0) {
    Write-ExtensionLog "All extensions installed successfully! 🎉" "SUCCESS"
}
elseif ($totalStats.Installed -eq 0) {
    Write-ExtensionLog "No action taken. Use -Essential, -AI, -Debug, -Productivity, or -All" "WARNING"
    Write-ExtensionLog "Example: .\InstallVSCodeExtensions.ps1 -Essential -AI" "INFO"
}

Write-ExtensionLog "VS Code extension setup completed!" "SUCCESS"
