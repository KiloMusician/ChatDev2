# AI Systems Integration Hub

**Purpose**: Unified artificial intelligence coordination, orchestration, and automation systems for CoreLink Foundation.

## Directory Structure

### `/orchestration/`
**Context**: Core AI coordination and provider management
- `council_bootstrap.cjs` - 5-member AI council for autonomous task delegation
- `coordination-core.ts` - Central AI coordination logic
- `llm-provider-selector.ts` - Multi-provider LLM routing (Ollama, OpenAI, Copilot)
- `api-endpoints.ts` - AI service API definitions
- `vscode-copilot-interface.ts` - VSCode Copilot integration

### `/chatdev-tasks/` 
**Context**: Autonomous development task agents
- `demo_task.cjs` - System health monitoring and performance analysis
- `repair_placeholders.cjs` - Autonomous code repair and placeholder replacement
- `storybeat_log.cjs` - Narrative progression and story continuity

### `/templates/`
**Context**: High-level AI project templates and organizational patterns
- `workflow-templates.json` - Reusable AI workflow patterns
- `/endpoints/` - Template API endpoint configurations
- `/projects/` - Project structure templates
- `/outputs/` - Generated content examples

### `/providers/`
**Context**: LLM provider implementations and adapters
- `provider.ts` - Base provider interface and implementations

## Integration Points

- **ΞNuSyQ Consciousness**: Council decisions guided by consciousness coherence levels
- **Token Guard**: Zero-cost operation with local Ollama fallback
- **Autonomous Pipeline**: ChatDev tasks integrate with Rube Goldberg workflow
- **Replit Integration**: Seamless integration with Replit development environment

## Key Features

- **Autonomous Council**: 5 specialized AI agents (Architect, Engineer, Tester, Optimizer, Guardian)
- **Multi-LLM Support**: Ollama local models + OpenAI + GitHub Copilot
- **Task Delegation**: Intelligent task routing based on agent specialization
- **Placeholder Repair**: Autonomous code quality improvement
- **Story Integration**: Narrative-driven development progression

**Last Consolidated**: August 2025 - Repository cleanup initiative
**Replaces**: AI_Warehouse/, src/ai-hub/, tools/ai/ (now consolidated)