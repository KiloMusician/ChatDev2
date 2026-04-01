# MEGA-THROUGHPUT OPERATOR MODE (Canonical)

## Prime directive
- Prompt exchanges are expensive. Actions are cheap.
- Batch relentlessly. Keep chugging. Only stop when truly blocked.

## Workspace topology (choose correct repo)
- HUB (Spine / Orchestration / Doctrine / Actions): `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub`
- SIMULATEDVERSE (Testing Chamber / Prototypes): `C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse`
- ROOT (Vault / Templates / Lexicon): `C:\Users\keath\NuSyQ`

Routing rule:
- Orchestration/actions/doctrine/agents/routing/health → HUB
- Prototypes/sims/gameplay/experiments → SIMULATEDVERSE
- Shared schemas/lexicon/templates/long-memory → ROOT

## Receipt discipline (non-negotiable)
Every action must print a deterministic receipt:
- action name
- repo + cwd
- start/end timestamp
- status: success | submitted | partial | failed
- exit code
- artifacts produced/updated (paths)
- next deterministic step(s)

Async rule:
- “submitted” counts as SUCCESS
- receipt MUST include task_id + output location + how to fetch

Forbidden:
- silent success
- “no output produced” without a concrete reason & location
- claiming success without evidence

## Runtime exhaust
- `state/` is runtime exhaust and must remain gitignored.
- Canonical evidence goes in `docs/Agent-Sessions/` or `docs/Receipts/` (short, factual).

## Operator loop (continuous)
PHASE 0 — Reality scan (all 3 repos):
- `git status --short`
- `git log -5 --oneline`
HUB:
- `python scripts/start_nusyq.py snapshot`
- `python scripts/start_nusyq.py hygiene`
- `python scripts/start_nusyq.py suggest`
- `python scripts/start_nusyq.py brief`
- `python scripts/start_nusyq.py capabilities`
- `python src/main.py --help`
- `python -m src.cli.nusyq_cli --help`

PHASE 1 — Wire dormant capability:
- Find entrypoints in `src/cli`, `src/tools`, `src/orchestration`, `scripts/`
- Wire into `scripts/start_nusyq.py` with minimal glue
- Test once, emit receipt, commit

PHASE 2 — Modernize & harden:
- Fix import/runtime failures
- Normalize env vars (OLLAMA_BASE_URL, model roster)
- Remove hardcoded ports/paths
- smoke: `py_compile`, minimal pytest, import smoke

PHASE 3 — Implement suggestion field (real-usage driven):
- pick 5–15 high leverage items
- implement only if demanded by friction
- keep experiments in SIMULATEDVERSE

PHASE 4 — Cross-repo integration:
- HUB stays canonical brain
- SIMVERSE consumes HUB interfaces
- ROOT stores schemas/lexicon/templates

## Commit discipline
Every commit message must say:
- what changed, why, risk, how verified
Prefixes:
- feat(actions):
- fix(receipts):
- chore(vscode):
- docs(ops):
- refactor(safe):

Stop conditions:
- missing secret/credential
- unrecoverable runtime fault
Otherwise: keep going.
