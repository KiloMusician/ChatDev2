# AI Universe Interface Architecture (Laptop-Scale, Game-First)

## Core principle

Do **not** reduce interface count. Make every interface a living portal into the same evolving world-state.

This architecture treats the ecosystem as a game organism:
- Gordon = director loop
- agents = entities/actors
- tools = abilities
- events = world signal spine
- dashboards/panels/terminal/sim = views into one state graph

## Design goals

1. **Alive**: system should wake, assess, act, narrate.
2. **Useful**: actions must produce measurable value (fixes, patches, summaries, routing).
3. **Extensible**: adding a new surface/agent should be low-friction.
4. **Solo-dev friendly**: low ceremony, local-first, one-command recovery.

## Canonical layers

### Layer 1 — State
Canonical local state contracts:
- `state/world_state.json`
- `state/ui_surface_registry.json`
- `state/shared_context.json`
- `state/task_queue.json`
- `state/event_log.jsonl` (append-only)

### Layer 2 — Event spine
Single event grammar, local-first. No distributed complexity required.

### Layer 3 — Agents (actors)
Each actor has:
- role
- allowed actions
- cooldown
- subscribed events
- outputs

### Layer 4 — Skills/Tools (abilities)
Small verbs with clear outcomes:
- inspect
- assign
- patch
- test
- summarize
- archive
- route

### Layer 5 — Director loop (game tick)
Per cycle:
1) ingest events
2) update world state
3) ask eligible actors for proposals
4) select actions (budget-limited)
5) execute
6) record results/events
7) narrate status

## Interface districts

- **Terminal District**: TerminalDepths (always-available shell/fallback)
- **Workspace District**: VS Code panels/webviews/editors
- **Simulation District**: SimulatedVerse / colony overlays
- **Memory District**: context browser, Serena memory graph
- **Build District**: ChatDev / Builder / patch pipelines
- **Ops District**: health, logs, alerts, recoveries

All districts must read/write the same world-state and publish/consume the same event grammar.

## One action grammar

Actions should map across all interfaces:
- `inspect`
- `activate`
- `assign`
- `route`
- `patch`
- `test`
- `promote`
- `suppress`
- `archive`

Button click, terminal command, and simulation action should compile to the same command model.

## Event grammar (minimum)

- `session_started`
- `state_refreshed`
- `error_detected`
- `task_created`
- `task_assigned`
- `patch_generated`
- `test_passed`
- `test_failed`
- `approval_requested`
- `action_executed`
- `action_blocked`
- `recovery_started`
- `recovery_completed`

## Actor roster (MVP)

- **Gordon** (director): prioritize + narrate + route
- **Watcher**: detect drift/errors/stalls
- **Builder**: generate patch/script
- **Tester**: verify outcomes
- **Archivist**: summarize + persist records
- **Council** (rare): approve only risky operations

## Council invocation rule

Use Council only for:
- destructive action
- core config mutation
- conflicting priorities
- nontrivial high-risk patch

All normal operations should flow without Council overhead.

## Friction budget controls

Soft guardrails only:
- dry-run
- confirm-on-destructive
- max actions per cycle

Recovery:
- snapshot before risky operation
- previous-file backup
- one-command restore

Visibility:
- plain-English action log
- one-screen current state

## Nexus (not replacement UI)

Nexus = index + router + synchronizer.

Responsibilities:
1. Discover all surfaces and status.
2. Route across districts with preserved context.
3. Reflect state/event changes everywhere.

## Milestone roadmap (replace 1–60 phase fatigue)

1. **Alive**: boot + status + one event processed
2. **Reactive**: issue -> task -> log
3. **Constructive**: patch -> test -> report
4. **Semi-autonomous**: small queue handled without intervention
5. **Expressive**: richer dashboard/activity feed/personality modes

## Success criteria

- One-screen state summary works.
- One-command reset works.
- Every surface has registry metadata and event links.
- Every action emits event + plain-English log.
- Gordon can complete at least one useful full loop autonomously per session.

## Immediate implementation order

1. Stand up registry + context + event contracts (done in this commit set).
2. Add `nexus status` command to read these contracts.
3. Wire TerminalDepths + one VS Code panel + one SimulatedVerse surface to same context object.
4. Route Watcher -> Builder -> Tester -> Archivist loop via event spine.
5. Keep Council opt-in for risky-only paths.
