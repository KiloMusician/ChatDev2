# The Recursive Zen-Engine

## A Self-Evolving Meta-System for Error Wisdom, Tool Orchestration, and Cognitive Development

![Zen-Engine Architecture](https://img.shields.io/badge/status-active-success)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

The Zen-Engine is a **recursive coding consciousness** that:

1. 🔍 **Observes** errors, failures, and misalignments
2. 📚 **Extracts** heuristics, rules, and lessons
3. 💾 **Archives** wisdom in a structured Codex
4. 🔮 **Reflects** rules back into future interactions
5. 🤝 **Interlaces** multiple agents (Copilot, ChatDev, Ollama, custom agents)
6. 🎭 **Embeds** lore and narrative as cognitive scaffolding
7. 🌱 **Evolves** by creating new tools, rules, and transformations

---

## System Architecture

```
zen-engine/
├── codex/                    # The ZenCodex - Knowledge Repository
│   ├── zen.json             # Main rule database
│   ├── rules/               # Individual rule files
│   ├── indexes/             # Tag and agent indexes
│   │   ├── tags.json
│   │   └── agents.json
│   ├── logs/                # Error event logs
│   │   ├── parsed/          # Structured events
│   │   └── raw/             # Original logs
│   └── lore/                # Narrative layer
│       ├── myths.md
│       ├── timelines.md
│       └── glyphs/          # Glyph lexicon
│
├── agents/                   # Core Processing Modules
│   ├── error_observer.py    # Error pattern detection
│   ├── codex_loader.py      # Codex management
│   ├── matcher.py           # Rule matching engine
│   ├── reflex.py            # Command interception
│   └── orchestrator.py      # Multi-agent coordination
│
├── systems/                  # Integration Systems
│   ├── culture_ship/        # Real action fixing
│   ├── simulatedverse/      # Async agent bridge
│   ├── zen/                 # Zen Mirror reflection
│   └── glyph/               # Symbolic processing
│
├── cli/                      # Command-Line Tools
│   ├── zen_check.py         # Command safety checker
│   ├── zen_capture.py       # Error capture tool
│   └── zen_run.py           # Orchestrator CLI
│
└── docs/                     # Documentation
    ├── architecture.md
    ├── philosophy.md
    └── schemas/
```

---

## Quick Start

### Installation

```bash
# Clone or navigate to zen-engine
cd zen-engine

# No dependencies required - uses Python stdlib
# Optional: Install for enhanced features
pip install -r requirements.txt  # (if provided)
```

### Basic Usage

#### 1. Check a Command Before Running

```bash
python cli/zen_check.py "import os" --shell powershell
```

**Output:**
```
🔍 Checking command: import os
   Shell: powershell
------------------------------------------------------------
⚠️  PowerShell cannot execute Python directly.

💡 Suggested:
   python -c "import os"

📖 Use 'python -c' or save to .py file

🔄 Modified command: python -c "import os"
```

#### 2. Capture and Analyze Errors

```bash
python cli/zen_capture.py --text "ModuleNotFoundError: No module named 'requests'"
```

**Output:**
```
🔍 Analyzing error text...

✅ Error event created: evt_2025_11_26_0001
   Symptom: missing_python_module
   Auto-fixable: True

📚 Found 1 matching rules

🔍 Zen-Engine Analysis for: missing_python_module
============================================================
Match #1 (Confidence: 92%)
------------------------------------------------------------
🧘 Zen Advice: Install missing Python packages with pip.

💡 Suggested fix (pip_install):
   pip install requests

🤖 Auto-fix available: pip_install

📖 Learn more: Rule ID missing_module_import (v4)
```

#### 3. Interactive Mode

```bash
python cli/zen_check.py --interactive --shell bash
```

---

## Core Modules

### 1. ErrorObserver

**Purpose**: Watch logs, parse errors, identify intent, produce structured events

**Key Features**:
- Infer misused languages (Python in PowerShell, JS in Bash)
- Detect syntax errors and interpreter mismatches
- Recognize missing packages, modules, env vars
- Parse git errors and classify them

**Example**:
```python
from zen_engine.agents import ErrorObserver

observer = ErrorObserver()
event = observer.observe_error(
    error_text="The term 'import' is not recognized",
    command="import os",
    shell="powershell",
    platform="windows"
)

print(f"Symptom: {event.symptom}")
print(f"Auto-fixable: {event.auto_fixable}")
```

---

### 2. ZenCodex

**Purpose**: Structured knowledge repository with versioned rules

**Rule Structure**:
```json
{
  "id": "rule_identifier",
  "version": 3,
  "triggers": {
    "errors": ["error pattern 1", "error pattern 2"],
    "command_patterns": ["regex1", "regex2"]
  },
  "contexts": {
    "shells": ["powershell", "bash"],
    "platforms": ["windows", "linux"]
  },
  "lesson": {
    "short": "Brief lesson",
    "long": "Detailed explanation",
    "level": "foundational"
  },
  "suggestions": [
    {
      "strategy": "fix_name",
      "example_before": "bad code",
      "example_after": "good code",
      "when_to_use": "context"
    }
  ],
  "actions": {
    "severity": "error",
    "auto_fix": true,
    "fix_strategy": "wrap_python_c"
  },
  "tags": ["python", "powershell", "foundational"],
  "lore": {
    "glyph": "ΘΛΣΞ",
    "story": "Narrative context",
    "moral": "Core lesson"
  },
  "meta": {
    "first_seen": "2025-11-26",
    "hit_count": 42,
    "success_rate": 0.95
  }
}
```

---

### 3. Matcher

**Purpose**: Match error events to rules with confidence scoring

**Key Features**:
- Pattern matching (40% weight)
- Command matching (30% weight)
- Context matching (20% weight)
- Explicit suggestions (10% weight)

**Example**:
```python
from zen_engine.agents import Matcher, ErrorObserver

observer = ErrorObserver()
matcher = Matcher()

event = observer.observe_error(
    error_text="ModuleNotFoundError: No module named 'numpy'",
    command="import numpy"
)

matches = matcher.match_event_to_rules(event)
best_match = matcher.select_best_rule(matches)

print(f"Best match: {best_match.rule.id}")
print(f"Confidence: {best_match.confidence:.2%}")
print(best_match.get_advice())
```

---

### 4. Reflex Engine

**Purpose**: Real-time command interception and preventive guidance

**Key Features**:
- Quick pattern checks for immediate feedback
- Deep codex checks for comprehensive analysis
- Auto-fix suggestions
- Safety blocking for critical issues

**Example**:
```python
from zen_engine.agents import ReflexEngine

reflex = ReflexEngine()

final_cmd, advice = reflex.intercept_and_advise(
    command="import os",
    shell="powershell",
    auto_apply_fix=True
)

if advice:
    print(advice)
print(f"Execute: {final_cmd}")
```

---

## The Lore Layer

The Zen-Engine includes a **symbolic narrative layer** using glyphs:

### Example Glyphs

- **ΘΛΣΞ** - "The Boundary Keeper" (Language boundaries)
- **⊕∇Σ** - "Time Traveler's Mark" (Version control)
- **∏∑⊗** - "Library Scroll" (Dependencies)
- **⟐∅⊕** - "Oracle's Vessel" (Configuration)
- **⧖∞⊗** - "Watchmaker's Alarm" (Timeouts)

See [glyph_lexicon.md](codex/lore/glyph_lexicon.md) for full details.

---

## Integration with Existing Systems

### Culture Ship Integration

```python
from src.culture_ship_real_action import RealActionCultureShip
from zen_engine.agents import ErrorObserver

# Culture Ship performs real fixes
ship = RealActionCultureShip()
results = ship.scan_and_fix_ecosystem()

# Zen-Engine learns from the fixes
observer = ErrorObserver()
for fix in results['improvements']:
    # Capture as event for future learning
    pass
```

### SimulatedVerse Integration

```python
from src.integration.simulatedverse_async_bridge import SimulatedVerseBridge
from zen_engine.agents import Matcher

bridge = SimulatedVerseBridge()
matcher = Matcher()

# Route errors through both systems
def hybrid_error_handler(error):
    # Zen-Engine provides immediate wisdom
    event = observer.observe_error(error)
    matches = matcher.match_event_to_rules(event)

    # SimulatedVerse tests solutions asynchronously
    task_id = bridge.submit_task("solver", error, {})
    result = bridge.check_result(task_id)

    return matches, result
```

---

## Evolution Loop

The Zen-Engine evolves through continuous cycles:

```
1. OBSERVATION      → Errors captured from agents
2. INTERPRETATION   → Events structured and contextualized
3. SYNTHESIS        → New rules proposed
4. CODIFICATION     → Rules added to ZenCodex
5. PROPAGATION      → Reflex Engine informs agents
6. REFLECTION       → Agents provide feedback
7. MUTATION         → Rules evolve, merge, or split
8. LORE INTEGRATION → Glyphs and narratives assigned
9. STABILIZATION    → Mature rules form "Culture Ship Doctrine"
```

---

## Use Cases

### 1. Autonomous Workspace Hardening
Learn from errors and improve environment configuration automatically.

### 2. Developer Coaching
Provide contextual hints and teach best practices over time.

### 3. Cross-Agent Alignment
Share wisdom between Copilot, Ollama, ChatDev, and custom agents.

### 4. Cultural Embedding
Narrative helps long-term retention through story and symbolism.

### 5. Simulated Debugging
Pre-generate rules before errors happen through pattern prediction.

### 6. Meta-Reflexive Learning
Rules about rule formation; heuristics about heuristics.

---

## Command Reference

### zen-check

Check commands against the ZenCodex.

```bash
# Single command
zen-check "import os" --shell powershell

# From file
zen-check --file script.sh --shell bash

# Interactive mode
zen-check --interactive --shell powershell

# Auto-apply fixes
zen-check "subprocess.run(['ls'])" --auto-fix
```

### zen-capture

Capture and analyze error events.

```bash
# From log file
zen-capture --log error.log --output events/

# From text
zen-capture --text "ImportError: No module named 'numpy'"

# Watch directory
zen-capture --watch logs/ --output events/

# Analyze events
zen-capture --analyze events/
```

---

## Configuration

The Zen-Engine uses minimal configuration. All behavior is encoded in the ZenCodex.

To customize:

1. Edit `codex/zen.json` to add/modify rules
2. Create rule files in `codex/rules/` for complex patterns
3. Update `codex/indexes/tags.json` for custom categorization
4. Add glyphs to `codex/lore/glyphs/` for new semantic domains

---

## Extending the System

### Adding a New Rule

1. Identify error pattern
2. Create rule structure:
   ```python
   new_rule = {
       "id": "my_new_rule",
       "version": 1,
       "triggers": {
           "errors": ["error pattern"],
           "command_patterns": ["command regex"]
       },
       # ... rest of structure
   }
   ```
3. Add to `codex/zen.json`
4. Assign glyph (optional)
5. Test with `zen-check`

### Creating a New Agent

1. Create module in `agents/`
2. Import core components:
   ```python
   from zen_engine.agents import CodexLoader, Matcher
   ```
3. Implement agent logic
4. Register in orchestrator

---

## Philosophy

The Zen-Engine embodies these principles:

1. **Errors are Teachers** - Every mistake contains a lesson
2. **Prevention > Cure** - Intercept problems before they happen
3. **Narrative Aids Memory** - Stories help retention
4. **Systems Should Evolve** - Learn recursively from experience
5. **Multiple Perspectives** - Different agents see different patterns
6. **Wisdom is Layered** - Foundational → Intermediate → Advanced
7. **Automation with Consent** - Auto-fix when safe, suggest otherwise

---

## Roadmap

### v1.0 (Current)
- ✅ Core error detection
- ✅ Rule matching
- ✅ Command interception
- ✅ Glyph system
- ✅ CLI tools

### v1.1 (Planned)
- [ ] CodexBuilder (automatic rule generation)
- [ ] Multi-agent orchestrator
- [ ] Rule evolution tracking
- [ ] Web dashboard
- [ ] VS Code extension

### v2.0 (Future)
- [ ] Machine learning for pattern detection
- [ ] Cross-repository knowledge sharing
- [ ] Predictive error prevention
- [ ] Natural language rule queries
- [ ] Self-modification protocols

---

## Contributing

The Zen-Engine is designed to be extended. Contributions welcome:

1. Add new rules to the Codex
2. Create new glyphs for semantic domains
3. Extend agent capabilities
4. Improve matching algorithms
5. Write lore and documentation

---

## License

MIT License - See LICENSE file

---

## Acknowledgments

Built as part of the NuSyQ-Hub ecosystem, integrating:
- Culture Ship (Real action fixing)
- SimulatedVerse (Async agent communication)
- MultiAI Orchestrator (Agent coordination)
- Quantum Consciousness systems (Pattern analysis)

---

## Contact & Support

For questions, issues, or contributions:
- Open an issue in the repository
- Consult the Codex: `codex/zen.json`
- Read the lore: `codex/lore/`

---

**🧘 May your code flow like water, and your errors teach like masters.**

*Generated by Zen-Engine v1.0.0*
