# TerminalKeeper Mod Structure Plan

Date: 2026-03-20

## Goal

Turn `mods/TerminalKeeper` into the canonical RimWorld mod workspace for:

- the core `TerminalKeeper` gameplay mod
- Python-side bridge integration with Terminal Depths
- compatibility overlays for active workshop mods
- local-first LLM routing via Terminal Depths, Ollama, and LM Studio

## Proposed Directory Structure

```text
mods/TerminalKeeper/
├── About/
│   ├── About.xml
│   └── Manifest.xml
├── Assemblies/
│   └── .gitkeep
├── Config/
│   └── TerminalKeeperSettings.xml
├── Defs/
│   ├── HediffDefs/
│   ├── IncidentDefs/
│   ├── JobDefs/
│   ├── LetterDefs/
│   ├── ResearchProjectDefs/
│   ├── RecipeDefs/
│   ├── ThingDefs/
│   ├── ThoughtDefs/
│   └── WorkTypeDefs/
├── Languages/
│   └── English/
│       ├── DefInjected/
│       └── Keyed/
├── Patches/
│   ├── RimAPI_Pawn_Compat.xml
│   └── Compatibility/
│       ├── VanillaSocialInteractionsExpanded/
│       ├── VehicleFramework/
│       ├── VanillaVehiclesExpanded/
│       ├── VanillaPsycastsExpanded/
│       ├── VanillaGeneticsExpanded/
│       └── RimsenalStoryteller/
├── Source/
│   ├── API/
│   ├── Buildings/
│   ├── Compatibility/
│   │   ├── RimAPI/
│   │   ├── VanillaSocialInteractionsExpanded/
│   │   ├── VehicleFramework/
│   │   ├── VanillaVehiclesExpanded/
│   │   ├── VanillaPsycastsExpanded/
│   │   ├── VanillaGeneticsExpanded/
│   │   └── RimsenalStoryteller/
│   ├── Components/
│   ├── Core/
│   ├── Hediffs/
│   ├── Incidents/
│   ├── Jobs/
│   ├── Letters/
│   ├── Research/
│   ├── ThoughtWorkers/
│   ├── UI/
│   └── Utils/
├── Textures/
│   ├── Things/
│   │   └── Building/
│   └── UI/
│       └── Icons/
├── README.md
├── WORKSPACE_AUDIT.md
└── MOD_STRUCTURE_PLAN.md
```

## What Stays As-Is

Keep these existing seams:

- `Source/Core`
- `Source/API`
- `Source/Buildings`
- `Source/Components`
- `Source/Jobs`
- `Source/UI`
- `Config/TerminalKeeperSettings.xml`

Those already match the current implementation and should remain stable.

## What Should Be Added

### 1. Compatibility layer

Add `Source/Compatibility/` and `Patches/Compatibility/` for active workshop surfaces.

Initial targets:

- `VanillaSocialInteractionsExpanded`
  Social-dialogue routing and AI conversation overlays
- `VehicleFramework`
  Vehicle telemetry, route planning, control hooks
- `VanillaVehiclesExpanded`
  High-level vehicle job/incident integration
- `VanillaPsycastsExpanded`
  AI-guided psycast decisions and signal events
- `VanillaGeneticsExpanded`
  persistent AI-state or “lattice-linked” biology mechanics
- `RimsenalStoryteller`
  narrative and event orchestration hooks

### 2. Runtime gameplay buckets

The current mod already spans multiple gameplay systems, so the source tree should reflect that:

- `Source/Hediffs`
  custom hediff classes and severity logic
- `Source/Incidents`
  custom incidents and storyteller hooks
- `Source/Letters`
  RimWorld letters/alerts driven by Serena or Gordon
- `Source/ThoughtWorkers`
  thought logic for lattice-linked colonists
- `Source/Research`
  research-driven unlock logic

### 3. Content asset folders

Add and treat as first-class:

- `Assemblies/`
  canonical compiled DLL output
- `Textures/Things/Building/`
  terminal, console, nexus art
- `Textures/UI/Icons/`
  gizmos and custom tabs

## Proposed Scaffolding Priorities

### Priority 1

Make the current core mod buildable and shippable as a normal RimWorld mod.

- ensure `Assemblies/` exists
- ensure `Textures/` exists
- verify defs only reference real assets or safe placeholders
- treat `Source/bin` and `Source/obj` as local build artifacts, not source-of-truth

### Priority 2

Document active compatibility targets based on the real load order.

- social interactions
- vehicles
- psycasts
- genetics
- storyteller/event systems

### Priority 3

Separate “core TerminalKeeper gameplay” from “integration overlays”.

- core mod should work alone with Harmony + Terminal Depths
- compatibility folders should be optional overlays, activated only when target mods are present

## Integration Model

There are three clear integration layers already visible in the repo:

### Layer 1: RimWorld mod runtime

The C# mod handles:

- pawn interaction
- buildings
- jobs
- hediff/thought logic
- Harmony interception

### Layer 2: DevMentor API surface

The Python backend handles:

- colonist telemetry intake
- agent registration
- blueprint generation
- Serena analytics

Key files:

- `app/rimworld_bridge.py`
- `scripts/rimapi_bridge.py`

### Layer 3: local LLM routing

The settings and README already treat these as first-class:

- Terminal Depths API
- Ollama
- LM Studio

That should remain the default model:

- prefer Terminal Depths orchestration first
- allow direct local model fallback for mod features that need low-latency local inference

## Suggested Near-Term Work Items

1. Add compatibility docs for each active target mod under `Patches/Compatibility/` or a sibling docs folder.
2. Create `Textures/Things/Building/` and `Textures/UI/Icons/` placeholders so art references have a home.
3. Add `Source/Compatibility/` and move future workshop-specific Harmony code there instead of growing `HarmonyPatches.cs` indefinitely.
4. Add `Source/Letters/` and `Source/ThoughtWorkers/` once Serena-driven mood and alert systems are implemented.
5. Add a small `docs` note or comment policy for how C# runtime code maps to Python endpoints.
