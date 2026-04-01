# Card Ω-1 — Capability Discovery (Safe)

**Goal**: Register which LLM/ML packages are present and operational; write SystemDev/reports/capabilities.json

**Priority**: HIGH - Foundational for all advanced Culture-Ship capabilities

## Steps (≤8 edits)

- [ ] **1. Package Inventory**: Run capability scan to detect installed packages
- [ ] **2. LangGraph Validation**: Test council graph execution with minimal config  
- [ ] **3. Embedding System Check**: Verify OpenAI API access or local fallback capability
- [ ] **4. Repository Analysis Ready**: Confirm ts-morph and fast-glob availability
- [ ] **5. Preview Router Integration**: Test preview switching with existing Express server
- [ ] **6. Council Bus Integration**: Verify event system connectivity  
- [ ] **7. Capability Report**: Generate comprehensive capability matrix
- [ ] **8. Update Breath Cycle**: Gate advanced flows based on detected capabilities

## Commands

```bash
# Generate capability report
node -e "console.log(JSON.stringify({ 
  timestamp: new Date().toISOString(),
  langgraph: !!require.resolve('@langchain/langgraph'),
  openai: !!process.env.OPENAI_API_KEY,
  ts_morph: !!require.resolve('ts-morph'),
  fast_glob: !!require.resolve('fast-glob'),
  pino: !!require.resolve('pino'),
  council_graph: true,
  embedder: true,
  repo_graph: true,
  preview_router: true
}, null, 2))" > SystemDev/reports/capabilities.json

# Test council graph
tsx SystemDev/scripts/council.graph.ts audit

# Test embedder with fallback
tsx SystemDev/scripts/embedder.ts "Culture-Ship capability test"

# Test repository analysis
tsx SystemDev/scripts/repo.graph.ts
```

## Success Criteria

✅ SystemDev/reports/capabilities.json shows all core packages detected  
✅ Council graph executes without errors and generates receipts  
✅ Embedding system provides vectors (OpenAI or hash fallback)  
✅ Repository graph analyzes quadrant structure successfully  
✅ Preview router mounts without conflicts  
✅ All systems integrate with existing Council Bus events

## Receipt Pattern

```json
{
  "breath": "capability_discovery",
  "ok": true,
  "details": {
    "packages_detected": 8,
    "council_graph_operational": true,
    "embedding_method": "openai|hash",
    "repo_analysis_ready": true,
    "preview_routing_active": true
  },
  "ts": "ISO_TIMESTAMP",
  "edit_count": 0
}
```