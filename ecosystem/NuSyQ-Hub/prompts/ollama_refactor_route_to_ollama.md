# Refactor Request: _route_to_ollama() Cognitive Complexity Reduction

## Current Status
**File:** `src/tools/agent_task_router.py`  
**Function:** `AgentTaskRouter._route_to_ollama()`  
**Lines:** 1121-1210  
**Current Complexity:** 19 (limit: 15)  
**Issue:** Function has too many nested branches and conditional paths

## Context
This async method routes Ollama tasks. It:
1. Defines a model_map (duplicated)
2. Tries EnhancedOllamaChatDevIntegrator (preferred, advanced)
3. Falls back to OllamaAdapter if integrator unavailable
4. Normalizes responses from both systems
5. Handles multiple error conditions

## Problem Areas
- **Lines 1125-1147:** Model mapping defined twice (duplicate)
- **Lines 1138-1150:** Nested try-except with branching logic
- **Lines 1151-1210:** Complex fallback logic with 6-level deep conditionals
- **Response normalization:** Checking multiple dict keys and response types

## Suggested Refactoring Strategy

### Extract Helper Methods
1. `_select_ollama_model(task_type: str) -> str`
   - Centralize model selection logic
   - Remove duplicate definition
   - Reduce nesting at call site

2. `_normalize_ollama_response(response: Any) -> dict[str, Any]`
   - Handle response type checking (str vs dict)
   - Standardize output format
   - Remove 6+ level deep conditionals

3. `_determine_response_status(response: dict[str, Any]) -> str`
   - Check error keys, exception keys, output validation
   - Return "success" or "failed"
   - Separate error detection from response processing

4. `_format_ollama_result(status: str, model: str, output: Any, task_id: str) -> dict[str, Any]`
   - Build final result dict
   - Apply error context if needed

### Refactored Flow

```python
async def _route_to_ollama(self, task: OrchestrationTask) -> dict[str, Any]:
    model = self._select_ollama_model(task.task_type)

    # Try integrator
    response = await self._try_chatdev_integrator(task, model)

    # Fallback to adapter if integrator fails
    if response is None:
        response = await self._try_ollama_adapter(task, model)

    # Normalize and determine status
    normalized = self._normalize_ollama_response(response)
    status = self._determine_response_status(normalized)

    # Build result
    return self._format_ollama_result(status, model, normalized, task.task_id)
```

### Benefits
- **Reduces complexity** by extracting 4 independent concerns
- **Removes duplication** (single model_map definition)
- **Improves testability** (each helper can be unit tested)
- **Reduces indentation depth** (max 3 levels → 2)
- **Clearer intent** (each method has single responsibility)

## Questions for Implementation
1. Should error messages be accumulated/logged during fallback?
2. Should we track which system was used (for metrics/debugging)?
3. Any telemetry logging needed in each extracted helper?

---

**Analyst Note:** This is a classic case of nested exceptions + conditional response handling. Breaking into focused helpers will make the function easily testable and maintainable.
