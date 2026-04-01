# CLAUDE.md — Claude Code Context for DevMentor / Terminal Depths

> You are working in **DevMentor**, a VS Code-native mentorship repository
> that contains a cyberpunk terminal RPG (**Terminal Depths**) and a RimWorld mod
> (**Terminal Keeper: Lattice Colonists**). Read this file before making any changes.

---

## First Actions (run these first)

```bash
# 1. Verify the system is healthy
curl -s http://localhost:7337/api/health | python3 -m json.tool

# 2. Check current validation state
python3 scripts/validate_all.py 2>/dev/null || python3 -m cli.devmentor doctor

# 3. See the engineering backlog
cat NEXT_ACTIONS.md | head -80

# 4. Understand the architecture
cat SYSTEM_ARCHITECTURE.md
```

---

## System Identity

Three systems share this repo:

| System | Role | Port |
|--------|------|------|
| **DevMentor** | Outer shell: VS Code mentor, CHUG, Serena, Gordon, ML | 7337 |
| **Terminal Depths** | Inner game: 534 handlers, NPCs, ARG, consciousness | 7337 |
| **Terminal Keeper** | RimWorld mod bridge: `mods/TerminalKeeper/` C# only | — |

Port rule: **5000 = Replit only. 7337 = Docker/VS Code/local only.**

---

## Critical Architecture Rules

1. **`app/game_engine/commands.py` is 37,000+ lines** — surgical edits only.
   Always check with `python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('OK')"` after any edit.

2. **Output primitive**: `_line(text, cls)` — NOT `_styled()`, NOT `print()`.

3. **Session ID**: Use `str(int(gs.run_start_time))` — NOT `gs.session_id` (doesn't exist).

4. **Port auto-detection — use the shim, not inline code**:
   ```python
   from core.port_resolver import TD_BASE, td_url, svc_url
   # TD_BASE → "http://localhost:5000" on Replit, "http://localhost:7337" elsewhere
   # NEVER write os.environ.get("TERMINAL_DEPTHS_URL", "http://localhost:5000") inline.
   # core/port_resolver.py is the canonical resolver. See SYSTEM_ARCHITECTURE.md.
   ```
   Override with env var: `TERMINAL_DEPTHS_URL=http://localhost:7337`

5. **Serena policy** (`agents/serena/policy.yaml`): Trust level is `standard`.
   L3 actions (create_file, change_logic, etc.) require human approval.
   L4 actions (delete_database, force_push, execute_shell_command) are NEVER done.

6. **CHUG acronym**: "Continuous Habitat Upgrade Generator" (not "Continuous Habit...")

---

## Key Files

| File | What |
|------|------|
| `TORCH.md` | 5-minute complete onboarding |
| `NEXT_ACTIONS.md` | Engineering backlog (prioritized) |
| `SYSTEM_ARCHITECTURE.md` | Three-system identity clarity |
| `AGENTS.md` | Universal agent entry point |
| `app/game_engine/commands.py` | All 534 game handlers |
| `app/backend/main.py` | FastAPI routes and startup |
| `agents/serena/policy.yaml` | Trust level matrix |
| `mcp/server.py` | MCP server (44 tools, Claude-accessible) |
| `state/serena_memory.db` | Serena Memory Palace (45MB) |
| `config/port_map.json` | Port registry |

---

## MCP Tools Available to You

You have access to these tools via the MCP server (`mcp/server.py`):

| Tool | What |
|------|------|
| **Files** | |
| `read_file` | Read any file in the repo |
| `write_file` | Write a file (triggers L2/L3 Serena review) |
| `list_dir` | List directory contents |
| `grep_files` | Search for patterns across files |
| **Game** | |
| `game_command` | Send a command to Terminal Depths game engine |
| `game_state` | Get current game state (player XP, location, inventory) |
| `run_game_batch` | Run multiple commands in one call |
| `run_exploit` | Trigger a scripted exploit chain |
| `list_commands` | Get all 534 Terminal Depths commands |
| `get_man_page` | Get the man page for a specific command |
| `search_commands` | Fuzzy-search command names/descriptions |
| **Narrative / ARG** | |
| `get_story_progress` | Current story beat / ARG state |
| `get_achievements` | Player achievements unlocked |
| `get_xp_breakdown` | XP by skill category |
| `award_xp` | Grant XP to a session |
| `get_lore_file` | Read a lore file from the VFS |
| `get_faction_status` | All 10 faction trust scores |
| `get_agent_states` | All 63 agent personalities + status |
| **Search** | |
| `semantic_search` | TF-IDF search over game knowledge base |
| `serena_search` | Serena MemoryPalace — 9446 symbols, 432 files |
| `lattice_search` | Lattice knowledge graph query |
| `nusyq_search` | NuSyQ-Hub 14,943-file SmartSearch index |
| `cocoindex_search` | CocoIndex semantic search (new) |
| `embed_search` | Pure vector search via nomic-embed-text |
| **Agents / Lattice** | |
| `agent_command` | Play as claude-prime (no auth required) |
| `register_agent` | Register as a named agent in the Lattice |
| `get_capabilities` | List all agent capabilities |
| `get_agent_leaderboard` | Agent XP/contribution rankings |
| `agent_bus_publish` | Publish to the T2 agent bus |
| `agent_bus_status` | T2 bus health + recent messages |
| **ML / RL** | |
| `llm_generate` | Direct LLM generation (Ollama / fallback) |
| `ollama_query` | Query Ollama directly (qwen2.5-coder:14b) |
| `list_models` | All registered models in model_registry.db |
| `rl_status` | PPO checkpoint status, policy shape |
| **Ops / Infra** | |
| `system_status` | Full system health check |
| `git_push` | Push commits (requires GITHUB_TOKEN) |
| `chronicle` | Read the project chronicle |
| `memory_stats` | Agent memory stats (24-hour window) |
| `memory_add_task` | Add a task to the agent queue |
| `chug_status` | CHUG 7-phase engine status |
| `swarm_status` | Swarm DP ledger snapshot |
| `swarm_tasks` | Pending swarm task queue |
| `get_backlog` | Engineering backlog from NEXT_ACTIONS.md |
| `nusyq_ops` | NuSyQ index health + rebuild ops |
| `cocoindex_ops` | CocoIndex build/rebuild ops |
| `serena_drift` | Check Serena ARCH_BOUNDARY drift |

---

## Database Schema (10 SQLite DBs)

| Database | Size | Key Tables |
|----------|------|------------|
| `state/serena_memory.db` | 45MB | code_index, observations, conversations, walks, **session_graph** |
| `state/embeddings.db` | 15MB | embedding_cache |
| `state/feature_store.db` | 2.5MB | feature_events, player_profiles, session_summary |
| `state/agents.db` | 48KB | agents, agent_memory |
| `state/economy.db` | 32KB | wallets, transactions, research, ledger |
| `state/swarm_ledger.db` | 32KB | ledger, swarm_meta |
| `state/lattice.db` | 188KB | nodes, edges, events, lattice_nodes, lattice_edges |
| `state/gordon_memory.db` | 28KB | memories, strategies, npc_interactions, gordon_log |
| `state/model_registry.db` | 20KB | models, inference_log |
| `.devmentor/agent_memory.db` | 980KB | interactions, errors, learnings, tasks, llm_cache |

---

## Current State

- **Handlers**: 534 (last added: `_cmd_todo`)
- **Validation**: PASS=26 WARN=0 FAIL=0 (clean as of 2026-03-26)
- **Serena drift**: 4 ARCH_BOUNDARY warnings (llm_client in game engine — intentional, in policy.yaml)
- **Consciousness system**: 5 layers, ~0% active. Hooks added for L1 (loop_reset), L5 (fifth, zeta). Project Emergence trigger active.
- **PPO**: COMPLETE — `PPOAgent` wrapper + `scenario_ppo()`; 0 episodes trained; numpy installed
- **ARG**: 7 PRIMUS fragments all at 0/7, temple floors 1-10 documented
- **MCP**: 44 tools in mcp/server.py (was 16 — fully expanded)

---

## What NOT to Do

- Do NOT use port 5000 in Docker or VS Code environments
- Do NOT use `gs.session_id` — use `str(int(gs.run_start_time))`
- Do NOT use `_styled()` — use `_line(text, cls)`
- Do NOT edit `commands.py` without an AST check afterward
- Do NOT run Serena L4 actions (delete_database, force_push, execute_shell_command)
- Do NOT modify `.gitignore` (Serena L4 deny)
- Do NOT change secrets files directly — use environment-secrets tooling

---

## Quick Commands

```bash
# Start the server (VS Code / Docker)
python -m cli.devmentor serve --host 0.0.0.0 --port 7337

# Run a game command
curl -s -X POST http://localhost:7337/api/game/command \
  -H "Content-Type: application/json" \
  -d '{"command": "status"}' | python3 -m json.tool

# Check Serena alignment
python3 agents/serena/check_alignment.py 2>/dev/null || python3 -c "
import sys; sys.path.insert(0,'.')
from agents.serena.serena import Serena
s = Serena(); result = s.align()
print(result)
"

# AST-check commands.py (run after any edit)
python3 -c "import ast; ast.parse(open('app/game_engine/commands.py').read()); print('AST OK')"

# See full command list
curl -s http://localhost:7337/api/game/commands | python3 -m json.tool | head -40
```
