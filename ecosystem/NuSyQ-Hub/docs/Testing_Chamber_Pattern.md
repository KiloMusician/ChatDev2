# Testing Chamber Pattern

## Overview

The Testing Chamber is a quarantined prototyping environment for experimental code that hasn't been vetted for the canonical codebase.

## Feature Flag

```json
{
  "testing_chamber_enabled": {
    "description": "Allow Testing Chamber operations for isolated prototyping",
    "default": true
  }
}
```

## Locations

| Repository | Testing Chamber Path |
|------------|---------------------|
| NuSyQ-Hub | `prototypes/` |
| SimulatedVerse | `SimulatedVerse/testing_chamber/` |
| NuSyQ Root | `NuSyQ/ChatDev/WareHouse/` |

## Lifecycle

### 1. Creation

Prototypes are created in quarantine:

```bash
# Tell the agent
"Create [prototype] in Testing Chamber"
```

### 2. Development

Code is developed and tested in isolation without affecting canonical systems.

### 3. Graduation

When ready, prototypes graduate to canonical locations:

```bash
# Tell the agent
"Graduate [prototype] to canonical"
```

## Graduation Criteria

Before graduation, prototypes must meet:

- [ ] **Works** - Passes smoke tests
- [ ] **Documented** - Has README or docstrings
- [ ] **Useful** - Solves a real problem
- [ ] **Reviewed** - Passed code review (automated or manual)
- [ ] **Integrated** - Has connection points to existing systems

## Agent Invocation

### Create Prototype

```
"Create <name> in Testing Chamber"
```

The agent will:
1. Create directory in appropriate Testing Chamber
2. Scaffold initial files
3. Log to quest system

### Graduate Prototype

```
"Graduate <prototype> to canonical"
```

The agent will:
1. Verify graduation criteria
2. Move files to canonical location
3. Update imports and references
4. Log graduation to quest system

## Configuration

### Overnight Safe Mode

In overnight safe mode, Testing Chamber operations are restricted:
- Creation: ✅ Allowed
- Graduation: ❌ Requires human approval

## Related Files

- `.github/instructions/COPILOT_INSTRUCTIONS_CONFIG.instructions.md` - Operating modes
- `config/feature_flags.json` - Feature configuration
- `src/Rosetta_Quest_System/quest_log.jsonl` - Quest logging
