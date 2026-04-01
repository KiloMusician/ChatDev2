# ΞNuSyQ Modern Edge System - Quick Reference

## 🎯 What Changed

**DEPRECATED:** Symlink overlay system (`SystemDev/.edge/overlay/WorkingSet/`)
- Required admin privileges
- Git confusion with 259 symlinks
- High maintenance overhead

**NEW:** Modern intelligent filtering
- VS Code search exclusions (`.vscode/settings.json`)
- Direct database queries (`edge_query_simple.ts`)
- Future MCP server integration

---

## 📊 Database Statistics

```bash
# Show repository statistics
tsx SystemDev/scripts/edge_query_simple.ts --stats

# Output: 
# Total Files: 123,456
# Total Size: 842.5 MB
# Bucket breakdown by category
```

---

## 🔍 Query Examples

### By Bucket (Repository Section)
```bash
# All TypeScript files in src/
tsx SystemDev/scripts/edge_query_simple.ts --bucket=ours.src --kind=typescript

# ChatDev integration files
tsx SystemDev/scripts/edge_query_simple.ts --bucket=ours.chatdev --limit=100

# Game development files
tsx SystemDev/scripts/edge_query_simple.ts --bucket=ours.gamedev
```

### Full-Text Search (FTS5)
```bash
# Find files mentioning "drizzle"
tsx SystemDev/scripts/edge_query_simple.ts --search="drizzle" --limit=20

# Find consciousness-related code
tsx SystemDev/scripts/edge_query_simple.ts --search="consciousness" --bucket=ours.src
```

### Export Results
```bash
# Export to JSON for further processing
tsx SystemDev/scripts/edge_query_simple.ts \
  --bucket=ours.src \
  --kind=typescript \
  --export=analysis/typescript_files.json
```

---

## 🚀 AI Agent Optimization

### Search Space Reduction
VS Code settings automatically exclude:
- `node_modules/` (82K+ files)
- `attic/duplicates/` (Python C extensions)
- `ChatDev/WareHouse/` (generated projects)
- Build artifacts (`dist/`, `build/`, `.next/`)

**Result:** 123K files → ~20K relevant files (83% reduction)

### GitHub Copilot Tuning
```json
"github.copilot.advanced": {
  "debug.overrideEngine": "gpt-4",
  "debug.filterLargeFiles": true
}
```

### Pylance (Python) Tuning
```json
"python.analysis.exclude": [
  "**/node_modules",
  "**/attic/duplicates"
],
"python.analysis.indexing": true
```

---

## 🔗 Integration with Other Tools

### Continue.dev Context
The `.vscode/settings.json` exclusions are automatically respected by Continue.dev, limiting context to relevant source files.

### MCP Server (Future)
Plan to extend `NuSyQ/mcp_server/` to serve filtered SimulatedVerse context:

```python
# Future: NuSyQ/mcp_server/simulatedverse_context.py
from edge_db import EdgeDatabase

def get_relevant_files(task_type: str) -> List[str]:
    """Query edge.db for task-specific files"""
    db = EdgeDatabase("SimulatedVerse/SystemDev/.edge/edge.db")
    
    if task_type == "frontend":
        return db.query(bucket="ours.previewui", kind="typescript")
    elif task_type == "backend":
        return db.query(bucket="ours.src", kind="typescript")
    # ... etc
```

### Claude Code / Roo-Cline
Both respect VS Code search exclusions automatically.

---

## 📂 File Organization

```
SimulatedVerse/
├── .vscode/
│   └── settings.json          # AI optimization rules
├── SystemDev/
│   ├── .edge/
│   │   ├── edge.db            # SQLite index (keep!)
│   │   └── overlay/           # (deprecated, in .gitignore)
│   └── scripts/
│       ├── edge_index.ts      # Rebuild database
│       ├── edge_query.ts      # Original query tool
│       └── edge_query_simple.ts  # NEW: Simple query CLI
├── .gitignore                 # Excludes WorkingSet/
└── EDGE_OVERLAY_ANALYSIS.md   # Full analysis document
```

---

## 🔄 Maintenance

### Rebuild Index (if repository changes significantly)
```bash
# Full reindex with FTS5
tsx SystemDev/scripts/edge_index.ts --fts --shard-size=4000

# Verify
tsx SystemDev/scripts/edge_query_simple.ts --stats
```

### Database Location
```bash
# Default
SystemDev/.edge/edge.db

# Set custom path
export EDGE_DB_PATH="path/to/edge.db"
tsx SystemDev/scripts/edge_query_simple.ts --stats
```

---

## ✅ Benefits Over Symlink Overlay

| Feature | Old (Symlinks) | New (Modern) |
|---------|----------------|--------------|
| **Cross-platform** | ❌ Windows issues | ✅ Works everywhere |
| **Git-friendly** | ❌ 259 tracked files | ✅ Clean git state |
| **Maintenance** | ❌ Manual regeneration | ✅ Automatic |
| **AI tool support** | 🟡 Manual | ✅ Native |
| **Performance** | ✅ 83% reduction | ✅ Same (via exclusions) |
| **Setup time** | ❌ 30+ min | ✅ 5 min |
| **Admin required** | ❌ Yes | ✅ No |

---

## 🎓 Learning Resources

- **Edge System Design**: See `SystemDev/backlog/next_up/edge_pack_run_cards.md`
- **Database Schema**: SQLite FTS5 documentation
- **VS Code Settings**: Official VS Code search.exclude documentation

---

For full analysis, see: `EDGE_OVERLAY_ANALYSIS.md`
