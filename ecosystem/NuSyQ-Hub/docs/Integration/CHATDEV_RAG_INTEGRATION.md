# ChatDev RAG Integration

## Overview

Automatic indexing of completed ChatDev projects into the RAG (Retrieval-Augmented Generation) and quest systems for reuse and pattern learning.

## Feature Flag

```json
{
  "project_auto_index_enabled": {
    "description": "Auto-index completed ChatDev projects to RAG/quest system",
    "default": false,
    "dependencies": ["chatdev_running"]
  }
}
```

## How It Works

1. ChatDev completes a project generation
2. System detects completion via MCP or file watcher
3. Project artifacts are extracted:
   - Source code
   - Generated documentation
   - Conversation logs
   - Configuration files
4. Artifacts are indexed into:
   - Semantic search index
   - Pattern catalog
   - Quest knowledge base

## Indexed Artifacts

| Artifact Type | Index Location | Purpose |
|---------------|----------------|---------|
| Source code | `state/indexes/code/` | Code reuse, pattern matching |
| Docs | `state/indexes/docs/` | Documentation search |
| Patterns | `config/pattern_catalog.json` | Three-Before-New checks |

## Configuration

### Index Settings

```python
RAG_INDEX_CONFIG = {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "embedding_model": "text-embedding-ada-002",
    "index_path": "state/indexes/"
}
```

### Project Completion Detection

Projects are detected via:
- MCP server notifications
- File system watching (`NuSyQ/ChatDev/WareHouse/`)
- Manual indexing trigger

## Usage

### Manual Indexing

```bash
python scripts/start_nusyq.py index_chatdev_project --path /path/to/project
```

### Query Indexed Projects

```python
from src.tools.summary_retrieval import query_indexed_projects

results = query_indexed_projects("Python CLI with database")
```

## Related Files

- `src/tools/summary_indexer.py` - Indexing implementation
- `src/tools/summary_retrieval.py` - Index queries
- `config/feature_flags.json` - Feature configuration
