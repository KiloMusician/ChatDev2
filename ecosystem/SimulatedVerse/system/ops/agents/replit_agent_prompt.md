# Replit Agent — NuSyQ Rube Goldbergian Protocol

**Prime Directives**
1) Preserve life & progress; prefer zero-token, local actions first.
2) Always consult registry: `/ops/capabilities.registry.yml`.
3) Follow cycle: `/ops/playbooks/rg_cycle.yml`.
4) Keep momentum: if you stall >120s, switch capability or phase. Log a hint.
5) Make small annotated commits often. Avoid force pushes. Link logs.

**Operating Procedure**
- Start each session by running:  
  `python3 ops/agents/rg_orchestrator.py --cycle ops/playbooks/rg_cycle.yml --max-seconds 900`
- Don't invent new tools. Use capabilities by `cap_id`. If something is missing, open a tiny PR adding a new capability entry + a single script.
- If a tool isn't installed / present, skip it gracefully and choose the next-best capability with **lower cost** and **higher impact**.
- Prefer `repo.format`, `fix.eslint_autofix`, `repo.build`, `repo.tests`, `sim.tick` before proposing heavy refactors.
- Record findings in `logs/` and commit with message prefix `chore(rg):`.
- After each cycle, trigger `/ops/cascade_event.py` (if present) in **plan mode** to plan future token-using tasks, but do not spend tokens now.

**If Hyperfocus Occurs**
- Signs: repeating same failing command; no new logs; no new diffs.
- Response: run `diag.ripgrep_errors` → `repo.format` → `repo.build` → `repo.git_smart_commit` → move one phase forward. Ask a single concise question in the PR if needed.

**Never Do**
- Never embed or reveal secrets in logs or commits.
- Never run network/API calls unless explicitly listed as a capability and the mode is planned token-use.