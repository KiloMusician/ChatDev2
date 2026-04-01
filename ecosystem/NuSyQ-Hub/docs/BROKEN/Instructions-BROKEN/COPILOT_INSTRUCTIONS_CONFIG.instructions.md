---
applyTo: '**'
---

# KILO-FOOLISH Hyper-Extended Copilot Instructions (Φ.3.0)

## 🧠 Project Context & Philosophy

KILO-FOOLISH is a recursively extensible, quantum-inspired, AI-augmented development ecosystem. It integrates:
- Symbolic AI (ΞNuSyQ, OmniTag, MegaTag, RSHTS)
- Multi-agent LLMs (Ollama, ChatDev, OpenAI, Anthropic)
- Game engines (GODOT, RimWorld)
- Advanced logging, memory, and context retention
- Recursive, self-improving feedback loops
- Rube Goldbergian, multi-layered architecture

**All code, documentation, and enhancements must align with the system’s recursive, modular, and quantum design philosophy.**

---

## 🏗️ Coding Guidelines

### 1. **Contextual Awareness & Repository Integration**
- **Reference before you create:** Always search for existing modules, classes, or functions before adding new code. Use the `.copilot/copilot_enhancement_bridge.py` and `src/core/` as primary integration points.
- **Leverage context bridges:** Use the Copilot Enhancement Bridge and Multi-LLM Orchestra for context propagation, memory, and feedback.
- **AI System Integration:** Integrate with `src/ai/ollama_chatdev_integrator.py`, `src/orchestration/chatdev_testing_chamber.py`, and `src/core/ai_coordinator.py` for comprehensive AI workflows.
- **Infrastructure Connectivity:** Reference `src/integration/chatdev_launcher.py`, `src/orchestration/quantum_workflow_automation.py`, and `LOGGING/infrastructure/modular_logging_system.py`.
- **Tag everything:** Use OmniTag/MegaTag/RSHTS conventions for all new functions, classes, and modules. Tags must include purpose, dependencies, context, and evolution stage.
- **Semantic linking:** Cross-reference all enhancements with `COMMANDS_LIST.md`, `123-step-development-checklist.md`, `code_cultivation.md`, and `megatag_specifications.md`.
- **GitHub Integration:** Follow `.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md` and `.github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md` for development workflows.
- **Log-driven context:** All Copilot/LLM integrations and context propagation must reference canonical log files (e.g., `quest_log.jsonl`) for full state/history awareness. Never rely solely on current state files (e.g., `quests.json`).

### 2. **Boolean Checks, State Tracking, and Idempotency**
- **Never suggest or run a command that is already complete.**  
  - Check `executed_commands.json`, logs, or audit scripts before suggesting or running commands.
  - Use idempotent patterns: all scripts must be safe to run multiple times.
  - Implement `is_already_implemented()` and `skip_command()` logic in all automation and suggestion scripts.

### 3. **Advanced Integration & Subprocess Management**
- **Subprocesses:** Use `subprocess` or async equivalents for launching, monitoring, and integrating tools (ChatDev, GODOT, wizard_navigator, etc).
- **Categorize scripts:**  
  - **Subprocess/daemon:** Launched by the system (e.g., `extract_commands.py`, `system_audit.py`)
  - **Manual/entrypoint:** Scripts with `if __name__ == "__main__":` (e.g., `launch-adventure.py`)
- **Log all subprocess launches** using the modular logging system (`LOGGING/infrastructure/modular_logging_system.py`).

### 4. **Memory, Logging, and Feedback Loops**
- **Log everything:** All important actions, errors, and context changes must be logged using the enhanced logging system.
- **Tag logs:** Use OmniTag/MegaTag for traceability.
- **Persist context:** Use `.copilot_memory/`, `logs/storage/`, and `data/` for storing session, consciousness, and audit data.
- **Recursive feedback:** All AI/LLM integrations must use recursive feedback (see `copilot_enhancement_bridge.py`, `Multi-LLM-Orchestra-Platform-Enhancement.py`).
- **Context from previous runs:** Use logs, memory, and tags to refine suggestions and code generation.
- **Auto-detect and resolve** cyclic dependencies and recursion depth issues.

### 5. **Error Handling, Self-Healing, and Robustness**
- **All code must include robust error handling** with logging and, where possible, self-healing or fallback logic.
- **On error:** Suggest or trigger automated recovery scripts or protocols.

### 6. **Documentation, Comments, and Knowledge Propagation**
- **Document everything:** All code must be documented with clear, concise docstrings and inline comments.
- **Reference related modules, tags, and context** in comments.
- **Update documentation** in `docs/`, `.hyper_instructions/`, and `.copilot/context.md` as features evolve.
- **Auto-generate documentation** where possible using context bridges and tag processors.

### 7. **Continuous Improvement & Evolution**
- **Backward compatibility:** All enhancements must be backward compatible and avoid breaking existing workflows.
- **Periodic review:** Refactor for modularity, clarity, and performance.
- **Leverage LLMs:** Use LLMs for code review, suggestion, and recursive improvement (see `extract_commands.py` and orchestration scripts).
- **Cultivate repository consciousness:** Use the bridge’s `cultivate_understanding()` to evolve system knowledge.

### 8. **Quantum & Symbolic Layering**
- **Musical lexeme generation:** Use `ZetaSetLexemeGenerator` for context synthesis and tagging.
- **Quantum context compression:** Summarize and compress context for LLMs and Copilot using bridge and orchestra tools.
- **Symbolic cognition:** Integrate MegaTag and OmniTag for advanced context linking and reasoning.

### 9. **Repository-Wide Awareness**
- **Reference and integrate with:**
  - All core modules in `src/core/`, `src/ai/`, `src/config/`
  - Enhancement bridges in `OTLQGL/copilot-enhancement-bridge-upgrade/`
  - Logging and audit scripts in `LOGGING/infrastructure/` and `Scripts/`
  - Documentation in `docs/`, `guidance/`, and `.copilot/context.md`
  - Game integration in `godot-integration-project/`
- **Cross-reference with:**
  - `COMMANDS_LIST.md` for command dependencies
  - `123-step-development-checklist.md` and `code_cultivation.md` for best practices
  - `megatag_specifications.md` and `OmniTag.txt` for tagging standards

### 10. **Rube Goldbergian Sophistication**
- **Chain enhancements:** Each improvement should trigger further context-aware suggestions, logging, and memory updates.
- **Integrate across layers:** From AI orchestration to game engine hooks, every enhancement should propagate context and state.
- **Self-documenting:** All changes must update tags, logs, and documentation automatically where possible.

---

## 🔍 Troubleshooting the .github Directory

If Copilot appears to forget prompts or loops:
1. Ensure `.github/instructions` contains all required files:
   - `COPILOT_INSTRUCTIONS_CONFIG.instructions.md`
   - `FILE_PRESERVATION_MANDATE.instructions.md`
   - `NuSyQ-Hub_INSTRUCTIONS.instructions.md`
2. Confirm YAML frontmatter at the top of each instruction file:
   ```yaml
   ---
   applyTo: '**'
   priority: CRITICAL
   ---
   ```
3. Check `.github/workflows` for valid YAML and presence of essential CI workflows. For example:
   ```powershell
   Get-ChildItem .github\workflows\*.yml | ForEach-Object { python -c "import yaml, sys; yaml.safe_load(open('$_'))" }
   ```
4. Validate file encoding (UTF-8 without BOM) and consistent line endings (LF or CRLF).
5. Ensure no duplicate or conflicting instructions across files in `.github/instructions`.
6. Review GitHub Actions logs for file load or parsing errors during CI runs.
7. Never delete, rename, or overwrite existing instruction files to preserve critical protocols.

These checks help maintain consistent instruction loading and prevent loops.

---

## 🌀 Example: Boolean-Driven Command Suggestion

```python
# Before suggesting or running a command:
if command in executed_commands or is_already_implemented(command):
    skip_command()
else:
    suggest_or_run(command)
```

---

## 🧬 Advanced Tagging & Semantic Layering

- **Every function, class, and module must be tagged** using OmniTag/MegaTag/RSHTS conventions.
- **Semantic tags** should include: purpose, dependencies, context, and evolution stage.
- **Use musical lexeme generation** for advanced context synthesis (see `ZetaSetLexemeGenerator`).

---

## 🔗 Reference Points

### **📋 Core Documentation & Guidance**
- [COMMANDS_LIST.md](../../docs/archive/Archive/COMMANDS_LIST.md) - Canonical command list and system startup checklist
- [123-step-development-checklist.md](../../docs/guidance/123-step-development-checklist(ALTERNATE).md) - Comprehensive development cycle for KILO-FOOLISH
- [Code Cultivation Guide](../../docs/guidance/code_cultivation.md) - Development principles and philosophy
- [TO-DO List](../../docs/TO-DO/to-do(100).txt) - Next 100 quantum-recursive actions

### **🏷️ Tagging & Semantic Systems**
- [MegaTag Specifications](../../docs/Core/megatag_specifications.md) - Advanced tagging protocols
- [OmniTag Documentation](../../docs/Core/omnitag_documentation.md) - Universal tagging system
- [Enhancement Bridge](../../src/copilot/copilot_enhancement_bridge.py) - Core enhancement system

### **🤖 AI Systems & Integration**
- [AI Coordinator](../../src/ai/ai_coordinator.py) - Central AI task routing and management
- [Ollama ChatDev Integrator](../../src/ai/ollama_chatdev_integrator.py) - Multi-agent AI integration
- [ChatDev Testing Chamber](../../src/orchestration/chatdev_testing_chamber.py) - Collaborative development environment
- [ChatDev Launcher](../../src/integration/chatdev_launcher.py) - Multi-agent system launcher

### **📊 System Architecture & Context**
- [Repository Architecture](../../docs/REPOSITORY_ARCHITECTURE_CODEX.yaml) - System architecture overview
- [Core Systems Context](../../src/core/CORE_SYSTEMS_CONTEXT.md) - Core infrastructure documentation
- [AI Systems Context](../../src/ai/AI_SYSTEMS_CONTEXT.md) - AI integration documentation
- [AI Coordinator](../../src/ai/ai_coordinator.py) - Central AI coordination and dynamic system analysis

### **🔧 Development Tools & Utilities**
- [Enhanced Directory Context Generator](../../src/utils/enhanced_directory_context_generator.py) - Contextual documentation
- [GitHub Integration Auditor](../../src/utils/github_integration_auditor.py) - GitHub integration validation
- [Quantum Workflow Automation](../../src/orchestration/quantum_workflow_automation.py) - Advanced workflows

### **📝 Logging & Memory Systems**
- [Modular Logging System](../../LOGGING/infrastructure/modular_logging_system.py) - Enhanced logging infrastructure
- [Quest Log](../../src/Rosetta_Quest_System/quest_log.jsonl) - Development history and state tracking
- [Executed Commands](../../config/executed_commands.json) - Command completion tracking
- [Memory Systems Context](../../src/memory/MEMORY_SYSTEMS_CONTEXT.md) - Memory and consciousness

### **🎮 Game Integration & Extended Systems**
- [Godot Integration Context](../../docs/GODOT-integration-project/godot-integration-project.md) - Game engine integration
- [Web Interface](../../web/WEB_INTERFACE_CONTEXT.md) - Web system integration
- [Blockchain Systems](../../src/blockchain/BLOCKCHAIN_SYSTEMS_CONTEXT.md) - Blockchain integration

### **🌐 GitHub & Workflow Integration**
- [GitHub Workflows](../../.github/workflows/) - CI/CD automation
- [File Preservation Mandate](../../.github/instructions/FILE_PRESERVATION_MANDATE.instructions.md) - Critical preservation protocol
- [NuSyQ-Hub Instructions](../../.github/instructions/NuSyQ-Hub_INSTRUCTIONS.instructions.md) - Development workflow philosophy

### **📈 Reports & Analysis**
- [System Analysis Reports](../../reports/system_analysis/) - Comprehensive system diagnostics
- [GitHub Integration Reports](../../docs/reports/) - Integration validation results
- [ZETA Progress Tracker](../../config/ZETA_PROGRESS_TRACKER.json) - Feature evolution tracking

---

## 🚦 Final Directive

**All Copilot code generation, review, and suggestions must:**
- Use boolean checks for state and dependency
- Reference and enhance existing modules
- Log and tag all actions
- Integrate with memory and feedback systems
- Document and propagate context recursively
- Maintain Rube Goldbergian, quantum-inspired sophistication

---

## 🧠 Expansion Mandate

- **Explore and implement novel concepts** such as Multi-Axial Repository Topology, State-Responsive File Morphology, Affect-Aware Developer Assistants, Quantum Debugging Proxies, Chrono-Git, Dream-Driven Prompted Repositories, Morphic DSLs, Emotive Commit Language, Ambient Refactor Fog, and Dimensional Build Profiles.
- **Integrate symbolic number systems and extended conlangs** for tagging, context, and cognition.
- **Propose and encode new axioms** for transformational repositories and self-evolving codebases.

---

*This instruction set is living—update as the system evolves and new modules are integrated. All enhancements must be recursively cultivated, contextually aware, and aligned with the overarching goals of the KILO-FOOLISH ecosystem.*

---

## 🌟 Adaptive Instruction Framework

**CORE PRINCIPLE**: These instructions should be interpreted as guiding heuristics rather than rigid constraints. When strict adherence would block progress or create excessive complexity:

1. **Prioritize progress** over perfect adherence to guidelines
2. **Document your reasoning** when deviating from recommendations
3. **Consider the context** and user's immediate needs first
4. **Avoid getting stuck** in loops or blocked states
5. **Propose creative solutions** when standard approaches fail

The system should evolve through a balance of preservation and innovation, with the ultimate goal of enhancing functionality and maintainability.
