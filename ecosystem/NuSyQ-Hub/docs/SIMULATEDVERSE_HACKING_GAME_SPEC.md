# SimulatedVerse Hacking-Game Integration Spec

This spec maps the proposed hacking-game commands to existing `src/api/systems.py` endpoints, flags missing data structures, aligns Rosetta Stone tiers to current XP/quest mechanics, and defines a short playtest checklist with success metrics.

## 1. Command-to-Endpoint Mapping (Systems API)

| Proposed Command | Systems Endpoint | Current Behavior | Missing Data Structures / Gaps |
| --- | --- | --- | --- |
| `scan` | `GET /api/actions` + `POST /api/actions/execute` with `scan` | Action registry includes `scan` (runs error report). | Needs component/network scan output structure (ports, services, vulnerabilities) to be useful for hacking loops. |
| `nmap` | `POST /api/hack/nmap` (new prototype) | Returns port/service/vuln list for a component using `HackingController.scan`. | Needs component-to-inventory mapping and persistence of scan results for later steps. |
| `connect` | Not in systems API | No connect endpoint in systems router. | Add access session model (component, access level, timestamps). |
| `sudo` | Not in systems API | No privilege escalation endpoint in systems router. | Needs access-level model and privilege escalation rules. |
| `exploit` | Not in systems API | No exploit endpoint in systems router. | Needs exploit catalog, vulnerability metadata, and XP reward hooks. |
| `patch` | Not in systems API | No patch endpoint in systems router. | Needs patch history, component versioning, and vulnerability state updates. |
| `upgrade` | Not in systems API | No upgrade endpoint in systems router. | Needs upgrade plan structure tied to inventory component versions. |
| `heal` | `GET /api/actions` + `POST /api/actions/execute` with `heal` | Action registry includes healing cycle. | Needs per-component heal result output and impact on vulnerability state. |
| `suggest` | `GET /api/actions` + `POST /api/actions/execute` with `suggest` | Action registry includes AI suggestion. | Needs suggestion-to-quest linking. |
| `work` | `GET /api/actions` + `POST /api/actions/execute` with `work` | Action registry includes work cycle. | Needs work result schema for XP, component changes. |
| `evolve` | `GET /api/actions` + `POST /api/actions/execute` with `evolve` or `POST /api/evolve` | Evolve uses suggestion artifacts. | Needs evolve results tied to skills or faction progression. |
| `queue` | `GET /api/actions` + `POST /api/actions/execute` with `queue` | Action registry includes queue listing. | Needs queue state to be exposed with priority and owners. |
| `fl1ght.exe` | `GET /api/fl1ght` | Smart search across hints/quests/commands/code. | Needs inventory and active-task indexing for state-aware suggestions. |
| `guild board` | `GET /api/guild/quests`, `GET /api/guild/summary` | Multi-agent quest coordination. | Needs quest claim/complete endpoints for multiplayer loop. |
| `rpg status` | `GET /api/rpg/status` | Component/skill snapshot. | Needs component port/access metadata to feed hacking mechanics. |
| `rpg xp` | `POST /api/rpg/xp` | Adds XP to RPG inventory skills. | Needs bridge to hacking skill tree XP. |
| `skills` | `GET /api/skills` | RPG inventory skills list. | Needs unification with hacking skill tree in `src/games/skill_tree.py`. |
| `trace` | `GET /api/hack/traces` (new prototype) | Returns active trace status + countdowns. | Needs persistence and linkage to specific actions/exploits. |

## 2. Missing Data Structures (Minimal Set)

These structures are required to complete the hacking-game loop end-to-end:

- Component network profile: ports, services, vulnerabilities per component.
- Access sessions: component access level, auth state, timestamps.
- Trace state persistence: active trace timers stored and recoverable.
- Script registry: background job state, memory cost, owner.
- Resource constraints: per-agent or per-session memory/CPU budget.
- Upgrade state model: version tracking, patch history, upgrade outcomes.
- Unified skill state: bridge `rpg_inventory` skills with `games.skill_tree` skills.
- Quest-to-command linkage: structured mapping between quests and actions.

## 3. Skill Tree Alignment (Rosetta Tiers + XP/Quest Mechanics)

Current XP mechanics:
- Actions XP: `GET /api/actions` and `POST /api/actions/execute`
- RPG XP: `POST /api/rpg/xp`
- Quests: `GET /api/quests`, `GET /api/guild/quests`

Proposed alignment table (based on `src/games/skill_tree.py` thresholds):

| Rosetta Tier | XP Threshold | Primary Unlocks | Example Skills | Related Endpoints |
| --- | --- | --- | --- | --- |
| Tier 1: Survival | 0 | Basic scan/repair | `basic_scan`, `ssh_crack`, `component_heal` | `POST /api/hack/nmap`, `POST /api/actions/execute` (`scan`, `heal`) |
| Tier 2: Automation | 500 | Background scripts | `script_writing`, `resource_optimization`, `multi_threading` | `POST /api/actions/execute` (`work`, `queue`), `POST /api/rpg/xp` |
| Tier 3: AI Integration | 2000 | AI-assisted ops | `ai_copilot`, `smart_search_plus`, `consciousness_bridge` | `GET /api/fl1ght`, `POST /api/actions/execute` (`suggest`, `evolve`) |
| Tier 4: Defense | 5000 | Trace defense | `trace_evasion`, `security_hardening`, `firewall_bypass` | `GET /api/hack/traces`, planned `patch` endpoint |
| Tier 5: Synthesis | 10000 | Multi-agent orchestration | `multi_faction_control`, `emergent_strategy` | `GET /api/guild/summary`, planned faction endpoints |

## 4. Playtest Checklist

Short checklist for validating pacing and reward loops:

- Run `POST /api/hack/nmap` on 2 components and verify ports/vulns returned.
- Trigger a trace by connecting/exploiting (if wired) and verify countdown in `GET /api/hack/traces`.
- Execute `scan`, `heal`, and `work` actions and verify XP rewards in responses.
- Use `GET /api/fl1ght` to find a recommended next action after a scan.
- Confirm Tier 1 unlocks are accessible with starting XP and that Tier 2 requires deliberate play.

## 5. Success Metrics

Metrics to evaluate loop quality:

- Time-to-first-success: < 5 minutes to complete a scan + gain XP.
- Trace pressure: 1–2 trace events per 5 actions at Tier 1–2.
- Reward balance: XP gained per action roughly matches tier thresholds (500 XP to Tier 2 feels reachable within a short session).
- Retention loop: at least one clear “next step” suggested after each action.
- Error rate: < 5% failed actions due to missing data or endpoint errors.
