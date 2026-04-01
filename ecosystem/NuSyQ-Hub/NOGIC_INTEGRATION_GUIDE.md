# 🎨 Nogic Integration Guide for NuSyQ-Hub

**Version:** 0.1.0  
**Last Updated:** February 15, 2026  
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Usage Patterns](#usage-patterns)
4. [Advanced Features](#advanced-features)
5. [Integration Points](#integration-points)
6. [Troubleshooting](#troubleshooting)
7. [Reference](#reference)

---

## Quick Start

### 1. Open Nogic Visualizer

**Via VS Code:**
```
Ctrl+Shift+P → "Nogic: Open Visualizer"
```

**Via Python:**
```python
from src.integrations import NogicBridge

ng = NogicBridge()
ng.open_visualizer()
```

### 2. Index Your Workspace

In Nogic UI: Click "Index Workspace" to scan and parse your codebase.

**Via Python:**
```python
ng.reindex_workspace()
```

### 3. Run Architecture Analysis

```python
from src.integrations import NogicQuestIntegration

with NogicQuestIntegration() as nqi:
    analysis = nqi.analyze_architecture()
    nqi.save_analysis(analysis)
    print(f"Found {analysis.total_symbols} symbols")
```

### 4. Query the Code Graph

```python
from src.integrations import NogicBridge

with NogicBridge() as ng:
    # Find all functions
    functions = ng.query_symbols(kind="Function")
    
    # Find high-complexity areas
    hotspots = ng.get_complexity_hotspots(threshold=10)
    
    # Get statistics
    stats = ng.get_statistics()
    print(f"Total files: {stats['total_files']}")
    print(f"Total symbols: {stats['total_symbols']}")
```

---

## Architecture

### Module Hierarchy

```
src/integrations/
├── __init__.py                    # Package exports
├── nogic_bridge.py               # Low-level API (91 KB)
│   ├── NogicBridge              # Main class
│   ├── Symbol, CodeFile classes
│   └── Direct SQLite access
├── nogic_quest_integration.py    # Quest system (63 KB)
│   ├── NogicQuestIntegration
│   ├── ArchitectureAnalysis
│   └── Quest generation
└── nogic_vscode_bridge.py        # VS Code integration (58 KB)
    ├── NogicVSCodeBridge
    ├── NogicTaskRunner
    └── NogicWebviewMessenger
```

### Data Flow

```
VS Code Nogic Extension
    ↓
    ├─→ FileWatcher (watches your code)
    ├─→ CodeParser (extracts symbols)
    ├─→ SQLite Database (.nogic/db.sqlite)
    │   └─→ NogicBridge (Python reads this)
    │       └─→ NogicQuestIntegration (analyzes & generates quests)
    │           └─→ NuSyQ-Hub Quest System
    └─→ Webview UI (React visualization)
```

---

## Usage Patterns

### Pattern 1: Graph Queries (Simple)

```python
from src.integrations import NogicBridge

with NogicBridge() as ng:
    # Get all files
    files = ng.get_files(language="python")
    print(f"Python files: {len(files)}")
    
    # Query symbols
    classes = ng.query_symbols(kind="Class")
    print(f"Classes: {len(classes)}")
    
    # Find functions containing "parse"
    parse_funcs = ng.query_symbols(
        kind="Function",
        name_pattern="parse"
    )
    for func in parse_funcs:
        print(f"  {func.name} at {func.file_id}:{func.line}")
```

### Pattern 2: Architecture Analysis (Medium)

```python
from src.integrations import NogicQuestIntegration

with NogicQuestIntegration() as nqi:
    # Run full analysis
    analysis = nqi.analyze_architecture()
    
    # Review results
    print(f"High complexity: {len(analysis.high_complexity_functions)}")
    print(f"Cyclic deps: {len(analysis.cyclic_dependencies)}")
    print(f"Dead code: {len(analysis.orphaned_symbols)}")
    
    # Generate quests
    quests = analysis.to_quest_items()
    for quest in quests[:5]:
        print(f"  [{quest['priority']}] {quest['title']}")
    
    # Create dashboard
    dashboard = nqi.create_dashboard()
    print(f"Dashboard sections: {len(dashboard['sections'])}")
```

### Pattern 3: Quest Integration (Advanced)

```python
from src.integrations import NogicQuestIntegration
from src.Rosetta_Quest_System.quest_system import QuestLog

with NogicQuestIntegration() as nqi:
    # Analyze architecture
    analysis = nqi.analyze_architecture()
    quests = analysis.to_quest_items()
    
    # Add to quest system
    quest_log = QuestLog()
    for quest in quests:
        quest_log.add_quest({
            "title": quest["title"],
            "description": quest["description"],
            "priority": quest["priority"],
            "tags": quest["tags"],
            "source": "nogic_architecture_analysis",
        })
    
    quest_log.save()
```

### Pattern 4: Real-Time Monitoring (Advanced)

```python
from src.integrations import NogicBridge
import time

# Monitor code complexity changes
with NogicBridge() as ng:
    while True:
        hotspots = ng.get_complexity_hotspots(threshold=15)
        print(f"[{time.time()}] Complexity hotspots: {len(hotspots)}")
        
        if len(hotspots) > 5:
            print("⚠️  High complexity detected!")
            for spot in hotspots[:3]:
                print(f"  - {spot['name']}: {spot['call_count']} calls")
        
        time.sleep(60)  # Check every minute
```

### Pattern 5: Custom Visualizations

```python
from src.integrations import NogicBridge
import json

with NogicBridge() as ng:
    # Export entire graph as JSON
    graph = {
        "nodes": [],
        "edges": [],
    }
    
    # Nodes from symbols
    for symbol in ng.query_symbols():
        graph["nodes"].append({
            "id": symbol.id,
            "label": symbol.name,
            "type": symbol.kind,
        })
    
    # Edges from calls
    for call in ng.get_calls():
        graph["edges"].append({
            "source": call["from_id"],
            "target": call["to_id"],
        })
    
    # Save for custom visualization
    with open("graph.json", "w") as f:
        json.dump(graph, f)
```

---

## Advanced Features

### 1. Database Direct Access

```python
from src.integrations import NogicBridge

with NogicBridge() as ng:
    conn = ng._get_connection()
    
    # Raw SQL queries
    cursor = conn.execute("""
        SELECT s.name, COUNT(c.id) as call_count
        FROM symbols s
        LEFT JOIN calls c ON s.id = c.from_id
        WHERE s.kind = 'Function'
        GROUP BY s.id
        ORDER BY call_count DESC
        LIMIT 10
    """)
    
    for row in cursor:
        print(f"{row[0]}: {row[1]} calls")
```

### 2. Watch Mode for Live Updates

```python
from src.integrations import NogicBridge

ng = NogicBridge()
ng.start_watch()  # Auto-sync on file changes
ng.open_visualizer()

# Your code changes will automatically update the visualization
```

### 3. Board Management

```python
from src.integrations import NogicBridge

ng = NogicBridge()

# Create board
ng.create_board("My Architecture Review")

# Add components to board
ng.add_to_board("src/core/orchestration")
ng.add_to_board("src/healing")

ng.open_visualizer()
```

### 4. Custom Analysis Pipeline

```python
from src.integrations import NogicQuestIntegration
from pathlib import Path

class CustomAnalyzer(NogicQuestIntegration):
    """Custom analyzer with domain-specific metrics."""
    
    def find_test_coverage_gaps(self):
        """Find untested functions."""
        symbols = self.nogic.query_symbols(kind="Function")
        
        gaps = []
        for symbol in symbols:
            # Check if there's a corresponding test
            test_symbol = self.nogic.query_symbols(
                name_pattern=f"test_{symbol.name}"
            )
            if not test_symbol:
                gaps.append(symbol)
        
        return gaps
    
    def find_documentation_gaps(self):
        """Find undocumented symbols."""
        symbols = self.nogic.query_symbols()
        return [s for s in symbols if not s.documentation]

# Use it
analyzer = CustomAnalyzer()
untested = analyzer.find_test_coverage_gaps()
undocumented = analyzer.find_documentation_gaps()
print(f"Untested functions: {len(untested)}")
print(f"Undocumented symbols: {len(undocumented)}")
```

---

## Integration Points

### 1. Quest System

```python
# In src/Rosetta_Quest_System/
from src.integrations import NogicQuestIntegration

# Auto-generate quests from architecture analysis
analysis = NogicQuestIntegration().analyze_architecture()
quests = analysis.to_quest_items()
# Add to quest_log.jsonl
```

### 2. Multi-AI Orchestrator

```python
# In src/orchestration/
from src.integrations import NogicBridge

class ArchitectureAnalysisTask:
    def execute(self):
        with NogicBridge() as ng:
            stats = ng.get_statistics()
            hotspots = ng.get_complexity_hotspots()
            # Route analysis to Ollama or ChatDev
```

### 3. Dashboard API

```python
# In src/web/dashboard_api.py
from src.integrations import NogicQuestIntegration

@app.route("/api/architecture")
def get_architecture():
    with NogicQuestIntegration() as nqi:
        dashboard = nqi.create_dashboard()
        return dashboard
```

### 4. VS Code Tasks

Add to `.vscode/tasks.json`:
```json
{
  "label": "🎨 Architecture Analysis",
  "type": "shell",
  "command": "${command:python.interpreterPath}",
  "args": ["-m", "src.integrations.nogic_quest_integration"],
  "group": {"kind": "test"}
}
```

---

## Troubleshooting

### Issue: "Nogic database not found"

**Cause:** Database doesn't exist or Nogic hasn't indexed yet.

**Solution:**
```python
from src.integrations import NogicBridge

ng = NogicBridge()
ng.open_visualizer()  # Opens Nogic
ng.reindex_workspace()  # Indexes the workspace
# Wait 30 seconds for indexing
```

### Issue: "Cannot connect to Nogic extension"

**Cause:** Extension not installed or VS Code remote debugging disabled.

**Solution:**
1. Verify: `code --list-extensions | grep nogic` (should show `nogic.nogic`)
2. Reinstall if missing: `code --install-extension nogic.nogic`
3. Restart VS Code

### Issue: "Query returns no results"

**Cause:** Database empty (workspace not indexed).

**Solution:**
```python
from src.integrations import NogicBridge

ng = NogicBridge()
# 1. Check if files are indexed
files = ng.get_files()
if not files:
    print("No files indexed yet")
    ng.reindex_workspace()
    # Wait for reindex to complete
```

### Issue: "SQLite database locked"

**Cause:** Multiple processes accessing database simultaneously.

**Solution:**
```python
# Don't hold connection open during long operations
with NogicBridge() as ng:  # Closes connection on exit
    symbols = ng.query_symbols()
    # Process symbols
# Connection closed here
```

---

## Reference

### Class: NogicBridge

**Methods:**
- `open_visualizer()` → Open VS Code panel
- `add_to_board(path)` → Add file/folder to board
- `create_board(name)` → Create new board
- `start_watch()` → Start watch mode
- `reindex_workspace()` → Reindex codebase
- `get_files()` → List all files
- `query_symbols()` → Query code symbols
- `get_imports()` → Get import relationships
- `get_calls()` → Get function calls
- `get_inheritance_chain()` → Get class inheritance
- `get_statistics()` → Get graph statistics
- `get_complexity_hotspots()` → Find high-complexity areas

### Class: NogicQuestIntegration

**Methods:**
- `analyze_architecture()` → Full architecture analysis
- `create_dashboard()` → Create visualization dashboard
- `save_analysis()` → Save results to file
- `board_from_analysis()` → Create board with analysis results
- `open_visualizer()` → Open Nogic in VS Code

### Class: NogicVSCodeBridge

**Methods:**
- `get_command(operation)` → Get VS Code command ID
- `register_message_handler()` → Register webview handler
- `handle_message()` → Process webview message
- `record_command()` → Audit trail

### Enums

**SymbolKind:**
- `FUNCTION`, `CLASS`, `INTERFACE`, `TYPE`, `ENUM`, `VARIABLE`, `CONSTANT`, `IMPORT`

**RelationType:**
- `IMPORTS`, `CALLS`, `INHERITS`, `IMPLEMENTS`, `TYPE_USES`

---

## Code Examples Repository

See the `examples/` directory for:
- `nogic_basic_queries.py` - Simple symbol queries
- `nogic_architecture_dashboard.py` - Create dashboards
- `nogic_quest_generation.py` - Generate quests
- `nogic_multi_ai_analysis.py` - AI-powered analysis

---

## Performance Notes

### Database Size
- Typical projects: 100MB-500MB
- All in memory (WASM SQLite)
- No network calls

### Query Performance
- Symbol queries: <100ms
- Call graph: <500ms
- Full reindex: 5-30 seconds

### Best Practices
1. Use context managers (`with ... as`) to free resources
2. Query once, process multiple times
3. Filter queries early (name_pattern, language)
4. Don't hold connections open during slow operations

---

## 🎓 Learn More

**Official Resources:**
- Website: https://nogic.dev
- GitHub: https://github.com/nogicdev/extension
- Discord: https://discord.gg/25bdAnuB4Y

**NuSyQ-Hub Integration:**
- Check `NOGIC_INVESTIGATION_REPORT.md` for architecture details
- See `src/integrations/` for example usages
- Review `.vscode/tasks.json` for task definitions

---

**Last Updated:** February 15, 2026  
**Maintained By:** NuSyQ-Hub AI Council  
**Status:** ✅ Production Ready (v0.1.0)

