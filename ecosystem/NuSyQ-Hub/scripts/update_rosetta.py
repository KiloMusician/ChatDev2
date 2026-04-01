#!/usr/bin/env python3
from __future__ import annotations

# update_rosetta.py
#
# Auto-update the LIVE_STATUS block in docs/ROSETTA_STONE.md using snapshots
# from state/ and optionally open a PR with the change. Intended to be run from
# the NuSyQ-Hub repository root.
#
# Usage:
#   python scripts/update_rosetta.py [--commit] [--push] [--create-pr]
#
# Notes:
#   - If `gh` CLI is installed and `--create-pr` is given, the script will
#     attempt to create a PR. Otherwise it prints the git commands to run.
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ROSETTA_STONE.md"
LIVE_START = "<!-- LIVE_STATUS_START -->"
LIVE_END = "<!-- LIVE_STATUS_END -->"


def load_snapshot(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def load_current_block(text: str) -> str | None:
    if LIVE_START not in text or LIVE_END not in text:
        return None
    _, rest = text.split(LIVE_START, 1)
    block, _ = rest.split(LIVE_END, 1)
    return block.strip()


def parse_model_counts(line: str) -> dict[str, int]:
    """Parse a models summary line of the form:
    - models: provider1(2), provider2(5)
    """
    counts: dict[str, int] = {}
    m = re.search(r"-\\s*models:\\s*(.*)", line)
    if not m:
        return counts
    parts = [p.strip() for p in m.group(1).split(",") if p.strip()]
    for part in parts:
        name_match = re.match(r"([^()]+)\\((\\d+)\\)", part)
        if name_match:
            provider = name_match.group(1).strip()
            try:
                counts[provider] = int(name_match.group(2))
            except ValueError:
                continue
    return counts


def extract_models_from_block(block: str) -> dict[str, int]:
    for line in block.splitlines():
        if "- models:" in line:
            return parse_model_counts(line)
    return {}


def model_delta(old: dict[str, int], new: dict[str, int]) -> int:
    all_keys = set(old) | set(new)
    return sum(abs(new.get(k, 0) - old.get(k, 0)) for k in all_keys)


def summarize_services(coord: Any) -> str:
    if not isinstance(coord, dict):
        return "- services: unknown"
    services = coord.get("services", {})
    if not isinstance(services, dict) or not services:
        return "- services: unknown"
    sorted_services = ", ".join(sorted(services.keys()))
    return f"- services: {sorted_services}"


def summarize_models(llm: Any) -> str:
    if not isinstance(llm, dict):
        return "- models: unknown"
    models = []
    for provider, data in llm.items():
        count = 0
        if isinstance(data, list):
            count = len(data)
        elif isinstance(data, dict):
            models_list = data.get("models")
            if isinstance(models_list, list):
                count = len(models_list)
        else:
            continue
        models.append(f"{provider}({count})")
    return f"- models: {', '.join(models) if models else 'none discovered'}"


def summarize_ignore(ignore: Any) -> str:
    if not isinstance(ignore, dict):
        return "- ignore_files: unknown"
    files = ignore.get("files")
    count = len(files) if isinstance(files, list) else 0
    return f"- ignore_files: {count}"


def raw_snapshot_sections(coord: Any, llm: Any) -> list[str]:
    sections = ["", "Raw snapshots (truncated):"]
    if coord:
        payload = coord if isinstance(coord, dict) else {}
        sections.append(json.dumps(payload, indent=2)[:2000])
    if llm:
        payload = llm if isinstance(llm, dict) else {}
        sections.append("\n" + json.dumps(payload, indent=2)[:2000])
    return sections


def build_live_block():
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    parts = [f"Generated: {now}"]

    llm = load_snapshot(ROOT / "state" / "llm_inventory.json")
    coord = load_snapshot(ROOT / "state" / "coordinator_status.json")
    ignore = load_snapshot(ROOT / "state" / "ignore_report.json")

    parts.append("")
    parts.append("Summary:")
    parts.append(summarize_services(coord))
    parts.append(summarize_models(llm))
    parts.append(summarize_ignore(ignore))
    parts.extend(raw_snapshot_sections(coord, llm))

    return "\n".join(parts)


def replace_live_block(text: str, block: str) -> str:
    if LIVE_START not in text or LIVE_END not in text:
        raise RuntimeError("LIVE_STATUS markers not found in ROSETTA_STONE.md")
    pre, rest = text.split(LIVE_START, 1)
    _, post = rest.split(LIVE_END, 1)
    new = pre + LIVE_START + "\n" + block + "\n" + LIVE_END + post
    return new


def should_skip_update(args, current_models: dict[str, int], delta: int) -> bool:
    if args.force:
        return False
    if args.min_model_delta <= 0 or not current_models:
        return False
    if delta < args.min_model_delta:
        print(f"Skip update: model delta {delta} < threshold {args.min_model_delta}")
        return True
    return False


def record_live_manifest(current_models: dict[str, int], new_models: dict[str, int], delta: int) -> None:
    backups_dir = ROOT / "docs" / "claude_backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    manifest = backups_dir / "live_status_manifest.jsonl"
    entry = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "models_before": current_models,
        "models_after": new_models,
        "delta": delta,
    }
    with manifest.open("a", encoding="utf-8") as mf:
        mf.write(json.dumps(entry) + "\n")


def _run_backup_script(backup_sh: Path, args) -> bool:
    if os.name == "nt":
        print("Skipping bash-based Claude backup script on Windows.")
        return True
    cmd = f'bash "{backup_sh}"'
    print("Would run backup script:" if args.dry_run else "Running backup script:")
    print("  ", cmd)
    if args.dry_run:
        return True
    res = subprocess.run(cmd, shell=True, check=False)
    if res.returncode != 0:
        print("Backup script reported non-zero exit; aborting Claude patch.")
        return False
    return True


def _run_patch_helper(patch_js: Path, args) -> None:
    cmd = f'node "{patch_js}" --apply'
    print("Would run patch helper:" if args.dry_run else "Running patch helper:")
    print("  ", cmd)
    if args.dry_run:
        return
    res = subprocess.run(cmd, shell=True, check=False)
    if res.returncode != 0:
        print("Patch helper returned non-zero; inspect output.")


def attempt_create_pr(branch: str) -> None:
    gh = subprocess.run("gh --version", shell=True, check=False, stdout=subprocess.DEVNULL)
    if gh.returncode == 0:
        print("Creating PR via gh CLI")
        git(
            'gh pr create --title "auto: update ROSETTA_STONE LIVE_STATUS" --body "Automated update of LIVE_STATUS block"'
        )
    else:
        print("\ngh CLI not available. To create a PR manually, run:")
        print(f"  git push --set-upstream origin {branch}")
        print(
            '  gh pr create --title "auto: update ROSETTA_STONE LIVE_STATUS" --body "Automated update of LIVE_STATUS block"'
        )


def perform_git_workflow(args, branch: str) -> None:
    print("Creating branch", branch)
    git(f"git checkout -b {branch}")
    git("git add docs/ROSETTA_STONE.md")
    git('git commit -m "chore: auto-update ROSETTA_STONE LIVE_STATUS"')
    if args.push:
        print("Pushing branch")
        git(f"git push --set-upstream origin {branch}")
    if args.create_pr:
        attempt_create_pr(branch)


def find_claude_root(args) -> Path | None:
    candidates = []
    if args.claude_path:
        candidates.append(Path(args.claude_path))
    candidates.append(ROOT.parent / "claude-code-tips")
    candidates.append(ROOT / ".." / "claude-code-tips")
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.exists():
            return resolved
    return None


def apply_claude_updates(args) -> None:
    claude_root = find_claude_root(args)
    if not claude_root:
        print("claude-code-tips not found in the workspace; skipping Claude update.")
        return

    sp_dir = None
    for trial in ["system-prompt", "system-prompt/2.1.9", "system-prompt/2.1.7"]:
        candidate = claude_root / trial
        if candidate.exists():
            sp_dir = candidate
            break

    if not sp_dir:
        print("No system-prompt helpers found under claude-code-tips; skipping Claude update.")
        return

    backup_sh = sp_dir / "backup-cli.sh"
    patch_js = sp_dir / "patch-cli.js"

    if backup_sh.exists():
        if not _run_backup_script(backup_sh, args):
            return
    else:
        print("Backup script not found, continuing cautiously.")

    if patch_js.exists():
        _run_patch_helper(patch_js, args)
    else:
        print("Patch helper not found; nothing to apply.")


def git(cmd, cwd=ROOT):
    return subprocess.run(cmd, cwd=cwd, shell=True, check=False)


def _update_live_status(args, orig: str) -> tuple[bool, dict[str, int], dict[str, int], int]:
    current_block = load_current_block(orig) or ""
    current_models = extract_models_from_block(current_block)

    block = build_live_block()
    new_models = extract_models_from_block(block)
    delta = model_delta(current_models, new_models)

    if should_skip_update(args, current_models, delta):
        return False, current_models, new_models, delta

    new = replace_live_block(orig, block)
    if new == orig:
        print("No changes to LIVE_STATUS block.")
        return False, current_models, new_models, delta

    if args.dry_run:
        print("Dry run: LIVE_STATUS block would change. Diff:")
        diff = difflib.unified_diff(
            orig.splitlines(),
            new.splitlines(),
            fromfile="current LIVE_STATUS",
            tofile="proposed LIVE_STATUS",
            lineterm="",
        )
        for line in diff:
            print(line)
        print("Dry run complete; no files were modified.")
        return False, current_models, new_models, delta

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tf:
        tf.write(new)
        tmp_path = Path(tf.name)

    tmp_path.replace(DOC)
    print("Updated LIVE_STATUS block in", DOC)
    record_live_manifest(current_models, new_models, delta)
    return True, current_models, new_models, delta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--create-pr", action="store_true")
    ap.add_argument(
        "--apply-claude",
        action="store_true",
        help="If set, attempt to invoke claude-code-tips backup/patch helpers",
    )
    ap.add_argument(
        "--claude-path",
        type=str,
        default=None,
        help="Path to a local claude-code-tips checkout (auto-detected if present in workspace)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not execute external patch commands; only simulate",
    )
    ap.add_argument(
        "--min-model-delta",
        type=int,
        default=0,
        help="Require at least this change in total model counts before writing/PR",
    )
    ap.add_argument("--force", action="store_true", help="Bypass threshold checks and always write")
    args = ap.parse_args()

    if not DOC.exists():
        print("ROSETTA_STONE.md not found at", DOC)
        sys.exit(2)

    orig = DOC.read_text()
    updated, _, _, _ = _update_live_status(args, orig)

    if updated and args.commit:
        branch = f"auto/update-rosetta-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        perform_git_workflow(args, branch)
    elif updated:
        print("Run with --commit --push --create-pr to commit, push and open a PR (gh CLI preferred).")

    if updated and args.apply_claude:
        apply_claude_updates(args)


if __name__ == "__main__":
    main()
