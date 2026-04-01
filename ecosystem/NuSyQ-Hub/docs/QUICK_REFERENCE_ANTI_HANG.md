# Anti-Hang Solution - Quick Reference Card

## ⚠️ Problem
`ruff check src/ --fix` hangs for **3-6+ hours**

## ✅ Solution
Use batch processors instead

---

## 🚀 Quick Start (3 Steps)

### Step 1: Analyze Complexity (optional but recommended)
```bash
python scripts/analyze_file_complexity.py
```
Takes ~2 minutes, shows file categories and timing estimates

### Step 2: Run Smart Orchestrator
```bash
python scripts/quality_orchestrator.py
```
Automatically:
- Analyzes if needed
- Batches by complexity
- Shows progress
- Saves checkpoints
**Expected time: 20-30 minutes** ✅

### Step 3: Resume if Interrupted
```bash
python scripts/quality_orchestrator.py --skip-analysis
```
Continues from last checkpoint

---

## 🎮 VS Code Tasks

Press **Ctrl+Shift+B** and select:
- **🧠 Quality: Smart Orchestrator (Anti-Hang)** ← Use this
- 🧠 Quality: Smart Orchestrator (Resume) ← Use if interrupted
- ⚡ Quality: Analyze File Complexity ← Learn about your files
- 📦 Quality: Batch Tools (Unified) ← Alternative
- ⚡ Quality: Ruff Batch (Fast) ← Ruff only
- 📋 Quality: Clear Batch Checkpoints ← Reset progress

---

## 📊 Performance

| Method | Time | Hang Risk |
|--------|------|-----------|
| Old: `ruff check src/` | 3-6+ hours ⚠️ | Very High |
| New: Smart Orchestrator | 20-30 min ✅ | None |
| Fast: Ruff Only | 15-20 min ✅ | None |

---

## 🔧 Advanced Options

### Ruff Only (Faster)
```bash
python scripts/ruff_batch_processor.py 20 15
# 20 files per batch, 15 second timeout
```

### Custom Batch Size
```bash
python scripts/quality_tools_batch.py --batch-size 5
# Smaller batches = safer but slower
```

### With Verbose Progress
```bash
python scripts/quality_orchestrator.py --verbose
# See each file being processed
```

### Monitor for Hangs (In Another Terminal)
```bash
python scripts/hang_detector.py --timeout 60
# Alerts if any file takes >60 seconds
```

---

## 📝 Logs

View progress in real-time:
```bash
# On Windows
Get-Content logs/quality_orchestrator.log -Wait

# On macOS/Linux
tail -f logs/quality_orchestrator.log
```

---

## 🔄 Checkpoint System

**Automatic checkpoints** saved after each file:
- `state/quality_orchestrator_checkpoint.json`
- `state/quality_batch_checkpoint.json`
- `state/ruff_batch_checkpoint.json`

**Resume automatically:** Just run the command again  
**Clear to restart:** `rm state/quality_*_checkpoint.json`

---

## ⚡ Quick Decisions

**Q: Which should I use?**
- A: Start with `python scripts/quality_orchestrator.py` → it's smart!

**Q: It's still taking too long?**
- A: It's likely working on complex files. Be patient or check logs.

**Q: Did it hang?**
- A: It has timeouts per file. Won't wait forever. Check logs.

**Q: Want just ruff (no black/mypy)?**
- A: Use `python scripts/ruff_batch_processor.py` (faster)

**Q: Want to resume?**
- A: Run same command again - checkpoints handle it

**Q: Want to restart from scratch?**
- A: `rm state/quality_*_checkpoint.json` then run

---

## 📚 Full Documentation

- [ANTI_HANG_SOLUTION.md](ANTI_HANG_SOLUTION.md) - Technical details
- [QUALITY_TOOLS_BATCH_PROCESSING.md](QUALITY_TOOLS_BATCH_PROCESSING.md) - Complete reference

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Still hangs on a file | Increase timeout: `--batch-size 1` with 120s timeout |
| Want to skip a file | Add to checkpoint's `"processed_files"` list |
| Progress not showing | Add `--verbose` flag |
| Restart from scratch | `rm state/quality_*_checkpoint.json` |
| Monitor in real-time | `tail -f logs/quality_orchestrator.log` |

---

**Last Updated:** February 17, 2026  
**Status:** ✅ Production Ready
