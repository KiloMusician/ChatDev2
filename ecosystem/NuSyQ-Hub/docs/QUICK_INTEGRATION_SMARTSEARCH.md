# Quick Integration: SmartSearch CLI Actions

**Objective:** Wire SmartSearch into CLI so developers can discover code patterns, dependencies, and related systems.

**Time Estimate:** 25 minutes  
**Impact:** High (enables discovery for all other integrations)

---

## Step 1: Create Search Actions Module

Create: `scripts/nusyq_actions/search_actions.py`

```python
"""Search actions — wire SmartSearch into CLI."""

from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

def handle_search_keyword(
    query: str,
    limit: int = 20,
    output_format: str = "text",
) -> dict[str, Any]:
    """Search by keyword across codebase.
    
    Usage:
        nusyq search keyword "authentication" --limit 10
        nusyq search keyword "consciousness" --format json
    """
    try:
        from src.search.smart_search import SmartSearch
        
        search = SmartSearch()
        results = search.search_keyword(query, limit=limit)
        
        if output_format == "json":
            import json
            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": [r.__dict__ if hasattr(r, "__dict__") else r for r in results],
            }
        else:
            # Text format
            lines = [f"📚 Search Results: '{query}' ({len(results)} matches)\n"]
            for i, result in enumerate(results, 1):
                if hasattr(result, "file_path"):
                    lines.append(
                        f"{i}. {result.file_path}:{getattr(result, 'line', '?')} "
                        f"— {getattr(result, 'context', '')[:60]}"
                    )
            return {
                "status": "success",
                "output": "\n".join(lines),
            }
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "suggestion": "Ensure SmartSearch index is up-to-date",
        }


def handle_search_class(
    class_name: str,
    exact: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    """Search for class definitions.
    
    Usage:
        nusyq search class "ConsciousnessBridge"
        nusyq search class "Orchestrator" --no-exact
    """
    try:
        from src.search.smart_search import SmartSearch
        
        search = SmartSearch()
        results = search.search_by_class(class_name, exact=exact)[:limit]
        
        lines = [f"🏗️  Class Definitions: '{class_name}' ({len(results)} matches)\n"]
        for i, result in enumerate(results, 1):
            if hasattr(result, "file_path"):
                lines.append(
                    f"{i}. {result.file_path}:{getattr(result, 'line', '?')}"
                )
        
        return {
            "status": "success",
            "output": "\n".join(lines),
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Class search failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


def handle_search_function(
    function_name: str,
    exact: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    """Search for function definitions.
    
    Usage:
        nusyq search function "route_task"
        nusyq search function "analyze" --no-exact
    """
    try:
        from src.search.smart_search import SmartSearch
        
        search = SmartSearch()
        results = search.search_by_function(function_name, exact=exact)[:limit]
        
        lines = [f"⚙️  Function Definitions: '{function_name}' ({len(results)} matches)\n"]
        for i, result in enumerate(results, 1):
            if hasattr(result, "file_path"):
                lines.append(
                    f"{i}. {result.file_path}:{getattr(result, 'line', '?')}"
                )
        
        return {
            "status": "success",
            "output": "\n".join(lines),
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Function search failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


def handle_search_index_health() -> dict[str, Any]:
    """Check search index health.
    
    Usage:
        nusyq search index-health
    """
    try:
        from src.search.smart_search import SmartSearch
        
        search = SmartSearch()
        health = search.get_index_health()
        stats = search.get_index_stats()
        
        return {
            "status": "success",
            "health": health,
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Index health check failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}


def handle_search_hacking_quests(
    quest_type: str = "all",
    limit: int = 10,
) -> dict[str, Any]:
    """Search for hacking game quests.
    
    Usage:
        nusyq search hacking-quests
        nusyq search hacking-quests --quest-type exploit
    """
    try:
        from src.search.smart_search import SmartSearch
        
        search = SmartSearch()
        results = search.search_hacking_quests(quest_type=quest_type, limit=limit)
        
        lines = [f"🎮 Hacking Quests: {quest_type} ({len(results)} matches)\n"]
        for i, result in enumerate(results, 1):
            if hasattr(result, "context"):
                lines.append(f"{i}. {getattr(result, 'context', '?')[:100]}")
        
        return {
            "status": "success",
            "output": "\n".join(lines),
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Hacking quest search failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
```

---

## Step 2: Wire into start_nusyq.py

Edit: `scripts/start_nusyq.py`

**Find these imports (around line 50):**

```python
from scripts.nusyq_actions.ai_actions import (
    handle_analyze,
    handle_debug,
    handle_generate,
    handle_review,
)
```

**Add after that section:**

```python
from scripts.nusyq_actions.search_actions import (
    handle_search_keyword,
    handle_search_class,
    handle_search_function,
    handle_search_index_health,
    handle_search_hacking_quests,
)
```

**Find the main argument parser (around line 500+):**

```python
parser = argparse.ArgumentParser(description="NuSyQ-Hub Orchestration System")
subparsers = parser.add_subparsers(dest="action", help="Available actions")
```

**Add search subparser after existing ones:**

```python
# Search operations
search_parser = subparsers.add_parser("search", help="Search codebase")
search_sub = search_parser.add_subparsers(dest="search_type", help="Search type")

search_keyword = search_sub.add_parser("keyword", help="Keyword search")
search_keyword.add_argument("query", help="Search query")
search_keyword.add_argument("--limit", type=int, default=20)
search_keyword.add_argument("--format", choices=["text", "json"], default="text")

search_class = search_sub.add_parser("class", help="Search classes")
search_class.add_argument("class_name", help="Class name")
search_class.add_argument("--exact", action="store_true", default=True)
search_class.add_argument("--limit", type=int, default=20)

search_func = search_sub.add_parser("function", help="Search functions")
search_func.add_argument("function_name", help="Function name")
search_func.add_argument("--exact", action="store_true", default=True)
search_func.add_argument("--limit", type=int, default=20)

search_health = search_sub.add_parser("index-health", help="Check index health")

search_hacking = search_sub.add_parser("hacking-quests", help="Search hacking quests")
search_hacking.add_argument("--quest-type", default="all", help="Quest type filter")
search_hacking.add_argument("--limit", type=int, default=10)
```

**Find the main action dispatch (around line 1000+):**

```python
elif args.action == "brief":
    result = _handle_brief(args)
elif args.action == "doctor":
    result = handle_doctor(args)
# ... more actions ...
```

**Add after existing actions:**

```python
elif args.action == "search":
    if args.search_type == "keyword":
        result = handle_search_keyword(
            args.query,
            limit=args.limit,
            output_format=args.format,
        )
    elif args.search_type == "class":
        result = handle_search_class(args.class_name, exact=args.exact, limit=args.limit)
    elif args.search_type == "function":
        result = handle_search_function(args.function_name, exact=args.exact, limit=args.limit)
    elif args.search_type == "index-health":
        result = handle_search_index_health()
    elif args.search_type == "hacking-quests":
        result = handle_search_hacking_quests(args.quest_type, limit=args.limit)
    else:
        result = {"status": "error", "error": "Unknown search type"}
```

---

## Step 3: Update Menu

Edit: `scripts/nusyq_actions/menu.py`

**Add to the menu options:**

```python
{
    "category": "Discovery",
    "actions": [
        {"command": "nusyq search keyword <term>", "description": "Search code by keyword"},
        {"command": "nusyq search class <name>", "description": "Find class definitions"},
        {"command": "nusyq search function <name>", "description": "Find function definitions"},
        {"command": "nusyq search index-health", "description": "Check search index status"},
        {"command": "nusyq search hacking-quests", "description": "Find hacking game quests"},
    ],
}
```

---

## Step 4: Test the Integration

```bash
# Test 1: Keyword search
python scripts/start_nusyq.py search keyword "consciousness"

# Test 2: Class search
python scripts/start_nusyq.py search class "ConsciousnessBridge"

# Test 3: Function search
python scripts/start_nusyq.py search function "route_task"

# Test 4: Index health
python scripts/start_nusyq.py search index-health

# Test 5: JSON output
python scripts/start_nusyq.py search keyword "orchestrator" --format json
```

---

## Step 5: Integrate with Quest Logging (Add Later)

Once this works, enhance `shared.py` to auto-log searches:

```python
# In emit_receipt()
if action_name == "search":
    quest_engine.add_quest(
        title=f"Searched: {args.query or args.class_name or args.function_name}",
        description=f"Search type: {args.search_type}",
        status="complete",
        metadata={"result_count": result.get("count", 0)},
    )
```

---

## Success Criteria

✅ `nusyq search keyword "term"` returns results  
✅ `nusyq search class "Name"` finds classes  
✅ `nusyq search function "name"` finds functions  
✅ `nusyq search index-health` shows stats  
✅ Results appear in menu help  
✅ All search commands run without errors  
✅ JSON output works for automation

---

## Next Integration (After Search)

Once SmartSearch is wired, next integrate **Healing** into Doctor:

```bash
python scripts/start_nusyq.py doctor --auto-heal
# → finds issues → suggests fixes → applies if approved
```

This follows same pattern: create `heal_actions.py`, wire routing, update menu.
