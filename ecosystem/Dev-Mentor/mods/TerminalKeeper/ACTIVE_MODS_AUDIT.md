# Active RimWorld AI/Chat Mod Audit

Date: 2026-03-20

## Current Active AI/Chat-Oriented Mods

These package IDs are active in the current RimWorld load order from:

- `C:\Users\keath\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Config\ModsConfig.xml`

## Confirmed Active Mods

### Core AI / chat surfaces

- `cj.rimtalk`
  - name: `RimTalk`
  - workshop folder: `3551203752`
  - path: `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3551203752`
- `brrainz.rimgpt`
  - name: `RimGPT`
  - workshop folder: `2960127000`
  - path: `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2960127000`
- `yancy.rimchat`
  - name: `RimChat`
  - workshop folder: `3683001105`
  - path: `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3683001105`
- `cj.rimind`
  - name: `RiMind`
  - workshop folder: `3562373405`
  - path: `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3562373405`
- `com.antediluvian.compterm`
  - name: `Rimnet Terminal`
  - workshop folder: `3592295301`
  - path: `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3592295301`
- `albion.aiuplift`
  - name: `AI Uplifting Assistant`
  - workshop folder: `1227757287`
  - path: `C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\1227757287`

### RimTalk extension stack

- `ruaji.rimtalkpromptenhance`
  - name: `RimTalk - Enhanced Prompt and Announcement`
  - workshop folder: `3628795263`
- `rimtalk.quests`
  - name: `RimTalk - Quests`
  - workshop folder: `3642675329`
- `qm.rimtalk.realitysync`
  - name: `RimTalk - Reality Sync`
  - workshop folder: `3685080119`
- `rp.rimtalk.personadirector`
  - name: `RimTalk: Persona Director`
  - workshop folder: `3619548407`
- `longyuetu.rimtalk.logtofile`
  - name: `RimTalk Log To File`
  - workshop folder: `3647398629`

Additional active RimTalk-related package IDs seen in config:

- `zruic.expand.action`
- `zruic.expand.dialogue`
- `cj.rimtalk.literature`
- `cj.rimtalk.expandmemory`
- `cj.rimtalk.expandmemorybeta`
- `zruic.expand.thoughts`
- `zruic.expand.relation`
- `wuren.rimtalkcontextupgrade`
- `neachi.rimtalkdialoguepatch`
- `saltgin.rimtalkeventmemory`
- `hh.rimtalk.diary`
- `oceantest6.rimtalk.promptcleaner`

## Current Crash Finding

The most concrete startup exception currently visible in `Player.log` is:

```text
Could not execute post-long-event action. Exception:
System.Collections.Generic.KeyNotFoundException:
The given key '-1§Vanilla' was not present in the dictionary.

at VBE.ModCompat.LoadRimThemesImages()
at VBE.VBEMod.Initialize()
```

This points at a compatibility issue involving:

- `vanillaexpanded.backgrounds`
- `rimthemes`

Observed log sequence:

- `[VBE] RimThemes detected, activating compatibility...`
- `[VBE] Unpatching RimThemes background patch...`
- later `VBE.ModCompat.LoadRimThemesImages()` throws

This is the strongest current crash lead.

## Other Notable Log Warnings

These may not be the hard crash, but they are part of the current instability surface:

- duplicate package IDs are present for several mods
  - `jecrell.doorsexpanded`
  - `LWM.DeepStorage`
  - `jecrell.jecstools`
  - `VanillaExpanded.BaseGeneration`
  - `vanillaexpanded.skills`
  - `moretraitslots.kv.rw`
  - `VanillaStorytellersExpanded.WinstonWave`
  - `SR.ModRimworld.FactionalWarContinued`
  - `Owlchemist.ToggleableOverlays`
  - `SR.ModRimworld.RaidExtension`
- XML patch failures exist in the current load
  - `VanillaExpandedExtraEmbrasures.xml`
  - `PawnInspectorTabs.xml`
- `VacskinGland` config errors exist
- keybinding conflicts include `Command_OpenRimGPT`

## Integration Value

For the DevMentor ecosystem, the highest-value active surfaces are now clearer:

### Direct AI/chat surfaces

- `RimTalk`
  likely best target for local LLM routing and prompt interception
- `RimGPT`
  likely best target for replacing or extending direct prompt UX
- `RimChat`
  already patches comms console and injects dialogue components
- `RiMind`
  likely another cognition/memory surface
- `Rimnet Terminal`
  terminal-flavored interaction surface, likely compatible with TerminalKeeper themes

### Active systems surfaces

- `vanillaexpanded.vanillasocialinteractionsexpanded`
- `smashphil.vehicleframework`
- `oskarpotocki.vanillavehiclesexpanded`
- `vanillaexpanded.vgeneticse`
- `maux36.rimpsyche`
- `rimsenal.storyteller`

## Recommended Compatibility Priority

1. Stabilise startup by testing `vanillaexpanded.backgrounds` + `rimthemes`
2. Inspect `RimTalk`, `RimGPT`, and `RimChat` folder contents for:
   - settings files
   - prompt files
   - local API URLs
   - Harmony patches
3. Add compatibility notes under `Source/Compatibility/` and `Patches/Compatibility/`
4. Treat `RimTalk` and `RimChat` as the first likely local-LLM bridge targets

## Proposed Follow-Up Docs

The next useful docs in this folder are:

- `COMPAT_RimTalk.md`
- `COMPAT_RimGPT.md`
- `COMPAT_RimChat.md`
- `CRASH_NOTES.md`

Those should record exact assemblies, settings files, and patch seams once inspected.

## Deep Compatibility Surfaces

This section maps reusable seams for `TerminalKeeper` compatibility work rather than
just naming active mods.

### 1. Prompt routing and model-provider surfaces

- `RimTalk`
  - strong evidence of a provider-routing layer in the compiled assembly:
    - OpenAI-compatible client support
    - Gemini support
    - Player2 support, including local-app detection
    - model fetching / model selection / base URL configuration
    - prompt import/export and context-variable registration
  - likely primary seam for:
    - prompt interception
    - provider reuse
    - local model routing
    - shared persona/context injection
- `RiMind`
  - extends the provider idea further with:
    - provider cooldowns
    - provider failure counts
    - common model lists
    - custom base URLs
    - OpenAI / Gemini / DeepSeek / Ollama-facing symbols
  - this makes `RiMind` a valuable reference for:
    - resilient multi-provider routing
    - local/cloud fallback
    - quota-aware provider rotation
- `RimChat`
  - also contains model fetching and provider dropdown logic
  - prompt files are filesystem-backed and editable:
    - `Prompt/Default/SystemPrompt_Default.json`
    - `Prompt/Default/PawnDialoguePrompt_Default.json`
    - `Prompt/Default/DiplomacyDialoguePrompt_Default.json`
    - `Prompt/Default/FactionPrompts_Default.json`
    - `Prompt/Default/SocialCirclePrompt_Default.json`
  - supports both OpenAI- and Google-model parsing in the DLL symbol surface
- `RimTalk - Quests`
  - confirms that the RimTalk ecosystem already has a reusable streaming abstraction
    for:
    - Gemini
    - OpenAI-compatible APIs
    - Player2 local/remote
  - source paths:
    - `Source/Services/Streaming/GeminiStreamingClient.cs`
    - `Source/Services/Streaming/OpenAIStreamingClient.cs`
    - `Source/Services/Streaming/Player2StreamingClient.cs`

### 2. Persona and memory surfaces

- `RimTalk`
  - persona-related symbols in assembly:
    - `GeneratePersona`
    - `PersonaService`
    - `Hediff_Persona`
    - `PersonaEditorWindow`
  - suggests persona is already a first-class state object in the RimTalk stack
- `RiMind`
  - highest-value active memory system found so far
  - reusable concepts visible from README + symbols:
    - typed memories:
      - heard speech
      - speech
      - battle
      - event
      - observation
    - memory viewer UI
    - memory manager cache
    - memory scoring / decay / freshness weighting
    - memory-based topic generation
    - conversation history assembly for prompts
  - this is the clearest template for a future `TerminalKeeper` memory adapter
- `RimChat`
  - memory is used not only for private dialogue, but for:
    - diplomacy summary memory
    - normalized memory records
    - memory JSON codecs
    - social-circle summary feedback into faction memory
  - this is more world-facing than `RiMind`
- `RimTalk: Persona Director`
  - deepest persona tooling surface found
  - evidence of:
    - prompt decoration patches
    - build-context patches
    - memory extraction
    - history extraction
    - evolve request generation
    - batch persona generation
    - director notes
    - world component persistence
  - live config already persists a large preset library in:
    - `C:\Users\keath\AppData\LocalLow\Ludeon Studios\RimWorld by Ludeon Studios\Config\Mod_3619548407_DirectorMod.xml`

### 3. Incidents, quests, raids, letters, and story surfaces

- `RimTalk - Quests`
  - very concrete quest seam
  - patches `Quest.PostAdded`
  - builds prompt from:
    - quest title
    - description
    - rewards
    - current scene
    - faction relationship / goodwill
    - recent faction quest history
  - streams generated text directly back into `quest.description`
- `RimChat`
  - exposes broader story machinery than any other active mod inspected so far
  - prompt contracts explicitly allow:
    - `create_quest`
    - `trigger_incident`
    - `request_raid`
    - `request_aid`
    - `request_caravan`
    - `send_image`
    - `publish_public_post`
    - presence-state actions like `go_offline` and `set_dnd`
  - DLL symbols indicate:
    - raid override logic
    - raid battle report history
    - quest trigger caches
    - dynamic quest guidance
    - strategy suggestion requests
    - request/session compression
- `RimGPT`
  - likely best storyteller/commentator/letter seam
  - DLL symbols indicate:
    - `LetterStack_ReceiveLetter_Patch`
    - storyteller UI patching
    - thought extraction
    - history condensation
    - Azure voice/audio surfaces
- `Rimnet Terminal`
  - not a quest mod, but it does expose a diegetic event surface:
    - hackable terminal comp
    - hack job
    - explicit `TriggerRaid` symbol in assembly
  - that makes it useful as a terminal-origin incident launcher

### 4. Terminal and physical device surfaces

- `Rimnet Terminal`
  - closest in-world physical analogue to `TerminalKeeper`
  - reusable concepts:
    - dedicated terminal building
    - custom terminal comp
    - hack duration / success chance / cooldown
    - joy/entertainment use path
    - event trigger on successful interaction
- `TerminalKeeper`
  - already has:
    - persistent terminal stats
    - terminal gizmos
    - modal terminal UI
    - per-terminal route metadata
    - agent registration
    - conversation reroute
    - colonist telemetry push
  - current source paths:
    - `Source/Buildings/Building_LatticeTerminal.cs`
    - `Source/Buildings/CompLatticeTerminal.cs`
    - `Source/UI/Dialog_TerminalAccess.cs`
    - `Source/Components/LatticeConversationSystem.cs`
    - `Source/Components/LatticeAgentManager.cs`
  - current limitation:
    - the mod is still mostly terminal-centric and command-centric
    - it has not yet expanded into world-facing comms, quest, or storyteller surfaces

### 5. Public comms and social surfaces

- `RimChat`
  - strongest active public-communications layer
  - includes:
    - diplomacy sessions
    - public social-circle posts
    - world-news cards
    - visibility to all factions and player
    - structured headline / lead / cause / process / outlook generation
  - this is a strong candidate for a `TerminalKeeper` bulletin-board or intranet layer
- `RimTalk Log To File`
  - simple but very useful bridge
  - logs AI dialogue to save-linked files
  - also supports HTTP push
  - this could serve as a low-risk compatibility ingest path for TerminalKeeper
    without replacing RimTalk internals
- `RimGPT`
  - likely useful for commentary overlays and narrated event output rather than
    direct social simulation

### 6. Research and AI infrastructure surfaces

- `AI Uplifting Assistant`
  - simple but structurally relevant
  - acts as AI-backed research infrastructure:
    - powered building
    - facility-linked to research bench
    - requires AI persona core
    - grants research speed factor bonus
  - useful for future `TerminalKeeper` compatibility around:
    - AI infrastructure networks
    - research-state aware prompts
    - “council recommends research” loops
- active adjacent systems likely worth later inspection for this category:
  - `petetimessix.researchreinvented.steppingstones`
  - `vanillaquestsexpanded.generator`
  - `vanillaquestsexpanded.cryptoforge`
  - `vanillaquestsexpanded.deadlife`

## Concrete Adapter Ideas For TerminalKeeper

### Prompt routing adapter

- introduce a provider-agnostic `ILLMProviderAdapter` layer inside `TerminalKeeper`
  that can target:
  - Terminal Depths
  - RimTalk-configured provider
  - RiMind-configured provider
  - direct local provider (`Ollama`, `LM Studio`, `Player2`)
- copy the practical capabilities, not the implementation details:
  - local-app detection
  - base URL normalization
  - provider-specific extra headers
  - long local timeout handling
  - stream-first response handling

### Persona and memory adapter

- add a `LatticeMemoryRecord` model in `TerminalKeeper` that can ingest:
  - RimTalk conversation summary
  - RiMind typed memories
  - RimChat diplomacy summaries
  - Persona Director notes/persona text
- do not try to mirror every foreign memory format 1:1
- better approach:
  - normalize to:
    - `scope`
    - `source_mod`
    - `pawn_or_faction_id`
    - `memory_type`
    - `summary`
    - `importance`
    - `timestamp`
    - `tags`

### Incident and quest adapter

- use the existing `scripts/rimapi_bridge.py` incident channel as the internal spine
  for world-facing AI reactions
- extend it conceptually to support:
  - `quest_created`
  - `letter_received`
  - `public_post_published`
  - `raid_scheduled`
  - `research_breakthrough`
- if TerminalKeeper eventually emits quests or incidents, route them through a
  common event bus instead of terminal-specific command callbacks

### Terminal/device adapter

- build a compatibility layer where `TerminalKeeper` can optionally recognize
  foreign terminal-like buildings such as `AncientTerminal`
- do not hard-bind to one mod class name
- use an adapter registry keyed by:
  - thing def name
  - comp type
  - interaction verb
  - optional success/failure callbacks

### Public comms adapter

- add a future `Lattice Bulletin` or `Colony Net` surface inspired by RimChat’s
  social-circle model
- inputs:
  - terminal sessions
  - incidents
  - council votes
  - research breakthroughs
  - faction comms
- outputs:
  - letters
  - bulletin feed
  - public summaries
  - per-faction memory injections

## Caution Areas

### 1. Competing Harmony patches

- `RimChat`, `RimGPT`, `RimTalk`, `RiMind`, and `TerminalKeeper` all touch
  conversational or event-adjacent surfaces
- risk areas:
  - social interaction reroutes
  - comms console patches
  - letter stack patches
  - quest lifecycle patches
  - memory/thought insertion

### 2. Prompt and action contract mismatch

- `RimChat` uses explicit JSON action contracts
- `RimTalk` and `RiMind` appear more prompt/context centric
- `TerminalKeeper` currently uses imperative command strings like:
  - `converse agent_a=... agent_b=...`
  - `upload_log ...`
  - `council vote`
- direct interoperability will need a translation layer, not shared raw prompts

### 3. State duplication

- multiple mods persist overlapping but non-identical state:
  - persona
  - chat history
  - memory
  - faction relation context
  - API/provider configuration
- `TerminalKeeper` should avoid becoming a second independent truth store for all
  of that data unless there is a clear reason

### 4. Provider drift and local model assumptions

- active mods do not share one provider stack
- observed stacks include:
  - OpenAI-compatible
  - Gemini / Google
  - Player2 local/remote
  - DeepSeek-facing logic
  - Ollama-facing logic
  - local OpenAI-like endpoints
- caution:
  - one mod’s “default model” should not be assumed safe for another mod’s prompt
    format or output contract

### 5. UI and file ownership

- `RimChat` prompt files are user-editable and also persist custom prompt config
- `Persona Director` persists user persona presets
- compatibility code should treat those files as user-owned
- avoid destructive rewrites or format migrations without explicit need

## Highest-Value Compatibility Targets

1. `RimTalk` provider/context reuse
   - best foundation for prompt routing and shared context hooks
2. `RiMind` typed memory concepts
   - best model for long-lived pawn memory
3. `RimChat` public comms + incidents + diplomacy actions
   - best path to expand beyond terminal-only UX
4. `RimTalk - Quests`
   - best quest-generation and streaming-description reference
5. `RimTalk Log To File`
   - best low-risk external bridge
6. `Rimnet Terminal`
   - best physical-device compatibility surface

## Owned-Seam Adapter Map

This section narrows scope to the owned seam set only:

- `RimTalk`
- `RimGPT`
- `RimChat`
- `RiMind`
- `Rimnet Terminal`
- `AI Uplifting Assistant`

### 1. Prompt routing

- primary adapter owner:
  - `RimTalk`
- supporting adapters:
  - `RiMind`
  - `RimChat`
  - `RimGPT`
- recommended `TerminalKeeper` adapter:
  - `PromptRouterAdapter`
- best first patch targets:
  - `RimTalk`
    - `AIClientFactory.cs`
    - `PromptService.cs`
    - `Settings_Api.cs`
    - `Settings.cs`
    - `ContextHookRegistry.cs`
  - `RiMind`
    - `InitializeProviders`
    - `GetProviders`
    - `GetActiveProvider`
    - `ProcessApiRequestQueue`
    - `OpenAICompatibleClient`
    - `DeepSeekClient`
  - `RimChat`
    - `DrawProviderDropdown`
    - `FetchModelsCoroutine`
    - `BuildContextVariableProviderDelegate`
  - `RimGPT`
    - `ProviderChoiceMenu`
    - `ProviderTypeMenu`
    - `GetCurrentChatGPTModel`
    - `ApiBaseUrl`
- why this order:
  - `RimTalk` appears to be the cleanest provider/context abstraction
  - `RiMind` appears to be the strongest fallback/provider-rotation reference
  - `RimChat` is more action-contract-heavy and should probably consume a shared
    router rather than define the primary one
  - `RimGPT` looks useful as a commentator/provider consumer, not as the base router

### 2. Persona and memory

- primary adapter owners:
  - `RiMind`
  - `RimTalk`
- supporting adapters:
  - `RimChat`
  - `RimGPT`
- recommended `TerminalKeeper` adapter:
  - `PersonaMemoryAdapter`
- best first patch targets:
  - `RimTalk`
    - `PersonaService.cs`
    - `Hediff_Persona.cs`
    - `TalkHistory.cs`
    - `RimTalkWorldComponent.cs`
    - `ThoughtPatch.cs`
  - `RiMind`
    - `Window_MemoryViewer`
    - `Dialog_PersonalityEditor`
    - `MemoryTopicProvider`
    - `BattleMemoryProvider`
    - `SpeechMemoryProvider`
    - `ObservationMemoryProvider`
    - `EventMemoryProvider`
    - `GetConversationHistoryForPrompt`
    - `GeneratePersonalityAsync`
  - `RimChat`
    - `LeaderMemoryJsonCodec`
    - `CreateLeaderMemorySeed`
  - `RimGPT`
    - `Personas`
    - `ReportColonistThoughts`
    - `CondenseHistory`
- recommended first compatibility behavior:
  - read foreign memory/persona state into `TerminalKeeper`
  - do not write back initially
  - treat `TerminalKeeper` memory as normalized cache, not the primary truth store

### 3. Incidents and quests

- primary adapter owners:
  - `RimChat`
  - `RimGPT`
  - `Rimnet Terminal`
- recommended `TerminalKeeper` adapter:
  - `IncidentQuestAdapter`
- best first patch targets:
  - `RimChat`
    - `ExecuteTriggerIncident`
    - `ValidateCreateQuest`
    - `ExecuteCreateQuest`
    - `OnQuestStateChanged`
    - `Notify_QuestSignalReceived`
    - `CreateRaidSeed`
    - `CreateQuestResultSeed`
  - `RimGPT`
    - `LetterStack_ReceiveLetter_Patch`
    - `StorytellerUI_DrawStorytellerSelectionInterface_Patch`
  - `Rimnet Terminal`
    - `CompHackableTerminal`
    - `JobDriver_HackAncientTerminal`
    - `TriggerRaid`
- first patching strategy:
  - patch at result/output points
  - avoid patching the raw LLM request path first
  - send normalized event objects into `TerminalKeeper` / `rimapi_bridge`

### 4. Terminals and device interactions

- primary adapter owner:
  - `Rimnet Terminal`
- supporting adapter owner:
  - `AI Uplifting Assistant`
- recommended `TerminalKeeper` adapter:
  - `ThingCompCompatibilityAdapter`
- best first patch targets:
  - `Rimnet Terminal`
    - `Defs/ThingDefs_CompTerm.xml`
    - `Defs/JobDefs/JobDefs_CompTerm.xml`
    - `Defs/JoyGiverDefs/JoyGiverDefs_CompTerm.xml`
    - `CompProperties_HackableTerminal`
    - `Building_AncientTerminal`
  - `AI Uplifting Assistant`
    - `Defs/ThingDefs_Buildings/Buildings_Misc_AUA.xml`
- recommended first compatibility behavior:
  - allow `TerminalKeeper` to recognize foreign AI/terminal buildings as valid
    lattice-adjacent endpoints
  - do not replace their existing gameplay loops
  - add optional side-channel telemetry and interaction outcomes

### 5. Social and public comms

- primary adapter owner:
  - `RimChat`
- supporting adapter owner:
  - `RimGPT`
- recommended `TerminalKeeper` adapter:
  - `PublicCommsAdapter`
- best first patch targets:
  - `RimChat`
    - `SocialCircleService`
    - `DrawSocialCirclePromptEditorScrollable`
    - `TryHandleSocialCircleAction`
    - `GetOrCreateSocialCirclePublishAction`
    - `ProcessSocialCircleTick`
    - `RaidBattleReportRecord`
  - `RimGPT`
    - `PlaySettings_DoPlaySettingsGlobalControls_Patch`
    - letter/commentary surfaces
- recommended first compatibility behavior:
  - mirror public events into a `TerminalKeeper` bulletin feed
  - do not try to own diplomacy UX yet
  - start with read-only ingestion plus optional summary publication

### 6. Research and AI infrastructure

- primary adapter owner:
  - `AI Uplifting Assistant`
- recommended `TerminalKeeper` adapter:
  - `ResearchInfrastructureAdapter`
- best first patch targets:
  - `Buildings_Misc_AUA.xml`
  - facility adjacency and powered-state inspection
- recommended first compatibility behavior:
  - observe bench link state, power state, and AI-core presence
  - translate that into:
    - research pressure
    - council recommendations
    - “AI infrastructure online/offline” colony state

## Local-Model Provider Opportunities

- `RimTalk`
  - local Player2 detection is already visible
  - OpenAI-compatible base URL handling is already visible
  - this is the cleanest route to local model reuse
- `RiMind`
  - strongest multi-provider local model opportunity
  - visible support patterns:
    - OpenAI-compatible
    - DeepSeek
    - Ollama model awareness
    - custom provider presets
    - provider rotation
- `RimChat`
  - can likely consume a shared local provider adapter once prompt/action contract
    translation exists
- `RimGPT`
  - local OpenAI-like and Ollama-facing symbols make it viable for commentary and
    storyteller-driven local output
- practical recommendation:
  - first local-model compatibility target should be:
    - `OpenAI-compatible local endpoint`
  - second should be:
    - `Player2`
  - third should be:
    - `Ollama`

## Highest-Risk Fragile Patch Areas

- `RimChat`
  - action resolver / quest / incident execution path
  - social-circle state machine
  - likely fragile because model output contract and gameplay effect contract are
    tightly coupled
- `RimGPT`
  - storyteller UI and letter stack patches
  - likely fragile because it patches core vanilla presentation surfaces
- `RimTalk`
  - thought / tick / save / bubble / overlay patches
  - likely fragile because it spans many pawn and UI hooks
- `RiMind`
  - provider queue and memory-creation paths
  - likely fragile because memory scoring, decay, and response timing appear to be
    coupled
- `Rimnet Terminal`
  - low overall complexity, but raid-trigger outcomes are high impact
- safest initial patch zones across the owned seam set:
  - config readers
  - context builders
  - result/output handlers
  - event emitters
  - public summary producers

## Phase Workflow For TerminalKeeper Compatibility

This section reframes the owned seam map as a phased adapter build order for
`TerminalKeeper`.

The target is not “patch everything.” The target is:

- normalize foreign AI/chat outputs into stable `TerminalKeeper` adapters
- reuse existing local event and analytics paths where they already exist
- avoid taking ownership of another mod’s prompt schema, UI, or persistence layer

### Phase 1. Group seams by subsystem and local ownership

- prompt routing
  - foreign seam owners:
    - `RimTalk`
    - `RiMind`
    - `RimChat`
    - `RimGPT`
  - local `TerminalKeeper` ownership points:
    - `Source/Core/TKSettings.cs`
    - `Source/API/TerminalDepthsClient.cs`
    - `Source/Components/LatticeConversationSystem.cs`
  - adapter boundary:
    - `TerminalKeeper` should own provider selection and normalized request shape
    - foreign mods should be treated as provider/context references, not the source
      of truth for routing

- persona and memory
  - foreign seam owners:
    - `RiMind`
    - `RimTalk`
    - `RimChat`
    - `RimGPT`
  - local `TerminalKeeper` ownership points:
    - `Source/Components/LatticeAgentManager.cs`
    - `Source/API/ColonistState.cs`
  - adapter boundary:
    - `TerminalKeeper` should ingest memory/persona summaries into a normalized cache
    - foreign mods should remain the authoritative source for their own editable
      persona and history stores

- incidents and quests
  - foreign seam owners:
    - `RimChat`
    - `RimGPT`
    - `Rimnet Terminal`
  - local `TerminalKeeper` ownership points:
    - `Source/Core/HarmonyPatches.cs`
    - `scripts/rimapi_bridge.py`
    - `app/rimworld_bridge.py`
  - adapter boundary:
    - `TerminalKeeper` should own event normalization and Serena-facing publication
    - foreign mods should continue executing the gameplay effect

- terminals and device interactions
  - foreign seam owners:
    - `Rimnet Terminal`
    - `AI Uplifting Assistant`
  - local `TerminalKeeper` ownership points:
    - `Source/Buildings/Building_LatticeTerminal.cs`
    - `Source/Buildings/CompLatticeTerminal.cs`
    - `Source/Jobs/JobDriver_UseLatticeTerminal.cs`
    - `Source/UI/Dialog_TerminalAccess.cs`
  - adapter boundary:
    - `TerminalKeeper` should recognize foreign devices as compatible endpoints
    - it should not replace their native jobs or building comps on the first pass

- social and public comms
  - foreign seam owners:
    - `RimChat`
    - `RimGPT`
  - local `TerminalKeeper` ownership points:
    - `scripts/rimapi_bridge.py`
    - `agents/serena/serena_agent.py`
    - `scripts/serena_analytics.py`
  - adapter boundary:
    - `TerminalKeeper` should mirror public posts, summaries, and bulletins into the
      Lattice event bus
    - Serena should index and analyse those events through the existing Redis and
      SQLite flow rather than a bespoke store

- research and AI infrastructure
  - foreign seam owners:
    - `AI Uplifting Assistant`
  - local `TerminalKeeper` ownership points:
    - `Source/API/ColonistState.cs`
    - `app/rimworld_bridge.py`
    - `scripts/serena_analytics.py`
  - adapter boundary:
    - `TerminalKeeper` should translate research-facility state into colony telemetry
    - it should not alter the facility-link gameplay loop

### Phase 2. First concrete adapter patches worth building

These are the first patches worth building because they fit the current local
architecture and avoid the most fragile foreign paths.

#### 1. Prompt router adapter

- local patch points:
  - `Source/Core/TKSettings.cs`
    - extend provider config to support normalized provider metadata instead of only
      a single `LLMBackend`
  - `Source/API/TerminalDepthsClient.cs`
    - add a provider-aware request envelope alongside the current `SendCommand`
  - `Source/Components/LatticeConversationSystem.cs`
    - stop encoding conversation intent as one opaque shell-style string
    - send a structured request with:
      - intent
      - participants
      - context
      - preferred provider
      - prompt schema version
- foreign reference seams:
  - `RimTalk`
    - `AIClientFactory.cs`
    - `PromptService.cs`
    - `ContextHookRegistry.cs`
  - `RiMind`
    - `InitializeProviders`
    - `GetActiveProvider`
    - `ProcessApiRequestQueue`
  - `RimChat`
    - `FetchModelsCoroutine`
    - `DrawProviderDropdown`
  - `RimGPT`
    - `ProviderChoiceMenu`
    - `ApiBaseUrl`
- adapter idea:
  - build one local `ProviderDescriptor` shape that can describe:
    - OpenAI-compatible endpoints
    - Player2
    - Ollama
    - LM Studio
  - then add foreign-mod translation shims later only if needed

#### 2. Persona and memory ingest adapter

- local patch points:
  - `Source/Components/LatticeAgentManager.cs`
    - extend persistence beyond `agentIds` and `lastPush`
    - add normalized pawn memory/persona digests keyed by pawn ID
  - `Source/API/ColonistState.cs`
    - add optional persona and memory summary fields rather than raw foreign payloads
- foreign hook targets:
  - `RimTalk`
    - `PersonaService.cs`
    - `TalkHistory.cs`
    - `RimTalkWorldComponent.cs`
  - `RiMind`
    - `GetConversationHistoryForPrompt`
    - `GeneratePersonalityAsync`
    - `BattleMemoryProvider`
    - `SpeechMemoryProvider`
    - `ObservationMemoryProvider`
    - `EventMemoryProvider`
  - `RimChat`
    - `LeaderMemoryJsonCodec`
  - `RimGPT`
    - `CondenseHistory`
    - `ReportColonistThoughts`
- adapter idea:
  - make first pass read-only
  - ingest:
    - top persona traits
    - last-summary text
    - recent memory digest
    - source mod tag
  - do not write back into foreign mod save structures

#### 3. Incident and quest bridge

- local patch points:
  - `scripts/rimapi_bridge.py`
    - reuse `/api/game/incident`
    - extend event payload normalization rather than inventing a new service
  - `app/rimworld_bridge.py`
    - add explicit structured event endpoints only if the existing bridge shape is too
      small
  - `Source/Core/HarmonyPatches.cs`
    - add new output-side patches only after identifying stable result points
- foreign hook targets:
  - `RimChat`
    - `ExecuteTriggerIncident`
    - `ExecuteCreateQuest`
    - `OnQuestStateChanged`
    - `Notify_QuestSignalReceived`
  - `RimGPT`
    - `LetterStack_ReceiveLetter_Patch`
  - `Rimnet Terminal`
    - `TriggerRaid`
    - `JobDriver_HackAncientTerminal`
- adapter idea:
  - normalize foreign results into one local event shape with:
    - source mod
    - event kind
    - quest or incident IDs when available
    - affected pawns or faction
    - summary text
    - prompt action provenance if present
  - publish to:
    - `lattice.rimworld.incident`
    - Serena embedding via the existing `lattice.*` subscription path

#### 4. Foreign terminal recognition adapter

- local patch points:
  - `Source/Buildings/Building_LatticeTerminal.cs`
  - `Source/Buildings/CompLatticeTerminal.cs`
  - `Source/Jobs/JobDriver_UseLatticeTerminal.cs`
  - `Source/UI/Dialog_TerminalAccess.cs`
- foreign hook targets:
  - `Rimnet Terminal`
    - `Defs/ThingDefs_CompTerm.xml`
    - `CompProperties_HackableTerminal`
    - `Building_AncientTerminal`
  - `AI Uplifting Assistant`
    - `Defs/ThingDefs_Buildings/Buildings_Misc_AUA.xml`
- adapter idea:
  - add a compatibility registry that tags foreign buildings as:
    - terminal endpoint
    - AI infrastructure endpoint
    - unsupported
  - let `TerminalKeeper` read power state, occupancy, and recent session state
  - do not override foreign job drivers on the first pass

#### 5. Public comms and Serena indexing adapter

- local patch points:
  - `scripts/rimapi_bridge.py`
    - publish public-summary and social-feed events over the existing Redis bus
  - `agents/serena/serena_agent.py`
    - rely on `walk`, `fast_walk`, and `ask` as the code-index side of the system
  - `scripts/serena_analytics.py`
    - keep using `lattice_events`, `lattice_insights`, and `colony_states`
- foreign hook targets:
  - `RimChat`
    - `SocialCircleService`
    - `TryHandleSocialCircleAction`
    - `GetOrCreateSocialCirclePublishAction`
    - `ProcessSocialCircleTick`
  - `RimGPT`
    - commentary and letter surfaces
- adapter idea:
  - ingest `RimChat` public posts and raid reports as bulletin events
  - let Serena embed them through the existing `lattice.*` subscriber path
  - avoid direct writes into Serena’s SQLite tables from the mod layer

### Phase 3. Fragile zones, patch caution, and local-model opportunities

#### Harmony caution areas

- `RimChat` is the highest-risk owned seam
  - patching before or during action parsing is fragile
  - safer hook points are:
    - post-action execution
    - quest-state notifications
    - public-post emission
- `RimGPT` is fragile around vanilla UI interception
  - avoid fighting its storyteller UI and play-settings patches
  - safer hook points are:
    - letter receive output
    - commentary result text
- `RimTalk` is broad and cross-cutting
  - avoid first-pass hooks on:
    - ticks
    - bubble drawing
    - thought generation
    - save patches
  - safer hook points are:
    - provider selection
    - prompt service boundaries
    - persona/history summaries
- `RiMind` is fragile where memory scoring and provider queue timing interact
  - avoid patching internal queue behavior on the first pass
  - safer hook points are:
    - conversation-history extraction
    - personality generation results
    - memory-provider outputs
- `Rimnet Terminal` has low patch density but high gameplay impact
  - `TriggerRaid` should be treated as an output event, not an interception target

#### Local-model provider opportunities

- best first target:
  - OpenAI-compatible local endpoints
  - reason:
    - all of `TerminalKeeper`, `RimTalk`, `RiMind`, and `RimGPT` already show
      compatibility signals around base URLs or OpenAI-like clients
- best second target:
  - `Player2`
  - reason:
    - `RimTalk` already appears to understand it directly
    - it provides a clean bridge for local desktop usage
- best third target:
  - `Ollama`
  - reason:
    - `TerminalKeeper` already has `OllamaEndpoint`
    - `RiMind` and `RimGPT` already show Ollama awareness
- best fourth target:
  - `LM Studio`
  - reason:
    - `TerminalKeeper` already has `LMStudioEndpoint`
    - it can usually sit behind the same OpenAI-compatible adapter contract

#### Concrete recommendation for provider ownership

- keep provider ownership local to `TerminalKeeper`
  - `Source/Core/TKSettings.cs` should define the selected backend and endpoint
  - `Source/API/TerminalDepthsClient.cs` should translate that into one outbound
    contract
- do not attempt first-pass cross-mod provider unification by editing foreign mod
  configs
- prefer these compatibility layers in order:
  - shared OpenAI-compatible endpoint contract
  - local provider registry in `TerminalKeeper`
  - foreign-mod read-only detection
  - optional later foreign-mod routing adapters
