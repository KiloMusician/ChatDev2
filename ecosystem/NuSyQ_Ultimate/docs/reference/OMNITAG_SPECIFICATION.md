# ΞNuSyQ OmniTag Specification
## Universal Context Marking and Semantic Codification System

**Version**: 1.0.0
**Status**: Active Standard ✓
**Last Updated**: 2025-10-06
**Framework**: ΞNuSyQ ∆ΨΣ Extended Protocols

---

## 🎯 Purpose

The **OmniTag System** provides a universal, semantic tagging framework for all files in the NuSyQ repository, enabling:

- **Instant Context Recognition** - Know what a file does at a glance
- **Semantic Search** - Find files by purpose, not just name
- **Automated Organization** - Tools can categorize and route files
- **Evolution Tracking** - Track file maturity and change velocity
- **Integration Hooks** - AI agents understand file purpose automatically
- **Fractal Coordination** - Files self-identify their role in the system

---

## 🏗️ OmniTag Structure

### Complete Tag Header Format (Markdown)

```markdown
<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: <domain>.<category>.<name>                                     ║
║ TYPE: <file-type>                                                       ║
║ STATUS: <lifecycle-status>                                              ║
║ VERSION: <semver>                                                       ║
║ TAGS: [tag1, tag2, tag3, ...]                                           ║
║ CONTEXT: <fractal-context-level>                                        ║
║ AGENTS: [agent1, agent2, ...]                                           ║
║ DEPS: [dependency1, dependency2, ...]                                   ║
║ INTEGRATIONS: [system1, system2, ...]                                   ║
║ CREATED: <YYYY-MM-DD>                                                   ║
║ UPDATED: <YYYY-MM-DD>                                                   ║
║ AUTHOR: <author-name>                                                   ║
║ STABILITY: <stability-index>                                            ║
╚══════════════════════════════════════════════════════════════════════════╝
-->
```

### Python File Header Format

```python
"""
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.core.orchestrator                                        ║
║ TYPE: Python Module                                                     ║
║ STATUS: Production                                                      ║
║ VERSION: 2.0.0                                                          ║
║ TAGS: [orchestration, multi-agent, ollama, chatdev, ai-core]           ║
║ CONTEXT: Σ∞ (Global Orchestration Layer)                               ║
║ AGENTS: [ClaudeCode, ChatDev, OllamaModels]                            ║
║ DEPS: [ollama, requests, knowledge-base.yaml]                          ║
║ INTEGRATIONS: [ChatDev, Ollama-API, ΞNuSyQ-Framework]                  ║
║ CREATED: 2025-10-05                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: NuSyQ Development Team                                          ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Module Description:
    [Brief description of what this module does]
"""
```

---

## 📋 Field Specifications

### 1. FILE-ID (Hierarchical Identifier)

**Format**: `<domain>.<category>.<component>.<name>`

**Purpose**: Unique identifier using dot notation for hierarchical organization

**Examples**:
```
nusyq.docs.guide.quickstart        # Documentation guide
nusyq.core.agent.chatdev           # Core agent module
nusyq.config.env.secrets           # Configuration file
nusyq.tools.analysis.quality       # Analysis tool
nusyq.docs.session.2025-10-06      # Session summary
```

**Domain**: `nusyq` (all files)

**Categories**:
- `core` - Core functionality
- `docs` - Documentation
- `config` - Configuration
- `tools` - Utilities/scripts
- `tests` - Test files
- `data` - Data files

---

### 2. TYPE (File Type)

**Values**:
- `Markdown Document`
- `Python Module`
- `Python Script`
- `YAML Config`
- `JSON Config`
- `PowerShell Script`

---

### 3. STATUS (Lifecycle)

**Values**:
- `Draft` → `Review` → `Active` → `Production`
- `Deprecated` → `Archived`
- `Experimental`

---

### 4. VERSION (Semantic)

**Format**: `MAJOR.MINOR.PATCH`

---

### 5. TAGS (Keywords)

**Categories**:
- **Functional**: `orchestration`, `ai-agent`, `llm-integration`, `ollama`, `chatdev`
- **Domain**: `documentation`, `configuration`, `automation`, `validation`
- **Technical**: `multi-agent`, `offline-capable`, `symbolic-protocol`, `fractal-coordination`
- **Workflow**: `quick-start`, `troubleshooting`, `reference`, `tutorial`
- **Priority**: `essential`, `recommended`, `advanced`, `historical`

---

### 6. CONTEXT (Fractal Level)

**Values**:
- `Σ∞` - Global Orchestration Layer
- `Σ0` - System Layer
- `Σ1` - Component Layer
- `Σ2` - Feature Layer
- `Σ3` - Detail Layer
- `Σ∆` - Meta Layer

---

### 7. AGENTS (AI Compatibility)

**Values**:
- `ClaudeCode`, `ChatDev`, `ChatDevCEO`, `ChatDevCTO`, `ChatDevProgrammer`
- `OllamaQwen14b`, `OllamaQwen7b`, `OllamaCodeLlama`, `OllamaGemma`
- `ContinueDev`, `GitHubCopilot`
- `AllAgents`

---

### 8. DEPS (Dependencies)

**Format**: `[file1, package1, system1]`

---

### 9. INTEGRATIONS (Systems)

**Values**: `Ollama-API`, `ChatDev`, `ΞNuSyQ-Framework`, `Continue-Dev`, `VS-Code`, `Git`

---

### 10. CREATED / UPDATED

**Format**: `YYYY-MM-DD`

---

### 11. AUTHOR

**Values**: `NuSyQ Development Team`, `Claude Code`, `KiloMusician`, `Claude Code + KiloMusician`

---

### 12. STABILITY

**Values**: `Experimental`, `Low`, `Medium`, `High`, `Locked`

---

## 🎨 Complete Examples

### Documentation File

```markdown
<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.guide.multi-agent-orchestration                     ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [orchestration, multi-agent, documentation, essential, workflows] ║
║ CONTEXT: Σ∞ (Global Orchestration Layer)                               ║
║ AGENTS: [AllAgents, ClaudeCode, ChatDev]                               ║
║ DEPS: [NuSyQ_Root_README.md, knowledge-base.yaml]                                 ║
║ INTEGRATIONS: [ΞNuSyQ-Framework, Ollama-API, ChatDev]                  ║
║ CREATED: 2025-10-06                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code + KiloMusician                                      ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# Multi-Agent AI Orchestration Strategy
...
```

### Python Module

```python
"""
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.core.chatdev.orchestrator                               ║
║ TYPE: Python Module                                                     ║
║ STATUS: Production                                                      ║
║ VERSION: 2.0.0                                                          ║
║ TAGS: [chatdev, orchestration, ollama, ai-agent, symbolic-protocol]    ║
║ CONTEXT: Σ1 (Component Layer)                                          ║
║ AGENTS: [ClaudeCode, ChatDev, OllamaModels]                            ║
║ DEPS: [ollama, requests, ChatDev/*, knowledge-base.yaml]               ║
║ INTEGRATIONS: [Ollama-API, ChatDev, ΞNuSyQ-Framework]                  ║
║ CREATED: 2025-10-05                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code + KiloMusician                                      ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝

Module: NuSyQ-ChatDev Integration
"""
```

---

## 🔍 Search Patterns

```bash
# Find by tag
grep -r "TAGS:.*orchestration" .

# Find by context
grep -r "CONTEXT: Σ∞" .

# Find by agent
grep -r "AGENTS:.*ChatDev" .

# Find by status
grep -r "STATUS: Production" .
```

---

## 🛠️ Tooling

### Validation Script
```bash
python scripts/validate_omnitags.py
```

### Search Utility
```bash
python scripts/search_tags.py --tag orchestration
python scripts/search_tags.py --context "Σ∞"
```

---

## 🚀 Rollout Plan

### Phase 1: Specification ✓
- [x] Define OmniTag structure
- [x] Create specification

### Phase 2: Documentation (IN PROGRESS)
- [ ] Tag all docs/ files
- [ ] Update INDEX.md with tags

### Phase 3: Code
- [ ] Tag all .py files
- [ ] Tag config files

### Phase 4: Automation
- [ ] Create validation tools
- [ ] Create search utilities

---

**Version**: 1.0.0
**Status**: Active Standard ✓
**Maintained By**: Claude Code + KiloMusician
