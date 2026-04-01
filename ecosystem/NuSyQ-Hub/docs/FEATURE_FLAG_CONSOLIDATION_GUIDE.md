# 🚩 Feature Flag Consolidation & Simplification Guide
**Date:** 2026-02-28  
**Current State:** 60+ flags → **Recommended:** ~25 core flags  
**Impact:** Reduce complexity, improve clarity, simplify maintenance

---

## Executive Summary

Current feature flag configuration has **60+ individual flags** with complex cross-dependencies, experimental conditions, and unclear deprecation timelines. This creates:

- ❌ **Complexity:** Too many flags to manage
- ❌ **Coupling:** Flags depend on each other
- ❌ **Confusion:** Unclear which flags are active
- ❌ **Technical Debt:** Experimental flags never cleaned up

**Goal:** Reduce to **~25 core flags** organized by category with clear lifecycle.

---

## Current Grouping Analysis

### ChatDev-Related Flags (8 flags)
```json
{
  "chatdev_autofix": true,           // Basic on/off
  "chatdev_mcp_enabled": true,       // MCP integration
  "chatdev_tools_enabled": false,    // Tools available
  "chatdev_environment_patcher": ?,  // Controls env patching
  "trust_artifacts_enabled": ?,      // Trusts artifacts
  "concurrent_chatdev_teams": ?,     // Multiple teams?
  "chatdev_context_caching": ?,      // Cache control
  "chatdev_modular_models": ?        // Model selection
}
```
**Consolidation:** Combine into single `chatdev` category with sub-modes

### Observability / SNS Flags (3 flags)
```json
{
  "sns_enabled": false,              // Main switch (disabled!)
  "sns_pilot_chatdev": true,         // Pilot for ChatDev
  "sns_metrics_collection": true     // Metrics on/off
}
```
**Issue:** SNS is "fully implemented but disabled" — keep pilot, deprecate main switch

### AI/Orchestration Flags (6+ flags)
```json
{
  "quantum_resolver_enabled": true,
  "consensus_mode_enabled": false,
  "chatdev_autofix": ?,
  "ollama_adaptive_timeout": ?,
  "multi_ai_orchestration": ?,
  "consciousness_integration": ?
}
```
**Issue:** Overlap with ChatDev, unclear boundaries

### Safety/System Flags (8+ flags)
```json
{
  "overnight_safe_mode": false,
  "acl_enabled": ?,
  "require_approval_security": ?,
  "project_auto_index_enabled": false,
  "cross_repo_sync_enabled": ?,
  "consciousness_awareness": ?,
  "temple_auto_storage_enabled": ?,
  "quest_auto_archival_enabled": ?
}
```
**Issue:** Mix of safety and automation, unclear purposes

### Testing/Experimental Flags (2+ flags)
```json
{
  "testing_chamber_enabled": true,
  "boss_rush_experiment": ?
}
```
**Issue:** Some experiments never cleaned up

---

## Proposed Consolidation Plan

### New Structure: 5 Categories → ~25 Flags

#### **Category 1: CORE ORCHESTRATION (4 flags)**
Control system-level behavior and integration.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `orchestration_enabled` | true | Main system on/off | Permanent |
| `multi_ai_enabled` | true | Multi-AI router active | Permanent |
| `consciousness_bridge_enabled` | true | Consciousness integration | Permanent |
| `quantum_resolver_enabled` | true | Self-healing system | Permanent |

**Migration Path:**
- `oracle` → `orchestration_enabled`
- `multi_ai_orchestration` → `multi_ai_enabled`
- Keep `consciousness_integration` → `consciousness_bridge_enabled`
- Keep `quantum_resolver_enabled`

---

#### **Category 2: CHATDEV INTEGRATION (5 flags)**
All ChatDev-related configuration consolidated under single category.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `chatdev_enabled` | true | ChatDev integration on/off | Permanent |
| `chatdev_autofix` | true | Auto-fix problems via ChatDev | Permanent |
| `chatdev_mcp_server` | true | ChatDev as MCP server | Permanent |
| `chatdev_adaptive_models` | false | Select models by task | Growth |
| `chatdev_context_cache` | true | Cache context for speed | Growth |

**Migration Path:**
- Keep `chatdev_enabled` (new parent)
- Keep `chatdev_autofix`
- Rename `chatdev_mcp_enabled` → `chatdev_mcp_server`
- NEW: `chatdev_adaptive_models` (consolidate all model selection logic)
- NEW: `chatdev_context_cache` (consolidate caching)
- **Delete:** `chatdev_tools_enabled`, `trust_artifacts_enabled`, `environment_patcher`

---

#### **Category 3: OBSERVABILITY (5 flags)**
Logging, metrics, tracing, and monitoring.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `observability_enabled` | true | All observability on/off | Permanent |
| `opentelemetry_tracing` | true | Distributed tracing | Permanent |
| `prometheus_metrics` | true | Metrics collection | Permanent |
| `sns_compression` | true | SNS token compression (ChatDev) | Growth |
| `metrics_auto_export` | false | Auto-export to external system | Growth |

**Migration Path:**
- NEW: `observability_enabled` (parent flag)
- Add sub: `opentelemetry_tracing` (existing trace collection)
- Add sub: `prometheus_metrics` (existing metrics)
- Rename `sns_pilot_chatdev` → `sns_compression` (clarify scope)
- Delete: `sns_enabled` (main switch disabled anyway)
- Delete: `sns_metrics_collection` (subsumed under observability_enabled)

---

#### **Category 4: CONSCIOUSNESS (4 flags)**
Consciousness metrics, Temple of Knowledge, breathing factor.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `consciousness_metrics` | true | Track consciousness points | Permanent |
| `temple_of_knowledge` | true | Temple system on/off | Permanent |
| `breathing_factor_adaptive` | true | Dynamic timeouts | Permanent |
| `culture_ship_approval` | true | Strategic oversight | Permanent |

**Migration Path:**
- NEW: Consolidate all consciousness-related flags under this category
- Keep: `consciousness_bridge_enabled` (from Core Orchestration)
- Add: Temple system control
- Add: Breathing factor control
- Add: Culture Ship veto system

---

#### **Category 5: SAFETY & GOVERNANCE (4 flags)**
ACL, approval workflows, compliance, safe modes.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `safe_mode_overnight` | false | Restricted overnight work | Permanent |
| `acl_enforcement` | true | Access control lists active | Permanent |
| `auto_approval_enabled` | false | Auto-approve low-risk tasks | Growth |
| `compliance_checks` | true | Security/compliance scanning | Permanent |

**Migration Path:**
- Rename `overnight_safe_mode` → `safe_mode_overnight`
- Rename `acl_enabled` → `acl_enforcement`
- NEW: `auto_approval_enabled` (replaces `require_approval_security`)
- Keep: `compliance_checks`

---

#### **Category 6: GROWTH & EXPERIMENTAL (4 flags)**
Testing Chamber, project auto-indexing, experimental features.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `testing_chamber_enabled` | true | Isolated prototyping | Permanent |
| `project_auto_index` | false | Auto-index projects to RAG | Experimental |
| `cross_repo_sync` | true | Multi-repo synchronization | Permanent |
| `llm_cache_enabled` | true | Cache LLM responses | Permanent |

**Migration Path:**
- Keep: `testing_chamber_enabled`
- Rename: `project_auto_index_enabled` → `project_auto_index`
- Keep: `cross_repo_sync_enabled` → `cross_repo_sync`
- NEW: `llm_cache_enabled` (from context caching)
- Delete deprecated experiments

---

#### **Category 7: QUEST SYSTEM (3 flags)**
Quest logging, archival, auto-generation.

| Flag | Default | Purpose | Lifecycle |
|------|---------|---------|-----------|
| `quest_logging_enabled` | true | Log all quests | Permanent |
| `quest_auto_archival` | false | Auto-archive old quests | Growth |
| `quest_auto_generation` | true | Generate quests from errors | Permanent |

**Migration Path:**
- NEW: Consolidate all quest-related flags
- Add: Quest logging control
- Add: Auto-archival (new!)
- Keep: Auto-generation from errors

---

## Migration Timeline

### Phase 1: Planning (Week 1)
- [ ] Review all 60+ current flags in `config/feature_flags.json`
- [ ] Identify which are truly active vs. abandoned
- [ ] Map each flag to new categories above
- [ ] Document deprecation timeline

### Phase 2: Implementation (Weeks 2-3)
- [ ] Update `config/feature_flags.json` with new structure
- [ ] Add deprecation warnings to old flag names
- [ ] Update all flag references in `src/**/*.py`
- [ ] Test with existing code

### Phase 3: Migration (Week 4)
- [ ] Mark old flags as deprecated (30-day sunset)
- [ ] Add console warnings when deprecated flags used
- [ ] Update documentation
- [ ] Train on new structure

### Phase 4: Cleanup (After 30 days)
- [ ] Remove deprecated flag definitions
- [ ] Remove deprecated references from code
- [ ] Archive old config for reference

---

## New Feature Flag Configuration Example

### Before (Complex, 60+ flags)
```json
{
  "chatdev_autofix": true,
  "chatdev_mcp_enabled": true,
  "chatdev_tools_enabled": false,
  "sns_enabled": false,
  "sns_pilot_chatdev": true,
  "sns_metrics_collection": true,
  "quantum_resolver_enabled": true,
  ...60+ more flags...
}
```

### After (Organized, ~25 flags)
```json
{
  "categories": {
    "core_orchestration": {
      "orchestration_enabled": true,
      "multi_ai_enabled": true,
      "consciousness_bridge_enabled": true,
      "quantum_resolver_enabled": true
    },
    "chatdev_integration": {
      "enabled": true,
      "autofix": true,
      "mcp_server": true,
      "adaptive_models": false,
      "context_cache": true
    },
    "observability": {
      "enabled": true,
      "opentelemetry_tracing": true,
      "prometheus_metrics": true,
      "sns_compression": true,
      "metrics_auto_export": false
    },
    "consciousness": {
      "metrics_enabled": true,
      "temple_enabled": true,
      "breathing_factor_adaptive": true,
      "culture_ship_approval": true
    },
    "safety_and_governance": {
      "safe_mode_overnight": false,
      "acl_enforcement": true,
      "auto_approval": false,
      "compliance_checks": true
    },
    "growth_and_experimental": {
      "testing_chamber_enabled": true,
      "project_auto_index": false,
      "cross_repo_sync": true,
      "llm_cache_enabled": true
    },
    "quest_system": {
      "logging_enabled": true,
      "auto_archival": false,
      "auto_generation": true
    }
  },
  "deprecated_flags": {
    "chatdev_tools_enabled": "REMOVE_BY_2026-03-31",
    "sns_enabled": "REMOVE_BY_2026-03-31",
    // ... mark all deprecated flags with sunset date
  }
}
```

---

## Benefits of Consolidation

| Benefit | Impact |
|---------|--------|
| **Fewer flags to track** | Configuration becomes clearer |
| **Organized by purpose** | Easy to find related settings |
| **Clear dependencies** | Simpler logic flow |
| **Easier maintenance** | Less cross-referencing needed |
| **Better documentation** | Category structure is self-documenting |
| **Reduced technical debt** | Deprecated flags cleaned up |

---

## Rollback Plan (If Something Breaks)

1. Keep old `config/feature_flags.json` as backup
2. If new structure causes issues, revert to backup
3. Keep deprecation warnings in code for 90 days
4. Provide migration helper script for custom configs

---

## Next Steps

1. **Review this plan** with team
2. **Map all 60+ current flags** to new categories
3. **Identify abandoned flags** for immediate deletion
4. **Run phase 1 analysis** to validate structure
5. **Implement phase 2** (code updates)
6. **Execute phases 3-4** (migration and cleanup)

---

*This consolidation will dramatically improve configuration clarity and maintainability.*

Last Updated: 2026-02-28
