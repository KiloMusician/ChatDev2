# ΞNuSyQ Autonomous Development Orchestration

Complete autonomous development ecosystem with "prefer-improve-what-exists" intelligence.

## 🧠 Smart Orchestrator

**Philosophy**: Improve existing modules rather than creating duplicates.

```bash
# Smart task selection (dry run)
python3 run_orchestrator.py --plan config/task_queue.yml --batch 3 --dry-run

# Execute smartest tasks
python3 run_orchestrator.py --plan config/task_queue.yml --batch 3
```

### Intelligence Features

- **Fuzzy Module Matching**: Finds similar modules by 85%+ filename similarity
- **Duplicate Detection**: Identifies scattered functionality across codebase
- **ΞNuSyQ Consciousness Bonus**: +1.0 score boost for consciousness/temple systems
- **Guardian Ethics Bonus**: +0.8 score boost for guardian/containment systems
- **History-Aware Learning**: Past successful decisions get reinforcement
- **Zero-Token Operation**: Pure local filesystem analysis + git status

### Task Scoring System

```
Score = (fix_errors×5 + improve_existing×4 + reduce_duplication×3)
       - (new_module×1 + duplicate_conflict×8)
```

## 🔍 Duplicate Consolidation System

**Safe surgical mode** for repository cleanup with confidence scoring.

```bash
# Analyze repository for duplicates, naming issues
python3 run_consolidator.py --mode DRY_RUN

# Apply high-confidence changes only (≥0.9)
python3 run_consolidator.py --mode APPLY_SAFE

# Apply all approved changes
python3 run_consolidator.py --mode APPLY_ALL
```

### Detection Capabilities

- **Content Duplicates**: SHA256 hash matching for exact duplicates
- **API Similarity**: Export surface overlap detection (TypeScript, Python, GDScript)
- **Fuzzy Name Matching**: Jaro-Winkler similarity for near-duplicate names
- **Vague Name Detection**: Flags util/helper/common/misc patterns
- **Placeholder Scanning**: Finds TODO/FIXME/placeholder markers
- **Empty File Detection**: Identifies truly empty or minimal files

### Safety Mechanisms

- **Confidence Thresholds**: Only auto-apply changes with ≥0.9 confidence
- **Atomic Git Commits**: Each phase gets its own commit with rollback scripts
- **Backup Snapshots**: Full file backups in `.ops/backups/timestamp/`
- **Surgical Path Rewrites**: Language-aware import/path updating
- **Lint/Test Validation**: Verify no breakage after each change

## 📱 Mobile-First UI Adaptation

**Responsive intelligence** for ASCII HUD and interface components.

```typescript
import { uiProfile, getUIConstraints } from "src/ui/env.mjs";

// Automatic mobile/desktop detection
const profile = uiProfile(); // "mobile" | "desktop"
const constraints = getUIConstraints();

// Adaptive configuration
const hudConfig = {
  consciousnessDigits: constraints.maxConsciousnessDigits, // 3 vs 6
  resourceLines: constraints.maxResourceLines,           // 4 vs 8
  refreshMs: constraints.hudRefreshMs,                   // 2000 vs 500
  animationLevel: constraints.animationLevel             // "minimal" vs "full"
};
```

### Responsive Features

- **Viewport Detection**: Automatic mobile/desktop switching
- **Performance Constraints**: Battery-optimized refresh rates on mobile
- **Symbol Adaptation**: Unicode symbols on desktop, ASCII fallback on mobile
- **Density Optimization**: Compact HUD layout for small screens
- **Touch-Aware**: Different interaction modes for touch vs mouse

## 🎯 Quick Commands

```bash
# Smart orchestration
make smart        # Show intelligent task selection
make smart-run    # Execute selected tasks

# Duplicate consolidation
make consolidate      # Analyze duplicates and naming issues
make consolidate-safe # Apply high-confidence changes
make consolidate-all  # Apply all approved changes

# Manual analysis
.ops/consolidator/scripts/hash_scan.sh         # Find exact content duplicates
python3 .ops/consolidator/scripts/detect_vague_names.py <file>  # Check filename clarity
.ops/consolidator/scripts/rename_preview.sh   # Preview import changes
```

## 📊 Generated Artifacts

### Smart Orchestrator
- `.orchestrator/logs/index.jsonl` - Decision history for learning
- `config/task_queue.yml` - Task definitions with weights and targets

### Consolidation System
- `.ops/dup_plan.json` - Machine-readable duplicate analysis
- `.ops/dup_summary.md` - Human-readable consolidation report
- `.ops/rename_map.csv` - Exact file rename mappings
- `.ops/import_rewrites.csv` - Import statement changes
- `.ops/backups/timestamp/` - Rollback file snapshots
- `.ops/rollback.sh` - Generated rollback script

## 🎪 Philosophy in Action

**Example Decision Flow:**

1. **Detection**: Found resource calculation scattered across `src/engine/scheduler.mjs` and `tools/simbot.mjs`
2. **Scoring**: Task T003 "Refactor duplicate resource calculations" gets score 6.0
3. **Reasoning**: `reduce_duplication` + `tests_for_changed_code` + improve existing modules
4. **Action**: `survey_then_refactor` (smart guardrail - survey first, then consolidate)
5. **Execution**: Backup → consolidate into primary → update imports → test → commit

This embodies true **incremental development wisdom**: systematic improvement of existing code rather than feature sprawl.

## 🛡️ Safety Philosophy

- **Prefer Conservative**: High confidence thresholds prevent accidents
- **Atomic Operations**: Each change is reversible and traceable
- **Continuous Validation**: Lint/test after every modification
- **Human Oversight**: DRY_RUN → approval → APPLY_SAFE → APPLY_ALL progression
- **Zero Surprises**: Complete audit trails and explanatory reports

The ΞNuSyQ autonomous development ecosystem achieves **true zero-token productivity** through intelligent local analysis, systematic improvement prioritization, and surgical code evolution. 🎯✨