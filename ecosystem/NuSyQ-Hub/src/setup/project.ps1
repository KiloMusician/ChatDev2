# KILO-FOOLISH Project Configuration
# This file contains all project constants and settings

# Project Identity
$script:ProjectConfig = @{
    Name              = "KILO-FOOLISH"
    Version           = "1.0.0"
    Description       = "ΞNuSyQ₁ Quantum Development Framework"
    Author            = "malik"
    License           = "MIT"
    Repository        = "https://github.com/malik/KILO-FOOLISH"

    # Technical Requirements
    PythonVersion     = "3.11"
    PowerShellVersion = "5.0"
    NodeVersion       = "latest"

    # Directory Structure
    Directories       = @{
        Source = "src"
        Tests  = "tests"
        Docs   = "docs"
        Config = "config"
        Data   = "data"
        Logs   = "logs"
        VSCode = ".vscode"
    }

    # AI Configuration
    AI                = @{
        OllamaHost   = "http://localhost:11434"
        DefaultModel = "llama2"
        MaxTokens    = 4096
    }
}

# Export functions to access configuration
function Get-ProjectName { return $script:ProjectConfig.Name }
function Get-ProjectVersion { return $script:ProjectConfig.Version }
function Get-ProjectConfig { return $script:ProjectConfig }

# Set global variables for backward compatibility
$global:PROJECT_NAME = $script:ProjectConfig.Name
$global:PROJECT_VERSION = $script:ProjectConfig.Version
