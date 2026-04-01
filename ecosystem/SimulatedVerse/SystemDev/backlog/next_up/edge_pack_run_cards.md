# EDGE PACK RUN CARDS - HYPER-INDEX & VFS OVERLAY

## 🎯 **EDGE PACK FOUNDATION DEPLOYED**
- **Multi-scale indexing**: SQLite FTS5 + LMDB ready
- **Sharded scanning**: 4K files per shard for massive repo support  
- **VFS overlay**: WorkingSet virtual filesystem for agent performance
- **Near-duplicate detection**: MinHash-style content similarity
- **Import rewriting**: ts-morph AST-based safe path updates

---

## **RUN CARD A: HYPER-INDEX FOUNDATION**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Create comprehensive sharded index of 123K+ repository with FTS5 content search

### Execution
```bash
# Initialize hyper-index with sharded scanning
tsx SystemDev/scripts/edge_index.ts --fts --shard-size=4000

# Verify database creation
ls -la SystemDev/.edge/edge.db

# Check initial counts
tsx SystemDev/scripts/edge_counts.ts
```

### Success Criteria
- SQLite database created with files table
- ≥30 shards processed (120K+ files / 4K per shard)
- FTS5 index populated for ours.* buckets
- Receipt generated with bucket breakdown

### Expected Results
- **packages vs ours breakdown**: Precise counts by bucket
- **External scope**: Confirmed clean (0 externals)
- **Processing time**: ~2-5 minutes for massive repo

### Next Card
"RUN CARD B: VFS WorkingSet Overlay"

---

## **RUN CARD B: VFS WORKINGSET OVERLAY**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Create filtered workspace overlay for lightning-fast agent operations

### Execution
```bash
# Create WorkingSet with symlinks for agent performance
tsx SystemDev/scripts/edge_overlay.ts --symlinks --max=20000 --include-buckets="ours.systemdev,ours.chatdev,ours.gamedev,ours.previewui,ours.src"

# Verify overlay structure
ls SystemDev/.edge/overlay/
ls SystemDev/.edge/overlay/WorkingSet/ | head -20
```

### Success Criteria
- roster.json created with ≤20K selected files
- WorkingSet/ directory with symlinks to source files
- Agent search space reduced from 123K→20K files
- Receipt with bucket breakdown

### Performance Impact
- **Agent queries**: 123K files → 20K files (83% reduction)
- **Search speed**: Sub-second vs multi-second scans
- **LSP performance**: Focused on relevant source only

### Next Card
"RUN CARD C: Fast Query Validation"

---

## **RUN CARD C: FAST QUERY VALIDATION**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Validate FTS5 search and metadata queries for instant repo analysis

### Execution
```bash
# Test full-text search
tsx SystemDev/scripts/edge_query.ts --text "import" --limit 10

# Test metadata queries
tsx SystemDev/scripts/edge_query.ts --bucket "ours.systemdev" --limit 20
tsx SystemDev/scripts/edge_query.ts --glob "%.ts" --bucket "ours.src" --limit 15

# Show database statistics
tsx SystemDev/scripts/edge_query.ts --stats
```

### Success Criteria
- FTS5 search returns results in <1 second
- Metadata queries work across all buckets
- Statistics show correct file counts
- No errors or timeouts

### Validation Points
- **Search accuracy**: Returns relevant matches
- **Performance**: Sub-second response times
- **Coverage**: All buckets represented
- **Fallback**: Ripgrep works if FTS unavailable

### Next Card
"RUN CARD D: Near-Duplicate Detection"

---

## **RUN CARD D: NEAR-DUPLICATE DETECTION**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Identify exact and near-duplicate files for consolidation targeting

### Execution
```bash
# Run deduplication analysis on ours.* buckets
tsx SystemDev/scripts/edge_dedupe.ts --threshold=82 --max=25000

# Review top duplicate groups
cat SystemDev/receipts/edge_dedupe_*.json | jq '.groups[:5]'
```

### Success Criteria
- ≥10 duplicate groups identified
- Exact duplicates vs near-duplicates separated
- Consolidation potential quantified
- Receipt with actionable duplicate clusters

### Expected Discoveries
- **Exact duplicates**: config.ts, util.js, common patterns
- **Near-duplicates**: Similar components, repeated logic
- **Consolidation potential**: 100-500 files could be merged
- **Safety**: Groups pre-verified for safe consolidation

### Next Card
"RUN CARD E: Import Path Analysis"

---

## **RUN CARD E: IMPORT PATH ANALYSIS (DRY RUN)**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Analyze import paths for rewriting potential using path aliases

### Execution
```bash
# Dry run import analysis
tsx SystemDev/scripts/edge_import_rewrite.ts --map SystemDev/scripts/path_alias_map.json --dry-run --max-changes=8

# Review proposed changes
cat SystemDev/receipts/edge_imports_*.json | jq '.change_details[:5]'
```

### Success Criteria
- ≤8 import rewrites identified per run
- Path alias mapping applied correctly
- No breaking changes proposed
- Dry run receipt shows safe transformations

### Safety Checks
- **AST-based**: Uses ts-morph for safe parsing
- **Reversible**: Changes tracked in receipts
- **Limited scope**: ≤8 edits per micro-cycle
- **Validation**: Import resolution verified

### Next Card
"RUN CARD F: Performance Measurement"

---

## **RUN CARD F: PERFORMANCE MEASUREMENT**
*SAGE-PILOT micro-cycle verification*

### Objective
Measure Edge Pack performance gains and system health

### Execution
```bash
# Compare performance: before vs after
time find . -name "*.ts" | wc -l  # Baseline scan
time tsx SystemDev/scripts/edge_query.ts --glob "%.ts" --limit 1000  # Edge scan

# System health check
tsx SystemDev/scripts/edge_query.ts --stats
tsx SystemDev/scripts/outside_scope_probe.ts  # Verify still clean
```

### Success Criteria
- Edge queries 5-10x faster than filesystem scans
- Database size reasonable (<100MB for 123K files)
- WorkingSet overlay functional
- External scope remains clean

### Performance Metrics
- **Index time**: 2-5 minutes for full repository
- **Query time**: <1 second for FTS, <0.1s for metadata
- **Overlay creation**: <30 seconds for 20K files
- **Agent speedup**: 80%+ reduction in search space

---

## **🔄 BREATH CYCLE INTEGRATION**

**SystemDev/pipelines/breath_cycle.yml additions:**
```yaml
breaths:
  - name: ΞΘΛΔ_index
    script: "tsx SystemDev/scripts/edge_index.ts --fts --shard-size=4000"
    receipts: true
    zeta_check: true
    cascade_on_success: [ΞΘΛΔ_overlay, ΞΘΛΔ_counts]

  - name: ΞΘΛΔ_overlay
    script: "tsx SystemDev/scripts/edge_overlay.ts --symlinks --max=20000"
    receipts: true
    cascade_on_success: [ΞΘΛΔ_query_test]

  - name: ΞΘΛΔ_counts
    script: "tsx SystemDev/scripts/edge_counts.ts"
    receipts: true

  - name: ΞΘΛΔ_dedupe
    script: "tsx SystemDev/scripts/edge_dedupe.ts --threshold=82"
    receipts: true
    cascade_on_success: [ΞΘΛΔ_imports_plan]
```

## **📊 SUCCESS METRICS**

- **Phase 1**: Complete repository indexing (SQLite + FTS5)
- **Phase 2**: WorkingSet overlay operational (≤20K files)
- **Phase 3**: Agent performance 80%+ improvement
- **Phase 4**: Near-duplicate consolidation ready
- **Phase 5**: Import path optimization via safe rewrites

---

**🚀 BEGIN: Execute RUN CARD A (Hyper-Index Foundation)**