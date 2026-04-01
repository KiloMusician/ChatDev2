#!/bin/bash
# Quick Reference: Query Decision Registry

# Location
# ~/.substrate/registry.jsonl  (JSONL format — one JSON object per line)

# ============================================================
# BASIC QUERIES (jq)
# ============================================================

# Show all entries
cat .substrate/registry.jsonl | jq '.'

# Show only decision IDs
cat .substrate/registry.jsonl | jq '.decision_id'

# Show phase/action/timestamp
cat .substrate/registry.jsonl | jq '.[] | {phase, action, timestamp}'

# ============================================================
# PHASE QUERIES
# ============================================================

# All Phase 3 decisions (ChatDev)
cat .substrate/registry.jsonl | jq '.[] | select(.phase=="phase_3")'

# All Phase 5 decisions (Culture Ship)
cat .substrate/registry.jsonl | jq '.[] | select(.phase=="phase_5")'

# Count decisions by phase
cat .substrate/registry.jsonl | jq -r '.phase' | sort | uniq -c

# ============================================================
# ACTION QUERIES
# ============================================================

# All orchestrator decisions
cat .substrate/registry.jsonl | jq '.[] | select(.type=="orchestrator_decision")'

# All remediation actions
cat .substrate/registry.jsonl | jq '.[] | select(.type=="remediation_executed")'

# ============================================================
# TIME-BASED QUERIES
# ============================================================

# Decisions from a specific timestamp
cat .substrate/registry.jsonl | jq '.[] | select(.timestamp | contains("2026-04-01T04:11"))'

# Decisions within a time range
cat .substrate/registry.jsonl | jq '.[] | select(.timestamp | startswith("2026-04-01T04:11:2"))'

# ============================================================
# COMPLEX QUERIES
# ============================================================

# Show decision timeline (phase → action → outcome)
cat .substrate/registry.jsonl | jq '.[] | {phase, action, status: .payload.status}'

# Get ChatDev task details
cat .substrate/registry.jsonl | jq '.[] | select(.phase=="phase_3") | .payload.task'

# Get Culture Ship pilot config
cat .substrate/registry.jsonl | jq '.[] | select(.phase=="phase_5") | .payload.pilot_config'

# Get validation results
cat .substrate/registry.jsonl | jq '.[] | select(.phase=="phase_6") | .payload.checks'

# ============================================================
# GREP ALTERNATIVES (if jq not available)
# ============================================================

# Find all phase 5 entries
grep '"phase_5"' .substrate/registry.jsonl

# Find decision IDs
grep '"decision_id"' .substrate/registry.jsonl | grep -o '"[a-f0-9-]*"' | sort -u

# ============================================================
# EXPORT/ANALYTICS
# ============================================================

# Export to CSV (phases and actions)
cat .substrate/registry.jsonl | jq -r '[.phase, .action, .timestamp] | @csv' > decisions.csv

# Count total decisions
cat .substrate/registry.jsonl | wc -l

# Show decision frequency over time (by hour)
cat .substrate/registry.jsonl | jq -r '.timestamp | .[0:13]' | sort | uniq -c

# ============================================================
# MONITORING (watch for new entries)
# ============================================================

# Watch for new entries (tail + follow)
tail -f .substrate/registry.jsonl | jq '.decision_id' --raw-output

# Check latest entry
tail -1 .substrate/registry.jsonl | jq '.'

# Watch registry size
watch -n 1 'wc -l .substrate/registry.jsonl'

# ============================================================
# VALIDATION QUERIES
# ============================================================

# Are all entries valid JSON?
for line in $(cat .substrate/registry.jsonl); do jq -e . <<< "$line" > /dev/null || echo "Invalid: $line"; done

# All decision IDs present?
cat .substrate/registry.jsonl | jq '.decision_id' | sort -u | wc -l

# Are all phases represented?
cat .substrate/registry.jsonl | jq -r '.phase' | sort -u

# ============================================================
# AUDIT COMPLIANCE
# ============================================================

# Full audit trail (human readable)
cat .substrate/registry.jsonl | jq '.[] | "\(.timestamp) | \(.phase) | \(.action) | \(.decision_id)"' -r

# Prove immutability (check all entries have timestamps)
cat .substrate/registry.jsonl | jq '.[] | select(.timestamp == null)' | wc -l  # Should be 0

# Verify source (all from orchestrator?)
cat .substrate/registry.jsonl | jq '.[] | select(.source != "multi-phase-orchestrator")' 

# ============================================================
# DEBUGGING
# ============================================================

# Show entry with most detail (Phase 5 pilot config)
cat .substrate/registry.jsonl | jq '.[] | select(.phase=="phase_5") | .payload' -r

# Pretty-print any entry
tail -1 .substrate/registry.jsonl | jq '.'

# Check for errors
grep '"error"' .substrate/registry.jsonl

# ============================================================
# INTEGRATION (with other systems)
# ============================================================

# Push to external logging system (example: curl)
# for entry in $(cat .substrate/registry.jsonl); do
#   curl -X POST https://logs.example.com -d "$entry"
# done

# Sync to version control
git add .substrate/registry.jsonl
git commit -m "Auto: decision registry sync"

# ============================================================
# NOTES
# ============================================================
# - Format: JSONL (one JSON object per line)
# - Immutable: entries never updated, only appended
# - Queryable: standard jq + grep tools work
# - Auditable: every decision logged with timestamp
# - Source: orchestrator writes entries (see .source field)
# - Phases: 2-6 currently (Phase 1 is base setup)
#
# For GraphQL-style queries, pipe to jq filters
# For SQL-style queries, convert to .csv and load into sqlite
