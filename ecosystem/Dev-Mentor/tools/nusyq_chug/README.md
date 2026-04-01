NuSyQ-Chug — Proof-of-Concept

A small prototype agent that runs phased "CHUG" cycles to scan a workspace
for small triage items (TODO/FIXME/BUG markers), perform best-effort health
probes, and log per-phase events.

This POC is intentionally conservative:
- dry-run by default (no commits or edits)
- commit logic gated behind --allow-commit
- use --fast to limit file scanning for quick runs

Quick usage

# Run one fast dry-run cycle on the Dev-Mentor root
python tools/nusyq_chug/nusyq_chug.py --once --fast --roots "c:\\Users\\keath\\Dev-Mentor"

# Run one cycle and allow commits (DANGEROUS) — only for tested environments
python tools/nusyq_chug/nusyq_chug.py --once --fast --roots "c:\\Users\\keath\\Dev-Mentor" --allow-commit

# Change phases or run multiple cycles
python tools/nusyq_chug/nusyq_chug.py --phases 5 10 15 --max-cycles 3 --fast

Logs

Event logs are written as JSONL into the chug_logs directory by default:

tools/nusyq_chug/chug_logs/events.jsonl

Each line is a JSON event describing phase start, triage picks, and any
commit metadata (if commits were allowed).

Notes

- Use --fast during development to avoid long scans.
- The POC is not a replacement for CI or humans; it is a helper to find and
  triage low-effort improvements.
