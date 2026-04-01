# NuSyQ-Hub — Routing Rules

## Tool/Agent Responsibilities
- **Copilot (operator)**
  - Executes explicit plans; edits limited to stated paths.
  - Shows diffs, runs checks, commits with Conventional Commit style.
  - Avoids architectural decisions unless pre-approved.
- **Claude (architect)**
  - Produces plans, decisions, summaries; must cite concrete paths.
  - Avoids direct file editing; hands off to Copilot for execution.
- **ChatDev / Ollama (ideation)**
  - Used for design space exploration or low-cost drafts.
  - Outputs are reviewed and ported manually; not merged blindly.
- **Human**
  - Owns ambiguity resolution, risk calls, secret handling, and approvals for force operations/history rewrites.

## Handoff Protocol
1) **Intent**: state goal, repo, path scope, and acceptance criteria.
2) **Plan**: architect (Claude) produces steps + verification commands.
3) **Execute**: operator (Copilot) makes scoped edits, runs checks, prepares commits.
4) **Verify**: run lint/tests/smoke as specified; capture evidence.
5) **Commit**: Conventional Commit message; note verification & risk.
6) **Push/PR**: respect branch protections; avoid force unless explicitly approved.

## Scope & Safety Rules
- Stay within declared paths; avoid touching secrets (`config/secrets.*`, `.env*`, `settings.local.*`).
- No additions to new top-level directories; use existing structure (`src/`, `docs/`, `tests/`, etc.).
- Logs/runtime artifacts stay untracked; if a summary is needed, move it to `docs/`.
- Before any history rewrite or force push: human approval required.

## Verification Defaults
- Lint: `python -m ruff .`
- Format check: `python -m black --check .`
- Tests: `python run_tests.py` (or `pytest -q` if scoped)
- Import sanity: `python -m compileall src`

## Commit Boundaries
- Prefer 1–3 commits per task: (a) config/CI changes, (b) code changes, (c) docs if large.
- Keep runtime clean: `git status -sb` before/after; stash or drop unrelated changes.

## Documentation Expectations
- Any new decision/workflow: add to `docs/` (or existing doctrine) with paths and commands.
- Any ambiguity encountered: record assumptions + follow-ups in the PR/commit message.
