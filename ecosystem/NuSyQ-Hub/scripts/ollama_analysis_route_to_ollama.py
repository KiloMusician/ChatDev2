#!/usr/bin/env python3
"""Demonstrate Option B: Using Ollama to Analyze Complex Function

This shows the conversational orchestration approach where we:
1. Identify a complex function (cognitive complexity > limit)
2. Prepare detailed analysis request
3. Route to Ollama for refactoring suggestions
4. Parse and apply improvements

The _route_to_ollama() function is a perfect case study.
"""

import json

# Detailed Analysis Request for Ollama
analysis_request = {
    "function": "_route_to_ollama",
    "file": "src/tools/agent_task_router.py",
    "lines": "1121-1210",
    "current_complexity": 19,
    "target_complexity": 15,
    "delta_needed": 4,
    "issues_identified": [
        {
            "type": "Duplicate Constant",
            "lines": "1125-1130 and 1147-1152",
            "problem": "model_map defined twice with identical content",
            "impact": "Increases cognitive load, violates DRY principle",
            "refactoring": "Extract to class-level constant or to helper method",
        },
        {
            "type": "Nested Exception Handling",
            "lines": "1138-1210",
            "problem": "Try-except with integrator, then fallback logic spans 70+ lines",
            "impact": "Deep nesting, hard to understand error paths",
            "refactoring": "Split into _try_chatdev_integrator() and _try_ollama_adapter()",
        },
        {
            "type": "Complex Response Normalization",
            "lines": "1170-1210",
            "problem": "6-level deep conditionals checking: isinstance, dict keys, response.get()",
            "impact": "Hard to follow status determination logic",
            "refactoring": "Extract _normalize_ollama_response() and _determine_response_status()",
        },
        {
            "type": "Duplicated Error Extraction",
            "lines": "1200-1204",
            "problem": "Same error message extraction logic could be centralized",
            "impact": "Maintenance burden if format changes",
            "refactoring": "_extract_error_message(response) helper",
        },
    ],
    "suggested_refactorings": [
        {
            "id": 1,
            "name": "_select_ollama_model",
            "signature": "def _select_ollama_model(self, task_type: str) -> str",
            "extract_from_lines": "1125-1130, 1147-1152",
            "removes_duplicate": True,
            "complexity_reduction": 1,
            "description": "Centralize model selection logic, remove duplicate map definition",
        },
        {
            "id": 2,
            "name": "_normalize_ollama_response",
            "signature": "def _normalize_ollama_response(self, response: Any) -> dict[str, Any]",
            "extract_from_lines": "1164-1172",
            "removes_duplicate": False,
            "complexity_reduction": 2,
            "description": "Handle str→dict conversion, standardize output format",
        },
        {
            "id": 3,
            "name": "_determine_response_status",
            "signature": "def _determine_response_status(self, response: dict[str, Any]) -> str",
            "extract_from_lines": "1174-1190",
            "removes_duplicate": False,
            "complexity_reduction": 2,
            "description": "Encapsulate all error-checking logic (3-5 conditionals)",
        },
        {
            "id": 4,
            "name": "_format_ollama_result",
            "signature": "def _format_ollama_result(self, status: str, model: str, output: Any, task_id: str, error_msg: str = None) -> dict[str, Any]",
            "extract_from_lines": "1158-1163, 1190-1210",
            "removes_duplicate": False,
            "complexity_reduction": 1,
            "description": "Build final result dict, apply error context if needed",
        },
    ],
    "refactored_flow": """
async def _route_to_ollama(self, task: OrchestrationTask) -> dict[str, Any]:
    '''Route task to Ollama local LLM.'''
    logger.info(f'🦙 Routing to Ollama: {task.content}')

    # Select model (centralized, single definition)
    model = self._select_ollama_model(task.task_type)

    # Try integrator first
    response = None
    try:
        integrator = EnhancedOllamaChatDevIntegrator()
        response = await integrator.chat_with_ollama(
            messages=[{'role': 'user', 'content': task.content}],
            model=model,
        )
    except Exception:
        pass  # Will try adapter below

    # Fallback to adapter
    if response is None:
        adapter = OllamaAdapter()
        response = adapter.query(prompt=task.content, model=model)

    # Normalize response type
    normalized = self._normalize_ollama_response(response)

    # Determine status from response content
    status = self._determine_response_status(normalized)

    # Build and return result
    result = self._format_ollama_result(status, model, normalized, task.task_id)
    return result
    """,
    "complexity_breakdown": {
        "original": {
            "duplicate_definition": 1,
            "top_level_try_except": 1,
            "fallback_exception": 1,
            "isinstance_checks": 3,
            "dict_get_chains": 4,
            "nested_conditionals": 5,
            "total": 19,
        },
        "refactored": {
            "model_selection_helper": 0,  # extracted
            "normalize_response_helper": 0,  # extracted
            "determine_status_helper": 0,  # extracted
            "format_result_helper": 0,  # extracted
            "main_function_logic": 5,  # simplified main flow
            "total": 5,
        },
    },
    "implementation_notes": [
        "Extract methods in order: _select_ollama_model → _normalize_ollama_response → _determine_response_status → _format_ollama_result",
        "Each extracted method should be independently testable with mocked responses",
        "Maintain backwards compatibility: public interface unchanged",
        "Consider adding @functools.lru_cache to _select_ollama_model since it's deterministic",
        "Add type hints to all new helpers for clarity",
        "Log at extraction points for debugging ('Normalizing integrator response...' etc)",
    ],
}

print("=" * 80)
print("🦙 OLLAMA REFACTORING ANALYSIS - _route_to_ollama()")
print("=" * 80)
print()
print(f"📍 Function: {analysis_request['function']}")
print(f"📄 File: {analysis_request['file']}")
print(f"📏 Lines: {analysis_request['lines']}")
print(
    f"📊 Complexity: {analysis_request['current_complexity']} → target {analysis_request['target_complexity']} (need to reduce by {analysis_request['delta_needed']})"
)
print()

print("🔍 ISSUES DETECTED:")
print("-" * 80)
for i, issue in enumerate(analysis_request["issues_identified"], 1):
    print(f"\n{i}. {issue['type']} (lines {issue['lines']})")
    print(f"   Problem: {issue['problem']}")
    print(f"   Impact: {issue['impact']}")
    print(f"   Solution: {issue['refactoring']}")

print()
print()
print("✨ SUGGESTED REFACTORINGS:")
print("-" * 80)
for refactor in analysis_request["suggested_refactorings"]:
    print(f"\n{refactor['id']}. {refactor['name']}()")
    print(f"   Extract from lines: {refactor['extract_from_lines']}")
    print(f"   Complexity reduction: {refactor['complexity_reduction']}")
    print(f"   Purpose: {refactor['description']}")

print()
print()
print("📋 REFACTORED MAIN FUNCTION FLOW:")
print("-" * 80)
print(analysis_request["refactored_flow"])

print()
print("📈 COMPLEXITY REDUCTION:")
print("-" * 80)
print(f"Current breakdown: {json.dumps(analysis_request['complexity_breakdown']['original'], indent=2)}")
print(f"\nAfter extraction: {json.dumps(analysis_request['complexity_breakdown']['refactored'], indent=2)}")

print()
print("💡 IMPLEMENTATION NOTES:")
print("-" * 80)
for note in analysis_request["implementation_notes"]:
    print(f"• {note}")

print()
print("✅ Analysis complete. Ready for implementation.")
print()
