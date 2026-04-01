# SNS-CORE Quick Reference for NuSyQ Developers

**Last Updated**: October 13, 2025  
**Version**: 1.0  
**Status**: Production-Ready ✅

---

## 🚀 Quick Start (30 seconds)

```python
from src.ai.sns_core_integration import SNSCoreHelper

helper = SNSCoreHelper()

# Convert natural language → SNS
traditional = "Extract keywords, classify intent, return results"
sns = helper.convert_to_sns(traditional)

# Get template for common use case
template = helper.get_sns_template("orchestrator")

# Validate SNS notation
is_valid, errors = helper.validate_sns("q → kw_extract → kw")
```

---

## 📖 Core Patterns

| Pattern         | Notation | Example                         | Use Case              |
| --------------- | -------- | ------------------------------- | --------------------- |
| **Flow**        | `→`      | `query → analyze → result`      | Sequential operations |
| **Pipeline**    | `\|`     | `data \| filter \| sort`        | Data transformations  |
| **Conditional** | `? :`    | `valid ? process : reject`      | If-then-else logic    |
| **Composition** | `+`      | `(keywords + context) → search` | Combine inputs        |
| **Parallel**    | `∥`      | `task1 ∥ task2 ∥ task3`         | Concurrent execution  |
| **Filter**      | `>>`     | `docs >> filter(score > 0.7)`   | Selection/filtering   |
| **Assignment**  | `=`      | `result = process(input)`       | Variable binding      |

---

## 🎯 NuSyQ Abbreviations

```python
ABBREVIATIONS = {
    "query": "q",              # User query/input
    "keywords": "kw",          # Extracted keywords
    "documents": "docs",       # Document collection
    "categories": "cats",      # Classification categories
    "intent": "intent",        # User intent
    "agent": "agent",          # AI agent
    "orchestrator": "orch",    # Orchestrator system
    "consciousness": "cons",   # Consciousness bridge
    "semantic": "sem",         # Semantic analysis
    "context": "ctx",          # Context information
    "parameters": "params",    # Function parameters
    "response": "resp"         # System response
}
```

---

## 📚 Use Case Templates

### 1. Multi-AI Orchestrator

```sns
# Multi-AI Orchestrator
task → classify(systems) → target
task → extract_params → params
target + params → route → {system, params, format}
```

**When to use**: Routing tasks across AI systems (Copilot, Ollama, ChatDev,
etc.)

---

### 2. ChatDev Agent Communication

```sns
# ChatDev Agent Communication
@{from_agent} → @{to_agent}:
task → analyze → {requirements, approach}
→ response
```

**When to use**: Agent-to-agent messages (CEO → CTO, etc.)

---

### 3. Quantum Problem Resolver

```sns
# Quantum Problem Resolver
error → classify(types) → type
type == "import" ? fix_import :
type == "config" ? check_secrets :
type == "deps" ? install :
escalate
```

**When to use**: Error analysis and automated resolution

---

### 4. Consciousness Bridge

```sns
# Consciousness Bridge
change → intent_extract → intent
change → deps_trace → affected
change → consciousness_impact → impact
(change + affected + impact) → update_awareness → new_state
```

**When to use**: Semantic awareness and context tracking

---

### 5. Ollama Model Router

```sns
# Ollama Model Router
task → classify(models) → best_model
task + best_model → format_request → {model, prompt, params}
```

**When to use**: Selecting optimal Ollama model for task

---

### 6. RAG Orchestrator

```sns
# RAG Orchestrator
q → kw_extract → kw
q → classify(intents) → intent
(kw + q) → expand_q → terms
terms → retrieve(docs) → results
results >> rank(score > 0.7) → top_docs
```

**When to use**: Retrieval-Augmented Generation pipelines

---

## 🔧 Integration Methods

### Method 1: Direct Helper (Simple)

```python
from src.ai.sns_core_integration import SNSCoreHelper

helper = SNSCoreHelper()

# Basic conversion
traditional = "Your verbose prompt here..."
sns = helper.convert_to_sns(traditional)

# Token comparison
metrics = helper.compare_token_counts(traditional, sns)
print(f"Saved {metrics['savings_percent']:.1f}%")
```

---

### Method 2: Templates (Recommended)

```python
# Get pre-built template
template = helper.get_sns_template("orchestrator")

# Customize for your task
customized = f"""
# My Task
{template}
# Additional logic here
"""
```

---

### Method 3: Orchestrator Adapter (Production)

```python
from src.orchestration.sns_orchestrator_adapter import (
    SNSOrchestratorAdapter,
    SNSMode
)

# Create orchestrator
orch = SNSOrchestratorAdapter(sns_mode=SNSMode.ENABLED)

# Execute with SNS
result = await orch.execute_task_sns(
    "Analyze code security",
    task_type="analysis"
)

# Check metrics
if 'sns_metrics' in result:
    print(f"Saved: {result['sns_metrics']['savings_percent']}")
```

---

## 📊 Token Savings Examples

### Example 1: Simple Task

```python
# Traditional (35.1 tokens)
traditional = """
Extract the main keywords from this query and return them as a list.
Query: "loud music complaint from neighbor at night"
Return format: JSON list of keywords
"""

# SNS-CORE (20.8 tokens) - 40.7% savings
sns = """
q → kw_extract → kw
q = "loud music complaint from neighbor at night"
→ [kw]
"""
```

---

### Example 2: Medium Task

```python
# Traditional (35.1 tokens)
traditional = """
Classify the user's intent for this query into one of these categories:
- information
- complaint
- procedure
Query: "how to pay property tax online"
Return the category name only.
"""

# SNS-CORE (19.5 tokens) - 44.4% savings
sns = """
q → classify(['information','complaint','procedure']) → intent
q = "how to pay property tax online"
→ intent
"""
```

---

### Example 3: Complex Task

```python
# Traditional (66.3 tokens)
traditional = """
You are a RAG orchestrator. For the given query:
1. Extract the main keywords
2. Classify the intent (information, complaint, or procedure)
3. Expand the query into search terms
4. Return a structured JSON with: keywords, intent, search_terms
Query: "neighbor noise at night what can I do"
Return structured JSON only.
"""

# SNS-CORE (40.3 tokens) - 39.2% savings
sns = """
q → kw_extract → kw
q → classify(['info','complaint','procedure']) → intent
(kw + q) → expand_q → terms
q = "neighbor noise at night what can I do"
→ {kw, intent, terms}
"""
```

**Average**: **41% token reduction** across examples

---

## ✅ Validation

### Valid SNS Notation

```python
# Flow
"q → kw_extract → kw"                           ✅ Valid

# Pipeline
"data | filter | sort | top(5)"                  ✅ Valid

# Conditional
"valid ? process : reject"                       ✅ Valid

# Function with parameters
"task → classify(['a','b','c']) → result"       ✅ Valid

# Composition
"(input1 + input2) → process → output"          ✅ Valid
```

---

### Invalid SNS Notation

```python
# Unbalanced brackets
"query → keywords → (missing"                    ❌ Invalid

# Missing operator
"query keywords result"                          ❌ Invalid

# Invalid symbols
"query # process * result"                       ❌ Invalid
```

---

## 🎛️ Operation Modes

### SNSMode.DISABLED

```python
orch = SNSOrchestratorAdapter(sns_mode=SNSMode.DISABLED)
# Uses traditional prompts only
```

---

### SNSMode.ENABLED

```python
orch = SNSOrchestratorAdapter(sns_mode=SNSMode.ENABLED)
# Uses SNS-CORE notation only
```

---

### SNSMode.AB_TEST

```python
orch = SNSOrchestratorAdapter(sns_mode=SNSMode.AB_TEST)
# Runs both traditional and SNS, compares results
result = await orch.execute_task_sns("task")
print(result['comparison'])  # Token savings, response match, etc.
```

---

### SNSMode.AUTO

```python
orch = SNSOrchestratorAdapter(sns_mode=SNSMode.AUTO)
# Auto-selects SNS for complex tasks (>50 tokens)
```

---

## 📈 Metrics and Reporting

### Get Metrics Summary

```python
summary = orch.get_sns_metrics_summary()
print(summary)

# Output:
# {
#   'total_tasks': 42,
#   'total_traditional_tokens': 5432,
#   'total_sns_tokens': 3204,
#   'total_tokens_saved': 2228,
#   'average_savings_percent': '41.0%',
#   'average_compression_ratio': '1.70x',
#   'estimated_annual_savings': '$69.83/year'
# }
```

---

### Export Metrics to JSON

```python
from pathlib import Path

output = Path("sns_metrics.json")
orch.export_sns_metrics(output)
```

---

## 🐛 Troubleshooting

### Issue: Import Error

```python
# Error: No module named 'src'

# Solution 1: Run as module
python -m src.orchestration.sns_orchestrator_adapter

# Solution 2: Add to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

### Issue: Validation Fails

```python
# Check what went wrong
is_valid, errors = helper.validate_sns(sns_prompt)
if not is_valid:
    print(f"Errors: {errors}")
    # Fix issues or fallback to traditional
```

---

### Issue: Timeout on Complex Prompt

```python
# Solution 1: Increase timeout
response = requests.post(url, json=payload, timeout=60)  # Was 30

# Solution 2: Chunk into smaller operations
result1 = ollama.generate("q → kw_extract → kw")
result2 = ollama.generate("q → classify → intent")
combined = {**result1, **result2}
```

---

## 💡 Best Practices

### ✅ DO

- ✅ Use templates for common patterns
- ✅ Validate SNS notation before execution
- ✅ Enable A/B testing during rollout
- ✅ Track metrics for ROI measurement
- ✅ Fallback to traditional on validation errors

---

### ❌ DON'T

- ❌ Mix SNS and traditional in same prompt
- ❌ Skip validation in production
- ❌ Use SNS for trivial tasks (<20 tokens)
- ❌ Ignore timeout issues on complex prompts
- ❌ Deploy without A/B testing first

---

## 📚 Resources

### Documentation

- **SNS-CORE Guide**: `docs/SNS-CORE/README.md`
- **Core Patterns**: `docs/SNS-CORE/core-patterns.md`
- **Philosophy**: `docs/SNS-CORE/philosophy.md`
- **Quick Start**: `docs/SNS-CORE/QUICKSTART.md`

### Code

- **Integration Module**: `src/ai/sns_core_integration.py`
- **Orchestrator Adapter**: `src/orchestration/sns_orchestrator_adapter.py`
- **Simple Demo**: `examples/sns_simple_demo.py`
- **Orchestrator Demo**: `examples/sns_orchestrator_demo.py`

### External

- **GitHub Repository**: https://github.com/EsotericShadow/sns-core
- **License**: MIT (free and open)

---

## 🎯 Quick Tips

1. **Start Simple**: Begin with `SNSMode.AUTO` to ease into SNS
2. **Use Templates**: Don't reinvent the wheel, use pre-built templates
3. **Validate First**: Always validate SNS before execution
4. **Track Metrics**: Monitor token savings and response quality
5. **A/B Test**: Validate accuracy before full rollout

---

## 📞 Support

**Questions?** Check:

1. `docs/SNS-CORE/README.md` - Complete guide
2. `examples/sns_simple_demo.py` - Working examples
3. `docs/Agent-Sessions/SNS_CORE_PHASE_2_COMPLETE.md` - Full documentation

---

**🚀 Happy SNS-CORE coding!**
