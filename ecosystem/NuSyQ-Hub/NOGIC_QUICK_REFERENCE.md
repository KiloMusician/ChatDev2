# 🎨 Nogic Quick Reference Card

**Print this! Keep it handy!**

---

## 🚀 Getting Started (60 seconds)

```python
# 1. Import the integration
from src.integrations import NogicBridge, NogicQuestIntegration

# 2. Open visualizer
ng = NogicBridge()
ng.open_visualizer()

# 3. Analyze architecture
with NogicQuestIntegration() as nqi:
    analysis = nqi.analyze_architecture()
    print(f"Found {analysis.total_symbols} symbols")
```

---

## 📚 Common Tasks

### Query Symbols
```python
from src.integrations import NogicBridge

with NogicBridge() as ng:
    # Find all functions
    functions = ng.query_symbols(kind="Function")
    
    # Find classes
    classes = ng.query_symbols(kind="Class")
    
    # Find by name pattern
    parse_funcs = ng.query_symbols(
        kind="Function",
        name_pattern="parse"
    )
    
    # Find in specific file
    core_symbols = ng.query_symbols(
        file_path="src/core"
    )
```

### Find Complexity Issues
```python
with NogicBridge() as ng:
    hotspots = ng.get_complexity_hotspots(threshold=10)
    for func in hotspots:
        print(f"{func['name']}: {func['call_count']} calls")
```

### Get Statistics
```python
with NogicBridge() as ng:
    stats = ng.get_statistics()
    # Returns: total_symbols, total_files, symbols_by_kind, etc.
    print(f"Total symbols: {stats['total_symbols']}")
```

### Run Full Analysis
```python
from src.integrations import NogicQuestIntegration

with NogicQuestIntegration() as nqi:
    analysis = nqi.analyze_architecture()
    
    # Access results
    print(f"High complexity: {len(analysis.high_complexity_functions)}")
    print(f"Cycles: {len(analysis.cyclic_dependencies)}")
    print(f"Dead code: {len(analysis.orphaned_symbols)}")
    
    # Generate quests
    quests = analysis.to_quest_items()
    
    # Save results
    nqi.save_analysis(analysis)
```

### Create Board
```python
ng = NogicBridge()
ng.create_board("My Architecture Review")
ng.add_to_board("src/core/orchestration")
ng.open_visualizer()
```

### Monitor Changes
```python
from src.integrations import NogicBridge

ng = NogicBridge()
ng.start_watch()  # Auto-sync as you code
ng.open_visualizer()
```

---

## 🎯 Symbol Kinds

```
FUNCTION      →  Functions, methods
CLASS         →  Classes
INTERFACE     →  Interfaces, protocols
TYPE          →  Type aliases
ENUM          →  Enumerations
VARIABLE      →  Variables, properties
CONSTANT      →  Constants
IMPORT        →  Imports, imports
```

---

## 📊 Available Commands

| Command | Use Case |
|---------|----------|
| `open_visualizer()` | Open Nogic in VS Code |
| `add_to_board(path)` | Add file/folder to board |
| `create_board(name)` | Create new board |
| `start_watch()` | Auto-sync on changes |
| `reindex_workspace()` | Reindex codebase |
| `get_files()` | List all files |
| `query_symbols()` | Find code symbols |
| `get_imports()` | Get import relationships |
| `get_calls()` | Get function calls |
| `get_statistics()` | Get graph stats |
| `get_complexity_hotspots()` | Find complex areas |

---

## 🔍 Query Examples

```python
# All Python files
files = ng.get_files(language="python")

# Find functions starting with "test_"
tests = ng.query_symbols(
    kind="Function",
    name_pattern="test_*"
)

# Find imports
imports = ng.get_imports()

# Find calls from a specific function
calls = ng.get_calls(from_symbol="orchestrate")

# Find class inheritance
inheritance = ng.get_inheritance_chain("BaseClass")
```

---

## 🧠 Architecture Analysis Results

```python
analysis.total_symbols           # int
analysis.total_files             # int
analysis.symbols_by_kind         # dict
analysis.high_complexity_functions  # list
analysis.cyclic_dependencies     # list
analysis.orphaned_symbols        # list of Symbol
analysis.recommendations         # list of strings
```

---

## 🎨 Visualization Tips

| Task | Steps |
|------|-------|
| **Explore Code** | Open Nogic → Click "Index Workspace" → Click a node |
| **Focus Area** | Right-click node → "Inspect Mode" → Explore connections |
| **Create Board** | Click "+" → Name board → Right-click files → "Add to Board" |
| **Search Symbol** | Ctrl/Cmd+K → Type name → Click to focus |
| **Watch Changes** | Ctrl/Cmd+Shift+P → "Nogic: Toggle Watch" → Live updates |

---

## ⚡ Performance Tips

1. **Use context managers** - Auto-closes database
   ```python
   with NogicBridge() as ng:  # Good!
       symbols = ng.query_symbols()
   # Connection closed automatically
   ```

2. **Filter early** - Reduce data transfers
   ```python
   # Better
   ng.query_symbols(kind="Function", file_path="src/core")
   
   # vs worse
   all_symbols = ng.query_symbols()
   [s for s in all_symbols if s.kind == "Function"]
   ```

3. **Cache results** - Reuse query results
   ```python
   symbols = ng.query_symbols()  # Query once
   # Process multiple times
   functions = [s for s in symbols if s.kind == "Function"]
   classes = [s for s in symbols if s.kind == "Class"]
   ```

4. **Batch operations** - Don't hold connection open
   ```python
   # Do this
   with NogicBridge() as ng:
       hotspots = ng.get_complexity_hotspots()
   analyze(hotspots)  # Analyze outside connection
   
   # Not this
   with NogicBridge() as ng:
       hotspots = ng.get_complexity_hotspots()
       slow_analysis(hotspots)  # Slow operation
   ```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Database not found"** | Run `ng.open_visualizer()` then `ng.reindex_workspace()` |
| **"No symbols returned"** | Workspace not indexed yet, wait 30s after reindex |
| **"Connection locked"** | Close previous connections: use `with` statements |
| **Performance slow** | Check workspace size, reduce query scope |
| **Extension not found** | `code --install-extension nogic.nogic` |

---

## 📦 Module Imports

```python
# Everything you need
from src.integrations import (
    NogicBridge,
    NogicQuestIntegration,
    Symbol,
    SymbolKind,
)

# Low-level control
from src.integrations.nogic_bridge import NogicBridge

# Analysis + quests
from src.integrations.nogic_quest_integration import NogicQuestIntegration

# VS Code integration
from src.integrations.nogic_vscode_bridge import (
    NogicVSCodeBridge,
    NogicTaskRunner,
)
```

---

## 🎓 Examples & Docs

| Resource | Location |
|----------|----------|
| **Usage Guide** | `NOGIC_INTEGRATION_GUIDE.md` |
| **Investigation** | `NOGIC_INVESTIGATION_REPORT.md` |
| **Summary** | `NOGIC_INTEGRATION_SUMMARY.md` |
| **API Docs** | Docstrings in module files |
| **Official Docs** | https://nogic.dev |

---

## 🚦 Decision Tree

```
Need to...

├─ VISUALIZE CODE?
│  └─→ ng.open_visualizer()
│
├─ QUERY CODE STRUCTURE?
│  └─→ ng.query_symbols(kind=...)
│
├─ FIND COMPLEXITY?
│  └─→ ng.get_complexity_hotspots()
│
├─ ANALYZE ARCHITECTURE?
│  └─→ nqi.analyze_architecture()
│
├─ GENERATE QUESTS?
│  └─→ analysis.to_quest_items()
│
├─ EXPORT DATA?
│  └─→ ng.query_symbols() → json.dump()
│
└─ CUSTOM ANALYSIS?
   └─→ Extend NogicQuestIntegration
```

---

## 💡 Pro Tips

1. **Combine queries for insights:**
   ```python
   symbols = ng.query_symbols()
   hotspots = ng.get_complexity_hotspots()
   undocumented = [s for s in symbols if not s.documentation]
   ```

2. **Export for visualization:**
   ```python
   import json
   symbols = ng.query_symbols()
   json.dump([s.to_dict() for s in symbols], open("symbols.json", "w"))
   ```

3. **Generate custom quests:**
   ```python
   analysis = nqi.analyze_architecture()
   quests = analysis.to_quest_items()
   # Customize and add to quest system
   ```

4. **Schedule analysis:**
   ```python
   # In cron/scheduler
   daily_analysis = NogicQuestIntegration().analyze_architecture()
   save_to_reports(daily_analysis)
   ```

---

## 📞 Quick Links

- **GitHub:** https://github.com/nogicdev/extension
- **Discord:** https://discord.gg/25bdAnuB4Y
- **Website:** https://nogic.dev
- **Support:** support@nogic.dev

---

**Pro Tip:** Bookmark this page and `NOGIC_INTEGRATION_GUIDE.md` for quick reference!

**Last Updated:** February 15, 2026  
**Version:** 0.1.0

