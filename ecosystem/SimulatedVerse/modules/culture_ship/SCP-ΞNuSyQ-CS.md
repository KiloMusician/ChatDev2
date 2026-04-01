# Item #: SCP-ΞNuSyQ-CS ("Culture-Class Infrastructure Vessel")

**Clearance**: Dev-Ops / Gameplay Leads  
**Object Class**: Thaumiel-Utility (Integrative)  
**Risk Profile**: Low (reversible), Elevated only when performing automated refactors; always gated by PR + tests.

## Special Containment / Integration Procedures

Integration, not isolation. SCP-ΞNuSyQ-CS mounts into the existing SimulatedVerse bootstrap; it does not replace existing systems.

**Token Governor**: config/token_policy.yml controls default "no/low token" mode. Budget overrides allowed per-task via justification.md.

**Change Safety**: All changes flow: proposal → dry-run → diff → tests → commit. Emergency rollback via scripts/rollback.mjs.

**Observability**: Ship emits structured logs to logs/ship.jsonl and human-readable summaries to reports/.

## Description

SCP-ΞNuSyQ-CS is a meta-module that equips the repository with:

**Planning & Cascade**: after every meaningful milestone, generate the next minimal-cost/max-impact plan (no/low token first).

**Knowledge Temples**:
1. **Temple of Knowledge** (10 floors): reference indices, FAQs, design docs, code maps.
2. **House of Leaves** (flexible architecture): polymorphic adapters, layered UIs (ASCII↔Tile↔WebGL), runtime graft points.
3. **Oldest House** (navigation & rituals): playbooks, emergency procedures, migrations, and "Special Circumstances" gates.

**Self-Healing**: detect duplicates, placeholders, broken imports, soft-locks, unbounded loops, and offer surgical fixes.

**Gameplay Couplers**: idler/core builder/tower defense/roguelike toggles, mobile/desktop responsive HUD, ASCII/Colorized streams.

## Infrastructure-First Principles (I-FP)

1. **Extend before create** (prefer integrating/extending existing modules).
2. **Local-first** (ripgrep, node/python, ollama) → cache → remote.
3. **Tiny PRs** (small diffs, green tests).
4. **Reversible by design** (migrations + rollback plans).
5. **Measure then decide** (profilers, timers, CPU/mem budgets).
6. **Narrative-aware** (UX, accessibility, respectful copy).

## Boot Narrative (start-up sequence)

- **Phase −1 (Primer)**: detect viewport; show minimal HUD; run micro-checks.
- **Phase 0 (Awakening)**: unlock Temple Floor 1 docs; run smoke tests; show base idler loop.
- **Phase 1 (Operational)**: enable toggles (idler/base/tower/rogue); begin quests from qbook.yml; cascade after each win.

## Ethics & Special Circumstances (SC)

**Ethic**: preserve life (game entities) and data integrity; intervene only when thresholds trip.

**SC Gates**: high-risk refactors, migration rewrites, or gameplay crisis events require "mediate → simulate → apply".

## Token-Minimization Policy

1. Local analyzers → 2) Cached embeddings / summaries → 3) Ollama (local LLM) → 4) Remote LLM with written justification + estimate.

All paid calls logged to reports/token-ledger.md with cost/benefit notes.