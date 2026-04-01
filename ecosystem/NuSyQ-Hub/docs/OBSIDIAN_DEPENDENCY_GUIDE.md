# 🧠 Obsidian Dependency Graph Integration Guide

**Purpose:** Visualize NuSyQ 3-repo ecosystem architecture in Obsidian with
interactive dependency graphs.  
**Generated:** 2026-01-05  
**Status:** Ready for Obsidian import

---

## 📂 Setup Instructions

### Prerequisites

- ✅ Obsidian vault pointing to `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\docs\`
- ✅ Obsidian Graph View plugin (built-in, may need enabling)
- ✅ Dependency analysis files (`dependency-analysis.json`,
  `dependency-graph.mmd`)

### Step 1: Enable Graph View Plugin

1. Open Obsidian → **Settings** → **Community Plugins**
2. Search for "Graph View" (built-in)
3. Enable if disabled
4. **Ctrl+Shift+G** opens the graph

### Step 2: Create Core Dependency Index

The following markdown template enables Obsidian graph linking:

```markdown
# NuSyQ Dependency Graph

## Critical Files (High Impact)

### Orchestration Layer

- [[multi_ai_orchestrator.py]] - Coordinates all AI systems

  - Depends on: [[ai_system_base.py]], [[consciousness_bridge.py]]
  - Depended by: [[start_nusyq.py]], [[agent_task_router.py]]
  - Complexity: 82/100

- [[start_nusyq.py]] - Main spine entry point
  - Depends on: [[config_loader.py]], [[terminal_router.py]]
  - Depended by: CLI, all workflows
  - Complexity: 69/100
```

### Step 3: Import JSON Data

Parse `dependency-analysis.json` and create wiki-link markdown files:

**Recommended Tool:** Python script to generate markdown from JSON

```python
import json

with open('docs/dependency-analysis/dependency-analysis.json') as f:
    deps = json.load(f)

# Create markdown files for each critical file
for file_info in deps['critical_files']:
    filename = file_info['name'].replace('/', '_').replace('\\', '_')
    with open(f'docs/critical-files/{filename}.md', 'w') as mf:
        mf.write(f"# {filename}\n\n")
        mf.write(f"- **Location:** {file_info['path']}\n")
        mf.write(f"- **Complexity:** {file_info['complexity']}/100\n")
        mf.write(f"- **Fan-in:** {file_info['fan_in']}\n")
        mf.write(f"- **Fan-out:** {file_info['fan_out']}\n\n")

        if file_info.get('imports'):
            mf.write("## Dependencies\n")
            for dep in file_info['imports']:
                safe_dep = dep.replace('/', '_').replace('\\', '_')
                mf.write(f"- [[{safe_dep}]]\n")

        if file_info.get('imported_by'):
            mf.write("\n## Dependents\n")
            for dep in file_info['imported_by']:
                safe_dep = dep.replace('/', '_').replace('\\', '_')
                mf.write(f"- [[{safe_dep}]]\n")
```

---

## 🔍 Key Files to Monitor in Obsidian

### Central Hub Files (Highest Impact)

These files affect the most other files and should be carefully maintained:

| File                       | Location             | Fan-In | Fan-Out | Complexity | Status      |
| -------------------------- | -------------------- | ------ | ------- | ---------- | ----------- |
| `multi_ai_orchestrator.py` | `src/orchestration/` | 8+     | 16+     | 82/100     | 🔴 CRITICAL |
| `start_nusyq.py`           | `scripts/`           | 5+     | 15+     | 69/100     | 🔴 CRITICAL |
| `agent_task_router.py`     | `src/tools/`         | 10+    | 8+      | 60/100     | 🔴 CRITICAL |
| `terminal_router.py`       | `src/output/`        | 12+    | 4+      | 35/100     | 🟠 HIGH     |
| `consciousness_bridge.py`  | `src/integration/`   | 6+     | 8+      | 50/100     | 🟠 HIGH     |

### Create Obsidian Links

In your notes, use wiki-link syntax:

```markdown
The [[multi_ai_orchestrator.py]] coordinates 16+ downstream dependencies. Review
this file before making breaking changes to AI system interfaces.

See also: [[start_nusyq.py]], [[agent_task_router.py]]
```

---

## 📊 Mermaid Diagram Integration

The generated `dependency-graph.mmd` contains the full dependency graph. To
view:

1. **In VS Code:**

   - Open `docs/dependency-analysis/dependency-graph.mmd`
   - Right-click → "Markdown Preview Mermaid Diagram Support"
   - View interactive diagram

2. **In Obsidian:**
   - Copy mermaid code into obsidian markdown block
   - Mermaid plugin (may need enabling) renders diagram

Example embed:

```markdown
# Dependency Graph

\`\`\`mermaid graph TD A[start_nusyq.py] --> B[multi_ai_orchestrator] B -->
C[agent_task_router] C --> D[Ollama Interface] \`\`\`
```

---

## 🎯 Usage Patterns in Obsidian

### Pattern 1: File Change Impact Analysis

When modifying a file, check:

1. **What it depends on:** Files you must not break in the dependency chain
2. **What depends on it:** Tests that may fail, scripts that may break
3. **Complexity:** High-complexity files need more careful testing

Example query in Obsidian:

```
Search: "Fan-in: 10+"  # Find files with 10+ dependents
```

### Pattern 2: Architecture Review

When planning refactoring:

1. Create issue note: `issues/refactor-architecture-2026-01.md`
2. Link to all affected files: `[[multi_ai_orchestrator.py]]`
3. Use graph view to visualize impact
4. Link to test files: `tests/test_orchestrator.py`

### Pattern 3: Onboarding New Developers

Create `onboarding/architecture-overview.md`:

```markdown
# NuSyQ Architecture Overview for New Developers

## Core Flow

1. Start here: [[start_nusyq.py]] (6,500 lines, all actions)
2. Entry routing: [[agent_task_router.py]] (where tasks go)
3. AI coordination: [[multi_ai_orchestrator.py]] (which AI executes)
4. Output: [[terminal_router.py]] (where results appear)

## Critical Files to Understand First

- [[orchestration/]] - System coordination
- [[consciousness_bridge.py]] - Semantic awareness
- [[config/secrets.json]] - Credentials & config

## Testing

- Start with: `tests/test_orchestrator.py`
- Then: `tests/test_routing.py`
- Finally: Integration tests in `tests/integration/`
```

---

## 📈 Graph View Tips

### 1. Filter to Critical Files Only

Obsidian Graph Settings → Filter by tag:

```
tag:critical OR tag:orchestration
```

### 2. Show 2-Hop Connections

Obsidian Graph Settings → Depth: 2  
Shows files that directly depend on/are depended on by selected file

### 3. Color Code by Type

Create tags for file categories:

- `#orchestration` - Orchestration files
- `#consciousness` - Consciousness/awareness files
- `#routing` - Routing/dispatch files
- `#config` - Configuration files
- `#critical` - High-impact files

Then in markdown front matter:

```yaml
---
tags: [critical, orchestration]
complexity: 82
fan-in: 8
fan-out: 16
---
```

---

## 🔗 Auto-Generated File Index

The dependency analyzer creates files with these naming conventions:

**Critical Files Directory:** `docs/critical-files/`

```
├── multi_ai_orchestrator.md
├── start_nusyq.md
├── agent_task_router.md
├── terminal_router.md
└── ... (477+ critical files)
```

**Dependency Report:** `docs/dependency-analysis/`

```
├── dependency-analysis.json    # Machine-readable
├── dependency-graph.mmd        # Mermaid visualization
└── circular-deps.txt           # Circular dependency report
```

**Link to These in Obsidian:**

```markdown
See [[critical-files/multi_ai_orchestrator]] for orchestration hub details.

Full dependency graph: [[dependency-graph.mmd]]

For tool reference: [[TERMINAL_ROUTING_GUIDE.md]]
```

---

## 🛠️ Maintenance

### Weekly

- Run dependency analyzer: `python src/tools/dependency_analyzer.py`
- Check for new circular dependencies
- Update Obsidian critical files if needed

### Monthly

- Review complexity scores (aim < 30 per file)
- Check for files with > 10 dependents (may need refactoring)
- Update onboarding guide

### Quarterly

- Conduct architecture review
- Plan refactoring for high-complexity files
- Review new dependencies added

---

## 📚 Related Files

- **Architecture:** [[ARCHITECTURE_MAP.md]]
- **Terminal Routing:** [[TERMINAL_ROUTING_GUIDE.md]]
- **Ecosystem Status:** [[ECOSYSTEM_VERIFICATION_REPORT.md]]
- **Dependencies:** `docs/dependency-analysis/dependency-analysis.json`

---

## 🎓 Example Obsidian Vault Structure

```
docs/
├── OBSIDIAN_DEPENDENCY_GUIDE.md (this file)
├── ARCHITECTURE_MAP.md
├── TERMINAL_ROUTING_GUIDE.md
├── ECOSYSTEM_VERIFICATION_REPORT.md
├── critical-files/
│   ├── multi_ai_orchestrator.md
│   ├── start_nusyq.md
│   ├── agent_task_router.md
│   └── ... (auto-generated from JSON)
├── dependency-analysis/
│   ├── dependency-analysis.json
│   ├── dependency-graph.mmd
│   └── circular-deps.txt
└── onboarding/
    └── architecture-overview.md
```

---

**Last Updated:** 2026-01-05  
**Audience:** Developers, architects, code reviewers  
**Obsidian Sync:** Enable for real-time graph updates
