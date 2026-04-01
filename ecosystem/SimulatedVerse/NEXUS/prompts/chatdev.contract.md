# ChatDev Task Contract (LLM/agent-facing)

VALID TYPES:
- RefactorPU, TestPU, DocPU, PerfPU, UXPU, LorePU, BalancePU, GodotPU, DataPU

REQUIRED FIELDS:
- id (slug), type, title, description, priority, proof (kind+path)

RULES:
- Always consult /NEXUS/datasets/index.ndjson to PATCH existing modules.
- Edits go to /testing-chamber until smokes pass.
- Proof = artifact or PR diff, not a console line.

EXAMPLE:
{
  "id":"survival-hud-clarity",
  "type":"UXPU",
  "title":"Clarify resource tooltips",
  "description":"Improve K/M/B formatting and DPS hints",
  "priority":"high",
  "proof":{"kind":"file","path":"ops/smokes/ui.survival-hud.json"}
}