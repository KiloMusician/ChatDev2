# Trace Taxonomy

NuSyQ-Hub uses the following span naming and attributes conventions:

## Span Names
- `nusyq.action.<action>` — root span per CLI action
- `nusyq.router.route` — agent router dispatch
- `nusyq.orchestrator.submit` — multi-AI orchestration submissions
- `nusyq.snapshot.collect` — snapshot data collection
- `nusyq.heal.apply` — healing operations

## Required Attributes
- `nusyq.repo`
- `nusyq.branch`
- `nusyq.head`
- `nusyq.dirty`
- `nusyq.ahead_behind`
- `nusyq.quest.last`
- `nusyq.task_id` (if async)
- `code.filepath` (for analyze/review/debug)
- `system.name` (copilot|claude|ollama|chatdev|zero-token)

## Baggage
- `nusyq.session_id`
- `nusyq.operator_mode`

## Receipts
- Every receipt prints `trace_id` and `span_id` when tracing is enabled.
