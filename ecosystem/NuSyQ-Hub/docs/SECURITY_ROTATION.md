# Security Rotation Guide

This guide explains how to rotate and manage API keys and secrets for the
NuSyQ-Hub workspace in a safe, auditable way.

## What changed

- Plaintext API keys were present in `.vscode/settings.json` for these
  extensions:
  - haselerdev.aiquickfix.apiKey
  - vscode-code-smell-gpt.gptKey
- These keys have been replaced with environment-variable references using VS
  Code's `${env:...}` support:
  - `AIQUICKFIX_API_KEY`
  - `CODE_SMELL_GPT_API_KEY`
- A `.env.example` file was updated to include the new variables.
- `.gitignore` already ignores `.env` and `config/secrets.json`.

This removes plaintext keys from the working tree and centralizes secrets in
environment variables while keeping functionality intact.

## Rotation steps

1. Generate new API keys in each provider's console (AIQuickFix, Code Smell
   GPT):
   - Save both old and new keys temporarily to verify the cutover.
2. Update your local `.env` (not committed) with the new values:

   ```env
   AIQUICKFIX_API_KEY=NEW_AIQUICKFIX_KEY
   CODE_SMELL_GPT_API_KEY=NEW_CODE_SMELL_GPT_KEY
   ```

3. Restart VS Code (or reload window) so settings pick up `${env:...}` values.
4. Validate extension functionality (quick run each tool once).
5. Revoke the old keys in provider consoles.
6. Optional: Add OS-level secret storage (Windows Credential Manager, 1Password,
   etc.) and avoid `.env` in production contexts.

## Auditing and compliance

- Confirm `.env` is ignored (see `.gitignore`).
- Verify that no secrets are logged or committed:
  - Search for patterns in the repo (e.g., `KEY=`, `sk-`, etc.).
  - Use internal security scans where available.
- If any secret is found in git history, plan a history rewrite (BFG or git
  filter-repo) and rotate keys again.

## References

- VS Code settings variable substitution: `${env:VAR}`
- Project policy: `.env` and `config/secrets.json` must never be committed.
- Contact: Maintainers of NuSyQ-Hub for escalation.
