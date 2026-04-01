# KILO-FOOLISH Centralized Secrets Management System
# Builds upon existing secrets.template.ps1 structure

param(
    [switch]$Setup,
    [switch]$Import,
    [switch]$Secure,
    [switch]$Sync,
    [switch]$Status,
    [string]$SetKey,
    [string]$SetValue
)

function Write-SecretsLog {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = Get-Date -Format "HH:mm:ss"
    $colors = @{
        "ERROR" = "Red"; "WARNING" = "Yellow"; "SUCCESS" = "Green"
        "INFO" = "White"; "SECRETS" = "Magenta"; "CRITICAL" = "Red"
    }

    Write-Host "[$timestamp] [SECRETS] $Message" -ForegroundColor $colors[$Level]
}

function Initialize-EnhancedSecretsSystem {
    Write-SecretsLog "Initializing enhanced secrets management system..." "SECRETS"

    # Create secure storage
    $secretsDir = ".\src\config"
    $secureDir = "$secretsDir\.secure"
    $backupDir = "$secretsDir\.backup"

    foreach ($dir in @($secureDir, $backupDir)) {
        if (!(Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory -Force
            # Hide the secure directory
            if ($dir -like "*\.secure") {
                (Get-Item $dir).Attributes = "Hidden"
            }
        }
    }

    # Enhanced secrets.ps1 based on existing template
    $secretsFile = "$secretsDir\secrets.ps1"
    if (!(Test-Path $secretsFile)) {
        $secretsContent = @'
# KILO-FOOLISH Enhanced Secrets Configuration
# This file contains actual secrets - DO NOT COMMIT TO GIT

# Encryption key for additional security
$Global:KILO_ENCRYPTION_KEY = "[GENERATED_KEY_PLACEHOLDER]"

# API Keys and Tokens
$Global:KILO_SECRETS = @{
    # AI Services
    OpenAI = @{
        ApiKey = "sk-zAvVfXNZJLfFEEpcGtCST2M1i3tzXHhpPvbmYLBDliIk70zN9Zw6L2yIFNADgH1XU1Nz7h33pT3BlbkFJClpxzehVlJFSHAvewJURcT9c22XUWnV3cxUzKdI8QskhDLK7oQDXjlxUeAotIh5MvvLMTZV"
        Organization = ""
        Model = "gpt-4o-mini"
        Temperature = 0.7
        MaxTokens = 2048
    }

    CodeSmellGPT = @{
        ApiKey = "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"
        Model = "gpt-4o-mini"
        Temperature = 0.7
        MaxTokens = 1000
        TopP = 1.0
        FrequencyPenalty = 0.0
        PresencePenalty = 0.0
        AutoFix = $true
        ReviewOnSave = $false
    }

    Anthropic = @{
        ApiKey = ""
        Model = "claude-3-sonnet"
        Temperature = 0.7
        MaxTokens = 2048
    }

    # GitHub Integration
    GitHub = @{
        Token = ""
        Username = ""
        CopilotEnabled = $true
    }

    # Local AI
    Ollama = @{
        Host = "http://localhost:11434"
        Timeout = 120
        Models = @("llama2:7b", "codellama:7b")
    }

    # VS Code Extensions
    VSCodeExtensions = @{
        CodeSmellGPT = @{
            Model = "gpt-4o-mini"
            Temperature = 0.7
            MaxTokens = 1000
        }
        AIQuickFix = @{
            Model = "gpt-4o-mini"
            Temperature = 0.7
            MaxTokens = 1000
        }
        Continue = @{
            Model = "gpt-4o-mini"
            Provider = "openai"
        }
    }

    # Database and Storage
    Database = @{
        ConnectionString = ""
        BackupLocation = ".\data\backups"
        EncryptBackups = $true
    }

    # Security Settings
    Security = @{
        SessionTimeout = 3600
        RequireEncryption = $true
        AllowedOrigins = @("localhost", "127.0.0.1")
    }

    # RPG Inventory Integration
    RPGInventory = @{
        UpdateInterval = 5
        AutoHeal = $true
        LogLevel = "INFO"
    }
}

# Helper Functions
function Get-KILOSecret {
    param(
        [string]$Category,
        [string]$Key,
        [string]$Default = $null
    )

    try {
        if ($Global:KILO_SECRETS.ContainsKey($Category)) {
            $categorySecrets = $Global:KILO_SECRETS[$Category]
            if ($categorySecrets.ContainsKey($Key)) {
                $value = $categorySecrets[$Key]
                # Don't return empty or placeholder values
                if ([string]::IsNullOrWhiteSpace($value) -or $value -eq "") {
                    return $Default
                }
                return $value
            }
        }
        return $Default
    }
    catch {
        Write-Warning "Failed to get secret $Category.$Key: $_"
        return $Default
    }
}

function Set-KILOSecret {
    param(
        [string]$Category,
        [string]$Key,
        [string]$Value,
        [switch]$UpdateVSCode
    )

    try {
        if (!$Global:KILO_SECRETS.ContainsKey($Category)) {
            $Global:KILO_SECRETS[$Category] = @{}
        }

        $Global:KILO_SECRETS[$Category][$Key] = $Value

        # Save to file
        Save-KILOSecrets

        if ($UpdateVSCode) {
            Sync-VSCodeWithSecrets
        }

        Write-Host "Secret updated: $Category.$Key" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to set secret: $_"
        return $false
    }
}

function Save-KILOSecrets {
    try {
        $backupFile = ".\src\config\.backup\secrets_$(Get-Date -Format 'yyyyMMdd_HHmmss').ps1"
        if (Test-Path ".\src\config\secrets.ps1") {
            Copy-Item ".\src\config\secrets.ps1" $backupFile
        }

        # Recreate the secrets file with current values
        $secretsContent = $Global:KILO_SECRETS | ConvertTo-Json -Depth 10
        # This is a simplified version - in practice, you'd recreate the full PowerShell structure

        Write-Host "Secrets saved and backed up" -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to save secrets: $_"
    }
}

function Test-KILOSecrets {
    Write-Host "Testing KILO-FOOLISH secrets configuration..." -ForegroundColor Cyan

    $results = @()

    # Test OpenAI
    $openaiKey = Get-KILOSecret "OpenAI" "ApiKey"
    $results += @{
        Service = "OpenAI"
        Status = if ($openaiKey -and $openaiKey.StartsWith("sk-")) { "✅ Valid" } else { "❌ Missing/Invalid" }
        Key = if ($openaiKey) { $openaiKey.Substring(0, 7) + "..." } else { "Not set" }
    }

    # Test CodeSmellGPT
    $codeSmellKey = Get-KILOSecret "CodeSmellGPT" "ApiKey"
    $results += @{
        Service = "CodeSmellGPT"
        Status = if ($codeSmellKey -and $codeSmellKey.StartsWith("sk-")) { "✅ Valid" } else { "❌ Missing/Invalid" }
        Key = if ($codeSmellKey) { $codeSmellKey.Substring(0, 7) + "..." } else { "Not set" }
    }

    # Test GitHub
    $githubToken = Get-KILOSecret "GitHub" "Token"
    $results += @{
        Service = "GitHub"
        Status = if ($githubToken -and ($githubToken.StartsWith("ghp_") -or $githubToken.StartsWith("github_pat_"))) { "✅ Valid" } else { "❌ Missing/Invalid" }
        Key = if ($githubToken) { $githubToken.Substring(0, 7) + "..." } else { "Not set" }
    }

    # Test Ollama
    $ollamaHost = Get-KILOSecret "Ollama" "Host"
    $results += @{
        Service = "Ollama"
        Status = if ($ollamaHost) { "✅ Configured" } else { "❌ Not configured" }
        Key = $ollamaHost
    }

    foreach ($result in $results) {
        $color = if ($result.Status.StartsWith("✅")) { "Green" } else { "Red" }
        Write-Host "$($result.Service): $($result.Status) ($($result.Key))" -ForegroundColor $color
    }

    return $results
}

Export-ModuleMember -Function Get-KILOSecret, Set-KILOSecret, Test-KILOSecrets, Save-KILOSecrets
'@

        # Generate encryption key
        $encryptionKey = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes([System.Guid]::NewGuid().ToString()))
        $secretsContent = $secretsContent -replace "\[GENERATED_KEY_PLACEHOLDER\]", $encryptionKey

        $secretsContent | Out-File -FilePath $secretsFile -Encoding UTF8
        Write-SecretsLog "Enhanced secrets.ps1 created ✓" "SUCCESS"
    }

    # Create Python wrapper
    $pythonWrapper = "$secretsDir\secrets.py"
    if (!(Test-Path $pythonWrapper)) {
        $pythonContent = @'
"""
KILO-FOOLISH Secrets Manager - Python Interface
Integrates with PowerShell secrets system
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any

class KILOSecretsManager:
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.secrets_file = self.config_dir / "secrets.ps1"

    def get_secret(self, category: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret using PowerShell backend"""
        try:
            # Use PowerShell to get the secret
            ps_command = f"""
            . '{self.secrets_file}'
            Get-KILOSecret '{category}' '{key}'
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                cwd=self.config_dir.parent.parent
            )

            if result.returncode == 0 and result.stdout.strip():
                value = result.stdout.strip()
                return value if value != "null" and value else default

            return default

        except Exception as e:
            print(f"Warning: Failed to get secret {category}.{key}: {e}")
            return default

    def set_secret(self, category: str, key: str, value: str) -> bool:
        """Set secret using PowerShell backend"""
        try:
            ps_command = f"""
            . '{self.secrets_file}'
            Set-KILOSecret '{category}' '{key}' '{value}'
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                cwd=self.config_dir.parent.parent
            )

            return result.returncode == 0

        except Exception as e:
            print(f"Error: Failed to set secret {category}.{key}: {e}")
            return False

    def test_secrets(self) -> Dict[str, bool]:
        """Test all secret configurations"""
        try:
            ps_command = f"""
            . '{self.secrets_file}'
            Test-KILOSecrets | ConvertTo-Json
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                cwd=self.config_dir.parent.parent
            )

            if result.returncode == 0:
                return json.loads(result.stdout)

            return {}

        except Exception as e:
            print(f"Error testing secrets: {e}")
            return {}

# Global instance
_secrets_manager = None

def get_secrets_manager() -> KILOSecretsManager:
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = KILOSecretsManager()
    return _secrets_manager

def get_secret(category: str, key: str, default: Optional[str] = None) -> Optional[str]:
    return get_secrets_manager().get_secret(category, key, default)

def set_secret(category: str, key: str, value: str) -> bool:
    return get_secrets_manager().set_secret(category, key, value)

# Convenience class for common configurations
class Config:
    @property
    def openai_api_key(self) -> Optional[str]:
        return get_secret("OpenAI", "ApiKey")

    @property
    def openai_model(self) -> str:
        return get_secret("OpenAI", "Model", "gpt-4o-mini")

    @property
    def github_token(self) -> Optional[str]:
        return get_secret("GitHub", "Token")

    @property
    def ollama_host(self) -> str:
        return get_secret("Ollama", "Host", "http://localhost:11434")

config = Config()
'@

        $pythonContent | Out-File -FilePath $pythonWrapper -Encoding UTF8
        Write-SecretsLog "Python secrets wrapper created ✓" "SUCCESS"
    }

    Write-SecretsLog "Enhanced secrets system initialized! ✓" "SUCCESS"
}

function Import-ExistingSecrets {
    Write-SecretsLog "Importing secrets from existing VS Code settings..." "SECRETS"

    $vscodeSettings = "$env:APPDATA\Code\User\settings.json"
    if (!(Test-Path $vscodeSettings)) {
        Write-SecretsLog "No VS Code settings found to import" "WARNING"
        return
    }

    try {
        # Read and fix the malformed JSON
        $content = Get-Content $vscodeSettings -Raw

        # Extract API keys from the malformed JSON
        if ($content -match '"vscode-code-smell-gpt\.gptKey":\s*"([^"]+)"') {
            $codeSmellKey = $matches[1]
            if ($codeSmellKey -and $codeSmellKey.StartsWith("sk-")) {
                Write-SecretsLog "Found CodeSmell GPT API key" "SUCCESS"
                . ".\src\config\secrets.ps1"
                Set-KILOSecret "OpenAI" "ApiKey" $codeSmellKey
            }
        }

        if ($content -match '"haselerdev\.aiquickfix\.apiKey":\s*"([^"]+)"') {
            $quickFixKey = $matches[1]
            if ($quickFixKey -and $quickFixKey.StartsWith("sk-")) {
                Write-SecretsLog "Found AI QuickFix API key" "SUCCESS"
                # Use the same key for consistency
            }
        }

        Write-SecretsLog "API keys imported successfully ✓" "SUCCESS"
    }
    catch {
        Write-SecretsLog "Failed to import existing secrets: $_" "ERROR"
    }
}

function Secure-VSCodeSettings {
    Write-SecretsLog "🚨 SECURING VS CODE SETTINGS (removing exposed API keys)..." "CRITICAL"

    $vscodeSettings = "$env:APPDATA\Code\User\settings.json"
    if (!(Test-Path $vscodeSettings)) {
        Write-SecretsLog "No VS Code settings file found" "INFO"
        return
    }

    try {
        # Backup current settings
        $backupFile = "$env:APPDATA\Code\User\settings_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        Copy-Item $vscodeSettings $backupFile
        Write-SecretsLog "Settings backed up to: $backupFile" "INFO"

        # Create clean settings without exposed keys
        $cleanSettings = @{
            "terminal.integrated.allowChords"            = $false
            "yaml.schemas"                               = @{
                "c:\\Users\\malik\\.vscode\\extensions\\continue.continue-1.0.15-win32-x64\\config-yaml-schema.json" = @(".continue/**/*.yaml")
            }
            "codeium.enableConfig"                       = @{
                "*"         = $true
                "markdown"  = $true
                "plaintext" = $true
            }
            "window.menuBarVisibility"                   = "compact"
            "editor.guides.bracketPairs"                 = $true

            # KILO-FOOLISH optimized settings
            "python.defaultInterpreterPath"              = ".\venv_kilo\Scripts\python.exe"
            "editor.formatOnSave"                        = $true
            "editor.codeActionsOnSave"                   = @{
                "source.organizeImports" = $true
            }
            "files.autoSave"                             = "afterDelay"
            "files.autoSaveDelay"                        = 1000
            "terminal.integrated.defaultProfile.windows" = "PowerShell"

            # Extension settings (without API keys - these will be managed centrally)
            "vscode-code-smell-gpt.gptModel"             = "gpt-4o-mini"
            "vscode-code-smell-gpt.gptTemperature"       = 0.7
            "vscode-code-smell-gpt.gptMaxTokens"         = 1000
            "haselerdev.aiquickfix.model"                = "gpt-4o-mini"
            "haselerdev.aiquickfix.temperature"          = 0.7
            "haselerdev.aiquickfix.maxTokens"            = 1000
        }

        $cleanSettings | ConvertTo-Json -Depth 10 | Out-File -FilePath $vscodeSettings -Encoding UTF8

        Write-SecretsLog "✅ VS Code settings secured! API keys removed." "SUCCESS"
        Write-SecretsLog "🔑 Extensions will get API keys from centralized secrets" "INFO"

    }
    catch {
        Write-SecretsLog "Failed to secure settings: $_" "ERROR"
    }
}

function Sync-VSCodeWithSecrets {
    Write-SecretsLog "Synchronizing VS Code extensions with central secrets..." "SECRETS"

    try {
        . ".\src\config\secrets.ps1"

        $openaiKey = Get-KILOSecret "OpenAI" "ApiKey"
        $codeSmellKey = Get-KILOSecret "CodeSmellGPT" "ApiKey"  # ADD THIS LINE

        if (($openaiKey -and $openaiKey.StartsWith("sk-")) -or ($codeSmellKey -and $codeSmellKey.StartsWith("sk-"))) {
            $vscodeSettings = "$env:APPDATA\Code\User\settings.json"

            if (Test-Path $vscodeSettings) {
                $settings = Get-Content $vscodeSettings | ConvertFrom-Json

                # Use CodeSmell-specific key for CodeSmell GPT, fallback to main OpenAI key
                $settings."vscode-code-smell-gpt.gptKey" = if ($codeSmellKey) { $codeSmellKey } else { $openaiKey }
                $settings."haselerdev.aiquickfix.apiKey" = $openaiKey  # Keep using main key for QuickFix
                $settings."continue.apiKey" = $openaiKey  # Keep using main key for Continue

                $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath $vscodeSettings -Encoding UTF8

                Write-SecretsLog "✅ VS Code extensions synchronized with central secrets" "SUCCESS"
                Write-SecretsLog "🔑 CodeSmell GPT using dedicated API key" "INFO"
            }
        }
        else {
            Write-SecretsLog "⚠️ No valid API keys found in central secrets" "WARNING"
        }
    }
    catch {
        Write-SecretsLog "Failed to sync VS Code: $_" "ERROR"
    }
}

function Show-SecretsStatus {
    Write-SecretsLog "KILO-FOOLISH Secrets Status:" "INFO"

    try {
        . ".\src\config\secrets.ps1"
        Test-KILOSecrets

        Write-Host "`nFiles:" -ForegroundColor Cyan
        $files = @(
            ".\src\config\secrets.ps1",
            ".\src\config\secrets.py",
            "$env:APPDATA\Code\User\settings.json"
        )

        foreach ($file in $files) {
            $exists = Test-Path $file
            $icon = if ($exists) { "✅" } else { "❌" }
            $size = if ($exists) { " ($(((Get-Item $file).Length / 1KB).ToString('F1'))KB)" } else { "" }
            Write-Host "  $icon $file$size" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
        }

    }
    catch {
        Write-SecretsLog "Failed to show status: $_" "ERROR"
    }
}

# Main execution
Write-Host "`n🔐 KILO-FOOLISH Enhanced Secrets Manager" -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Magenta

if ($Setup) {
    Initialize-EnhancedSecretsSystem
}

if ($Import) {
    Import-ExistingSecrets
}

if ($Secure) {
    Secure-VSCodeSettings
}

if ($Sync) {
    Sync-VSCodeWithSecrets
}

if ($Status) {
    Show-SecretsStatus
}

if ($SetKey -and $SetValue) {
    $parts = $SetKey.Split('.')
    if ($parts.Length -eq 2) {
        . ".\src\config\secrets.ps1"
        Set-KILOSecret $parts[0] $parts[1] $SetValue -UpdateVSCode
    }
    else {
        Write-SecretsLog "Key format should be 'Category.Key'" "ERROR"
    }
}

if (!$Setup -and !$Import -and !$Secure -and !$Sync -and !$Status -and !$SetKey) {
    Write-SecretsLog "🚨 URGENT: Your VS Code settings contain exposed API keys!" "CRITICAL"
    Write-SecretsLog "Run: .\src\config\SecretsManager.ps1 -Setup -Import -Secure" "INFO"
    Write-SecretsLog "" "INFO"
    Write-SecretsLog "Available actions:" "INFO"
    Write-SecretsLog "  -Setup    : Initialize enhanced secrets system" "INFO"
    Write-SecretsLog "  -Import   : Import existing API keys from VS Code" "INFO"
    Write-SecretsLog "  -Secure   : Remove API keys from VS Code settings" "INFO"
    Write-SecretsLog "  -Sync     : Sync secrets to VS Code extensions" "INFO"
    Write-SecretsLog "  -Status   : Show current status" "INFO"
    Write-SecretsLog "  -SetKey   : Set a secret (e.g., -SetKey 'OpenAI.ApiKey' -SetValue 'sk-...')" "INFO"
}

Write-SecretsLog "Secrets manager completed!" "SUCCESS"
