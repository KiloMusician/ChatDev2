# Anti-Hang Quality Tools Processing - Quick Reference

## Problem
Running `ruff check src/ --fix` hangs for **many hours** on the full codebase due to:
- Large file count (300+ Python files)
- Complex interdependencies
- Monolithic "all at once" processing
- Missing per-file timeouts

## Solution: Batch Processing System

We've implemented a **smart batch processor** that:
- ✅ Processes files in small batches (10-20 files per batch)
- ✅ Sets per-file timeouts (10-120 seconds based on complexity)
- ✅ Skips problematic files and continues
- ✅ Saves progress in checkpoints (resumable)
- ✅ Shows real-time progress with ETA
- ✅ Analyzes file complexity first to optimize batching

## Quick Start

### Option 1: Intelligent Orchestrator (Recommended)
Automatically analyzes files and processes in optimal batches:
```bash
python scripts/quality_orchestrator.py
```

This will:
1. Analyze file complexity (~2 minutes)
2. Process "simple" files (20 per batch)
3. Process "moderate" files (10 per batch)
4. Process "complex" files (5 per batch)
5. Process "problematic" files (1 per batch)

**Resume after interruption:**
```bash
python scripts/quality_orchestrator.py --skip-analysis
```

### Option 2: Direct Batch Processing
Process specific tools in batches:
```bash
# Basic: 10 files per batch, 30s timeout per file
python scripts/quality_tools_batch.py

# Advanced: More aggressive settings for faster files
python scripts/quality_tools_batch.py --tools ruff black --batch-size 20

# With progress details
python scripts/quality_tools_batch.py --verbose
```

### Option 3: Ruff Only
Process only ruff (faster):
```bash
# Default: 10 files per batch, 30s per file
python scripts/ruff_batch_processor.py

# Custom: 20 files per batch, 15s per file
python scripts/ruff_batch_processor.py 20 15
```

## File Analysis

To understand your file complexity before processing:
```bash
python scripts/analyze_file_complexity.py
```

This will:
- Categorize files as simple/moderate/complex/problematic
- Show estimated processing time
- Recommend batch settings

**Output:** `state/file_complexity_analysis.json`

## Progress Tracking

All processes save checkpoints:
- **Orchestrator:** `state/quality_orchestrator_checkpoint.json`
- **Batch tools:** `state/quality_batch_checkpoint.json`
- **Ruff only:** `state/ruff_batch_checkpoint.json`

Checkpoints allow resuming interrupted work without reprocessing.

## Logs

Real-time logs are saved to:
- `logs/quality_orchestrator.log`
- `logs/quality_batch_processor.log`
- `logs/ruff_batch_processor.log`

## Expected Performance

Assuming ~350 Python files with mixed complexity:

| Strategy | Time | Notes |
|----------|------|-------|
| `ruff check src/ --fix` (old) | **3-6 hours** ⚠️ | Hangs frequently |
| Batch (size=10) | ~30-45 min | Reasonable, safe |
| Orchestrator (optimized) | ~20-30 min | Smart batching by complexity |
| Ruff only (fast) | ~15-20 min | Skips mypy/black |

## What Each Tool Does

### `quality_orchestrator.py` (Master Controller)
- Analyzes file complexity first
- Routes files by category to optimized batch sizes
- Monitors progress and ETA
- **Best for:** Full quality suite run

### `quality_tools_batch.py` (Unified Processor)
- Runs ruff, black, and mypy on files
- Batch size configurable (default: 10)
- Tool selection configurable
- **Best for:** All tools with custom settings

### `ruff_batch_processor.py` (Fast Lane)
- Runs only ruff (fastest)
- Very simple resume logic
- **Best for:** Quick ruff-only pass

### `analyze_file_complexity.py` (Intelligence)
- Profiles all files
- Predicts processing time
- Recommends settings
- **Best for:** Understanding your codebase

## Troubleshooting

### Still hanging on a specific file?
1. Run analysis: `python scripts/analyze_file_complexity.py`
2. Find the "problematic" category files
3. They'll be processed 1 per batch with 120s timeout

### Want to skip complicated files?
- Manually add paths to `state/quality_batch_checkpoint.json`
- Set them in the "processed_files" list to skip them

### Need to clear progress?
```bash
rm state/quality_*_checkpoint.json
```

## VS Code Tasks

Added tasks for quick access:
- `Quality: Smart Orchestrator` - Run `quality_orchestrator.py`
- `Quality: Batch Tools` - Run `quality_tools_batch.py`
- `Quality: Analyze Files` - Run `analyze_file_complexity.py`

Access via: **Ctrl+Shift+B** → Choose task

## Architecture

```
User Request
     ↓
Quality Orchestrator (master control)
     ├→ Complexity Analyzer (profile files)
     ├→ Simple Files Processor (batch=20, timeout=10s)
     ├→ Moderate Files Processor (batch=10, timeout=30s)
     ├→ Complex Files Processor (batch=5, timeout=60s)
     └→ Problematic Files Processor (batch=1, timeout=120s)
          ↓
     (checkpoints after each file)
          ↓
     Summary Report
```

## Key Improvements Over Old Approach

| Feature | Old | New | Benefit |
|---------|-----|-----|---------|
| Batch size | All files at once | 1-20 per batch | Prevents hangs |
| Timeout | None | 10-120s per file | Recovers from stuck files |
| Resumable | ❌ Restart from scratch | ✅ Checkpoint-based | No wasted work |
| Progress | ❌ No visibility | ✅ Real-time logging | Know what's happening |
| Smart routing | ❌ One-size-fits-all | ✅ By complexity | Optimized speeds |

---

**Remember:** If using the old monolithic command fails, use one of these batch processors instead!
