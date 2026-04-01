<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.guide.github-token-setup                            ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [github, authentication, security, setup, tokens]                ║
║ CONTEXT: Σ2 (Feature Layer)                                            ║
║ AGENTS: [AllAgents, ClaudeCode]                                        ║
║ DEPS: [.env.secrets, GitHub]                                           ║
║ INTEGRATIONS: [GitHub, Git]                                            ║
║ CREATED: 2025-10-06                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code + KiloMusician                                      ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# GitHub Token Setup - Complete ✅

**Date:** 2025-10-06
**User:** KiloMusician
**Status:** Configured and secured

---

## Tokens Configured

### 1. Fine-Grained Personal Access Token
**Name:** `KATANA_GITHUB_FINE_GRAINED_TOKEN`
**Expires:** 2026-09-10
**Scope:** All repositories
**Permissions:** 30 permissions including:
- Actions (R/W)
- Administration (R/W)
- Contents (R/W)
- Issues (R/W)
- Pull Requests (R/W)
- Workflows (R/W)
- Secrets (R/W)
- And 23 more...

### 2. Classic Personal Access Token
**Name:** `KATANA_GITHUB_TOKEN_CLASSIC`
**Expires:** 2026-09-10
**Scopes:** Full access including:
- repo (full control)
- workflow
- admin:org
- user
- delete_repo
- copilot
- project
- And all available scopes

---

## Storage Locations

### Primary Storage: `.env.secrets`
```bash
# Location
C:\Users\keath\NuSyQ\.env.secrets

# Contents
KATANA_GITHUB_FINE_GRAINED_TOKEN=github_pat_11BDFALEA056QxwyioLceD_***
KATANA_GITHUB_TOKEN_CLASSIC=ghp_orO2vqUb1IlHWzy6EJA8gcj4deXopH***
GITHUB_TOKEN=${KATANA_GITHUB_FINE_GRAINED_TOKEN}
```

### Configuration Reference: `config/environment.json`
```json
{
  "GITHUB_USER": "KiloMusician",
  "GITHUB_AUTHENTICATED": true,
  "GITHUB_TOKEN_LOCATION": ".env.secrets"
}
```

### GitHub CLI Keyring
The fine-grained token is also stored in Windows Credential Manager via GitHub CLI.

---

## Security Measures Applied

✅ **Added to `.gitignore`**
```
.env.secrets
```

✅ **File Permissions**
- Located in local repository only
- Not committed to Git
- Excluded from version control

✅ **Token Management**
- Tokens expire: 2026-09-10 (11 months)
- Can be revoked at: https://github.com/settings/tokens
- Stored locally only

---

## Usage

### Load Tokens in PowerShell
```powershell
# Load all environment variables from .env.secrets
Get-Content .env.secrets | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Verify loaded
$env:KATANA_GITHUB_FINE_GRAINED_TOKEN
```

### Load Tokens in Bash/Linux
```bash
# Source the file
set -a
source .env.secrets
set +a

# Verify
echo $KATANA_GITHUB_FINE_GRAINED_TOKEN
```

### Use with GitHub CLI
```bash
# Already authenticated via gh auth login
gh auth status

# Use in commands
gh repo list
gh issue create --title "Test" --body "Testing token"
```

### Use with Git Operations
```bash
# Git automatically uses gh credentials
git push origin main

# Or set explicitly
git config --global credential.helper store
echo "https://KiloMusician:$KATANA_GITHUB_FINE_GRAINED_TOKEN@github.com" >> ~/.git-credentials
```

### Use with GitHub API
```python
import os
import requests

# Load token
token = os.getenv('KATANA_GITHUB_FINE_GRAINED_TOKEN')

# Make API request
headers = {'Authorization': f'token {token}'}
response = requests.get('https://api.github.com/user/repos', headers=headers)
repos = response.json()
```

```bash
# curl example
curl -H "Authorization: token $KATANA_GITHUB_FINE_GRAINED_TOKEN" \
  https://api.github.com/user/repos
```

---

## Integration with NuSyQ Components

### Flexibility Manager
The `config/flexibility_manager.py` can now use these tokens:

```python
import os

class GitHubAuthManager:
    def __init__(self):
        # Load token from environment
        self.token = os.getenv('KATANA_GITHUB_FINE_GRAINED_TOKEN')
        self.username = "KiloMusician"

    def check_authentication(self):
        if self.token:
            return True
        return False
```

### VS Code Extensions
Extensions can use the GitHub CLI authentication automatically:
- GitHub Copilot ✅
- GitHub Pull Requests ✅
- GitLens ✅

### ChatDev Integration
Can now access private repositories:
```python
os.environ['GITHUB_TOKEN'] = os.getenv('KATANA_GITHUB_FINE_GRAINED_TOKEN')
```

---

## Automatic Workflows Enabled

With these tokens, you can now:

1. **Automated Releases**
   ```yaml
   # .github/workflows/release.yml
   - uses: actions/create-release@v1
     env:
       GITHUB_TOKEN: ${{ secrets.KATANA_GITHUB_FINE_GRAINED_TOKEN }}
   ```

2. **Automated PR Creation**
   ```bash
   gh pr create --title "Auto Update" --body "Automated changes"
   ```

3. **Repository Management**
   ```bash
   gh repo create new-project --private
   gh repo clone KiloMusician/NuSyQ
   ```

4. **Issue/Project Automation**
   ```bash
   gh issue create --title "Bug" --label bug
   gh project create --name "Q4 2025"
   ```

---

## Token Rotation Reminder

**Expiration Date:** September 10, 2026

**Before expiration:**
1. Generate new tokens at https://github.com/settings/tokens
2. Update `.env.secrets` file
3. Re-authenticate GitHub CLI:
   ```bash
   gh auth logout
   gh auth login --with-token < new_token.txt
   ```

---

## Troubleshooting

### Token Not Working
```bash
# Verify token is loaded
echo $KATANA_GITHUB_FINE_GRAINED_TOKEN

# Test with GitHub API
curl -H "Authorization: token $KATANA_GITHUB_FINE_GRAINED_TOKEN" \
  https://api.github.com/user
```

### Permission Denied
```bash
# Check token scopes
curl -H "Authorization: token $KATANA_GITHUB_FINE_GRAINED_TOKEN" \
  https://api.github.com/user | jq '.scopes'

# Verify against required permissions at:
# https://docs.github.com/rest/overview/permissions-required-for-fine-grained-personal-access-tokens
```

### Token Exposed
If token is accidentally exposed:
1. Immediately revoke at https://github.com/settings/tokens
2. Generate new token
3. Update `.env.secrets`
4. Re-authenticate: `gh auth login`

---

## Security Best Practices

✅ **Never commit tokens to Git**
✅ **Use environment variables**
✅ **Set expiration dates**
✅ **Use fine-grained tokens when possible** (more secure)
✅ **Regularly rotate tokens**
✅ **Revoke unused tokens**
✅ **Monitor token usage** at https://github.com/settings/tokens

---

## Related Documentation

- [GitHub Token Best Practices](https://docs.github.com/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Guide_Contributing_AllUsers.md](Guide_Contributing_AllUsers.md) - Authentication setup guide
- [config/flexibility_manager.py](config/flexibility_manager.py) - GitHub integration

---

**Setup Complete!** 🎉

GitHub authentication is now fully configured for the NuSyQ repository with both fine-grained and classic tokens.
