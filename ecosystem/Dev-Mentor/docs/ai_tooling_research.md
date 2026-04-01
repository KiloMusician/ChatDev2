# AI Tooling Research — Dev-Mentor Ecosystem

Researched 2026-03-25. Tools evaluated for Dev-Mentor integration.

---

## 1. CocoIndex — INTEGRATED

**Repo:** https://github.com/cocoindex-io/cocoindex
**PyPI:** `pip install cocoindex`
**Status:** Integration layer written at `agents/serena/cocoindex_bridge.py`

### What it is
CocoIndex is a high-performance incremental data transformation and indexing framework
designed for AI/LLM pipelines. Key properties:
- Declarative `Flow` API: define Sources → Transformers → Embedders → Targets
- Incremental re-indexing: only processes changed files (content-addressed state)
- Supports pluggable embedding backends: OpenAI, Ollama, HuggingFace sentence-transformers
- Stores results in vector databases: SQLite, Qdrant, Postgres pgvector, Weaviate

### Integration in Dev-Mentor
- **Bridge file:** `agents/serena/cocoindex_bridge.py`
- **MCP tools added:** `cocoindex_search`, `cocoindex_ops`
- **Embedding backend:** `nomic-embed-text` via Ollama at `localhost:11434`
- **Vector DB:** SQLite at `state/cocoindex.db`
- **Fallback:** built-in incremental pipeline + keyword scoring (no cocoindex install required)

### How to activate

```bash
# 1. Install cocoindex (optional but enables native Flow API)
pip install cocoindex

# 2. Load nomic-embed-text into Ollama (required for vector search)
ollama pull nomic-embed-text

# 3. Run the initial index (2-5 min first run, incremental after)
python agents/serena/cocoindex_bridge.py --index

# 4. Test a semantic query
python agents/serena/cocoindex_bridge.py --query "XP gain logic"

# 5. Via MCP tool (after server restart)
# cocoindex_ops(op="index")          → build/update index
# cocoindex_search(query="...")      → semantic search
```

### Upgrade over existing TF-IDF search
| Feature | serena_search (existing) | cocoindex_search (new) |
|---------|-------------------------|------------------------|
| Algorithm | TF-IDF keyword counting | Dense vector cosine similarity |
| Embedding | None (word overlap only) | nomic-embed-text (768-dim) |
| Semantic understanding | No | Yes |
| Incremental updates | Full re-walk every time | File-hash based, changed files only |
| Query: "how does XP work" | Finds literal "XP" occurrences | Finds XP logic semantically |

---

## 2. llmfit — NOT FOUND ON PyPI

**Searched:** PyPI `pip show llmfit`, PyPI JSON API
**Status:** No package named `llmfit` found on PyPI (as of 2026-03-25).

### Alternatives for LLM fine-tuning in this ecosystem
The following are well-established and available:

| Package | Install | Use case |
|---------|---------|----------|
| `unsloth` | `pip install unsloth` | Fast LoRA fine-tuning for Llama/Qwen/Mistral |
| `peft` | `pip install peft` | LoRA, QLoRA, prefix tuning (HuggingFace) |
| `trl` | `pip install trl` | RLHF, DPO, PPO for LLMs (HuggingFace) |
| `axolotl` | GitHub: OpenAccess-AI-Collective/axolotl | YAML-configured fine-tuning pipelines |
| `lit-gpt` | GitHub: Lightning-AI/lit-gpt | Lightning-based fine-tuning |

Dev-Mentor already has `scripts/finetune.py` which generates training data from game play.
The natural next step is to wire it to `unsloth` + `trl` for actual LoRA fine-tuning of
`qwen2.5-coder:7b` on game command patterns.

**Recommendation:** Install `unsloth` + `trl` when ready to fine-tune:
```bash
pip install unsloth trl peft
```

---

## 3. Agentic Design Patterns — Bookmarked

The most canonical and widely-cited reference is:

### microsoft/autogen
**Repo:** https://github.com/microsoft/autogen
**Relevance:** HIGH — directly applicable to Dev-Mentor's multi-agent architecture
**Key patterns:**
- **Conversation patterns:** Two-agent, Group Chat, Nested Chat
- **Tool use agents:** Agents that call functions/APIs as tools
- **Code-executing agents:** Agents that write and run code
- **Human-in-the-loop:** Consent gates (maps directly to Serena's `ConsentGate`)
- **Swarm orchestration:** Handoff patterns between specialized agents

**Dev-Mentor mappings:**
- `ConversableAgent` → `AgentBase` pattern
- `GroupChatManager` → `SwarmController`
- Tool use → MCP server tools
- Human feedback gate → Serena `ConsentGate` L3 actions

### anthropics-cookbook / agent patterns
**Repo:** https://github.com/anthropics/anthropic-cookbook
**Path:** `patterns/agents/`
**Key patterns:**
- Orchestrator → Subagent pattern (matches Dev-Mentor's Gordon Orchestrator)
- Tool-use loop with retry
- Memory-augmented agents (matches Serena MemoryPalace)
- Parallel subagent dispatch (matches `dispatch_task.py`)

### Additional high-relevance references
| Repo | Pattern coverage |
|------|-----------------|
| `BerriAI/litellm` | Multi-LLM routing (matches `llm_client.py` design) |
| `openai/swarm` | Lightweight agent handoff / routing |
| `agentops-ai/agentops` | Agent observability + session tracing |
| `langchain-ai/langgraph` | Stateful agent graphs with cycles |

**Most directly applicable to Dev-Mentor:** `microsoft/autogen` for its Group Chat and
Swarm patterns, and `langchain-ai/langgraph` for the state-machine approach to agent
orchestration (relevant to Gordon's orchestration phase).

---

## 4. code-review-graph — NOT FOUND AS INSTALLABLE PACKAGE

**Searched:** PyPI `pip show code-review-graph`
**Status:** No standalone `code-review-graph` pip package found.

### What exists with this concept
| Tool | Install | What it does |
|------|---------|-------------|
| `pydriller` | `pip install pydriller` | Git commit/diff analysis, code change graphs |
| `pydeps` | `pip install pydeps` | Python module dependency graphs |
| `sourcegraph/scip-python` | GitHub | Code intelligence graph for Python |
| `joernio/joern` | GitHub | Code property graph (CPG) for security analysis |
| `networkx` | `pip install networkx` | Already usable — Dev-Mentor uses it in `graph_theory_engine.py` |

**Recommendation for Dev-Mentor:** Use `pydriller` to analyze commit history for
code review patterns, and `pydeps` to generate the module dependency graph. Both
are installable and directly useful:
```bash
pip install pydriller pydeps
```

---

## Summary: Installation Actions Required

Run these in the `DM: Dev` terminal (Python 3.12):

```bash
PYTHON="C:/Users/keath/AppData/Local/Programs/Python/Python312/python.exe"

# Priority 1: nomic-embed-text for semantic search (via Ollama, not pip)
ollama pull nomic-embed-text

# Priority 2: CocoIndex (optional — bridge works without it)
$PYTHON -m pip install cocoindex

# Priority 3: Build the vector index
$PYTHON agents/serena/cocoindex_bridge.py --index

# Optional: fine-tuning stack (when ready to fine-tune qwen2.5-coder)
$PYTHON -m pip install unsloth trl peft

# Optional: code analysis tools
$PYTHON -m pip install pydriller pydeps
```
