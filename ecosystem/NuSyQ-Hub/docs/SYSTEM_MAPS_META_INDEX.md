# 🗺️ System Maps Meta-Index (Unified Navigation)

**Purpose:** Single search engine for all system maps and documentation  
**Updated:** February 26, 2026  
**Maintenance:** Monthly verification cycle  
**Owner:** System documentation oversight

---

## 🚀 Quick Start: Find Your Map

### **"I want to understand..."**

| Goal | Primary Map | Secondary Reference | Type |
|------|-----------|-----|------|
| **How orchestration works** | [AGENT_COORDINATION_MAP.md](AGENT_COORDINATION_MAP.md) | [NUSYQ_MODULE_MAP.md](NUSYQ_MODULE_MAP.md) | Architecture |
| **Where boundary contracts are enforced** | [SYSTEM_WIRING_MAP_2026-02-25.md](SYSTEM_WIRING_MAP_2026-02-25.md) | `tests/test_unified_chatdev_bridge_contract.py` | Runtime contracts |
| **Why WSL/Windows behavior differs** | [WSL_INTEGRATION.md](WSL_INTEGRATION.md) | [SYSTEM_WIRING_MAP_2026-02-25.md](SYSTEM_WIRING_MAP_2026-02-25.md) | Runtime environment |
| **How healing system works** | [ARCHITECTURE_MAP.md](ARCHITECTURE_MAP.md) | [ERROR_LANDSCAPE_MAP.md](ERROR_LANDSCAPE_MAP.md) | Architecture |
| **Directory structure & setup** | [SYSTEM_MAP.md](SYSTEM_MAP.md) | [WORKSPACE_FOLDER_MAPPING_TECHNICAL.md](WORKSPACE_FOLDER_MAPPING_TECHNICAL.md) | Infrastructure |
| **How to route output/terminals** | [TERMINAL_MAPPING.md](TERMINAL_MAPPING.md) | [CAPABILITY_MAP.md](CAPABILITY_MAP.md) | Infrastructure |
| **What commands I can run** | [CAPABILITY_MAP.md](CAPABILITY_MAP.md) | [ACTION_MENU_QUICK_REFERENCE.md](ACTION_MENU_QUICK_REFERENCE.md) | Operational |
| **API functions & signatures** | [NUSYQ_MODULE_MAP.md](NUSYQ_MODULE_MAP.md) | [SYSTEM_ARCHITECTURE_DEEP_DIVE.md](../SYSTEM_ARCHITECTURE_DEEP_DIVE.md) | Developer |
| **Error status & hotspots** | [ERROR_LANDSCAPE_MAP.md](ERROR_LANDSCAPE_MAP.md) | [DIAGNOSTIC_SYSTEMS_ANALYSIS.md](DIAGNOSTIC_SYSTEMS_ANALYSIS.md) | Diagnostics |
| **How to run system autonomously** | [AUTONOMOUS_QUICK_START.md](AUTONOMOUS_QUICK_START.md) | [PRACTICAL_USAGE_GUIDE.md](../PRACTICAL_USAGE_GUIDE.md) | Operational |

---

## 📚 Complete Maps Library

### Layer 1: Architecture Understanding (Strategic)

#### **[AGENT_COORDINATION_MAP.md](AGENT_COORDINATION_MAP.md)** ⭐ Core Reference
- **Lines:** 301
- **Last Updated:** Dec 24, 2025
- **Focus:** AI agents, orchestration, quest system, guild board
- **Best For:** Understanding agent relationships and task routing
- **Key Sections:**
  - Primary Orchestrators (multi_ai_orchestrator, agent_orchestration_hub)
  - Quest System (persistent logging)
  - Guild Board System (task tracking)
  - Terminal Manager integration
- **Use When:** "How do agents coordinate?"

#### **[ARCHITECTURE_MAP.md](ARCHITECTURE_MAP.md)** ⭐ Healing Focus
- **Lines:** 308
- **Last Updated:** Dec 24, 2025
- **Focus:** 5-layer healing ecosystem, detection methods, resolution tracking
- **Best For:** Understanding autonomous healing and issue resolution
- **Key Sections:**
  - Presentation Layer (CLI, Dashboard, Monitor)
  - Orchestration Layer (Cycle Runner, ChatDev Router)
  - Analytics Layer (Tracker, Cache)
  - Detection Layer (9 detection methods)
  - Codebase Layer
- **Use When:** "How does self-healing work?"

#### **[SYSTEM_MAP.md](SYSTEM_MAP.md)** 📋 Operational Reference
- **Lines:** ~50
- **Last Updated:** Dec 24, 2025
- **Focus:** Directory structure, entry points, CI, artifact management
- **Best For:** Repository navigation and operational setup
- **Key Sections:**
  - Key Directories (src/, scripts/, docs/, config/, logs/, tests/)
  - Entry Points (run_tests.py, lint, format)
  - CI Workflow integration
  - Contacts & responsibility matrix
- **Use When:** "Where does code go? How do I contribute?"

#### **[WORKSPACE_FOLDER_MAPPING_TECHNICAL.md](WORKSPACE_FOLDER_MAPPING_TECHNICAL.md)** 🔧 Technical Layout
- **Lines:** TBD (not fully read in audit)
- **Focus:** Detailed workspace structure for multi-repo setup
- **Best For:** Understanding complete folder organization
- **Use When:** "How are the 3 repos laid out?"

---

### Layer 2: Capability & Operation (Tactical)

#### **[CAPABILITY_MAP.md](CAPABILITY_MAP.md)** ✅ Wired Actions Catalog
- **Lines:** 216
- **Last Updated:** Dec 24, 2025
- **Focus:** All wired actions, safety levels, commands, outputs
- **Best For:** "What can I actually run?"
- **Key Sections:**
  - Core Operations (snapshot, brief, hygiene)
  - Analysis Actions (analyze, review)
  - Healing Actions (heal, doctor)
  - Testing & Diagnostics (test, selfcheck)
  - Intelligence (suggest, capabilities)
- **Status:** Phase 4A - Production Ready
- **Use When:** "I want to run a command"

#### **[TERMINAL_MAPPING.md](TERMINAL_MAPPING.md)** 🖥️ Output Organization
- **Lines:** ~40
- **Last Updated:** Dec 24, 2025
- **Focus:** VS Code terminal → channel mapping
- **Best For:** Understanding output routing and terminal organization
- **Key Sections:**
  - 17 Named Terminals (Claude, Copilot, ChatDev, Errors, etc.)
  - Channel assignments and purposes
  - Log file locations
- **Use When:** "Where should my output go?"

#### **[NUSYQ_MODULE_MAP.md](NUSYQ_MODULE_MAP.md)** 💻 Developer API Reference
- **Lines:** 204
- **Last Updated:** Dec 24, 2025
- **Focus:** Classes, methods, signatures, usage examples
- **Best For:** Writing code that uses the system
- **Key Sections:**
  - Orchestration Layer (MultiAIOrchestrator)
  - Integration Layer (ConsciousnessBridge)
  - Healing & Resolution (QuantumProblemResolver)
  - AI Coordination (AICoordinator)
- **Use When:** "I need to write code using system APIs"

#### **[ERROR_LANDSCAPE_MAP.md](ERROR_LANDSCAPE_MAP.md)** 🚨 Error Diagnostics
- **Lines:** 125
- **Last Updated:** Jan 8, 2026
- **Focus:** Canonical error counts, hotspots, extraction workflows
- **Best For:** Understanding current error state and remediation approach
- **Key Sections:**
  - Canonical Counts (2856 diagnostics: 64 errors, 118 warnings)
  - Error Code Breakdown (attr-defined, return-value, etc.)
  - Top Error Files (quantum_analyzer.py, ollama_integrator.py)
  - Repeatable Extraction Workflow
- **Ground Truth:** `docs/Reports/diagnostics/unified_error_report_20260108_231504.md`
- **Use When:** "What errors exist and where?"

---

### Layer 3: Operational Guides (Procedural)

#### **[ACTION_MENU_QUICK_REFERENCE.md](ACTION_MENU_QUICK_REFERENCE.md)** 🎯 Operator Guide
- **Lines:** 300+
- **Focus:** Action menu structure, categories, commands
- **Best For:** Operating the system interactively
- **Relevant To:** CAPABILITY_MAP.md (detailed menu operations)

#### **[AUTONOMOUS_QUICK_START.md](AUTONOMOUS_QUICK_START.md)** 🤖 Autonomous Loop Guide
- **Focus:** Running autonomous development cycles
- **Best For:** Understanding self-directed system behavior

#### **[PRACTICAL_USAGE_GUIDE.md](../PRACTICAL_USAGE_GUIDE.md)** 📖 Full Operational Reference
- **Lines:** 400+
- **Focus:** Examples, terminal routing, workflows
- **Best For:** Learning by example

---

### Layer 4: Deep Dives & Architecture (Comprehensive)

#### **[SYSTEM_ARCHITECTURE_DEEP_DIVE.md](../SYSTEM_ARCHITECTURE_DEEP_DIVE.md)** 🏗️ ChatDev Integration Deep Dive
- **Focus:** ChatDev + multi-AI orchestration details
- **Related To:** AGENT_COORDINATION_MAP.md (high-level)

#### **[CHATDEV_INTEGRATION_DETAILED.md](../CHATDEV_INTEGRATION_DETAILED.md)** 📋 ChatDev Workflow Visualization
- **Focus:** Visual ChatDev pipeline (CEO → CTO → Programmer → Tester → Reviewer)

#### **[ECOSYSTEM_INTEGRATION_GUIDE.md](ECOSYSTEM_INTEGRATION_GUIDE.md)** 🌐 Cross-Repo Integration
- **Focus:** NuSyQ-Hub ↔ NuSyQ ↔ SimulatedVerse coordination

---

### Layer 5: Status & Diagnostics (Real-Time)

#### **[SYSTEM_ACTIVATION_REPORT.md](../SYSTEM_ACTIVATION_REPORT.md)** 📊 System Status Snapshot
- **Focus:** Full system status, infrastructure, features

#### **[DIAGNOSTIC_SYSTEMS_ANALYSIS.md](DIAGNOSTIC_SYSTEMS_ANALYSIS.md)** 🔍 Diagnostic Subsystem Status
- **Focus:** Diagnostic tools, health check frameworks

#### **[GUILD_BOARD_OPERATIONAL_DOCTRINE.md](GUILD_BOARD_OPERATIONAL_DOCTRINE.md)** 📋 Task Management
- **Focus:** Guild board functionality and operations

---

### Layer 6: Runtime Contract Tracing (Integration Boundaries)

#### **[SYSTEM_WIRING_MAP_2026-02-25.md](SYSTEM_WIRING_MAP_2026-02-25.md)** 🔌 Boundary Traceability
- **Focus:** Integration boundaries, contract normalization points, and verification routes
- **Best For:** Tracing "idea → boundary → test" quickly
- **Key Sections:**
  - Boundary contract matrix (producer/consumer/normalizer)
  - Terminal API smoke coverage path
  - ChatDev and orchestration contract verification hooks
  - Known runtime caveats and operator-safe smoke commands
- **Use When:** "Which existing infrastructure already solves this gap?"

#### **[scripts/integration_health_check.py](../scripts/integration_health_check.py)** 🧪 Contract Smoke Gate
- **Focus:** Health check orchestration with explicit contract smoke targets
- **Best For:** Running cross-boundary checks with optional coverage
- **Use When:** "Run the contract smoke gate in one command"

#### **[WSL_INTEGRATION.md](WSL_INTEGRATION.md)** 🪟↔🐧 Windows/WSL Runtime Split
- **Focus:** Auth, hook, interpreter, and network boundary behavior between Windows and WSL shells
- **Best For:** Debugging localhost-vs-gateway failures and mixed-shell command drift
- **Use When:** "A command works in one shell but fails in another"

---

## 🔗 Map Inter-Dependencies

```
SYSTEM_MAPS_META_INDEX.md (YOU ARE HERE)
│
├─→ AGENT_COORDINATION_MAP.md ⭐
│   ├─→ NUSYQ_MODULE_MAP.md (API details)
│   ├─→ CAPABILITY_MAP.md (what actions exist)
│   └─→ TERMINAL_MAPPING.md (output routing)
│
├─→ ARCHITECTURE_MAP.md ⭐
│   ├─→ ERROR_LANDSCAPE_MAP.md (error detection)
│   └─→ DIAGNOSTIC_SYSTEMS_ANALYSIS.md (diagnostics detail)
│
├─→ SYSTEM_MAP.md ⭐
│   ├─→ WORKSPACE_FOLDER_MAPPING_TECHNICAL.md (folder details)
│   └─→ [CI workflows, entry points]
│
└─→ Supporting Guides
    ├─→ ACTION_MENU_QUICK_REFERENCE.md
    ├─→ AUTONOMOUS_QUICK_START.md
    ├─→ PRACTICAL_USAGE_GUIDE.md
    ├─→ SYSTEM_ARCHITECTURE_DEEP_DIVE.md
    └─→ [20+ session docs & reports]
```

---

## 👥 Type-Based Navigation

### **For Operators** (Running commands)
1. Start: [CAPABILITY_MAP.md](CAPABILITY_MAP.md) — What can I run?
2. Dive: [ACTION_MENU_QUICK_REFERENCE.md](ACTION_MENU_QUICK_REFERENCE.md) — How do I navigate?
3. Operate: [PRACTICAL_USAGE_GUIDE.md](../PRACTICAL_USAGE_GUIDE.md) — Examples and workflows
4. Troubleshoot: [ERROR_LANDSCAPE_MAP.md](ERROR_LANDSCAPE_MAP.md) — What's wrong?

### **For Developers** (Writing code)
1. Start: [NUSYQ_MODULE_MAP.md](NUSYQ_MODULE_MAP.md) — What APIs exist?
2. Understand: [AGENT_COORDINATION_MAP.md](AGENT_COORDINATION_MAP.md) — How do they work together?
3. Trace: [SYSTEM_WIRING_MAP_2026-02-25.md](SYSTEM_WIRING_MAP_2026-02-25.md) — Boundary contracts + runtime checks
4. Integrate: [SYSTEM_ARCHITECTURE_DEEP_DIVE.md](../SYSTEM_ARCHITECTURE_DEEP_DIVE.md) — Advanced patterns
5. Reference: [SYSTEM_MAP.md](SYSTEM_MAP.md) — Directory structure

### **For AI Agents** (Self-directed work)
1. Orient: [AGENT_COORDINATION_MAP.md](AGENT_COORDINATION_MAP.md) — Your orchestration system
2. Learn: [AUTONOMOUS_QUICK_START.md](AUTONOMOUS_QUICK_START.md) — Autonomous mode
3. Execute: [CAPABILITY_MAP.md](CAPABILITY_MAP.md) — Available actions
4. Trace: [SYSTEM_WIRING_MAP_2026-02-25.md](SYSTEM_WIRING_MAP_2026-02-25.md) — Boundary contracts + known gaps
5. Route: [TERMINAL_MAPPING.md](TERMINAL_MAPPING.md) — Output organization

### **For Architects/Planners** (System design)
1. Macro: [ARCHITECTURE_MAP.md](ARCHITECTURE_MAP.md) — System layers
2. Agents: [AGENT_COORDINATION_MAP.md](AGENT_COORDINATION_MAP.md) — Agent flow
3. Integration: [ECOSYSTEM_INTEGRATION_GUIDE.md](ECOSYSTEM_INTEGRATION_GUIDE.md) — Cross-repo
4. Health: [ERROR_LANDSCAPE_MAP.md](ERROR_LANDSCAPE_MAP.md) — Error state

### **For DevOps/Infrastructure** (Operations, CI/CD)
1. Layout: [SYSTEM_MAP.md](SYSTEM_MAP.md) — Directory organization
2. Folders: [WORKSPACE_FOLDER_MAPPING_TECHNICAL.md](WORKSPACE_FOLDER_MAPPING_TECHNICAL.md) — Multi-repo setup
3. Diagnostics: [DIAGNOSTIC_SYSTEMS_ANALYSIS.md](DIAGNOSTIC_SYSTEMS_ANALYSIS.md) — Health checking
4. Errors: [ERROR_LANDSCAPE_MAP.md](ERROR_LANDSCAPE_MAP.md) — Error tracking

---

## 📊 Map Maintenance Status

| Map | Created | Last Verified | Next Review | Owner | Status |
|-----|---------|---------------|-------------|-------|--------|
| AGENT_COORDINATION_MAP.md | Dec 24 | Dec 24 | Mar 16 | Agents | ✅ Active |
| ARCHITECTURE_MAP.md | Dec 24 | Dec 24 | Mar 16 | Healing System | ✅ Active |
| SYSTEM_MAP.md | Dec 24 | Dec 24 | Mar 16 | Infrastructure | ✅ Active |
| CAPABILITY_MAP.md | Dec 24 | Dec 24 | Mar 16 | Operations | ✅ Active |
| NUSYQ_MODULE_MAP.md | Dec 24 | Dec 24 | Mar 16 | Developers | ✅ Active |
| TERMINAL_MAPPING.md | Dec 24 | Dec 24 | Mar 16 | Output Routing | ✅ Active |
| ERROR_LANDSCAPE_MAP.md | Jan 8 | Jan 8 | Mar 16 | Diagnostics | ✅ Active |
| WORKSPACE_FOLDER_MAPPING_TECHNICAL.md | ? | ? | ? | Infrastructure | ⚠️ Check |
| SYSTEM_WIRING_MAP_2026-02-25.md | Feb 25 | Feb 26 | Mar 26 | Integration | ✅ Active |

---

## 🚀 Future Maps (Planned - "Three Before New" Protocol)

These maps should be created to fill existing gaps:

| Map | Purpose | Status | Priority |
|-----|---------|--------|----------|
| **DATA_FLOW_ARCHITECTURE.md** | Request journey through system | Planning | 🔴 HIGH |
| **CONSCIOUSNESS_STATE_MACHINE.md** | Consciousness layer state transitions | Planning | 🟡 MEDIUM |
| **MULTI_REPO_INTEGRATION_PROTOCOL.md** | Cross-repo coordination & data flow | Planning | 🟡 MEDIUM |
| **TERMINAL_ROUTING_DECISION_TREE.md** | Algorithm for routing actions to terminals | Planning | 🟢 LOW |

---

## 🔍 How to Search This System

### **By Problem**
- "System won't start" → SYSTEM_MAP.md, DIAGNOSTIC_SYSTEMS_ANALYSIS.md
- "What does error X mean" → ERROR_LANDSCAPE_MAP.md
- "How do I add a new action" → AGENT_COORDINATION_MAP.md, CAPABILITY_MAP.md
- "Agents aren't coordinating" → AGENT_COORDINATION_MAP.md, NUSYQ_MODULE_MAP.md

### **By Component**
- **ChatDev** → AGENT_COORDINATION_MAP.md, CHATDEV_INTEGRATION_DETAILED.md
- **Ollama** → NUSYQ_MODULE_MAP.md, CAPABILITY_MAP.md
- **Quest Log** → AGENT_COORDINATION_MAP.md
- **Healing System** → ARCHITECTURE_MAP.md, ERROR_LANDSCAPE_MAP.md
- **Consciousness Bridge** → AGENT_COORDINATION_MAP.md, NUSYQ_MODULE_MAP.md

### **By Task**
- "Run a command" → CAPABILITY_MAP.md, PRACTICAL_USAGE_GUIDE.md
- "Write orchestration code" → NUSYQ_MODULE_MAP.md, SYSTEM_ARCHITECTURE_DEEP_DIVE.md
- "Fix errors" → ERROR_LANDSCAPE_MAP.md, ARCHITECTURE_MAP.md
- "Understand system flow" → AGENT_COORDINATION_MAP.md, ARCHITECTURE_MAP.md

---

## 📋 Documentation Quality Checklist

Each map should have:
- ✅ Clear purpose statement (why this map exists)
- ✅ Target audience identified (who should read this)
- ✅ Last updated date (when was it verified)
- ✅ Cross-references to related maps (links to "see also")
- ✅ Example code or usage patterns (practical guidance)
- ✅ Visual diagrams (ASCII art or structured layout)
- ✅ Maintenance schedule (when to verify again)

**Compliance Status:**
- ✅ AGENT_COORDINATION_MAP.md (7/7)
- ✅ ARCHITECTURE_MAP.md (7/7)
- ⚠️ SYSTEM_MAP.md (6/7 - needs maintenance schedule)
- ✅ CAPABILITY_MAP.md (7/7)
- ✅ NUSYQ_MODULE_MAP.md (6/7 - needs explicit audience)
- ⚠️ TERMINAL_MAPPING.md (5/7 - needs examples, clearer purpose)
- ✅ ERROR_LANDSCAPE_MAP.md (7/7)

---

## 🎯 Using This Meta-Index

### **I'm lost and need direction**
→ Read this entire page, find yourself in the "👥 Type-Based Navigation" section

### **I need a specific map**
→ Use "🚀 Quick Start: Find Your Map" table at the top

### **I want to understand relationships**
→ Skip to "🔗 Map Inter-Dependencies" section

### **I need to create a new map**
→ Check "🚀 Future Maps (Planned)" first; if not there, follow Three Before New Protocol and reference this audit document

### **Something seems wrong or stale**
→ Check "📊 Map Maintenance Status" and submit update request

---

## 📞 Contacts & Ownership

**Meta-Index Maintainer:** System Documentation Oversight  
**Update Frequency:** Monthly verification cycle  
**Last Verified:** February 16, 2026  
**Next Review:** March 16, 2026

**For questions about:**
- **Orchestration** → See AGENT_COORDINATION_MAP.md
- **Healing** → See ARCHITECTURE_MAP.md
- **Operations & Commands** → See CAPABILITY_MAP.md
- **Errors & Diagnostics** → See ERROR_LANDSCAPE_MAP.md
- **API Code** → See NUSYQ_MODULE_MAP.md

---

## Related Audit Documents

- **[SYSTEM_MAPS_AUDIT_AND_CONSOLIDATION.md](SYSTEM_MAPS_AUDIT_AND_CONSOLIDATION.md)** — Full audit of map system, overlaps, gaps, and consolidation plan

---

**Status:** ✅ OPERATIONAL - Use this as your map search engine
