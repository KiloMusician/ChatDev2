# Terminal Keeper: Lattice Colonists

**RimWorld mod** that wires your colony into the [Terminal Depths](https://github.com/KiloMusician/Dev-Mentor) AI ecosystem.

---

## What it does

| Feature | Description |
|---|---|
| **Lattice Terminal** (Tier 1) | Colonists upload daily logs and receive task assignments from Gordon |
| **Lattice Console** (Tier 2) | AI Council voting, blueprint download, Serena analytics |
| **Lattice Nexus** (Tier 3) | Colony-wide telemetry broadcast, Lattice-linked aura, NuSyQ-Hub integration |
| **Colonist Agents** | Each colonist auto-registers as a persistent Terminal Depths agent |
| **Conversation intercepts** | Lattice-linked colonists route social interactions through the AI |
| **Lattice-linked hediff** | Passive buff (work speed, social, research) when near a Nexus |
| **CHUG integration** | Every terminal session feeds XP back to the DevMentor improvement engine |

---

## Requirements

- RimWorld 1.4 or 1.5
- **Harmony** (Steam Workshop ID 2009463077)
- Terminal Depths server (the DevMentor Console) running at `http://localhost:5000`

### Optional
- Ollama running at `http://localhost:11434` for direct LLM fallback
- LM Studio at `http://localhost:1234`

---

## Installation

### From source (this repo)
1. Open `mods/TerminalKeeper/Source/TerminalKeeper.csproj` in Visual Studio or Rider
2. Set `RimWorldDir` to your RimWorld install path
3. Build — the DLL is copied to `mods/TerminalKeeper/Assemblies/` automatically
4. Copy `mods/TerminalKeeper/` to `<RimWorld>/Mods/`
5. Enable in the mod manager

### Running the Terminal Depths server
```bash
# From the DevMentor repo root:
python -m cli.devmentor serve --host 0.0.0.0 --port 5000

# Or via Docker:
docker-compose up devmentor
```

---

## Configuration

Edit `mods/TerminalKeeper/Config/TerminalKeeperSettings.xml`:

```xml
<ApiEndpoint>http://localhost:5000</ApiEndpoint>
<LLMBackend>terminal_depths</LLMBackend>
<EnableAICouncil>true</EnableAICouncil>
<EnableBlueprintGeneration>true</EnableBlueprintGeneration>
```

---

## Architecture

```
RimWorld (C#)
  └── Terminal Keeper mod
        ├── Harmony patches (Pawn.Tick, GetGizmos, JobTracker)
        ├── Building_LatticeTerminal / LatticeNexus
        ├── LatticeAgentManager (WorldComponent, colonist↔agentId map)
        ├── LatticeConversationSystem (AI-routed social interactions)
        ├── TerminalDepthsClient (async HTTP → REST API)
        └── Dialog_TerminalAccess (in-game UI)
              │
              │  HTTP/JSON
              ▼
Terminal Depths API (Python / FastAPI)
  ├── /api/game/command        — execute game commands as agent
  ├── /api/agent/register      — persistent agent accounts
  ├── /api/nusyq/colonist_state — telemetry → NuSyQ-Hub
  ├── /api/council/blueprint   — AI Council blueprint generation
  └── /api/serena/colony_analytics — Serena drift/analytics
```

---

## Research tree

```
Lattice Integration (600 pts)
  └── Advanced Lattice Protocols (1200 pts)
        └── Lattice Nexus (2400 pts)
```

---

## Roadmap

- [ ] Blueprint → actual RimWorld construction planner integration
- [ ] Gordon autonomous colonist controller (opt-in per pawn)
- [ ] Faction rep sync: Terminal Depths faction standings → RimWorld faction relations
- [ ] NPC Terminal Depths agents as RimWorld visitors / traders
- [ ] Colonist "dream" thoughts driven by Terminal Depths narrative engine
- [ ] Serena drift alerts displayed as RimWorld letters
