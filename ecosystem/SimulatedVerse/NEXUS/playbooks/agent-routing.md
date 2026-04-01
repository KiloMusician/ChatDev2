# Agent Routing — Decision→Dispatch

**Purpose**: route tasks to appropriate agents without theater or hallucination.

## Decision Matrix
- **UI/UX tasks** → Designer agent (tags: ui:*, ux:*)
- **Infrastructure** → Engineer agent (tags: ops:*, infra:*)
- **Game mechanics** → Gameplay agent (tags: game:*, balance:*)
- **Documentation** → Writer agent (tags: docs:*, lore:*)

## Dispatch Rules
1. Check `/NEXUS/datasets/index.ndjson` for existing modules by TAGS
2. Assign to module OWNER if available
3. Route to Testing Chamber if no clear owner
4. Require proof artifact before marking complete

## No Theater
- No "suggested tasks" without real work backing them
- No completion claims without file changes in git tree
- No duplicated effort - check index first