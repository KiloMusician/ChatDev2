<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.directory.examples                                  ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [documentation, directory-guide, examples, tutorials]             ║
║ CONTEXT: Σ2 (Feature Layer)                                            ║
║ AGENTS: [AllAgents]                                                     ║
║ DEPS: [NuSyQ_Root_README.md, docs/guides/QUICK_START_MULTI_AGENT.md]               ║
║ INTEGRATIONS: [ΞNuSyQ-Framework]                                        ║
║ CREATED: 2025-10-07                                                     ║
║ UPDATED: 2025-10-07                                                     ║
║ AUTHOR: Claude Code                                                     ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# examples/ - Usage Examples & Demonstrations

## 📋 Quick Summary

**Purpose**: Practical examples demonstrating NuSyQ's multi-agent orchestration capabilities
**File Count**: 1 example (more to come)
**Last Updated**: 2025-10-07
**Maintenance**: Active (Growing)

---

## 🎯 What This Directory Does

The `examples/` directory provides **copy-paste-ready code** showing how to use NuSyQ's multi-agent system:

- **Agent orchestration patterns** - Turn-taking, consensus, parallel execution
- **Real-world workflows** - Code review, architecture debates, testing strategies
- **Integration examples** - ChatDev, Ollama, Claude Code collaboration
- **Best practices** - Cost optimization, session management, error handling

**Philosophy**: "Learn by example" - Working code you can run immediately.

---

## 📂 File Structure

### 🤖 Agent Orchestration

**`agent_orchestration_demo.py`** - Multi-Agent Collaboration Demo ✅ OmniTagged

**What it demonstrates**:
- Turn-taking conversation (2+ agents)
- Parallel consensus voting (3+ agents)
- Quick helper functions (`quick_turn_taking`, `quick_consensus`)
- Session result handling (turns, conclusion, cost, tokens)

**Usage**:
```bash
# Run the demo
python examples/agent_orchestration_demo.py

# Shows live multi-agent collaboration:
# - Agents debate REST vs GraphQL
# - Agents vote on Python vs Rust
# - Real Ollama API calls
# - $0.00 cost (free models)
```

**Key Concepts Shown**:
```python
from config.multi_agent_session import quick_turn_taking, quick_consensus

# Pattern 1: Turn-taking debate
result = quick_turn_taking(
    agents=["ollama_qwen_14b", "ollama_gemma_9b"],
    task="What's better: REST or GraphQL?",
    max_turns=4
)

# Pattern 2: Consensus voting
result = quick_consensus(
    agents=["ollama_qwen_14b", "ollama_gemma_9b", "ollama_qwen_7b"],
    task="Best language for web APIs: Python or Rust?"
)

# Access results
print(f"Agents: {result.agents_used}")
print(f"Cost: ${result.total_cost:.4f}")  # Always $0.00 for Ollama
print(f"Conclusion: {result.conclusion}")
```

**Status**: ✅ PRODUCTION READY (OmniTagged)

---

## 🚀 Quick Start

### For Users

**Run the demo**:
```bash
# Make sure Ollama is running
ollama list

# Run demo
python examples/agent_orchestration_demo.py

# Expected output:
# - 2 agents debating (turn-taking)
# - 3 agents voting (consensus)
# - Live conversation output
# - Final conclusion
# - Cost summary ($0.00)
```

**Adapt for your use case**:
```python
# Copy agent_orchestration_demo.py
# Modify the task prompts
# Add your own agents
# Change number of turns
```

### For Developers

**Creating a new example**:

1. **Create example file**:
   ```python
   # examples/my_workflow_demo.py
   """
   ╔══════════════════════════════════════════════════════════════════════╗
   ║ ΞNuSyQ OmniTag Metadata                                              ║
   ╠══════════════════════════════════════════════════════════════════════╣
   ║ FILE-ID: nusyq.examples.my-workflow                                  ║
   ║ TYPE: Python Script                                                  ║
   ║ STATUS: Production                                                   ║
   ║ VERSION: 1.0.0                                                       ║
   ║ TAGS: [examples, demonstration, my-workflow]                         ║
   ║ CONTEXT: Σ1 (Component Layer)                                       ║
   ║ AGENTS: [AllAgents]                                                  ║
   ║ DEPS: [config.multi_agent_session]                                   ║
   ║ INTEGRATIONS: [ΞNuSyQ-Framework, Ollama-API]                        ║
   ║ CREATED: YYYY-MM-DD                                                  ║
   ║ UPDATED: YYYY-MM-DD                                                  ║
   ║ AUTHOR: Your Name                                                    ║
   ║ STABILITY: Production                                                ║
   ╚══════════════════════════════════════════════════════════════════════╝

   Demonstrate: [What this example shows]

   Usage: python examples/my_workflow_demo.py
   """

   from config.multi_agent_session import quick_turn_taking

   def main():
       result = quick_turn_taking(
           agents=["ollama_qwen_14b", "ollama_gemma_9b"],
           task="Your task here",
           max_turns=4
       )
       print(result.conclusion)

   if __name__ == "__main__":
       main()
   ```

2. **Update this README** with example description

3. **Test the example**:
   ```bash
   python examples/my_workflow_demo.py
   ```

---

## 🔗 Dependencies

### Required
- **config/multi_agent_session.py** - Core orchestration system
- **Ollama** - Must be running with models downloaded

### Suggested Models
```bash
# Download recommended models for examples
ollama pull qwen2.5-coder:14b  # Primary reasoning
ollama pull qwen2.5-coder:7b   # Fast responses
ollama pull gemma2:9b          # Alternative perspective
```

---

## 📖 Related Documentation

### Essential Reading
- **[docs/guides/QUICK_START_MULTI_AGENT.md](../docs/guides/QUICK_START_MULTI_AGENT.md)** - Multi-agent tutorial
- **[config/NuSyQ_Root_README.md](../config/NuSyQ_Root_README.md)** - Configuration architecture
- **[docs/reference/MULTI_AGENT_ORCHESTRATION.md](../docs/reference/MULTI_AGENT_ORCHESTRATION.md)** - Orchestration design

### Guides
- **[NuSyQ_Root_README.md](../NuSyQ_Root_README.md)** - NuSyQ overview
- **[Guide_Contributing_AllUsers.md](../Guide_Contributing_AllUsers.md)** - How to contribute examples

---

## 🤖 AI Agent Notes

### Agents Using This Directory
- **All Agents** - Can learn from examples
- **Claude Code** - Creates new examples based on user workflows
- **ChatDev** - Uses examples as templates

### Context Level
**Σ1 (Component Layer)** - Demonstrates specific components/workflows

### Integration Points

**For Learning**:
- Read `agent_orchestration_demo.py` to understand multi-agent patterns
- Copy-paste code into your own scripts
- Modify task prompts for your use case

**For Documentation**:
- Examples serve as executable documentation
- Show real API usage (not theoretical)
- Prove system works ($0.00 cost with Ollama)

---

## 📊 Statistics

| Example | Lines | OmniTagged | Tested |
|---------|-------|------------|--------|
| `agent_orchestration_demo.py` | ~100 | ✅ Yes | ✅ Yes |

**Total Examples**: 1
**OmniTag Coverage**: 100% (1/1)
**Next Addition**: Code review workflow example

---

## 🎯 Planned Examples (Coming Soon)

### HIGH PRIORITY

1. **`code_review_workflow.py`** - Multi-agent code review
   - Reviewer agent analyzes code
   - Tester agent suggests test cases
   - Security agent checks vulnerabilities
   - Consensus on approval/changes

2. **`architecture_debate.py`** - Architecture decision-making
   - Multiple agents propose designs
   - Vote on best approach
   - Document reasoning

3. **`chatdev_integration.py`** - ChatDev + Ollama workflow
   - Generate software with ChatDev
   - Review with Ollama agents
   - Hybrid AI collaboration

### MEDIUM PRIORITY

4. **`cost_optimization.py`** - FREE vs PAID model selection
   - Show when to use Ollama (free)
   - Show when to escalate to Claude (paid)
   - Cost tracking demonstration

5. **`session_persistence.py`** - Multi-session conversations
   - Save conversation state
   - Resume from previous session
   - Long-term collaboration

6. **`error_handling.py`** - Robust error handling
   - Timeout management (ProcessTracker)
   - API failure recovery
   - Fallback strategies

---

## ⚠️ Important Notes

### For New Contributors

1. **Examples should be RUNNABLE immediately**
   - No complex setup required
   - Clear instructions in docstring
   - Real output examples in comments

2. **Use FREE models only** (Ollama)
   - Examples should cost $0.00
   - Don't require API keys
   - Work offline

3. **Keep examples FOCUSED**
   - One concept per example
   - 50-200 lines of code
   - Clear purpose in filename

### For AI Agents

1. **Learn from examples before creating new code**
   - Read `agent_orchestration_demo.py` first
   - Follow established patterns
   - Don't reinvent patterns

2. **Examples are EXECUTABLE DOCUMENTATION**
   - If example works, system works
   - If example breaks, investigate before blaming example
   - Examples validate system functionality

---

## 🔄 Recent Changes

### 2025-10-07: Directory Documentation Created
- Created this README (first documentation for examples/)
- Confirmed `agent_orchestration_demo.py` is OmniTagged
- Planned future examples (6 identified)

### 2025-10-06: OmniTag Integration
- Tagged `agent_orchestration_demo.py` with full metadata
- Established example tagging standard

---

## 📞 Maintainer

**Primary**: Claude Code (github_copilot)
**Repository**: NuSyQ
**Last Audit**: 2025-10-07

For questions or improvements, update this README and commit changes.

---

**Status**: ✅ DIRECTORY DOCUMENTED
**Example Coverage**: 1 example (more planned)
**OmniTag Coverage**: 100% (1/1 files)
**Next Action**: Create code_review_workflow.py, architecture_debate.py
