# Card Ω-4 — Path-Safe DeepMerge (Plan-only)

**Goal**: Prepare repository consolidation merges with import rewriting (no destructive writes)

**Priority**: MEDIUM - Foundation for 123K→25K file reduction

## Steps (≤8 edits)

- [ ] **1. Candidate Analysis**: Use ts-morph to identify mergeable file clusters
- [ ] **2. Import Graph Mapping**: Map all import dependencies before any moves
- [ ] **3. Merge Plan Generation**: Create detailed from→to file movement plan  
- [ ] **4. Import Rewrite Calculation**: Generate codemod patches for all affected imports
- [ ] **5. Conflict Detection**: Identify naming conflicts and resolution strategies
- [ ] **6. Diff Generation**: Build human-readable deepmerge.md with conflict hunks
- [ ] **7. Safety Validation**: Verify no circular dependencies or orphaned imports
- [ ] **8. Zeta Gate Preparation**: Stage plan for execution approval via Zeta protocol

## Analysis Commands

```bash
# Generate merge candidates using ts-morph
tsx -e "
import { Project } from 'ts-morph';
const project = new Project();
project.addSourceFilesAtPaths('src/**/*.{ts,tsx}');
const files = project.getSourceFiles();
console.log('Files analyzed:', files.length);
console.log('Potential merge candidates:', files.filter(f => f.getClasses().length === 0 && f.getFunctions().length < 3).length);
"

# Repository graph for dependency analysis
tsx SystemDev/scripts/repo.graph.ts

# Find duplicate patterns
find src/ -name "*.ts" -exec basename {} \; | sort | uniq -d
```

## Merge Plan Structure

```json
// SystemDev/reports/deepmerge_plan_TIMESTAMP.json
{
  "analysis_timestamp": "ISO_TIMESTAMP",
  "merge_candidates": [
    {
      "cluster_id": "utilities",
      "target_file": "shared/utils/index.ts",
      "source_files": [
        "src/utils/helpers.ts",
        "client/src/lib/utils.ts", 
        "server/utils/common.ts"
      ],
      "import_rewrites": [
        {
          "file": "src/components/Button.tsx",
          "from": "import { cn } from '../utils/helpers'",
          "to": "import { cn } from '@shared/utils'"
        }
      ],
      "conflicts": [],
      "risk_level": "low"
    }
  ],
  "total_reduction": {
    "files_before": 847,
    "files_after": 412,
    "reduction_percentage": 51.4
  },
  "execution_ready": false
}
```

## Diff Generation

```typescript
// Generate human-readable deepmerge.md
import * as diff from 'diff-match-patch';

function generateMergeDiff(plan) {
  const dmp = new diff.diff_match_patch();
  // Create visual diff showing before/after file structure
  // Highlight import rewrite changes
  // Show conflict resolution strategies
}
```

## Safety Validation

```bash
# Check for circular dependencies
npx madge --circular src/

# Validate TypeScript compilation after plan
npx tsc --noEmit --project tsconfig.json

# Import resolution verification
tsx -e "
import { Project } from 'ts-morph';
const project = new Project();
// Verify all imports resolve correctly in planned structure
"
```

## Success Criteria

✅ Complete merge plan generated without errors  
✅ All import dependencies mapped and rewrite paths calculated  
✅ No circular dependencies detected in planned structure  
✅ Human-readable deepmerge.md shows clear before/after  
✅ Risk assessment shows low-risk consolidation opportunities  
✅ Zeta protocol approval gates prepared for execution phase

## Receipt Pattern

```json
{
  "breath": "path_safe_deepmerge_plan",
  "ok": true,
  "details": {
    "merge_clusters_identified": 12,
    "files_consolidation_ready": 435,
    "import_rewrites_planned": 1247,
    "circular_dependencies": 0,
    "risk_assessment": "low",
    "execution_ready": false
  },
  "ts": "ISO_TIMESTAMP", 
  "edit_count": 0
}
```

## Guardrails

⚠️ **PLAN-ONLY MODE**: No files moved or deleted in this card  
⚠️ **Zeta Gate Required**: Execution requires explicit Zeta protocol approval  
⚠️ **Receipt-First**: Every change must generate proper receipt  
⚠️ **Rollback Ready**: All operations must be reversible via git