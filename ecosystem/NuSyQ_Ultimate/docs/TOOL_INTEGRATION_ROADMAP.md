# NuSyQ Tool Integration Roadmap
<!-- cSpell:ignore Sourcegraph sourcegraph rsev omnitag FAISS nsyq matplotlib eamodio Plotly ipynb Simpliflow Milvus RSEV coala -->

## ✅ Installed (2026-01-08)

### VS Code Extensions
- ✅ **Sourcegraph Cody** (1.136.0) - Semantic code search + AI Q&A
- ✅ **GitLens** (17.8.1) - Git insights and history
- ✅ **Docker** (2.0.0) - Container management
- ✅ **Test Explorer** (2.22.1) - Unified test UI
- ✅ **Python Test Adapter** (0.8.2) - pytest integration
- ✅ **AI Toolkit** (0.28.0) - Local model control plane
- ✅ **Dev Containers** (0.434.0) - Containerized dev environments

### Python Packages
- ✅ **Haystack** (1.26.4) - RAG + AI orchestration framework
- ✅ **pre-commit** (4.5.1) - Git hooks for quality gates

## 🎯 Phase 1: Observability + Quality (Next 2 weeks)

### A. Pre-commit Integration
**Why**: Enforce RosettaStone normalization + OmniTag validation at commit time

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: rsev-normalize
        name: RosettaStone Normalize
        entry: python scripts/pre_commit_rsev.py
        language: system
        pass_filenames: false
      - id: omnitag-validate
        name: OmniTag Schema Check
        entry: python scripts/pre_commit_omnitag.py
        language: system
        files: '^(src|tests)/.*\.py$'
```

**Tasks**:
1. Create `scripts/pre_commit_rsev.py` - validate staged files against RS schema
2. Create `scripts/pre_commit_omnitag.py` - check event log integrity
3. Run `pre-commit install` to activate hooks

### B. Haystack Agent Router Enhancement
**Why**: Replace simple AgentRouter with Haystack pipelines for RAG-enhanced routing

**Integration Points**:
- Query agent capabilities via vector search (embed agent descriptions)
- Retrieve past successful routing decisions for similar tasks
- Feed into catalyst_evolve for data-driven suggestions

**Tasks**:
1. Create `src/haystack_integration/agent_retriever.py`
2. Embed agent profiles into vector store (FAISS/in-memory)
3. Modify `nsyq_route()` to query Haystack pipeline before AgentRouter

### C. Cody Semantic Search for Event Analysis
**Why**: Natural language queries over OmniTag event logs

**Tasks**:
1. Index `Reports/events/*.jsonl` into Cody workspace
2. Create saved queries: "Show all routing failures for BUG_FIX tasks"
3. Document in `docs/OBSERVABILITY_GUIDE.md`

## 🚀 Phase 2: Workflow Orchestration (Weeks 3-4)

### D. Temporal Integration (Optional - for production)
**Why**: Durable execution for long-running agent workflows

**Alternative**: Leverage existing `consensus_orchestrator.py` + enhance with retry/checkpoint logic

**Decision**: Skip Temporal for now; enhance current orchestrator with:
- Checkpoint persistence to `State/checkpoints/*.json`
- Retry logic with exponential backoff
- Event-driven resume from last good state

### E. GitHub Actions Pipeline
**Why**: Automate event analysis + agent trend reports on push

```yaml
# .github/workflows/nusyq-metrics.yml
name: NuSyQ Metrics
on: [push, schedule]
jobs:
  export-trends:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Export Agent Trends
        run: python scripts/export_agent_trends.py
      - name: Export Event Index
        run: python scripts/export_event_index.py
      - uses: actions/upload-artifact@v4
        with:
          name: metrics
          path: Reports/
```

**Tasks**:
1. Create `.github/workflows/nusyq-metrics.yml`
2. Add artifact retention policy (7 days)
3. Optional: Generate trend visualizations with matplotlib

## 🧪 Phase 3: Evaluation Framework (Weeks 5-6)

### F. Agent Evaluation Suite
**Why**: Systematic testing of routing decisions + agent performance

**Framework**:
```python
# tests/evaluation/test_routing_quality.py
@pytest.mark.parametrize("task_desc,expected_agent", [
    ("Fix Python import bug", "Python"),
    ("Debug async race condition", "Python"),
    ("Optimize database query", "DataOps"),
])
def test_routing_accuracy(task_desc, expected_agent):
    route = nsyq_route(task_desc, TaskType.BUG_FIX, TaskComplexity.SIMPLE)
    assert route["primary_agent"] == expected_agent
```

**Tasks**:
1. Create `tests/evaluation/` directory
2. Build test dataset from past successful events
3. Run weekly regression suite via GitHub Actions

### G. Haystack Evaluation Metrics
**Why**: Quantify retrieval quality for agent selection

**Tasks**:
1. Implement `evaluate_agent_retrieval()` using Haystack metrics
2. Log results to OmniTag events
3. Feed into catalyst_evolve thresholds

## 🌐 Phase 4: Dev Container Setup (Week 7)

### H. Reproducible Environment
**Why**: One-command setup for new contributors

```json
// .devcontainer/devcontainer.json
{
  "name": "NuSyQ Development",
  "build": {
    "dockerfile": "../Dockerfile",
    "context": ".."
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "eamodio.gitlens",
        "sourcegraph.cody-ai",
        "ms-windows-ai-studio.windows-ai-studio"
      ]
    }
  },
  "postCreateCommand": "pip install -e . && pre-commit install",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {},
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  }
}
```

**Tasks**:
1. Create `.devcontainer/devcontainer.json`
2. Add Python 3.12, Ollama client, pytest
3. Test on clean Windows + Linux environments

## 📊 Phase 5: Metrics Dashboard (Week 8)

### I. Event Trend Visualization
**Why**: Visual feedback loop for agent evolution

**Stack**: Jupyter + Plotly (already have Jupyter Lab task)

**Notebook**: `Jupyter/agent_performance_dashboard.ipynb`
- Load `Reports/events/events_*.jsonl`
- Group by component, agent, outcome
- Plot success rate over time
- Identify degradation patterns

**Tasks**:
1. Create notebook with template cells
2. Add task to refresh dashboard weekly
3. Link from `README.md`

## 🧬 Future Explorations (Backlog)

### AutoGen Workflow Patterns
Study multi-agent conversation patterns from Microsoft AutoGen for:
- Consensus logic improvements
- Agent handoff protocols
- Reflection/self-correction loops

### Simpliflow Integration
Lightweight alternative to Haystack if:
- Current stack becomes too heavy
- Need simpler debugging experience

### Vector DB for Event Retrieval
When event logs exceed 100k entries:
- Migrate to Milvus/Weaviate
- Enable semantic event search
- Power anomaly detection

---

## 🎯 **Recommended Next Action**

**Start with Phase 1A**: Pre-commit hooks for RSEV normalization

This gives you:
1. Immediate quality gate
2. Validates your event schema at commit time
3. Prevents malformed events from entering the system

Once hooks are working, move to **Phase 1B** (Haystack router enhancement) to leverage the RAG framework you just installed.

---

## 📝 Notes

- **coala-bears**: Skipped due to Python 3.12 incompatibility (uses deprecated `imp` module)
- **Pydantic downgraded**: Haystack requires Pydantic v1; may need isolation in future
- **Ollama**: Already configured; AI Toolkit can browse models via VS Code sidebar
- **GitLens**: Enhances PR review workflow when pushing to -NuSyQ_Ultimate_Repo

---

**Last Updated**: 2026-01-08
**Status**: Phase 1 foundations installed, ready for integration work
