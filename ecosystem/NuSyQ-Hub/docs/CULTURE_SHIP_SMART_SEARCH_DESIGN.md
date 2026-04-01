# Culture Ship Smart Search System - Design Document

**Date**: 2026-01-24
**Status**: 🚀 DESIGN PHASE - Culture Ship Simulation
**Inspired By**: Iain M. Banks' Culture (simulation and precognition)

---

## Problem Statement

**Current Reality**: 139,130 files, 45,266 Python files
**Grep Performance**: Agents timing out or getting incomplete results
**Root Cause**: Linear scanning doesn't scale to massive ecosystems

**Culture Ship Insight**:
> "The Culture's Minds don't search - they already know. They simulate futures
> and precompute answers before questions are asked."

---

## Solution: Smart Search Index (Zero-Token + Culture Ship)

### Core Concept

Instead of grepping 139K files every time, we:
1. **Precompute** a search index (Culture Ship simulation)
2. **Cache** using zero-token techniques (instant retrieval)
3. **Route** intelligently via terminal system
4. **Update** incrementally (not full rescans)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Culture Ship Strategic Advisor                  │
│    (Orchestrates index building and maintenance)        │
└─────────────────────────────────────────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Index        │ │   Zero-Token │ │   Spine      │
│ Builder      │ │   Cache      │ │   Registry   │
│              │ │   (3-layer)  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
            ┌─────────────────────┐
            │  Smart Search API   │
            │  (Agent Interface)  │
            └─────────────────────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Pattern      │ │   Content    │ │   Semantic   │
│ Search       │ │   Search     │ │   Search     │
│ (file names) │ │   (in files) │ │   (meanings) │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## Index Structure

### 1. File Metadata Index
**Location**: `state/search_index/file_metadata.json`

```json
{
  "version": "1.0.0",
  "indexed_at": "2026-01-24T01:30:00Z",
  "total_files": 139130,
  "indexed_files": 139130,
  "index": {
    "src/orchestration/culture_ship_strategic_advisor.py": {
      "size": 12745,
      "modified": "2026-01-24T01:25:13Z",
      "type": "python",
      "imports": ["logging", "dataclasses", "typing"],
      "classes": ["CultureShipStrategicAdvisor", "StrategicIssue"],
      "functions": ["identify_strategic_issues", "make_strategic_decisions"],
      "keywords": ["culture_ship", "strategic", "advisor", "healing"],
      "symbol_hash": "a1b2c3d4"
    }
  }
}
```

### 2. Keyword Inverted Index
**Location**: `state/search_index/keyword_index.json`

```json
{
  "culture_ship": [
    "src/orchestration/culture_ship_strategic_advisor.py",
    "scripts/activate_culture_ship.py",
    "docs/CULTURE_SHIP_SERVICE_ARCHITECTURE.md"
  ],
  "orchestrator": [
    "src/orchestration/unified_ai_orchestrator.py",
    "src/orchestration/multi_ai_orchestrator.py"
  ],
  "grep": [
    "docs/CULTURE_SHIP_SMART_SEARCH_DESIGN.md"
  ]
}
```

### 3. Content Snippets Index
**Location**: `state/search_index/content_snippets.json`

```json
{
  "src/orchestration/culture_ship_strategic_advisor.py": {
    "snippets": {
      "culture_ship": [
        {"line": 1, "context": "Culture Ship Strategic Advisor - Orchestrates Strategic"},
        {"line": 80, "context": "class CultureShipStrategicAdvisor:"}
      ],
      "run_full_strategic_cycle": [
        {"line": 311, "context": "def run_full_strategic_cycle(self) -> dict[str, Any]:"}
      ]
    }
  }
}
```

### 4. Zero-Token Cache
**Location**: Memory (LRU) → Disk (`state/search_index/cache/`)

```python
# 3-layer cache (existing technique)
# Layer 1: Memory LRU (instant)
# Layer 2: Disk cache (0.1s)
# Layer 3: Index lookup (0.5s)
# Fallback: Grep (30-60s)
```

---

## Smart Search API

### For Agents (Python)

```python
from src.search.smart_search import SmartSearch

# Initialize (loads cached index)
search = SmartSearch()

# Pattern search (file names)
files = search.find_files("*culture_ship*")
# Returns: ['src/orchestration/culture_ship_strategic_advisor.py', ...]
# Speed: <10ms (from index)

# Keyword search (content)
results = search.search_keyword("orchestrator", limit=10)
# Returns: [SearchResult(file='...', line=42, snippet='...'), ...]
# Speed: <50ms (from inverted index)

# Semantic search (meaning)
results = search.search_semantic("self-healing autonomous system")
# Returns: [SearchResult(file='culture_ship...', relevance=0.95), ...]
# Speed: <100ms (precomputed embeddings)

# Multi-term search
results = search.search_all(
    keywords=["culture", "ship"],
    file_pattern="*.py",
    content_pattern="strategic"
)
# Returns: Intersection of all criteria
# Speed: <100ms (index intersection)
```

### For CLI (Bash)

```bash
# Pattern search
python -m src.search.smart_search find "culture_ship"

# Keyword search
python -m src.search.smart_search search "orchestrator" --limit 10

# Semantic search
python -m src.search.smart_search semantic "self-healing system"

# Check index status
python -m src.search.smart_search status
```

---

## Zero-Token Optimizations

### 1. Precomputed at Build Time
**When**: During Culture Ship healing cycles (every 6 hours)
**What**: Full index rebuild with incremental updates
**Cost**: $0 tokens (happens offline)

### 2. Symbolic Notation (SNS-Core)
**What**: 41% token reduction via symbolic representation
**Example**:
```
Before: "orchestration system integration point" (6 tokens)
After:  "⨳ ⦾" (3 tokens, 50% savings)
```

### 3. Three-Layer Cache
**Memory**: Most recent 1000 searches (instant)
**Disk**: Last 10K searches (0.1s)
**Index**: All searches (0.5s)
**Fallback**: Grep (30-60s) - only if index fails

### 4. Incremental Updates
**Watch**: File system events
**Update**: Only changed files (not full reindex)
**Merge**: New entries into existing index
**Cost**: Milliseconds, not minutes

---

## Culture Ship Integration

### 1. Index Building (Strategic Cycle)
```python
def run_full_strategic_cycle(self) -> dict[str, Any]:
    # Phase 1: Identify issues
    issues = self.identify_strategic_issues()

    # Phase 2: Make decisions
    decisions = self.make_strategic_decisions(issues)

    # Phase 3: Implement fixes
    results = self.implement_decisions()

    # 🆕 Phase 4: Rebuild Smart Search Index
    self.rebuild_search_index()

    return results
```

### 2. Auto-Maintenance
**Scheduler**: Every 6 hours (with healing cycle)
**Trigger**: After git commits (via hooks)
**Monitor**: File system watcher (inotify/FSEvents)

### 3. Self-Healing
**If index corrupted**: Rebuild from scratch
**If cache stale**: Invalidate and refresh
**If performance degrades**: Optimize index structure

---

## Implementation Plan

### Phase 1: Index Builder (Culture Ship Simulation)
**File**: `src/search/index_builder.py`

**Capabilities**:
- Scan all 139K files
- Extract metadata (imports, classes, functions)
- Build keyword inverted index
- Generate content snippets
- Persist to JSON (or SQLite for performance)

**Time**: 30-60 seconds (one-time, then incremental)

### Phase 2: Smart Search API
**File**: `src/search/smart_search.py`

**Capabilities**:
- Load cached index (instant)
- Pattern search (files)
- Keyword search (content)
- Semantic search (embeddings - optional)
- Multi-term search (intersection)

**Time**: <100ms per query

### Phase 3: Zero-Token Cache Integration
**File**: `src/search/search_cache.py`

**Capabilities**:
- LRU memory cache (1000 queries)
- Disk cache (10K queries)
- Cache invalidation (on file changes)
- Cache warming (preload common queries)

**Time**: <10ms (cache hit)

### Phase 4: Spine Registry Integration
**File**: `src/spine/registry.py` (extend)

**Changes**:
- Register Smart Search as service
- Expose via `get_service("smart_search")`
- Enable dependency injection

### Phase 5: Culture Ship Orchestration
**File**: `src/orchestration/culture_ship_strategic_advisor.py` (extend)

**Changes**:
- Add `rebuild_search_index()` method
- Call after every strategic cycle
- Monitor index health
- Auto-rebuild if degraded

### Phase 6: Intelligent Terminal Routing
**File**: `src/system/intelligent_terminal_router.py` (new)

**Capabilities**:
- Route search queries to appropriate index
- "Find all Culture Ship files" → Pattern search
- "Search for orchestrator usage" → Keyword search
- "Where is self-healing implemented?" → Semantic search

---

## Performance Targets

| Operation | Current (Grep) | Target (Smart Search) | Improvement |
|-----------|----------------|----------------------|-------------|
| Find files by name | 10-30s | <10ms | 1000-3000x |
| Search keyword | 30-60s | <50ms | 600-1200x |
| Multi-term search | 60-120s | <100ms | 600-1200x |
| Semantic search | N/A (not possible) | <100ms | ∞ |

---

## Zero-Token Savings

### Current Cost (Grep)
- Average grep: 139K files scanned
- Token cost: ~5-10 tokens per search (instructions)
- Searches per day: ~50-100
- Annual cost: **$50-100** (assuming grep works)

### Smart Search Cost
- Index build: One-time + incremental (offline, $0)
- Cache retrieval: 0 tokens (local lookup)
- Index query: 0 tokens (local lookup)
- Fallback grep: Rare (1% of searches)
- Annual cost: **~$1** (fallback only)

**Savings**: **$49-99/year + massive time savings**

---

## Culture Ship "Simulation"

Like the Culture's Minds, Smart Search **simulates the future**:

### Traditional Search (Reactive)
1. User asks: "Find Culture Ship files"
2. System scans 139K files (30-60s)
3. Returns results
4. Throws away work
5. Next search: Repeat from step 1

### Smart Search (Precognitive)
1. Culture Ship **simulates**: "Agents will search for X, Y, Z"
2. Precomputes index for all likely queries
3. User asks: "Find Culture Ship files"
4. Returns instantly from index (<10ms)
5. Culture Ship updates index incrementally

**This is the Culture way**: Predict needs before they arise.

---

## Integration with Existing Systems

### 1. Spine Registry
```python
# Register Smart Search
from src.search.smart_search import SmartSearch
from src.spine.registry import register_service

smart_search = SmartSearch()
register_service("search.smart", smart_search)

# Use anywhere
from src.spine.registry import get_service
search = get_service("search.smart")
results = search.find_files("*orchestrator*")
```

### 2. Intelligent Terminals
```python
# Route search to appropriate terminal
from src.system.intelligent_terminal_router import route_to_terminal

result = route_to_terminal(
    query="Find Culture Ship files",
    auto_detect_intent=True
)
# Routes to: "search" terminal
# Executes: SmartSearch.find_files("*culture_ship*")
```

### 3. Culture Ship Healing Cycle
```python
# Add to strategic cycle
def run_full_strategic_cycle(self) -> dict[str, Any]:
    # ... existing phases ...

    # Phase 4: Maintain Smart Search
    self.rebuild_search_index()

    return {
        "issues_identified": len(issues),
        "decisions_made": len(decisions),
        "fixes_applied": results["total_fixes_applied"],
        "index_updated": True  # 🆕
    }
```

### 4. Git Hooks
```python
# .githooks/post-commit-impl.py
# After commit, update search index incrementally

from src.search.index_builder import IndexBuilder

builder = IndexBuilder()
builder.update_incremental(changed_files=get_changed_files())
```

---

## File Structure

```
src/search/
├── __init__.py
├── smart_search.py           # Main API
├── index_builder.py          # Index construction
├── search_cache.py           # 3-layer cache
├── semantic_embeddings.py   # Optional: vector search
└── README.md                # Usage guide

state/search_index/
├── file_metadata.json       # File index
├── keyword_index.json       # Inverted index
├── content_snippets.json    # Search contexts
├── cache/                   # Disk cache
│   ├── pattern_*.json
│   ├── keyword_*.json
│   └── semantic_*.json
└── index_health.json        # Index status

scripts/
├── build_search_index.py    # CLI for index building
└── test_smart_search.py     # Integration tests
```

---

## Testing Strategy

### 1. Index Building Test
```python
def test_index_builder():
    builder = IndexBuilder()
    index = builder.build_full_index()

    assert len(index["files"]) > 100_000
    assert "culture_ship" in index["keywords"]
    assert index["version"] == "1.0.0"
```

### 2. Search Performance Test
```python
def test_search_performance():
    search = SmartSearch()

    start = time.time()
    results = search.find_files("*orchestrator*")
    elapsed = time.time() - start

    assert elapsed < 0.01  # <10ms
    assert len(results) > 0
```

### 3. Cache Hit Rate Test
```python
def test_cache_effectiveness():
    search = SmartSearch()

    # First search (cache miss)
    search.search_keyword("culture_ship")

    # Second search (cache hit)
    start = time.time()
    results = search.search_keyword("culture_ship")
    elapsed = time.time() - start

    assert elapsed < 0.001  # <1ms (cache hit)
```

---

## Rollout Plan

### Week 1: Foundation
- ✅ Design document (this file)
- [ ] Implement `index_builder.py`
- [ ] Test on small subset (1000 files)
- [ ] Benchmark performance

### Week 2: Core Search
- [ ] Implement `smart_search.py`
- [ ] Add pattern, keyword, content search
- [ ] Integrate with zero-token cache
- [ ] Test on full ecosystem (139K files)

### Week 3: Integration
- [ ] Wire into Spine Registry
- [ ] Add to Culture Ship strategic cycle
- [ ] Integrate with git hooks
- [ ] Update agent documentation

### Week 4: Enhancement
- [ ] Add semantic search (optional)
- [ ] Optimize index structure (SQLite?)
- [ ] Add incremental updates
- [ ] Performance tuning

---

## Success Metrics

### Performance
- ✅ File search: <10ms (target)
- ✅ Keyword search: <50ms (target)
- ✅ Multi-term: <100ms (target)
- ✅ 1000x improvement over grep

### Reliability
- ✅ 99.9% cache hit rate
- ✅ Auto-rebuild on corruption
- ✅ Incremental updates <1s
- ✅ Zero downtime updates

### Cost
- ✅ $49-99/year savings
- ✅ 95%+ zero-token operations
- ✅ One-time index build cost

### Adoption
- ✅ All agents use Smart Search
- ✅ Zero grep timeouts
- ✅ Faster development velocity
- ✅ Culture Ship maintains automatically

---

## Conclusion

**Smart Search** combines:
1. **Culture Ship simulation** - Precompute answers before questions
2. **Zero-token techniques** - 3-layer cache, offline indexing
3. **Spine integration** - Central service registry
4. **Intelligent routing** - Terminal-aware search

**Result**:
- 1000x faster searches
- $49-99/year savings
- Fully autonomous maintenance
- Scale to millions of files

**The Culture way**: Don't search. Already know. 🚢✨

---

**Status**: 🎨 DESIGN COMPLETE - Ready for implementation
**Next**: Phase 1 - Build index_builder.py
**Estimated Time**: 2-4 hours for full implementation
**ROI**: Immediate (agents stop timing out)
