# -NuSyQ_Ultimate_Repo
🗃️ The Self-Aware, Context-Persistent Repository Engine for LLM-Optimized Development

## 🚀 **Quick Start & New Tools**

- **[New Tools Quick Start](docs/NEW_TOOLS_QUICKSTART.md)** - Just installed: Haystack, Sourcegraph Cody, pre-commit hooks
- **[Tool Integration Roadmap](docs/TOOL_INTEGRATION_ROADMAP.md)** - 8-week plan for production-grade multi-agent system
- **[Modernization Audit Report](docs/MODERNIZATION_AUDIT_REPORT.md)** - Repository assessment + 4 quick wins delivered
- **[Contributing Guide](Guide_Contributing_AllUsers.md)** - How to work with this repository

## 🧪 **Core Pipelines & Commands**

### RosettaStone Pipeline (Normalize → Route → Evolve → Gate)
Run the end-to-end pipeline with automated quality gates:
```bash
python scripts/run_rosetta_pipeline.py --task "Your task description" --type CODE_GENERATION --complexity MODERATE
```
Output: persisted artifacts in `Reports/rosetta/` with proof verification.

See [TOOL_INTEGRATION_ROADMAP.md](docs/TOOL_INTEGRATION_ROADMAP.md#-phase-1-observability--quality-next-2-weeks) for full pipeline details.

## Ecosystem Role

`NuSyQ` is the Rosetta and proof-gate layer of the wider local stack.

- `CONCEPT / Keeper` handles machine pressure, modes, maintenance, and safe-start.
- `Dev-Mentor / TerminalDepths` handles interactive MCP/game/task workflows.
- `SimulatedVerse` handles simulation, patch-bay runtime, and ChatDev-adjacent UX.
- `NuSyQ-Hub` handles orchestration, healing, Nogic visualization, and GitNexus repo matrix.
- `NuSyQ` turns work into durable normalized artifacts through RosettaStone.

## Low-Token / Zero-Token Surfaces

Prefer these before broad LLM analysis:

- `python scripts/build_rosetta_bootstrap.py`
  - compiles the distributed Rosetta bundle into a compact boot capsule
- `state/boot/rosetta_bootstrap.json`
  - first-load anti-rediscovery capsule for agents, cockpits, and scripts
- `state/registry.json`
  - canonical machine-readable repo/service/bridge map
- `state/reports/control_plane_snapshot.json`
  - current control-plane truth refreshed by `NuSyQ-Hub`
- `python scripts/run_rosetta_pipeline.py ...`
  - deterministic normalization, routing, persistence, and proof-gate outputs
- `Reports/rosetta/`
  - reusable artifacts instead of re-querying the same context
- local backends such as `Ollama` and `LM Studio`
  - use local inference before external/token-costly paths when practical
- `NuSyQ-Hub` GitNexus
  - use `http://127.0.0.1:8000/api/gitnexus/matrix` for cross-repo git truth
- `NuSyQ-Hub` Nogic
  - use the bridge as the architecture visualization surface

## Recommended Use Order

Use the cheapest authoritative surface first, then escalate:

1. `CONCEPT / Keeper`
   - machine pressure, disk, Docker, WSL, and safe-start truth
2. `NuSyQ-Hub / GitNexus`
   - cross-repo git and branch truth
3. `NuSyQ-Hub / Nogic`
   - topology and architecture visualization
4. `NuSyQ / Rosetta boot capsule`
   - bootstrap, registry, snapshot, and deprecation contract
5. `NuSyQ / RosettaStone`
   - normalization, routing, persistence, and proof artifacts
6. local inference
   - `Ollama`, then `LM Studio` when the task needs a model backend

This avoids rediscovering machine state, repo state, and topology through
repeated broad analysis.

## Structured Artifact Authority

- `docs/ROSETTA_STONE.md`
  - hand-authored canonical contract
- `config/control_plane_manifest.json`
  - hand-authored machine-consumed manifest
- `state/registry.json`
  - generated canonical registry
- `state/reports/control_plane_snapshot.json`
  - generated ephemeral control-plane truth
- `state/deprecation_registry.json`
  - machine-visible deprecated path map
- `state/boot/rosetta_bootstrap.json`
  - generated compact boot capsule
- `state/boot/ROSETTA_BOOT.txt`
  - generated human attach twin
