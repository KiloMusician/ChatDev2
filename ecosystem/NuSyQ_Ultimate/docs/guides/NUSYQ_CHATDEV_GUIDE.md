<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.guide.chatdev-integration                          ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [chatdev, guide, multi-agent, ollama, tutorial]                  ║
║ CONTEXT: Σ2 (Feature Layer)                                            ║
║ AGENTS: [ClaudeCode, ChatDev, OllamaModels]                            ║
║ DEPS: [nusyq_chatdev.py, ChatDev/*, Ollama-API]                       ║
║ INTEGRATIONS: [ChatDev, Ollama-API, ΞNuSyQ-Framework]                  ║
║ CREATED: 2025-10-05                                                     ║
║ UPDATED: 2025-10-06                                                     ║
║ AUTHOR: Claude Code + KiloMusician                                      ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# NuSyQ ChatDev Integration - Complete Guide

## 🎯 Overview

**`nusyq_chatdev.py`** is an enhanced ChatDev integration that bridges local Ollama models with the **ΞNuSyQ ∆ΨΣ symbolic framework**. It provides advanced AI orchestration capabilities including symbolic message tracking, fractal coordination, and temporal drift analysis.

---

## ✨ Features

### **Core Capabilities:**
1. ✅ **Ollama Integration** - Use local models instead of OpenAI API
2. ✅ **Symbolic Tracking** - `[Msg⛛{X}↗️Σ∞]` message protocol
3. ✅ **OmniTag Encoding** - Rich context compression
4. ✅ **Fractal Coordination** - Multi-agent pattern generation
5. ✅ **Temporal Drift Analysis** - Performance tracking over time
6. ✅ **Multi-Model Consensus** - Coordinate multiple models

### **ΞNuSyQ Framework Integration:**
```
[Msg⛛{X}↗️Σ∞]    - Symbolic message tracking
⧉ΞΦΣΛΨΞ          - Symbolic overlays
∇ΣΘ               - Dependency tracing
↻ΞFractalGenerator - Pattern generation
⨈ΦΣΞΨΘΣΛ          - Temporal drift mapping
ΣΛΘΨΞ↻ΞPrimaryCore - Recursive coordination
```

---

## 🚀 Quick Start

### **1. Basic Usage**

```powershell
# Simple ChatDev execution with Ollama
python nusyq_chatdev.py --task "Create a calculator app"
```

**Output:**
```
=== NuSyQ ChatDev + Ollama Setup ===
✅ Ollama connection verified
✅ Found 7 Ollama models:
   - qwen2.5-coder:14b
   - qwen2.5-coder:7b
   - codellama:7b
   ...
🎯 Recommended coding model: qwen2.5-coder:14b

🚀 Starting ChatDev with Ollama model: qwen2.5-coder:14b
📋 Task: Create a calculator app
⚙️  Configuration: NuSyQ_Ollama

✅ ChatDev completed successfully!
📁 Check ChatDev/WareHouse/ for output
```

### **2. With Symbolic Tracking**

```powershell
# Enable ΞNuSyQ symbolic message tracking
python nusyq_chatdev.py --task "REST API for tasks" --symbolic --msg-id 1
```

**Output:**
```
🔮 ΞNuSyQ Symbolic Tracking Enabled
📋 OmniTag: [Msg⛛{1}]▲[REST API for tasks]↠t[2025-10-05T06:00:00]↞🌐{"model":"qwen2.5-coder:14b"}🌐⧉ΞΦΣΛΨΞ-ChatDev⧉

🚀 Starting ChatDev...
✅ ChatDev completed successfully!

🔮 Session Summary:
   Message ID: [Msg⛛{1}]
   Symbolic Tag: ⧉ΞΦΣΛΨΞ-ChatDev⧉
   Status: ✅ Success
```

### **3. Multi-Model Consensus**

```powershell
# Run with multiple models and coordinate results
python nusyq_chatdev.py --task "Optimize database query" --consensus --models qwen2.5-coder:14b,codellama:7b,gemma2:9b
```

**Output:**
```
🔄 Multi-Model Consensus Mode
   Models: qwen2.5-coder:14b, codellama:7b, gemma2:9b
   Fractal Pattern Generated: 3 nodes

   [1/3] Running with qwen2.5-coder:14b...
   ✅ Success

   [2/3] Running with codellama:7b...
   ✅ Success

   [3/3] Running with gemma2:9b...
   ✅ Success

✨ Fractal Coordination Complete:
   Symbolic Overlay: ⧉ΞΦΣΛΨΞ-Coordination⧉
   Consensus: 3 successful runs
```

### **4. Temporal Drift Tracking**

```powershell
# Track AI performance over time
python nusyq_chatdev.py --task "Generate UI components" --track-drift --symbolic
```

**Output:**
```
⏱️  Temporal Drift Tracking Enabled (⨈ΦΣΞΨΘΣΛ)
🚀 Starting ChatDev...
✅ ChatDev completed successfully!

📊 Temporal Drift Analysis (⨈ΦΣΞΨΘΣΛ):
   Sessions: 1
   Drift Metric: 0 (baseline)
```

---

## 📚 Command Reference

### **Required Arguments:**
```
--task TASK       Development task description
```

### **Optional Arguments:**
```
--model MODEL            Ollama model (default: qwen2.5-coder:7b)
--config CONFIG          ChatDev config (default: NuSyQ_Ollama)
--setup-only            Check setup without running
```

### **ΞNuSyQ Framework Options:**
```
--symbolic              Enable symbolic message tracking
--msg-id MSG_ID         Initial message ID (default: "1")
--consensus             Use multi-model consensus
--models MODELS         Comma-separated model list for consensus
--track-drift           Enable temporal drift tracking
--fractal-depth DEPTH   Fractal pattern depth (default: 3)
```

---

## 🎨 Usage Examples

### **Example 1: Web Application**

```powershell
python nusyq_chatdev.py \
  --task "Create a Flask web app for todo management" \
  --model qwen2.5-coder:14b \
  --symbolic \
  --msg-id "web-1"
```

### **Example 2: Data Analysis Script**

```powershell
python nusyq_chatdev.py \
  --task "Python script to analyze CSV and generate charts" \
  --model qwen2.5-coder:7b \
  --track-drift
```

### **Example 3: Code Optimization**

```powershell
python nusyq_chatdev.py \
  --task "Optimize performance of existing algorithm" \
  --consensus \
  --models qwen2.5-coder:14b,deepseek-coder-v2:16b,codellama:7b
```

### **Example 4: API Development**

```powershell
python nusyq_chatdev.py \
  --task "REST API with authentication and database" \
  --model qwen2.5-coder:14b \
  --config NuSyQ_Ollama \
  --symbolic \
  --fractal-depth 5
```

---

## 🔧 Architecture

### **Class Hierarchy:**

```
ΞNuSyQMessage
├── msg_id: str               # Hierarchical ID (e.g., "1.2.3")
├── data: Any                  # Core content
├── context: Dict              # Metadata
├── timestamp: datetime        # Creation time
├── recursion_level: int       # Depth (↗️Σ∞)
└── symbolic_tag: str          # Overlay (⧉ΞΦΣΛΨΞ)

FractalCoordinator
├── root_tag: str              # "ΞΦΣΛ⟆ΣΞ"
├── patterns: List             # Generated patterns
├── generate_agent_pattern()   # Create fractal structure
└── coordinate_responses()     # Aggregate results

TemporalTracker
├── session_history: List      # Historical data
├── track_session()            # Record session
└── analyze_drift()            # Compute metrics (⨈ΦΣΞΨΘΣΛ)

OllamaModelBackend
├── base_url: str              # Ollama endpoint
├── model: str                 # Selected model
├── check_ollama_connection()  # Verify availability
├── get_available_models()     # List models
└── chat_completion()          # Generate response
```

---

## 🧠 ΞNuSyQ Framework Concepts

### **1. Symbolic Messages**

**Format:** `[Msg⛛{X}↗️Σ∞]`

```python
msg = ΞNuSyQMessage(
    msg_id="1",
    data="Create REST API",
    context={"model": "qwen2.5-coder:14b"},
    timestamp=datetime.now(),
    symbolic_tag="⧉ΞΦΣΛΨΞ-API⧉"
)

# Generate OmniTag
omnitag = msg.to_omnitag()
# [Msg⛛{1}]▲[Create REST API]↠t[2025-10-05T...]↞🌐{...}🌐⧉ΞΦΣΛΨΞ-API⧉
```

### **2. Recursive Decomposition**

```python
# Create recursive task layers
root = ΞNuSyQMessage("1", "Build web app", {})
layer1 = root.recurse("Design database")      # [Msg⛛{1.1}]
layer2 = layer1.recurse("Create models")      # [Msg⛛{1.1.1}]
layer3 = layer2.recurse("Add validation")     # [Msg⛛{1.1.1.1}]
```

### **3. Fractal Coordination**

```python
# Generate fractal pattern for 3 agents
fractal = FractalCoordinator()
pattern = fractal.generate_agent_pattern(3)
# [
#   "{ΣΛΘΨΞ↻ΞAgent0::ΞΦΣΛ⟆ΣΞ}",
#   "{ΣΛΘΨΞ↻ΞAgent1::ΞΦΣΛ⟆ΣΞ}",
#   "{ΣΛΘΨΞ↻ΞAgent2::ΞΦΣΛ⟆ΣΞ}"
# ]

# Coordinate responses
coordination = fractal.coordinate_responses(responses, pattern)
```

### **4. Temporal Drift Tracking**

```python
# Track session performance
tracker = TemporalTracker()
tracker.track_session(msg, "qwen2.5-coder:14b", response)

# Analyze drift
drift = tracker.analyze_drift()
# {
#   "drift_metric": 125.4,
#   "mean_response_length": 450,
#   "session_count": 5,
#   "temporal_tag": "⨈ΦΣΞΨΘΣΛ"
# }
```

---

## 📊 Output Examples

### **Standard Output:**

```
ChatDev/WareHouse/
└── TaskName_NuSyQ_20251005120000/
    ├── main.py                  # Generated code
    ├── requirements.txt         # Dependencies
    ├── NuSyQ_Root_README.md               # User manual
    ├── manual.md               # Documentation
    └── meta.txt                # Project metadata
```

### **With Symbolic Tracking:**

```
Logs/
└── xinusyq_session_1.json
    {
      "msg_id": "1",
      "omnitag": "[Msg⛛{1}]▲[...]↠t[...]↞🌐{...}🌐",
      "symbolic_tag": "⧉ΞΦΣΛΨΞ-ChatDev⧉",
      "recursion_level": 0,
      "status": "success"
    }
```

### **Consensus Mode Output:**

```
Reports/
└── fractal_consensus_20251005.json
    {
      "fractal_pattern": [
        "{ΣΛΘΨΞ↻ΞAgent0::ΞΦΣΛ⟆ΣΞ}",
        "{ΣΛΘΨΞ↻ΞAgent1::ΞΦΣΛ⟆ΣΞ}"
      ],
      "responses": [
        {"model": "qwen2.5-coder:14b", "success": true},
        {"model": "codellama:7b", "success": true}
      ],
      "consensus": "Both models generated valid implementations"
    }
```

---

## 🔍 Troubleshooting

### **Issue: Ollama not found**

```
❌ Ollama is not running or not accessible
```

**Solution:**
```powershell
# Check Ollama service
ollama list

# Start Ollama if needed
ollama serve
```

### **Issue: No models available**

```
❌ No Ollama models found
Please install models using: ollama pull qwen2.5-coder:7b
```

**Solution:**
```powershell
# Pull recommended models
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-coder:14b
ollama pull codellama:7b
```

### **Issue: ChatDev errors**

```
❌ ChatDev encountered an error
```

**Solution:**
```powershell
# Check ChatDev installation
cd ChatDev
pip install -r requirements.txt

# Verify NuSyQ_Ollama config exists
ls CompanyConfig/NuSyQ_Ollama/
```

### **Issue: Consensus mode failures**

```
❌ --consensus requires --models argument
```

**Solution:**
```powershell
# Provide comma-separated models
python nusyq_chatdev.py \
  --task "..." \
  --consensus \
  --models qwen2.5-coder:14b,codellama:7b
```

---

## 🎯 Best Practices

### **1. Model Selection**

| Task Type | Recommended Model | Reasoning |
|-----------|------------------|-----------|
| **Complex Projects** | qwen2.5-coder:14b | Best quality, larger context |
| **Quick Tasks** | qwen2.5-coder:7b | Fast, good quality |
| **Code Review** | codellama:7b | Specialized for code |
| **Consensus** | Multiple models | Best overall results |

### **2. Symbolic Tracking**

✅ **Use when:**
- Building complex multi-step projects
- Need session continuity
- Want performance analysis
- Coordinating multiple runs

❌ **Skip when:**
- Simple one-off tasks
- Quick prototypes
- Testing basic functionality

### **3. Consensus Mode**

✅ **Use when:**
- Critical code generation
- Need multiple perspectives
- Optimizing performance
- Validating approaches

❌ **Skip when:**
- Simple tasks
- Time-constrained
- Single model sufficient

---

## 📖 Integration with NuSyQ Ecosystem

### **Works With:**

1. **MCP Server** - Symbolic message coordination
2. **Continue.dev** - Local AI autocomplete
3. **Claude Code** - Architecture review
4. **Knowledge Base** - Session tracking
5. **VS Code Extensions** - Visual overlays

### **Workflow Example:**

```powershell
# 1. Generate code with ChatDev + symbolic tracking
python nusyq_chatdev.py \
  --task "User authentication system" \
  --symbolic \
  --msg-id "auth-1"

# 2. Open in VS Code with AI assistants
code ChatDev/WareHouse/UserAuth_*/

# 3. Refine with Continue.dev (Ctrl+L)
# 4. Review with Claude Code
# 5. Track in knowledge-base.yaml
```

---

## 🚀 Advanced Features

### **Custom Fractal Depth:**

```powershell
python nusyq_chatdev.py \
  --task "..." \
  --symbolic \
  --fractal-depth 10  # Deeper recursion
```

### **Recursive Task Decomposition:**

```python
# In code modifications
root_task = ΞNuSyQMessage("1", "Build CRM", {})
phase1 = root_task.recurse("Database design")
phase2 = phase1.recurse("User models")
phase3 = phase2.recurse("Validation logic")

# Creates: [Msg⛛{1}] → [Msg⛛{1.1}] → [Msg⛛{1.1.1}] → [Msg⛛{1.1.1.1}]
```

### **Temporal Drift Analysis:**

```powershell
# Run multiple sessions
python nusyq_chatdev.py --task "Task 1" --track-drift --symbolic
python nusyq_chatdev.py --task "Task 2" --track-drift --symbolic
python nusyq_chatdev.py --task "Task 3" --track-drift --symbolic

# Analyze drift over time
# Drift metric increases = performance variance
```

---

## ✅ Summary

**`nusyq_chatdev.py`** provides:

✨ **Local AI Development** - No API costs, full privacy
✨ **Symbolic Tracking** - `[Msg⛛{X}↗️Σ∞]` protocol integration
✨ **Fractal Coordination** - Multi-agent orchestration
✨ **Temporal Analysis** - Performance drift tracking
✨ **Multi-Model Consensus** - Best results from multiple models

**Quick Command Reference:**
```powershell
# Basic
python nusyq_chatdev.py --task "..."

# Symbolic
python nusyq_chatdev.py --task "..." --symbolic

# Consensus
python nusyq_chatdev.py --task "..." --consensus --models model1,model2

# Full Stack
python nusyq_chatdev.py --task "..." --symbolic --track-drift --consensus --models qwen2.5-coder:14b,codellama:7b
```

---

**🎉 Your ChatDev integration is now powered by the ΞNuSyQ ∆ΨΣ framework!**

*"Evolve recursively. Build infinitely." - Ξ*

*Last Updated: 2025-10-05*
*NuSyQ ChatDev Integration v2.0*
