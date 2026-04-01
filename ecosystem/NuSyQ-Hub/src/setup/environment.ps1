# KILO-FOOLISH Environment Management
# Handles different environments (dev, staging, prod) securely

param(
    [ValidateSet("development", "staging", "production")]
    [string]$Environment = "development"
)

# Load base configuration
. ".\config\project.ps1"

# Load secrets securely
$secretsPath = ".\config\secrets.ps1"
if (Test-Path $secretsPath) {
    . $secretsPath
    Write-Host "✓ Secrets loaded for $Environment environment" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Secrets file not found. Copy config/secrets.template.ps1 to config/secrets.ps1" -ForegroundColor Yellow
    Write-Host "   and fill in your API keys." -ForegroundColor Yellow
}

# Environment-specific configuration
$script:EnvironmentConfig = switch ($Environment) {
    "development" {
        @{
            Debug            = $true
            LogLevel         = "DEBUG"
            OllamaHost       = "http://localhost:11434"
            DatabaseUrl      = "sqlite:///./data/dev_kilo_foolish.db"
            CacheEnabled     = $false
            RateLimitEnabled = $false
        }
    }
    "staging" {
        @{
            Debug            = $false
            LogLevel         = "INFO"
            OllamaHost       = "http://staging-ollama:11434"
            DatabaseUrl      = "postgresql://staging-db:5432/kilo_foolish"
            CacheEnabled     = $true
            RateLimitEnabled = $true
        }
    }
    "production" {
        @{
            Debug             = $false
            LogLevel          = "WARNING"
            OllamaHost        = "http://prod-ollama:11434"
            DatabaseUrl       = "postgresql://prod-db:5432/kilo_foolish"
            CacheEnabled      = $true
            RateLimitEnabled  = $true
            EncryptionEnabled = $true
        }
    }
}

# Export functions
function Get-EnvironmentConfig { return $script:EnvironmentConfig }
function Get-CurrentEnvironment { return $Environment }

# Validate critical configuration
function Test-EnvironmentSetup {
    $issues = @()

    # Check for required secrets
    $requiredSecrets = @("OpenAI.APIKey", "GitHub.Token")
    foreach ($secret in $requiredSecrets) {
        $parts = $secret.Split(".")
        $value = Get-Secret $parts[0] $parts[1]
        if (!$value -or $value.Contains("your-") -or $value.Contains("sk-your")) {
            $issues += "Missing or template value for: $secret"
        }
    }

    # Check API connectivity
    if (!(Test-APIConnectivity "Ollama")) {
        $issues += "Ollama service not accessible"
    }

    return $issues
}
