# Snapshot ID Enforcement Protocol

**Status:** MANDATORY (Tier 0 Control Plane)  
**Effective Date:** 2026-01-10  
**Authority:** Canonical Truth Loop Doctrine

---

## Rule

> **Every report, quest, and decision MUST reference a snapshot ID.**

---

## Implementation

### 1. Snapshot ID Generation

**Format:** `snapshot_YYYYMMDD_HHMMSS_<8-char-hash>`  
**Example:** `snapshot_20260110_004530_7afc65c1`

**Generator:** `scripts/start_nusyq.py snapshot`

**Schema:**

```json
{
  "snapshot_id": "snapshot_20260110_004530_7afc65c1",
  "timestamp": "2026-01-10T00:45:30.123456+00:00",
  "run_id": "run_2026-01-10_004530_7afc65c1",
  "repos": {
    "nusyq-hub": {
      "path": "/path/to/NuSyQ-Hub",
      "branch": "master",
      "sha": "24b125ebef01",
      "dirty": true,
      "ahead_behind": [0, 145]
    },
    "simulated-verse": {
      /* ... */
    },
    "nusyq": {
      /* ... */
    }
  },
  "diagnostics": {
    "total": 2682,
    "errors": 12,
    "warnings": 118,
    "infos": 2552
  }
}
```

---

### 2. Mandatory Snapshot ID in Artifacts

**All outputs must include snapshot ID in header:**

#### Markdown Reports

```markdown
# Report Title

**Snapshot ID:** `snapshot_20260110_004530_7afc65c1`  
**Generated:** 2026-01-10 00:45:30 UTC  
**Run ID:** `run_2026-01-10_004530_7afc65c1`

---

[Report content...]
```

#### JSON Reports

```json
{
  "_metadata": {
    "snapshot_id": "snapshot_20260110_004530_7afc65c1",
    "timestamp": "2026-01-10T00:45:30.123456+00:00",
    "run_id": "run_2026-01-10_004530_7afc65c1"
  },
  "data": {
    /* ... */
  }
}
```

#### Quest Log Entries

```json
{
  "timestamp": "2026-01-10T00:45:30.123456+00:00",
  "event": "create_quest",
  "snapshot_id": "snapshot_20260110_004530_7afc65c1",
  "details": {
    "title": "Fix import errors",
    "derived_from_snapshot": "snapshot_20260110_004530_7afc65c1"
    /* ... */
  }
}
```

---

### 3. Validation Rules

**Stale Artifact Detection:**

```python
def is_stale(artifact: dict, max_age_minutes: int = 30) -> bool:
    """
    Check if artifact is stale (missing snapshot ID or too old).

    Returns:
        True if artifact should be ignored/regenerated
    """
    # Rule 1: No snapshot ID = stale
    if "snapshot_id" not in artifact.get("_metadata", {}):
        return True

    # Rule 2: Snapshot ID older than threshold = stale
    snapshot_time = parse_snapshot_timestamp(artifact["_metadata"]["snapshot_id"])
    age_minutes = (datetime.utcnow() - snapshot_time).total_seconds() / 60

    return age_minutes > max_age_minutes
```

**Enforcement Points:**

1. **Quest Creation:** Must reference snapshot ID or be rejected
2. **Error Reports:** Must include snapshot ID or marked as "unverified"
3. **System State:** Must be tied to snapshot or considered "drifted"
4. **CI/CD:** Snapshot ID required for all automated operations

---

### 4. Snapshot ID Lifecycle

**Creation:**

```bash
python scripts/start_nusyq.py snapshot
# Generates: state/reports/current_state.md
# Emits: snapshot_20260110_004530_7afc65c1
```

**Verification:**

```bash
python scripts/start_nusyq.py verify_snapshot <snapshot_id>
# Returns: VALID | STALE | INVALID
```

**Comparison:**

```bash
python scripts/start_nusyq.py diff_snapshots <old_id> <new_id>
# Shows: changed files, new errors, resolved issues
```

---

### 5. Integration Points

**Quest System:**

- Quest creation requires `--snapshot-id` flag
- Quest closure verifies snapshot still valid
- Quest log entries auto-tagged with snapshot

**Error Reporter:**

- All error reports embed snapshot ID
- Cached reports include staleness indicator
- Fresh reports force new snapshot

**Healing Orchestrator:**

- Healing runs require snapshot baseline
- Post-healing verification uses new snapshot
- Healing results diff snapshots

**CI/CD:**

- Pre-commit: snapshot required
- Test runs: snapshot anchors results
- Deployment: snapshot verification mandatory

---

### 6. Migration Path

**Phase 1: Soft Enforcement (Current)**

- Snapshot ID added to all new artifacts
- Warnings for missing snapshot IDs
- Existing artifacts grandfathered

**Phase 2: Hard Enforcement (2026-01-15)**

- Missing snapshot ID = operation blocked
- Stale snapshots auto-regenerated
- Quest system enforces snapshot

**Phase 3: Full Automation (2026-01-20)**

- All operations auto-snapshot
- Stale detection automatic
- Quest reconciliation from snapshots

---

### 7. Exemptions

**Explicitly Exempt Operations:**

- Read-only queries (health checks, status)
- Emergency recovery operations
- Manual debugging sessions
- Documentation generation

**Exemption Requires:**

- Explicit `--no-snapshot` flag
- Logged justification
- Manual approval for automated ops

---

### 8. Monitoring

**Compliance Metrics:**

```bash
python scripts/start_nusyq.py snapshot_compliance
```

**Output:**

```
📊 Snapshot ID Compliance Report

Total Operations: 1,234
  ✅ With Snapshot ID: 987 (80%)
  ⚠️  Without Snapshot ID: 247 (20%)

By Category:
  Quests: 95% compliant
  Error Reports: 100% compliant
  System State: 75% compliant
  Healing Runs: 90% compliant

Oldest Valid Snapshot: 2 hours ago
Stale Snapshots: 3
```

---

### 9. Developer Workflow

**Before Starting Work:**

```bash
# Generate fresh snapshot
python scripts/start_nusyq.py snapshot

# Note the snapshot ID
# snapshot_20260110_004530_7afc65c1
```

**During Work:**

```bash
# All operations auto-reference latest snapshot
python scripts/start_nusyq.py heal --snapshot-id auto

# Quests created with snapshot context
python scripts/start_nusyq.py create_quest "Fix imports" --from-snapshot
```

**After Work:**

```bash
# Generate new snapshot to capture changes
python scripts/start_nusyq.py snapshot

# Compare before/after
python scripts/start_nusyq.py diff_snapshots <old> <new>
```

---

### 10. Error Messages

**Missing Snapshot ID:**

```
❌ ERROR: Operation requires snapshot ID

This operation modifies system state and must reference
a canonical snapshot for traceability.

Fix:
  1. Generate snapshot: python scripts/start_nusyq.py snapshot
  2. Use --snapshot-id flag: --snapshot-id <snapshot_id>
  3. Or use --snapshot-id auto for latest

Exemption: Add --no-snapshot flag with justification
```

**Stale Snapshot:**

```
⚠️  WARNING: Snapshot is stale (45 minutes old)

Snapshot: snapshot_20260110_003000_abcd1234
Age: 45 minutes
Threshold: 30 minutes

Recommendation: Generate fresh snapshot before proceeding.

Override: Add --allow-stale flag (not recommended)
```

---

## Summary

This protocol ensures **one canonical truth** by requiring all state-changing
operations to reference a snapshot ID. This eliminates diagnostic drift, quest
context mismatch, and planning ambiguity.

**Implementation Status:** ✅ Core infrastructure complete, enforcement in
progress

**Next Steps:**

1. Add snapshot ID to all `start_nusyq.py` actions
2. Enable stale detection in quest system
3. Wire snapshot diff into healing workflows
4. Add compliance dashboard to system status

---

**Last Updated:** 2026-01-10  
**Owner:** System Reliability Engineering  
**Review Cycle:** Weekly
