# CONTEXT: src/integration

This directory contains all integration modules for the NuSyQ-Hub system. It is the primary hub for connecting ChatDev, Copilot, Ollama, and other AI systems.

## Key Modules
- `chatdev_integration.py`: Manages ChatDev integration, bridge connectivity, and fallback logic.
- `copilot_chatdev_bridge.py`: Enables advanced collaboration between Copilot and ChatDev.
- `chatdev_launcher.py`: Handles launching and environment setup for ChatDev, including API key and Ollama fallback.
- `chatdev_llm_adapter.py`: Routes ChatDev LLM requests to Ollama first, with OpenAI fallback.
- `chatdev_environment_patcher.py`, `chatdev_llm_adapter.py`, `quantum_bridge.py`: Additional adapters and patchers for advanced workflows.

## Integration Philosophy
- **Ollama First:** All LLM requests are routed to Ollama (local) first for privacy, speed, and cost savings.
- **OpenAI Fallback:** If Ollama is unavailable, OpenAI is used as a backup.
- **Bridge System:** Copilot-ChatDev Bridge enables seamless multi-agent collaboration.

## Usage
- Use the enhanced launcher (`enhanced_agent_launcher.py`) to orchestrate all integrations.
- All modules are designed for extensibility and robust fallback.

## See Also
- `../ai/ai_coordinator.py` (KILO-FOOLISH): Multi-LLM orchestration
- `../setup/secrets.py`: Secrets/configuration management
- `../../.github/WORKFLOWS.md`: System-wide workflow documentation
