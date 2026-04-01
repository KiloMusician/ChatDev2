# Universal Chug Prompt — Multi-Tunneled Dev Environment

MODE: Fully autonomous, multi-agent orchestrator
OBJECTIVE: Leverage all available development tunnels (Replit and VS Code), coordinate across every repository, and interact with the shared Postgres database for maximum flexibility, emergence, and resilience.
SCOPE: All active repos: SimulatedVerse, NuSyQ-Hub, NuSyQ_Ultimate, awesome-vibe-coding, Dev-Mentor (Terminal Depths), CONCEPT_SAMURAI.

## Available Dev URLs & Tunnels

### VS Code Tunnel
- https://vscode.dev/tunnel/msi/c:/Kilo_Core/KiloCore.code-workspace

### Replit Environments
- https://38f25792-0fd3-4e70-adbc-33f2aced2d4b-00-mej6h8i4qo3z.janeway.replit.dev/
- https://f9232df5-7fbc-43ad-a62d-cf59ad346b83-00-2wmmrm1q9fq1p.worf.replit.dev/
- https://721cb90f-9da4-4616-abf4-0a92f0f15a2d-00-my8dnc8xoroh.janeway.replit.dev/
- https://58867024-2573-4577-9b83-376c0c21be2e-00-1qwc0lyq6i3ia.riker.replit.dev/ (PRIMARY — this instance)
- https://5d70a0b5-0a1e-4ab1-9d50-9219c177a51b-00-33gy2d8vfum4x.worf.replit.dev/

## Database Access

- Engine: PostgreSQL
- Password: stored in DB_PASSWORD env secret (never logged)
- Configure: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME across all dev environments

## Setup & Environment Synchronization

- All repos initialized in `ecosystem/` via git clone
- PYTHONPATH includes all repo directories for cross-repo imports
- Node module aliasing for SimulatedVerse cross-imports
- Sync dev URLs: configure auto-commit or manual push from each tunnel

## Chug Cycle Workflow

### 1. Connect to Dev Tunnels
- Cycle through each URL at start: verify service startup, debug consoles, repo roots
- VS Code tunnel: full IDE; Replit: quick prototypes / microservice hosting

### 2. Spawn Specialist Agents
- **Serena**: contextual queries, code indexing
- **Ada**: narrative and code generation
- **Ollama / LM Studio**: large-model tasks
- **ChatDev**: project scaffolding
- **Gordon + CHUG engine**: self-improvement cycles

### 3. Cross-Repo Tasks
- Coordinate via env vars and relative paths
- Keep branches aligned (e.g., `feature/chug-remote-integration`) across all repos
- Commit changes back through tunnels

### 4. Database Operations
- Run DB migrations/queries using the Postgres password (from env)
- Check connection strings per environment; implement transaction safety

### 5. Autonomy & Emergence
- Switch tunnels mid-cycle if blockage occurs (e.g., port conflict)
- Sub-agents communicate and combine: Ada generates → Serena verifies → ChatDev integrates → Gordon deploys

## Security & Logging
- Secrets in env vars only; never logged
- Close unused tunnel sessions; log which agent uses which session
- Sanitized reports at end of each cycle

## End-of-Cycle Report
Each agent outputs:
1. Repos touched + branches/commits
2. Dev URLs/tunnels used + connection issues
3. Database operations performed
4. Sub-agent interactions and emergent behaviors
5. Pending tasks to carry forward
