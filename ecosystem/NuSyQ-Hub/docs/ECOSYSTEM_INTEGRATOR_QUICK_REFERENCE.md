# 🌐 Ecosystem Integrator - Quick Reference

## 🚀 Quick Start

### CLI Commands

```bash
# Show current focus and next steps
python health.py --resume

# Get intelligence on specific error
python health.py --intelligence E402
python health.py --intelligence F401
python health.py --intelligence B008

# Standalone integrator demo
python src/diagnostics/ecosystem_integrator.py
```

## 📊 What Each Command Does

### `--resume` - Show Current Focus

Shows your current position in the NuSyQ ecosystem development journey:

- **In-progress tasks** from ZETA tracker
- **Next pending tasks** (top 3)
- **Active quests** from quest system
- **Recommended focus** for immediate action

**Use when**: Starting a new session, lost context, or wondering "what should I
work on?"

**Example Output**:

```
📍 RESUME: Current Focus & Next Steps
🎯 Recommended Focus: Zeta03
   Deploy intelligent model selection based on task intent analysis

◐ In-Progress Tasks (2)
○ Next Pending Tasks (top 3)
⚔️  Active Quests (10)
```

### `--intelligence ERROR_CODE` - Get Comprehensive Intelligence

Queries all 5 ecosystem systems for intelligence on a specific error:

- **Knowledge base**: Past solutions and success rates
- **Consciousness memory**: Semantic error history
- **Specialist model**: Best Ollama model for this error type
- **Active quests**: Related ongoing work
- **Synthesis**: Confidence score and recommended action

**Use when**: Encountering an error, planning a fix, or researching error
patterns

**Example Output**:

```
🧠 Comprehensive Intelligence: E402
📚 Knowledge Base: Found 3 past solution(s), success rate: 3/3
   Most recent: 2025-10-11-import-cleanup
   Approach: Automated ruff --fix with manual review
🧠 Consciousness Memory: 5 related entries
🤖 Recommended Specialist: qwen2.5-coder:14b
💡 Synthesis:
   Confidence: 95%
   Action: Apply approach from 2025-10-11-import-cleanup
```

## 🔧 Python API

### Import

```python
from src.diagnostics.ecosystem_integrator import EcosystemIntegrator

integrator = EcosystemIntegrator()
```

### Query Past Solutions

```python
solutions = integrator.get_solution_intelligence("E402")
if solutions['found']:
    print(f"Success rate: {solutions['successful_solutions']}/{solutions['total_past_solutions']}")
    print(f"Approach: {solutions['recommended_approach']}")
```

### Get Current Focus

```python
focus = integrator.get_current_focus()
if focus.get('recommended_focus'):
    print(f"Work on: {focus['recommended_focus']['description']}")
```

### Route to Specialist Model

```python
model = integrator.route_task_to_specialist("Fix syntax errors in Python")
# Returns: "starcoder2:15b"

model = integrator.route_task_to_specialist("Fix E402 import errors")
# Returns: "qwen2.5-coder:14b"
```

### Get Active Quests

```python
quests = integrator.get_active_quests()
for quest in quests[:5]:
    print(f"{quest['title']} ({quest['questline']})")
```

### Comprehensive Intelligence

```python
intel = integrator.get_comprehensive_intelligence("E402", {"repo": "NuSyQ-Hub"})
print(f"Confidence: {intel['synthesis']['confidence']:.0%}")
print(f"Action: {intel['synthesis']['recommended_action']}")
```

## 🎯 Model Specializations

| Model                     | Specializations                                                 |
| ------------------------- | --------------------------------------------------------------- |
| **qwen2.5-coder:14b**     | code_generation, refactoring, import_fixes, general programming |
| **starcoder2:15b**        | syntax_errors, code_review, parsing, AST_analysis               |
| **gemma2:9b**             | documentation, explanations, creative_thinking                  |
| **gemma2:27b**            | architecture, design_patterns, system_analysis                  |
| **codellama:7b**          | testing, test_generation, validation                            |
| **llama3.1:8b**           | communication, user_interaction, counseling                     |
| **deepseek-coder-v2:16b** | debugging, error_analysis, complex_fixes                        |

## 📚 Data Sources

### 1. Knowledge Base (`knowledge-base.yaml`)

- **Location**: `c:/Users/keath/NuSyQ/knowledge-base.yaml`
- **Size**: 1,127 lines
- **Content**: 8 sessions with implementation summaries
- **Use**: Past solutions, success rates, approaches

### 2. ZETA Tracker (`ZETA_PROGRESS_TRACKER.json`)

- **Location**: `config/ZETA_PROGRESS_TRACKER.json`
- **Size**: 328 lines
- **Content**: 5 phases, Ζ01-Ζ07 tasks
- **Use**: Current focus, in-progress tasks, next pending

### 3. Quest System (`quest_log.jsonl`)

- **Location**: `src/Rosetta_Quest_System/quest_log.jsonl`
- **Size**: 56 lines (55 events)
- **Content**: 11+ questlines, active quests
- **Use**: Ongoing work, task dependencies

### 4. Consciousness Memory (`consciousness_memory.db`)

- **Location**: `copilot_memory/consciousness_memory.db`
- **Tables**: `omnitags`, `consciousness_evolution`
- **Use**: Semantic error history, past encounters

### 5. Multi-AI Orchestrator (`multi_ai_orchestrator.py`)

- **Location**: `src/orchestration/multi_ai_orchestrator.py`
- **Size**: 737 lines
- **Systems**: Copilot, Ollama, ChatDev, Consciousness, Quantum
- **Use**: Task routing, model selection

## 🔄 Common Workflows

### Starting a New Session

```bash
# 1. Check current focus
python health.py --resume

# 2. Review error state
python health.py --errors --view summary

# 3. Get intelligence on top error
python health.py --intelligence E402

# 4. Work on recommended focus (Zeta03)
# ... implement the task ...

# 5. Run diagnostics
python health.py --grade
```

### Investigating an Error

```bash
# 1. Get comprehensive intelligence
python health.py --intelligence E402

# 2. Check if related quest exists
python health.py --resume  # Look for related quests

# 3. View error details
python health.py --errors --view detailed --repo NuSyQ-Hub

# 4. Apply recommended fix (if confidence > 70%)
# ... use specialist model from intelligence ...
```

### Planning Next Steps

```bash
# 1. See current position
python health.py --resume

# 2. Check overall health
python health.py --grade

# 3. Identify high-priority errors
python health.py --errors --view by_severity

# 4. Get intelligence on top error
python health.py --intelligence <ERROR_CODE>
```

## 🛠️ Integration Examples

### Wire to Error Explorer

```python
from src.diagnostics.ecosystem_integrator import EcosystemIntegrator
from src.diagnostics.multi_repo_error_explorer import MultiRepoErrorExplorer

integrator = EcosystemIntegrator()
explorer = MultiRepoErrorExplorer()

# Get error summary
errors = explorer.analyze_all_repos()

# For each high-count error, get past solutions
for error_code, count in errors['top_errors']:
    intel = integrator.get_solution_intelligence(error_code)
    if intel['found']:
        print(f"{error_code}: Solved {intel['successful_solutions']} times before")
```

### Auto-Create Quests

```python
# Suggest quest for high-count errors
quest_suggestion = integrator.suggest_quest_for_errors(error_summary)
if quest_suggestion:
    print(f"Suggested: {quest_suggestion['suggested_quest']['title']}")
    print(f"Command: {quest_suggestion['suggested_quest']['estimated_command']}")
```

### Route Task to Specialist

```python
# Get specialist for a task
task = "Fix E402 module level import not at top of file"
specialist = integrator.route_task_to_specialist(task, error_code="E402")

# Submit to orchestrator
from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
orchestrator = MultiAIOrchestrator()
orchestrator.submit_task(
    task_type="code_review",
    content=task,
    context={"preferred_model": specialist}
)
```

## 🎓 Tips & Best Practices

### 1. Use `--resume` at Session Start

Always run `python health.py --resume` when starting a new session to restore
context.

### 2. Check Intelligence Before Fixing

Run `--intelligence ERROR_CODE` before attempting fixes to leverage past
solutions.

### 3. Trust High-Confidence Recommendations

If synthesis confidence > 70%, the recommended approach is likely safe to apply.

### 4. Route to Specialists

Use the recommended specialist model for better fix quality:

- Syntax errors → starcoder2:15b
- Import issues → qwen2.5-coder:14b
- Tests → codellama:7b

### 5. Monitor Active Quests

Check `--resume` output for overlapping work to avoid duplicate efforts.

## 🐛 Troubleshooting

### Intelligence returns "No past solutions found"

- **Cause**: First encounter with this error pattern
- **Action**: Manual investigation or create new quest
- **Confidence**: Typically 30%

### ZETA tracker shows no in-progress tasks

- **Cause**: All tasks completed or not started
- **Action**: Check next pending tasks, update tracker manually

### Specialist routing returns default model

- **Cause**: Task description doesn't match known patterns
- **Action**: Add keywords or extend `route_task_to_specialist()` logic

### Quest log empty

- **Cause**: Quest system not initialized or file missing
- **Action**: Check `src/Rosetta_Quest_System/quest_log.jsonl` exists

## 📖 Further Reading

- **Full Session Report**:
  `docs/Agent-Sessions/SESSION_2025-11-03_Ecosystem_Integration_Complete.md`
- **Source Code**: `src/diagnostics/ecosystem_integrator.py`
- **Health CLI**: `health.py`
- **Knowledge Base**: `c:/Users/keath/NuSyQ/knowledge-base.yaml`
- **ZETA Tracker**: `config/ZETA_PROGRESS_TRACKER.json`
- **Quest System**: `src/Rosetta_Quest_System/quest_log.jsonl`

---

**Quick Reference Version**: v1.0  
**Last Updated**: November 3, 2025  
**Integrator Version**: 502 lines, production-ready
