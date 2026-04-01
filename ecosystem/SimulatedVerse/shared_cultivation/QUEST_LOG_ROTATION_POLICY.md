# Shared Quest Log Rotation Policy

Artifact authority: hand-authored operational policy

## Purpose

`shared_cultivation/quest_log.jsonl` is a useful runtime ledger, but it should not grow without bound.
Large ledger growth increases scan friction, slows mounted-worktree operations, and makes low-token inspection worse.

## Policy

- keep the live ledger small enough for fast local inspection
- archive older entries instead of deleting them
- prefer compressed archive files under `shared_cultivation/archive/`
- keep the active file as the canonical write target
- surface rotation status through `shared_cultivation/quest_log_rotation_status.json`

## Default Rotation Contract

- maximum active size: `5_000_000` bytes
- minimum retained tail: `10_000` lines
- archive format: `.jsonl.gz`

## Operator Commands

Dry-run:

```bash
python3 ops/rotate_shared_quest_log.py
```

Apply:

```bash
python3 ops/rotate_shared_quest_log.py --apply
```
