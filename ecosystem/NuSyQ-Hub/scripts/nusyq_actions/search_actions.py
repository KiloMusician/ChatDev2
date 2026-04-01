"""Search actions — wire SmartSearch into CLI for code discovery.

Usage:
    nusyq search keyword "authentication" --limit 20
    nusyq search class "ConsciousnessBridge"
    nusyq search function "route_task" --limit 10
    nusyq search index-health
    nusyq search hacking-quests --quest-type exploit
"""

import logging
from typing import Any

from scripts.nusyq_actions.shared import emit_action_receipt

logger = logging.getLogger(__name__)
NO_RESULTS_LINE = "  (no results)"


def handle_search_keyword(
    query: str,
    limit: int = 20,
    output_format: str = "text",
) -> dict[str, Any]:
    """Search by keyword across codebase.

    Examples:
        nusyq search keyword "consciousness" --limit 10
        nusyq search keyword "orchestration" --format json
    """
    try:
        from src.search.smart_search import SmartSearch

        search = SmartSearch()
        results = search.search_keyword(query, limit=limit)

        if output_format == "json":
            return {
                "status": "success",
                "action": "search_keyword",
                "query": query,
                "result_count": len(results),
                "results": [
                    {
                        "file": getattr(r, "file_path", ""),
                        "line": getattr(r, "line", 0),
                        "context": getattr(r, "context", "")[:100],
                    }
                    for r in results
                ],
            }
        else:
            # Text format with nice rendering
            lines = [f"\n🔍 Keyword Search: '{query}' ({len(results)} matches)\n"]
            if results:
                for i, result in enumerate(results, 1):
                    file = getattr(result, "file_path", "?")
                    line = getattr(result, "line", "?")
                    context = getattr(result, "context", "")[:60].replace("\n", " ")
                    lines.append(f"  {i}. {file}:{line}")
                    if context:
                        lines.append(f"     → {context}")
            else:
                lines.append(NO_RESULTS_LINE)

            result = {
                "status": "success",
                "action": "search_keyword",
                "output": "\n".join(lines),
                "result_count": len(results),
            }
            emit_action_receipt(
                "search_keyword",
                exit_code=0,
                metadata={"query": query, "result_count": len(results)},
            )
            return result
    except Exception as e:
        logger.error(f"Keyword search failed: {e}", exc_info=True)
        result = {
            "status": "failed",
            "action": "search_keyword",
            "error": str(e),
            "suggestion": "Ensure SmartSearch index is up-to-date. Run: python -m compileall src/",
        }
        emit_action_receipt("search_keyword", exit_code=1, metadata={"error": str(e)})
        return result


def handle_search_class(
    class_name: str,
    exact: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    """Search for class definitions.

    Examples:
        nusyq search class "ConsciousnessBridge"
        nusyq search class "Orchestrator" --no-exact
    """
    try:
        from src.search.smart_search import SmartSearch

        search = SmartSearch()
        results = search.search_by_class(class_name, exact=exact)[:limit]

        lines = [f"\n🏗️  Class Definitions: '{class_name}' ({len(results)} matches)\n"]
        if results:
            for i, result in enumerate(results, 1):
                file = getattr(result, "file_path", "?")
                line = getattr(result, "line", "?")
                lines.append(f"  {i}. {file}:{line}")
        else:
            lines.append(NO_RESULTS_LINE)

        result = {
            "status": "success",
            "action": "search_class",
            "output": "\n".join(lines),
            "result_count": len(results),
            "class_name": class_name,
        }
        emit_action_receipt(
            "search_class",
            exit_code=0,
            metadata={"class_name": class_name, "result_count": len(results)},
        )
        return result
    except Exception as e:
        logger.error(f"Class search failed: {e}", exc_info=True)
        result = {
            "status": "failed",
            "action": "search_class",
            "error": str(e),
        }
        emit_action_receipt(
            "search_class",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return result


def handle_search_function(
    function_name: str,
    exact: bool = True,
    limit: int = 20,
) -> dict[str, Any]:
    """Search for function definitions.

    Examples:
        nusyq search function "route_task"
        nusyq search function "analyze" --no-exact
    """
    try:
        from src.search.smart_search import SmartSearch

        search = SmartSearch()
        results = search.search_by_function(function_name, exact=exact)[:limit]

        lines = [f"\n⚙️  Function Definitions: '{function_name}' ({len(results)} matches)\n"]
        if results:
            for i, result in enumerate(results, 1):
                file = getattr(result, "file_path", "?")
                line = getattr(result, "line", "?")
                lines.append(f"  {i}. {file}:{line}")
        else:
            lines.append(NO_RESULTS_LINE)

        result = {
            "status": "success",
            "action": "search_function",
            "output": "\n".join(lines),
            "result_count": len(results),
            "function_name": function_name,
        }
        emit_action_receipt(
            "search_function",
            exit_code=0,
            metadata={"function_name": function_name, "result_count": len(results)},
        )
        return result
    except Exception as e:
        logger.error(f"Function search failed: {e}", exc_info=True)
        result = {
            "status": "failed",
            "action": "search_function",
            "error": str(e),
        }
        emit_action_receipt(
            "search_function",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return result


def handle_search_index_health() -> dict[str, Any]:
    """Check SmartSearch index health and statistics.

    Examples:
        nusyq search index-health
    """
    try:
        from src.search.smart_search import SmartSearch

        search = SmartSearch()
        health = search.get_index_health()
        stats = search.get_index_stats()
        file_metadata = getattr(search, "file_metadata", {}) or {}

        functions_count = stats.get("functions")
        if functions_count is None:
            functions_count = sum(
                len(item.get("functions", [])) for item in file_metadata.values() if isinstance(item, dict)
            )

        classes_count = stats.get("classes")
        if classes_count is None:
            classes_count = sum(
                len(item.get("classes", [])) for item in file_metadata.values() if isinstance(item, dict)
            )

        keywords_count = stats.get("keywords")
        if keywords_count is None:
            keywords_count = stats.get("total_keywords")
        if keywords_count is None:
            keyword_index = getattr(search, "keyword_index", {}) or {}
            keywords_count = len(keyword_index)

        stats.setdefault("functions", functions_count)
        stats.setdefault("classes", classes_count)
        stats.setdefault("keywords", keywords_count)

        # Format for display
        output_lines = [
            "\n📊 SmartSearch Index Health\n",
            f"  Status: {health.get('status', 'unknown')}",
            f"  Files indexed: {stats.get('total_files', 0)}",
            f"  Functions found: {functions_count}",
            f"  Classes found: {classes_count}",
            f"  Keywords tracked: {keywords_count}",
        ]

        if "last_updated" in stats:
            output_lines.append(f"  Last updated: {stats['last_updated']}")

        result = {
            "status": "success",
            "action": "search_index_health",
            "output": "\n".join(output_lines),
            "health": health,
            "stats": stats,
        }
        emit_action_receipt(
            "search_index_health",
            exit_code=0,
            metadata={"status": health.get("status", "unknown")},
        )
        return result
    except Exception as e:
        logger.error(f"Index health check failed: {e}", exc_info=True)
        result = {
            "status": "failed",
            "action": "search_index_health",
            "error": str(e),
        }
        emit_action_receipt(
            "search_index_health",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return result


def handle_search_hacking_quests(
    quest_type: str = "all",
    limit: int = 10,
) -> dict[str, Any]:
    """Search for hacking game quests.

    Examples:
        nusyq search hacking-quests
        nusyq search hacking-quests --quest-type exploit
    """
    try:
        from src.search.smart_search import SmartSearch

        search = SmartSearch()
        results = search.search_hacking_quests(quest_type=quest_type, limit=limit)

        lines = [f"\n🎮 Hacking Quests: {quest_type} ({len(results)} matches)\n"]
        if results:
            for i, result in enumerate(results, 1):
                context = getattr(result, "context", "?")[:80]
                lines.append(f"  {i}. {context}")
                file = getattr(result, "file_path", None)
                if file:
                    lines.append(f"     (in {file})")
        else:
            lines.append("  (no quests found)")

        result = {
            "status": "success",
            "action": "search_hacking_quests",
            "output": "\n".join(lines),
            "result_count": len(results),
            "quest_type": quest_type,
        }
        emit_action_receipt(
            "search_hacking_quests",
            exit_code=0,
            metadata={"quest_type": quest_type, "result_count": len(results)},
        )
        return result
    except Exception as e:
        logger.error(f"Hacking quest search failed: {e}", exc_info=True)
        result = {
            "status": "failed",
            "action": "search_hacking_quests",
            "error": str(e),
        }
        emit_action_receipt(
            "search_hacking_quests",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return result


def handle_search_patterns(
    pattern: str,
    pattern_type: str = "all",
    limit: int = 10,
) -> dict[str, Any]:
    """Search for code patterns (consciousness, tagging, architecture).

    Examples:
        nusyq search patterns "consciousness_aware"
        nusyq search patterns "omnitag" --pattern-type tagging
    """
    try:
        from src.search.smart_search import SmartSearch

        search = SmartSearch()

        # Map pattern types to search methods
        if pattern_type == "consciousness":
            results = search.search_keyword("@consciousness_aware", limit=limit)
        elif pattern_type == "tagging":
            results = search.search_keyword("omnitag|megatag|rshts", limit=limit)
        elif pattern_type == "bridge":
            results = search.search_keyword("bridge", limit=limit)
        else:
            results = search.search_keyword(pattern, limit=limit)

        lines = [f"\n🎨 Code Patterns: '{pattern}' ({len(results)} matches)\n"]
        if results:
            for i, result in enumerate(results, 1):
                file = getattr(result, "file_path", "?")
                line = getattr(result, "line", "?")
                context = getattr(result, "context", "")[:60].replace("\n", " ")
                lines.append(f"  {i}. {file}:{line}")
                if context:
                    lines.append(f"     → {context}")
        else:
            lines.append("  (no patterns found)")

        result = {
            "status": "success",
            "action": "search_patterns",
            "output": "\n".join(lines),
            "result_count": len(results),
            "pattern": pattern,
            "pattern_type": pattern_type,
        }
        emit_action_receipt(
            "search_patterns",
            exit_code=0,
            metadata={
                "pattern": pattern,
                "pattern_type": pattern_type,
                "result_count": len(results),
            },
        )
        return result
    except Exception as e:
        logger.error(f"Pattern search failed: {e}", exc_info=True)
        result = {
            "status": "failed",
            "action": "search_patterns",
            "error": str(e),
        }
        emit_action_receipt(
            "search_patterns",
            exit_code=1,
            metadata={"error": str(e)},
        )
        return result
