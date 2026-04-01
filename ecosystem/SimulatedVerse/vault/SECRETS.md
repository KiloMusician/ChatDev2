---
source: docs/SECRETS.md
updated: 2025-08-30T05:30:30.575Z
tags: [corelink, documentation]
---

# Secret Configuration Guide

## Required Secrets (Production)
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - Authentication token signing key

## Optional Secrets (Development)
- `OPENAI_API_KEY` - AI functionality (fallback to mock)
- `ANTHROPIC_API_KEY` - Alternative AI provider
- `SENTRY_DSN` - Error monitoring (development optional)

## Setup in Replit
1. Click "Secrets" in sidebar
2. Add key-value pairs (no quotes needed)
3. Restart application after adding secrets

## Mock Mode
Set `FAKE_MODE=true` to use mock providers when secrets are missing.
This allows development without external API dependencies.