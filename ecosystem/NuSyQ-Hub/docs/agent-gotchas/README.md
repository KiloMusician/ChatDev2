# Agent-Specific Lessons

This directory contains lessons learned specific to each AI agent type (Claude, Copilot, Codex).

## Purpose

Different agents have different tendencies and blind spots. Capturing agent-specific gotchas prevents repeat mistakes and enables cross-agent learning.

## Files

- **`claude-lessons.md`** - Lessons specific to Claude (tends to over-explain, verbose)
- **`copilot-lessons.md`** - Lessons specific to GitHub Copilot (context-sensitive, fast)
- **`codex-lessons.md`** - Lessons specific to OpenAI Codex (code-focused, direct)
- **`common-gotchas.md`** - Mistakes all agents make (delete scaffolding, create duplicate systems)

## Format

Each lesson should include:
- **What went wrong**: Description of the mistake
- **Why it happened**: Agent tendency that caused it
- **Correct behavior**: What should happen instead
- **Prevention**: How to catch this in the future
- **Rule candidate**: Whether this should become a system rule

## Integration

These lessons are:
1. Read by agents during orientation (if relevant)
2. Referenced in System Brief for high-impact gotchas
3. Used to create `.cursor/rules/` when patterns emerge
4. Shared via `insights.jsonl` for real-time learning
