# TerminalKeeper Workspace Audit

Date: 2026-03-20

## Current State

`mods/TerminalKeeper` already exists as the in-repo RimWorld mod scaffold for the DevMentor ecosystem.

The mod is not a blank stub. It already contains:

- RimWorld mod metadata in `About/About.xml`
- gameplay defs in `Defs/`
- local settings in `Config/TerminalKeeperSettings.xml`
- Harmony-based C# source in `Source/`
- compatibility placeholders in `Patches/`
- language keys in `Languages/English/Keyed/`

The mod assumes a local-first AI stack:

- Terminal Depths API at `http://localhost:5000`
- Ollama at `http://localhost:11434`
- LM Studio at `http://localhost:1234`

## In-Repo RimWorld Surfaces

### Mod

- `mods/TerminalKeeper/About/About.xml`
- `mods/TerminalKeeper/Config/TerminalKeeperSettings.xml`
- `mods/TerminalKeeper/Defs/`
- `mods/TerminalKeeper/Source/`

### Python bridge / ecosystem side

- `app/rimworld_bridge.py`
- `scripts/rimapi_bridge.py`
- `scripts/rimworld_entrypoint.sh`
- `Dockerfile.rimworld`
- `scripts/cascade.sh`

These files together already define the intended RimWorld integration path:

1. RimWorld mod sends colonist and command traffic over HTTP
2. Terminal Depths receives colony telemetry at `/api/nusyq/*`, `/api/agent/register`, and `/api/council/blueprint`
3. optional compatibility traffic can flow through the standalone RimAPI bridge on `:8765`
4. the Docker/VNC path can host a RimWorld runtime if game assets are available

## TerminalKeeper Source Layout

Current C# source layout:

- `Source/API`
- `Source/Buildings`
- `Source/Components`
- `Source/Core`
- `Source/Jobs`
- `Source/UI`
- `Source/Utils`

Key current responsibilities:

- `Source/Core/ModInit.cs`
  Loads settings and applies Harmony patches
- `Source/API/TerminalDepthsClient.cs`
  Sends HTTP requests to Terminal Depths and local LLM backends
- `Source/Components/LatticeAgentManager.cs`
  Maps colonists to persistent agent IDs and pushes telemetry
- `Source/Components/LatticeConversationSystem.cs`
  Reroutes some social interactions through the Lattice
- `Source/Core/HarmonyPatches.cs`
  Hooks pawn tick, gizmos, romance interaction routing, and job completion

## Defs Present

Current XML defs include:

- `Defs/ThingDefs/Buildings_TerminalKeeper.xml`
- `Defs/ThingDefs/ResearchProjects_TerminalKeeper.xml`
- `Defs/JobDefs/Jobs_TerminalKeeper.xml`
- `Defs/HediffDefs/Hediffs_TerminalKeeper.xml`
- `Defs/ThoughtDefs/Thoughts_TerminalKeeper.xml`
- `Defs/WorkTypeDefs/WorkTypes_TerminalKeeper.xml`

This confirms the mod already has a three-tier building concept:

- Tier 1: `TK_LatticeTerminal`
- Tier 2: `TK_LatticeConsole`
- Tier 3: `TK_LatticeNexus`

## Missing Standard Mod Folders

The following standard RimWorld mod folders were missing before this audit scaffold:

- `Assemblies/`
- `Textures/`

That means the repo had source and defs, but not yet the standard output/art folders in place.

## RimWorld Install Findings

From the live machine audit:

- workshop root exists at `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100`
- local `Documents\\My Games\\RimWorld\\Mods` folder does not currently exist
- active mod loadout is workshop-driven

No obvious active LLM/API mods were found in the active load list.
The strongest active integration targets are systems mods, not cloud-LLM mods:

- `vanillaexpanded.vanillasocialinteractionsexpanded`
- `vanillaexpanded.vpersonaweaponse`
- `vanillaexpanded.vpsycastse`
- `vanillaexpanded.vgeneticse`
- `smashphil.vehicleframework`
- `oskarpotocki.vanillavehiclesexpanded`
- `rimsenal.storyteller`

One inactive AI-themed workshop mod was confirmed:

- `Albion.AIUplift` (`AI Uplifting Assistant`)

It is XML-only and AI-themed, not an actual LLM/API mod.

This later changed during runtime inspection: the current active `ModsConfig.xml`
now includes a meaningful AI/chat stack:

- `cj.rimtalk`
- `brrainz.rimgpt`
- `yancy.rimchat`
- `cj.rimind`
- `com.antediluvian.compterm`
- multiple RimTalk extensions

That active-stack detail and the latest crash lead are captured in
`ACTIVE_MODS_AUDIT.md`.

## Immediate Risks

- `README.md` still says RimWorld `1.4 or 1.5`, but workshop findings and local config suggest the surrounding ecosystem has moved beyond that baseline.
- `Source/bin` and `Source/obj` are present in-tree, which is useful for local work but should not be treated as canonical mod content.
- `TerminalKeeper.csproj` copies into `Assemblies/`, but that folder was not present until this scaffold.
- `Textures/` is not present, so the current building defs reference art paths that may not yet exist.

## Recommended Next Slice

The next useful documentation/engineering slice is:

1. stabilise the in-repo mod directory as a canonical source tree
2. split current code into clearer runtime seams
3. add compatibility folders for active workshop mods
4. document exact integration targets for social, vehicle, genetics, psycasts, and storyteller systems

That is captured in `MOD_STRUCTURE_PLAN.md`.
