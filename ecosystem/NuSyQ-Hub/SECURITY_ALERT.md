# 🚨 CRITICAL SECURITY ALERT

**Date**: October 20, 2025  
**Severity**: CRITICAL  
**Status**: REQUIRES IMMEDIATE ACTION

## Exposed Credentials in Git History

The following credentials were found committed to git history and are
potentially compromised:

### 1. OpenAI API Key

- **Location**: `config/secrets.json` (commit 4f8ed2e)
- **Key Pattern**: REDACTED
- **Action Required**: REVOKE ANY EXPOSED KEY IMMEDIATELY via your provider's dashboard (e.g. OpenAI)

### 2. GitHub Personal Access Token

- **Location**: `config/secrets.json` (commit 4f8ed2e)
- **Token**: REDACTED
- **Action Required**: REVOKE ANY EXPOSED TOKEN IMMEDIATELY via GitHub settings

### 3. Additional Exposure in NuSyQ Repository

- **Location**: `c:\Users\keath\NuSyQ\docs\VSCODE_EXTENSION_CONFIG.md` (line 368)
- **Key Pattern**: REDACTED
- **Status**: REDACTED in working tree; may still exist in git history
- **Action Required**: Revoke any discovered keys and clean git history if needed

## Immediate Actions Required

### 1. Revoke Credentials (DO THIS FIRST!)

```bash
# Go to these URLs and revoke the keys:
# OpenAI: https://platform.openai.com/api-keys
# GitHub: https://github.com/settings/tokens
```

### 2. Remove from Git History

```bash
# Using BFG Repo-Cleaner (recommended)
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
java -jar bfg.jar --delete-files secrets.json
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# OR using git-filter-repo (alternative)
git filter-repo --path config/secrets.json --invert-paths
```

### 3. Verify Removal

```bash
git log --all --full-history -- config/secrets.json
# Should return nothing after cleaning
```

### 4. Update GitHub Remote

```bash
# After cleaning, force push (⚠️ WARNING: destructive)
git push origin --force --all
git push origin --force --tags
```

## Prevention Measures Implemented

✅ Added `config/secrets.json` to `.gitignore`  
✅ Created `SecretsManager.ps1` for centralized secrets management  
✅ Redacted exposed keys in documentation  
✅ Created this security alert

## Still To Do

- [ ] Revoke exposed OpenAI API key
- [ ] Revoke exposed GitHub token
- [ ] Clean git history with BFG or git-filter-repo
- [ ] Force push cleaned history to GitHub
- [ ] Generate new API keys
- [ ] Update secrets using SecretsManager.ps1
- [ ] Scan NuSyQ and SimulatedVerse repos for similar issues

## How to Use SecretsManager Going Forward

```powershell
# Setup secure secrets storage
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
.\src\security\SecretsManager.ps1 -Setup

# Set new API keys securely
.\src\security\SecretsManager.ps1 -SetKey "OpenAI.ApiKey" -SetValue "sk-NEW-KEY-HERE"
.\src\security\SecretsManager.ps1 -SetKey "GitHub.Token" -SetValue "ghp_NEW-TOKEN-HERE"

# Sync to VS Code extensions
.\src\security\SecretsManager.ps1 -Sync

# Check status
.\src\security\SecretsManager.ps1 -Status
```

## Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [OpenAI API Keys Management](https://platform.openai.com/api-keys)
- [GitHub Tokens Management](https://github.com/settings/tokens)

---

**Generated**: October 20, 2025  
**Priority**: CRITICAL - Act immediately
