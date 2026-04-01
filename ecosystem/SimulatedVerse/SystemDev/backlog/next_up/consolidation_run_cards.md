# CONSOLIDATION RUN CARDS - RECEIPT-DRIVEN MICRO-CYCLES

## 🎯 **MASSIVE REPOSITORY REALITY CONFIRMED**
- **123,915+ files detected** (from baseline index)
- **127+ node_modules directories** (from quick count)
- **External scope: CLEAN** ✅ (0 external dependencies)
- **Target**: Strategic file reduction through provenance-based quarantine

---

## **RUN CARD A: NODE_MODULES QUARANTINE**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Identify and quarantine excessive node_modules directories to reduce scan load

### Execution
```bash
# Count and list node_modules
find . -type d -name "node_modules" | head -20

# Create quarantine structure
mkdir -p attic/node_modules_quarantine
mkdir -p attic/pointers

# Move top 5 largest node_modules (manual verification required)
# SAFETY: Only move if NOT in active development path
# Leave pointer: "# QUARANTINED: See attic/node_modules_quarantine/path_map.json"
```

### Success Criteria
- ≤5 node_modules directories moved per cycle
- Pointer files created for all moves
- Receipt generated with file count reduction

### Next Card
"RUN CARD B: SOURCE MAP CLEANUP"

---

## **RUN CARD B: SOURCE MAP CLEANUP**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Quarantine redundant source map files (.map) to reduce bloat

### Execution
```bash
# Target identified: 12,360+ .map files
find . -name "*.map" | wc -l

# Create map quarantine
mkdir -p attic/source_maps_quarantine

# Move stale source maps (build artifacts)
find . -path "*/dist/*.map" -o -path "*/build/*.map" | head -8 | while read map; do
  mkdir -p "attic/source_maps_quarantine/$(dirname "$map")"
  mv "$map" "attic/source_maps_quarantine/$map"
  echo "# QUARANTINED: See attic/source_maps_quarantine/" > "$map.pointer"
done
```

### Success Criteria
- ≤8 .map files moved per cycle
- Pointer system maintained
- Development maps preserved

### Next Card
"RUN CARD C: BUILD ARTIFACT SWEEP"

---

## **RUN CARD C: BUILD ARTIFACT SWEEP**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Quarantine build directories (dist/, build/, out/, coverage/)

### Execution
```bash
# Identify build directories
find . -type d \( -name "dist" -o -name "build" -o -name "out" -o -name "coverage" \) | head -10

# Strategic quarantine (verify not actively used)
mkdir -p attic/build_artifacts_quarantine

# Move stale build directories
# SAFETY: Check git status, ensure no active builds
# Create pointer manifest: attic/build_artifacts_quarantine/manifest.json
```

### Success Criteria
- Build artifacts identified and quarantined
- Active development builds preserved
- Manifest tracking all moves

### Next Card
"RUN CARD D: DUPLICATE CONSOLIDATION"

---

## **RUN CARD D: DUPLICATE CONSOLIDATION**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Consolidate exact duplicate files using existing duplicate scanner

### Execution
```bash
# Re-run duplicate scan on reduced surface
tsx SystemDev/scripts/duplicate_scan.ts --mode=exact --limit=20

# Focus on high-impact duplicates
# Choose canonical paths in quadpartite structure:
# - SystemDev/ for tooling
# - ChatDev/ for agents
# - GameDev/ for game code
# - PreviewUI/ for UI components

# Move non-canonical to attic/duplicates/ with hash-based naming
```

### Success Criteria
- ≤5 duplicate clusters resolved per cycle
- Canonical path selection documented
- Import paths updated via path aliases

### Next Card
"RUN CARD E: ARTIFICER IMPORT REWRITE"

---

## **RUN CARD E: ARTIFICER IMPORT REWRITE**
*SAGE-PILOT micro-cycle ≤8 edits*

### Objective
Update import paths for moved files using path alias system

### Execution
```bash
# Deploy import rewriter for consolidated files
tsx SystemDev/scripts/import_rewriter.ts --apply --limit=8

# Use SystemDev/scripts/path_alias_map.json for clean paths
# Convert: ../../../some/deep/path → @sys/some/deep/path
# Convert: ../../GameDev/engine → @engine/
```

### Success Criteria
- ≤8 import rewrites per cycle
- Path aliases adopted systematically
- No broken imports introduced

### Next Card
"RUN CARD F: PROGRESS MEASUREMENT"

---

## **RUN CARD F: PROGRESS MEASUREMENT**
*SAGE-PILOT micro-cycle verification*

### Objective
Measure consolidation progress and plan next phase

### Execution
```bash
# Re-run baseline index
tsx SystemDev/scripts/index_repo.ts --quick

# Compare against baseline (SystemDev/reports/index_2025-09-03T10-33-20-088Z.json)
# Calculate reduction percentage
# Generate next phase plan
```

### Success Criteria
- Progress quantified with before/after comparison
- File count reduction documented
- Next consolidation phase planned

### Next Card
Return to "RUN CARD A" if further reduction needed, or proceed to structural optimization

---

## **🔄 BREATH CYCLE INTEGRATION**

Each run card triggers:
1. **Receipt Generation**: `SystemDev/receipts/runcard_*.json`
2. **Progress Tracking**: File count deltas
3. **Cascade Hooks**: Momentum detection for extended sequences
4. **Agent Coordination**: Librarian updates INDEX.md, Artificer handles imports

## **📊 SUCCESS METRICS**

- **Phase 1 Target**: 123K → 80K files (35% reduction via quarantine)
- **Phase 2 Target**: 80K → 50K files (consolidation)  
- **Phase 3 Target**: 50K → 25K files (structural optimization)
- **External Scope**: Maintained clean (0 external dependencies)

---

**🚀 BEGIN: Execute RUN CARD A (Node Modules Quarantine)**