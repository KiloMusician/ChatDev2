# Unified Dev Environment Chug Prompt

MODE: Autonomous multi-repo orchestrator
OBJECTIVE: Seamlessly integrate local and remote dev surfaces (Replit, VS Code tunnel, Postgres) while honoring system consistency and emergent behavior.
CONTEXT: The NuSyQ ecosystem consists of the repositories SimulatedVerse, NuSyQ-Hub, NuSyQ_Ultimate, awesome-vibe-coding, Dev-Mentor, and CONCEPT_SAMURAI. Tasks span these repos and rely on shared infrastructure and remote development surfaces.

## Environment Setup

### Remote Dev URLs
- Replit (primary): https://58867024-2573-4577-9b83-376c0c21be2e-00-1qwc0lyq6i3ia.riker.replit.dev/
- Replit (alt 1): https://5d70a0b5-0a1e-4ab1-9d50-9219c177a51b-00-33gy2d8vfum4x.worf.replit.dev/
- VS Code Tunnel: https://vscode.dev/tunnel/msi/c:/Kilo_Core/KiloCore.code-workspace

### Database
- Engine: PostgreSQL
- Password env var: DB_PASSWORD (set via secrets, never hardcoded)
- Connect via dev tunnel for remote DB access

### Working Directories
- All repos mapped to `ecosystem/` directory
- PYTHONPATH includes all repo roots for cross-repo imports

## Chug Cycle Actions

### Contextual Awareness
- Identify which repo is being edited when connecting to a remote URL
- Propagate context: SimulatedVerse ↔ NuSyQ-Hub dependency awareness

### Task Hydration via Remote Surfaces
- Replit: quick experiments, prototyping, microservice hosting
- VS Code tunnel: full IDE (lint, debug, test), propagates to git repo

### Agent Delegation
- **Serena**: code indexing and contextual Q&A
- **Ada**: content and code generation
- **Ollama/LM Studio**: large-model tasks, refactoring
- **ChatDev**: project scaffolding
- **Gordon**: self-improvement cycles + CHUG orchestration

### Cross-Repo Operations
- Track dependencies explicitly across repos
- Use consistent git branches (e.g., `feature/chug-upgrade`) across all repos
- Push changes via tunnels for coherence

### Database Operations
- Run migrations/queries via Postgres connection
- Implement transaction safety to avoid conflicts
- Use tunnels to ensure DB reachability from both local and remote

### Security & State Hygiene
- Never expose DB password or remote URLs in logs
- After each cycle: sanitize logs, strip secrets before transmitting

## End-of-Cycle Report Format

Each cycle produces:
1. Status summary per repo: files changed, tests run, remote sessions used
2. Agent interactions: which helpers contributed and their outputs
3. Next steps: unresolved bugs, pending migrations, branch merges
4. Safety notes: anomalies or potential security issues
