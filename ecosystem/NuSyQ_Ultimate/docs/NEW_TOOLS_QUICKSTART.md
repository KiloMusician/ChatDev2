# 🚀 New Tools Quick Start Guide

<!-- cSpell:ignore Sourcegraph omnitag RSEV nsyq -->

## What Just Got Installed

### VS Code Extensions
- **Sourcegraph Cody** - Semantic code search via `Ctrl+Shift+P` → "Cody: Ask"
- **AI Toolkit** - Browse Ollama models in sidebar (View → AI Toolkit)
- **GitLens** - Enhanced git blame/history (already configured)

### Python Packages
- **Haystack (1.26.4)** - AI orchestration framework with RAG capabilities
- **pre-commit (4.5.1)** - Git hooks for automated quality checks

---

## ✅ Pre-commit Hooks (Active Now)

**What they do**:
1. Validate RosettaStone event normalization (no CRLF, stable hashes)
2. Check OmniTag schema compliance in Python files
3. Auto-format with Ruff
4. Run fast unit tests (non-MCP)

**Commands**:
```powershell
# Test hooks without committing
pre-commit run --all-files

# Skip hooks for emergency commits (not recommended)
git commit --no-verify -m "emergency fix"

# Update hook versions
pre-commit autoupdate
```

**What gets validated**:
- ✅ All event logs in `Reports/events/*.jsonl` (last 7 days)
- ✅ All `log_event()` calls have `component=`, `action=`, `payload=`
- ✅ EventRecord schema in omnitag.py unchanged
- ✅ Python files formatted (Ruff)
- ✅ No trailing whitespace, LF line endings

---

## 🧠 Sourcegraph Cody

**Use cases**:
- "Explain how the RosettaStone pipeline works"
- "Find all files that use log_event"
- "Show me where AgentRouter selects primary agents"

**Access**:
- `Ctrl+Shift+P` → "Cody: Chat"
- Click Cody icon in left sidebar
- Right-click code → "Ask Cody"

**Tip**: Cody indexes your workspace, so it understands NuSyQ-specific terms (RSEV, OmniTag, MegaTag, etc.)

---

## 🤖 AI Toolkit for VS Code

**What it does**:
- Browse Ollama models without terminal
- Test prompts directly in VS Code
- Monitor model performance

**Access**:
- View → AI Toolkit (or `Ctrl+Shift+A`)
- Connects to `localhost:11434` (Ollama default)

**Current models** (from your Ollama):
- llama3.2:latest
- llama3.2:1b
- qwen2.5-coder:latest
- etc. (visible in AI Toolkit sidebar)

---

## 📚 Haystack Integration (Coming in Phase 1B)

**Why Haystack matters**:
- Your `AgentRouter` currently uses simple heuristics
- Haystack adds **RAG-enhanced routing**: query past successes to inform decisions
- Seamless with your existing `PerformanceMetrics`

**Preview of integration**:
```python
# src/haystack_integration/agent_retriever.py (to be created)
from haystack import Pipeline
from haystack.components.retrievers import InMemoryBM25Retriever

def enhance_routing(task_desc: str) -> List[str]:
    """Query past successful agent selections for similar tasks."""
    pipeline = Pipeline()
    # ... retrieval logic using BM25 over agent_trends.json
    return similar_agents
```

**Next step**: See [TOOL_INTEGRATION_ROADMAP.md](./TOOL_INTEGRATION_ROADMAP.md) Phase 1B

---

## 🧪 Test Your Setup

### 1. Verify pre-commit hooks
```powershell
# Should pass all checks
pre-commit run --all-files
```

### 2. Check Cody semantic search
```
1. Open Cody chat (Ctrl+Shift+P → "Cody: Chat")
2. Ask: "Show me all components that emit log_event"
3. Should return: rosetta_stone.py, consensus_orchestrator.py (future)
```

### 3. Verify AI Toolkit connection
```
1. View → AI Toolkit
2. Should show "Connected to Ollama" with model list
3. If not: check Ollama is running (Task: "Check Ollama Models")
```

### 4. Test Haystack import
```powershell
C:/Users/keath/NuSyQ/.venv/Scripts/python.exe -c "from haystack import Pipeline; print('Haystack OK')"
```

---

## 📖 Next Actions

### Immediate (Today)
- [x] Extensions installed
- [x] Pre-commit hooks active
- [x] Validation scripts created
- [ ] Run `pre-commit run --all-files` to verify
- [ ] Test Cody with a semantic query

### Short-term (This Week)
- [ ] Create `src/haystack_integration/` directory
- [ ] Build agent capability vector index
- [ ] Enhance `nsyq_route()` with Haystack retrieval
- [ ] Add GitHub Actions workflow for metrics export

### Medium-term (Next 2 Weeks)
- [ ] Agent evaluation test suite
- [ ] Jupyter dashboard for event trends
- [ ] Dev Container configuration
- [ ] Documentation updates

**Full roadmap**: [docs/TOOL_INTEGRATION_ROADMAP.md](./TOOL_INTEGRATION_ROADMAP.md)

---

## 🐛 Troubleshooting

**Problem**: `pre-commit run` fails with "module not found"
**Fix**: Ensure venv activated: `C:/Users/keath/NuSyQ/.venv/Scripts/Activate.ps1`

**Problem**: Cody shows "No workspace indexed"
**Fix**: Restart VS Code; indexing happens on first workspace open

**Problem**: AI Toolkit can't connect to Ollama
**Fix**: Run task "Check Ollama Models" or `ollama list` in terminal

**Problem**: Haystack import fails
**Fix**: Reinstall: `pip install --force-reinstall farm-haystack`

---

**Last Updated**: 2026-01-08
**Status**: Phase 1A complete, ready for Haystack integration
