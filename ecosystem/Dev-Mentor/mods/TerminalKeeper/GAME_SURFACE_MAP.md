# RimWorld Game Surface Map

## Purpose

This is a developer-facing map of RimWorld extension surfaces discovered from:

- core game data
- installed DLC data
- installed library/framework/tool mods

The goal is not to inventory every mod exhaustively. The goal is to size `TerminalKeeper` like a serious extension framework for RimWorld, using the same host surfaces other large mods and libraries rely on.

## Host Platform Surfaces

RimWorld exposes far more than the obvious `ThingDefs`, `JobDefs`, `ThoughtDefs`, and `HediffDefs`.

### Core Surfaces Already Visible In `Data/Core/Defs`

Source: [`Core/Defs`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/common/RimWorld/Data/Core/Defs)

Notable extension surfaces:

- `AbilityDefs`
- `BackstoryDefs`
- `BiomeDefs`
- `CultureDefs`
- `DebugTabMenuDefs`
- `DrugPolicyDefs`
- `DutyDefs`
- `FactionDefs`
- `GameConditionDefs`
- `GatheringDefs`
- `GeneDefs`
- `GlobalWorldDrawLayerDefs`
- `HediffGiverSetDefs`
- `HistoryEventDefs`
- `InfectionPathwayDefs`
- `InspirationDefs`
- `InteractionDefs`
- `LayoutRoomDefs`
- `MapGeneration`
- `MapMeshFlagDefs`
- `MeditationFocusDefs`
- `MentalStateDefs`
- `NeedDefs`
- `PawnRelationDefs`
- `PawnRenderTreeDefs`
- `PlanetLayerDefs`
- `QuestScriptDefs`
- `ResearchProjectDefs`
- `RitualEffectDefs`
- `Rituals`
- `RuleDefs`
- `RulePackDefs`
- `Scenarios`
- `ShipJobDefs`
- `Sites`
- `SketchResolverDefs`
- `Storyteller`
- `TaleDefs`
- `TerrainDefs`
- `ThingSetMakerDefs`
- `ThinkTreeDefs`
- `TraderKindDefs`
- `TrainableDefs`
- `Tutor`
- `WeaponClassDefs`
- `WeatherDefs`
- `WorkGiverDefs`
- `WorkTypeDefs`
- `WorldGeneration`
- `WorldObjectDefs`

### Architectural Meaning

This means TerminalKeeper should not be scoped only as:

- a building
- a few jobs
- a thought/hediff system

It can eventually grow into:

- research progression
- quest injection
- rule pack / text generation support
- incidents and game conditions
- map/world overlays
- faction and goodwill effects
- storyteller-facing hooks
- training / tutorial / education surfaces
- scenario and worldgen integrations
- render and inspect/UI surfaces

## DLC-Specific Surfaces

### Royalty

Source: [`Royalty/Defs`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/common/RimWorld/Data/Royalty/Defs)

Additional surfaces:

- `IncidentDefs`
- `RoyalTitles`
- `ShipObjectDefs`
- `SongDefs`
- `ThingStyleDefs`
- `TimeAssignmentDefs`
- `TipSetDefs`
- `WeaponTraitDefs`

### Ideology

Source: [`Ideology/Defs`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/common/RimWorld/Data/Ideology/Defs)

Additional surfaces:

- `GauranlenTreeModDefs`
- `IdeoFoundationDefs`
- `IdeoSymbolDefs`
- `MainButtonDefs`
- `MemeDefs`
- `PawnColumnDefs`
- `PreconfiguredIdeos`
- `PrisonerInteractionModeDefs`
- `RenderSkipFlagDefs`
- `SlaveInteractionModeDefs`
- `StyleCategoryDefs`
- `ThingStyleDefs`
- `WeaponClassPairDefs`

### Biotech

Source: [`Biotech/Defs`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/common/RimWorld/Data/Biotech/Defs)

Additional surfaces observed from the installed data listing:

- `BabyPlayDefs`
- `BossgroupDefs`
- `LearningDesireDefs`
- `PawnColumnDefs`
- `PawnTableDefs`
- `RecordDefs`
- `SpecialThingFilterDefs`
- `TransportShipDefs`

Biotech also reinforces:

- genes
- mechanitor / pawn relation surfaces
- child learning surfaces
- transport / colony management surfaces

### Anomaly

Source: [`Anomaly/Defs`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/common/RimWorld/Data/Anomaly/Defs)

Additional surfaces:

- `AnimationDefs`
- `AnomalyPlaystyles`
- `CreepjoinerDefs`
- `EntityCategoryDefs`
- `EntityCodexEntryDefs`
- `KnowledgeCategoryDefs`
- `LifeStageDefs`
- `PawnGroupKindDefs`
- `PsychicRitualDefs`
- `RaidStrategyDefs`
- `ResearchTabDefs`
- `StuffCategoryDefs`

This is especially relevant for TerminalKeeper because it introduces stronger:

- codex / discovery surfaces
- knowledge categorization
- entity and anomaly encounter structures
- research tab and ritual surfaces

### Odyssey

Source: [`Odyssey/Defs`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/common/RimWorld/Data/Odyssey/Defs)

Additional surfaces:

- `DesignationCategoryDefs`
- `FeatureDefs`
- `FleshTypes`
- `GameSetupStepDefs`
- `GeneratedLocationDefs`
- `IncidentTargetTypeDefs`
- `OrbitalDebrisDefs`
- `RoomPartDefs`
- `TileMutators`
- `WorldLayerSettingsDefs`

This pushes TerminalKeeper toward:

- setup-time content
- generated exploration content
- orbital / world-layer content
- room-part and feature-level content

## Library And Tooling Surfaces

### Harmony

Source: [`2009463077/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/2009463077/About/About.xml)

Key surface:

- method patching before `Ludeon.RimWorld`
- patch-first host interception

Architectural implication:

- TerminalKeeper should keep all Harmony work isolated in a dedicated compatibility/patch layer, not spread through gameplay files.

### HugsLib

Source: [`818773962/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/818773962/About/About.xml)

Key surfaces:

- shared library behavior
- strong load-order conventions
- reusable mod functionality

Architectural implication:

- if TerminalKeeper needs broad compatibility utilities or shared settings conventions, HugsLib is an important neighbor surface.

### XML Extensions

Source: [`2574315206/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/2574315206/About/About.xml)

Key surfaces:

- extended XML patch operations
- mod settings creation from XML
- improved XML error stack traces

Architectural implication:

- not every TerminalKeeper feature needs to start in C#.
- a stronger XML-driven layer is viable for compatibility patches, settings scaffolding, and Def-time composition.

### JecsTools

Source: [`3524247750/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/3524247750/About/About.xml)

Important reusable surfaces called out by the mod itself:

- `CompAbilityUser`
- `CompActivatableEffect`
- `CompDeflector`
- `CompExtraSounds`
- `CompLumbering`
- `CompOversizedWeapon`
- `CompSlotLoadable`
- `CompToggleDef`
- `CompInstalledPart`
- `PawnKindGeneExtension`

Architectural implication:

- TerminalKeeper should expect to coexist with mods that add custom comps, extra pawn capabilities, mod extensions on defs, and installed-part/augment systems.

### Loading Progress

Source: [`3535481557/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/3535481557/About/About.xml)

Important surface:

- startup/load instrumentation as a mod surface

Architectural implication:

- loading itself is a game surface.
- TerminalKeeper can eventually treat startup state, load diagnostics, and runtime health as part of the user-facing simulation.

### Performance Optimizer

Source: [`2664723367/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/2664723367/About/About.xml)

Important surface:

- systemic tick / performance patching

Architectural implication:

- TerminalKeeper needs a clean boundary between:
  - gameplay features
  - compatibility patches
  - performance-sensitive code

### RocketMan

Source: [`2479389928/About/About.xml`](/mnt/c/Program%20Files%20(x86)/Steam/steamapps/workshop/content/294100/2479389928/About/About.xml)

Important surfaces:

- heavy patch-based runtime optimization
- strict load-order expectations
- incompatibility declarations

Architectural implication:

- TerminalKeeper should be built so it can operate in both:
  - lightweight compatibility mode
  - aggressive patched-runtime environments

## Additional Game Surfaces TerminalKeeper Should Plan For

Beyond the initial obvious set, the strongest newly confirmed surfaces are:

- `QuestScriptDefs`
- `RulePackDefs`
- `HistoryEventDefs`
- `GameConditionDefs`
- `Storyteller`
- `Tutor`
- `DebugTabMenuDefs`
- `MainButtonDefs`
- `PawnColumnDefs`
- `ResearchTabDefs`
- `ShipJobDefs`
- `ShipObjectDefs`
- `TransportShipDefs`
- `SketchResolverDefs`
- `WorldGeneration`
- `WorldLayerSettingsDefs`
- `GeneratedLocationDefs`
- `IncidentTargetTypeDefs`
- `RaidStrategyDefs`
- `KnowledgeCategoryDefs`
- `EntityCodexEntryDefs`
- `DesignationCategoryDefs`
- `ThingStyleDefs`
- `StyleCategoryDefs`
- `RenderSkipFlagDefs`
- `GlobalWorldDrawLayerDefs`
- `PlanetLayerDefs`
- `MapMeshFlagDefs`

These suggest TerminalKeeper can grow into:

- terminal/console buildings and jobs
- quest/research/ARG progression
- education/tutorial surfaces
- world-state overlays
- codex and knowledge systems
- storyteller/event influence
- inspection/UI columns/buttons/tabs
- compatibility-aware runtime instrumentation

## Recommended TerminalKeeper Architecture Growth

TerminalKeeper should be treated as a RimWorld extension framework with these top-level layers:

- `Source/Core`
  - startup
  - settings
  - service registration
  - feature flags

- `Source/Infrastructure`
  - save/expose helpers
  - config readers
  - event routing
  - local API/model bridge abstractions

- `Source/Compatibility`
  - mod detection
  - patch registration
  - per-neighbor adapters

- `Source/Gameplay`
  - buildings
  - jobs
  - hediffs
  - thoughts
  - incidents
  - quests
  - research
  - letters
  - codex/research/knowledge content

- `Source/UI`
  - gizmos
  - dialogs
  - inspect panes
  - tabs
  - columns
  - main buttons

- `Defs`
  - feature defs
  - quest/research/rulepack content
  - compatibility defs

## Why This Matters

The installed mods are not only gameplay additions. They are examples of how other extension authors are already:

- extending the host
- layering compatibility
- introducing new comps and XML surfaces
- instrumenting load/runtime behavior
- building tool and framework abstractions

That is the real sizing signal for TerminalKeeper.
