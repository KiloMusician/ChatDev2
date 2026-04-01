# Configuration Quick Start Guide

## 🔐 Missing API Keys & Credentials

The system detected **REDACTED placeholders** in `config/secrets.json`. Here's
how to properly configure:

### Option 1: Environment Variables (Recommended)

```powershell
# Add to your PowerShell profile or .env file
$env:OPENAI_API_KEY = "sk-your-actual-key-here"
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
$env:GITHUB_TOKEN = "ghp_your-token-here"
```

### Option 2: Update secrets.json Directly

```json
{
  "openai": {
    "api_key": "sk-your-actual-key-here", // Replace REDACTED
    "organization": "org-your-org-id",
    "project": "proj_your-project-id"
  },
  "anthropic": {
    "api_key": "sk-ant-your-key-here" // Replace REDACTED
  },
  "github": {
    "token": "ghp_your-token-here", // Replace REDACTED
    "username": "KiloMusician" // Your actual GitHub username
  }
}
```

### Option 3: Run Configuration Helper

```powershell
python scripts/setup_integrations.py
# Guides you through interactive setup
```

## 🔍 Configuration Validation

Check if your secrets are loaded:

```powershell
python -c "from src.setup.secrets import config; print('OpenAI:', 'CONFIGURED' if config.get_secret('openai', 'api_key') and 'REDACTED' not in config.get_secret('openai', 'api_key') else 'MISSING'); print('Anthropic:', 'CONFIGURED' if config.get_secret('anthropic', 'api_key') and 'REDACTED' not in config.get_secret('anthropic', 'api_key') else 'MISSING')"
```

## ⚡ Quick Test

```powershell
# Verify Ollama (local, no API key needed)
python scripts/start_nusyq.py test_ollama

# Verify full stack
python scripts/quick_status.py
```

## 🔒 Security Best Practices

1. **Never commit actual API keys** - Keep `config/secrets.json` in `.gitignore`
2. **Use environment variables for CI/CD** - Safer for automated workflows
3. **Rotate keys regularly** - Especially if accidentally exposed
4. **Keep REDACTED placeholders** - Helps other contributors know what's needed

---

**Status:** Configuration incomplete - please populate actual credentials to
unlock full AI capabilities.
