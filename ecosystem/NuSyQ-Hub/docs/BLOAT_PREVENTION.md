# Bloat Prevention Guidelines

**Version**: 1.0
**Effective**: 2026-01-30
**Philosophy**: "Think like professional engineers, not creative vibers"

---

## 🎯 Core Principle

**Database-First Architecture**: When you have a production-grade database and API infrastructure, USE IT. Don't create parallel file-based systems.

---

## ⚠️ What Causes Bloat

### 1. **JSON File Dumps Instead of Database**
**Problem**: Writing `docs/Reports/aggregated_insights.json` instead of querying DuckDB
**Impact**: 236+ JSON files, hard to query, no real-time updates
**Solution**: Use `/api/status` endpoint that queries DuckDB

### 2. **No Retention Policies**
**Problem**: Files accumulate forever (21GB single maze_summary file!)
**Impact**: Workspace >100GB, slow git operations, disk space exhaustion
**Solution**: Auto-delete files >N days old, keep latest 3

### 3. **Duplicate Tracking Systems**
**Problem**: Quest JSON files + DuckDB quests table + Resolution tracker JSONL
**Impact**: Data inconsistency, maintenance nightmare, 3x storage
**Solution**: Single source of truth (DuckDB)

### 4. **Legacy Build Contexts**
**Problem**: `.docker_build_context/`, `.sanitized_build_context/` never cleaned
**Impact**: 5-10GB of stale directory copies
**Solution**: Delete on sight (should be gitignored anyway)

---

## ✅ Prevention Rules

### Rule 1: Database-First
**DO**:
- Write to DuckDB using `dual_write()` pattern
- Query `/api/status`, `/api/health`, `/api/problems` endpoints
- Use WebSocket (port 5001) for real-time updates
- Store events in DuckDB `events` table
- Store quests in DuckDB `quests` table

**DON'T**:
- Write to `docs/Reports/` directory
- Create JSON snapshot files
- Maintain parallel quest/status tracking in files
- Use file polling for status updates

**Example**:
```python
# ❌ BAD (File-based):
def update_quest_status(quest_id, status):
    with open("quests.json", "r+") as f:
        quests = json.load(f)
        quests[quest_id]["status"] = status
        f.seek(0)
        json.dump(quests, f)

# ✅ GOOD (Database-first):
def update_quest_status(quest_id, status):
    from src.duckdb_integration.dual_write import dual_write

    dual_write(
        event_name="quest_status_changed",
        data={"quest_id": quest_id, "status": status},
        fallback_jsonl="quest_updates.jsonl"  # Backup only
    )
```

### Rule 2: Retention Policies
**DO**:
- Add cleanup to any tool that generates files
- Keep only N most recent (e.g., 3 maze_summaries)
- Compress old JSONL files after 30 days
- Delete compressed files after 90 days

**DON'T**:
- Generate files without cleanup
- Let logs/ directory grow indefinitely
- Keep every historical snapshot

**Example**:
```python
# Add to maze_solver.py:
def cleanup_old_summaries(log_dir: Path, keep_count: int = 3):
    summaries = sorted(
        log_dir.glob("maze_summary_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    for old_file in summaries[keep_count:]:
        old_file.unlink()

# Call after writing new summary:
cleanup_old_summaries(log_dir, keep_count=3)
```

### Rule 3: Single Source of Truth
**DO**:
- Choose ONE system per capability
- Prefer DuckDB over JSON files
- Prefer APIs over file reads
- Document the canonical source

**DON'T**:
- Maintain duplicate quest systems
- Create "backup" tracking in files
- Split data across multiple stores

**Canonical Sources**:
- **Quests**: DuckDB `quests` table (query via `/api/quests`)
- **Events**: DuckDB `events` table (query via `/api/events`)
- **Status**: DuckDB events with type `system_status_changed`
- **Reports**: Generated on-demand from DuckDB queries

### Rule 4: Compression Strategy
**DO**:
- Compress JSONL files older than 30 days
- Use `.jsonl.gz` format (70% space savings)
- Delete compressed files after 90 days

**DON'T**:
- Store uncompressed audit logs forever
- Skip compression to "save time"

**Automated**:
```bash
# Run weekly via cron:
python scripts/automated_cleanup.py
```

---

## 🤖 Automated Cleanup

### Weekly Automation

Add to crontab (Linux/Mac) or Task Scheduler (Windows):

```bash
# Every Sunday at 2 AM:
0 2 * * 0 cd /path/to/NuSyQ-Hub && python scripts/automated_cleanup.py
```

### Manual Invocation

```bash
# Dry-run (preview what would be deleted):
python scripts/automated_cleanup.py --dry-run

# Execute cleanup:
python scripts/automated_cleanup.py
```

### What Gets Cleaned

| Artifact | Age | Action |
|----------|-----|--------|
| JSONL files | >30 days | Compress to `.jsonl.gz` |
| Compressed JSONL | >90 days | Delete |
| Report JSON files | >90 days | Delete |
| maze_summary_*.json | >3 most recent | Delete |
| Legacy contexts | Any | Delete immediately |

---

## 📊 Acceptable vs. Bloat

### ✅ Acceptable File Usage

**Configuration files**:
- `config/*.yaml` - Service configuration
- `.env` - Environment variables
- `pyproject.toml` - Python project metadata

**Backup JSONL** (for DuckDB reconciliation):
- `quest_log.jsonl` - Append-only quest history
- `system_status_backup.jsonl` - Fallback for DB failure
- Compressed after 30 days, deleted after 90 days

**Search Indexes** (generated, gitignored):
- `State/search_index/file_metadata.json` - 25 MB (regenerated by hooks)
- `State/search_index/keyword_index.json` - 22 MB (regenerated by hooks)

### ❌ Bloat Examples

**JSON report dumps**:
- `docs/Reports/aggregated_insights.*.json` - Use `/api/status` instead
- `docs/Reports/problem_signal_snapshot.json` - Use `/api/problems` instead
- `.snapshots/system_snapshot_*.json` - Use `/api/snapshot` instead

**Duplicate tracking**:
- `quests.json` + DuckDB `quests` table - Pick ONE (DuckDB)
- `resolutions_database.jsonl` + DuckDB `events` - Pick ONE (DuckDB)

**Old summaries**:
- `logs/maze_summary_20250814_*.json` - Delete (>30 days old)
- Keep only latest 3

---

## 🔍 Monitoring

### Check Workspace Size

```bash
# Total size (excluding .venv):
du -sh . --exclude=.venv

# Largest files:
find . -type f -size +100M -exec ls -lh {} \; | sort -k5 -hr

# Largest directories:
du -h --max-depth=1 | sort -hr | head -20
```

### Red Flags

🚨 **Immediate action required** if:
- Any single file >1 GB
- `logs/` directory >50 GB
- `docs/Reports/` has >50 files
- Workspace total >100 GB (excluding .venv)

### Green Signals

✅ **Healthy workspace**:
- No single file >500 MB
- `logs/` directory <10 GB
- `docs/Reports/` has <10 files
- Workspace total <20 GB (excluding .venv)

---

## 🛠️ Tools & Commands

### Cleanup Tools

| Tool | Purpose | When to Run |
|------|---------|-------------|
| `scripts/automated_cleanup.py` | Weekly workspace cleanup | Every Sunday |
| `scripts/cleanup_bloat.py` | Archive old reports/logs | Monthly |
| `scripts/cleanup_runtime_artifacts.py` | Clean temp state files | After test runs |
| `scripts/emergency_cleanup.py` | Immediate bloat removal | When >100 GB |

### Git Ignore Rules

All generated artifacts are gitignored:

```gitignore
# Generated Artifacts (never commit)
logs/maze_summary_*.json
State/search_index/*.json
docs/Reports/
**/*_audit.json
**/*_analysis.json
*.json.gz
.docker_build_context/
.sanitized_build_context/
```

---

## 📚 Integration Points

### DuckDB Infrastructure

**Location**: `/data/state.duckdb` (536 KB)
**Schema**:
```sql
events (timestamp, event, details)
quests (id, title, description, status, created_at, updated_at)
questlines (name, description, tags, created_at)
```

**Dual-Write Pattern**:
```python
from src.duckdb_integration.dual_write import dual_write

# Writes to DuckDB + backup JSONL
dual_write(
    event_name="quest_added",
    data={"title": "Fix bloat", "priority": 5},
    fallback_jsonl="quest_backup.jsonl"
)
```

### API Endpoints

**FastAPI Server** (port 8000):
- `GET /api/status` - System status from DuckDB
- `GET /api/health` - Health metrics from DuckDB
- `GET /api/problems` - Current problems (no file generation)
- `GET /api/snapshot` - Real-time snapshot (no file write)

**Flask+WebSocket** (port 5001):
- Real-time metrics dashboard
- WebSocket broadcasts for live updates
- No file polling required

---

## 🎓 Lessons Learned

### Why This Matters (2026-01-30 Cleanup)

**Before Cleanup**:
- 21.8 GB single maze_summary file
- 236+ JSON report files
- 3 overlapping quest systems
- >100 GB total workspace

**After Cleanup**:
- 6.68 GB recovered immediately
- Automated retention policies
- Database-first architecture
- <50 GB total workspace

**Root Cause**: Tools generated files without cleanup, JSON dumps instead of database queries, no retention policies.

**Fix**: Retention policy in maze_solver, automated weekly cleanup, database-first principle in ROSETTA_STONE.

---

## 📋 Checklist for New Features

Before creating ANY file-generating feature:

- [ ] Is this data already in DuckDB? (Use that instead)
- [ ] Can this be an API endpoint? (Don't write files)
- [ ] Does this need cleanup? (Add retention policy)
- [ ] Is this creating a duplicate system? (Merge with existing)
- [ ] Will this accumulate >1 GB over time? (Add compression)
- [ ] Is this gitignored? (Generated data should be)

---

## 🚀 Quick Reference

### DO THIS ✅
```python
# Query database
from src.duckdb_integration.realtime_status import get_recent_events
events = get_recent_events(hours=24)

# Use API
import requests
status = requests.get("http://localhost:8000/api/status").json()

# Cleanup after generating
cleanup_old_summaries(log_dir, keep_count=3)
```

### NOT THIS ❌
```python
# Write JSON file
with open("docs/Reports/status.json", "w") as f:
    json.dump(status, f)

# No cleanup (files accumulate forever)
summary_path = log_dir / f"summary_{timestamp}.json"
summary_path.write_text(json.dumps(data))
```

---

**Last Updated**: 2026-01-30
**Maintained By**: DevOps / System Hygiene
**Review Cycle**: Quarterly
**Next Review**: 2026-04-30
