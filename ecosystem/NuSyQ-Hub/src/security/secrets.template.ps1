# KILO-FOOLISH Secrets Template
# Copy this to secrets.ps1 and fill in your actual API keys
# NEVER commit secrets.ps1 to version control

$script:Secrets = @{
    # AI API Keys
    OpenAI    = @{
        APIKey       = "sk-zAvVfXNZJLfFEEpcGtCST2M1i3tzXHhpPvbmYLBDliIk70zN9Zw6L2yIFNADgH1XU1Nz7h33pT3BlbkFJClpxzehVlJFSHAvewJURcT9c22XUWnV3cxUzKdI8QskhDLK7oQDXjlxUeAotIh5MvvLMTZV-MA"
        Organization = "org-your-org-here"
        Project      = "proj_your-project-here"
    }

    # Ollama Configuration
    Ollama    = @{
        Host   = "http://localhost:11434"
        APIKey = $null  # Usually not needed for local Ollama
    }

    # Anthropic Claude
    Anthropic = @{
        APIKey = "your-claude-key-here"
    }

    # GitHub Configuration
    GitHub    = @{
        Token    = "ghp_your-github-token-here"
        Username = "malik"
    }

    # Database Credentials (if needed)
    Database  = @{
        ConnectionString = "your-secure-connection-string"
        Password         = "your-secure-password"


    }

    # SonarQube Configuration
    SonarQube = @{
        Host      = "http://localhost:9000"
        Token     = "5c28d45e085e3828f3ea5a5179b66a1b20a40aa7"
        Namespace = "SONAR_TOKEN"
    }
}

# Export function to get secrets safely
function Get-Secret {
    param([string]$Category, [string]$Key)

    if ($script:Secrets.ContainsKey($Category) -and $script:Secrets[$Category].ContainsKey($Key)) {
        return $script:Secrets[$Category][$Key]
    }
    return $null
}

# Export function to test API connectivity
function Test-APIConnectivity {
    param([string]$Service)

    switch ($Service) {
        "OpenAI" {
            $apiKey = Get-Secret "OpenAI" "APIKey"
            # Add your OpenAI connectivity test logic here
            return $true
        }
        default {
            Write-Warning "Service '$Service' not supported"
            return $false
        }
    }
}
