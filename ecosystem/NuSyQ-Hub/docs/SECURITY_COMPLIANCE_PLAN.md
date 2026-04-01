# Security & Compliance Automation Plan

## Goals
- Enforce secrets management (Key Vault, .env, never commit secrets)
- Add RBAC, audit logging, and compliance checks (azqr, SonarQube)
- Harden containers (non-root, minimal base images, health checks)

## Steps
1. Audit current secrets/config usage
2. Add/extend .env and Key Vault integration
3. Add RBAC and audit logging to orchestration
4. Integrate azqr and SonarQube in CI/CD
5. Harden Dockerfiles and add health checks

## Status
- [ ] Secrets audit complete
- [ ] RBAC and audit logging added
- [ ] Compliance checks in CI
- [ ] Docker hardening complete

---
Update this plan as security/compliance features are implemented.
