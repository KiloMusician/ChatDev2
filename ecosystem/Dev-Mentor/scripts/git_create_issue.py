"""scripts/git_create_issue.py — Create GitHub Issues from the task queue.

Reads pending tasks from:
  • tasks/ directory (*.json or *.md files)
  • memory.py task queue (priority 8+)
  • todo.md (lines starting with - [ ])

Creates GitHub Issues via REST API, adds labels, and marks tasks as issued.

Usage:
    python scripts/git_create_issue.py                  # process all pending
    python scripts/git_create_issue.py --dry-run        # preview without creating
    python scripts/git_create_issue.py --limit 5        # max 5 issues
    python scripts/git_create_issue.py --source tasks   # only tasks/ dir
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
GH_REPO = "KiloMusician/Dev-Mentor"
GH_API = f"https://api.github.com/repos/{GH_REPO}/issues"

LABEL_MAP = {
    "bug": {"name": "bug", "color": "d73a4a"},
    "enhancement": {"name": "enhancement", "color": "a2eeef"},
    "game": {"name": "game-content", "color": "0075ca"},
    "llm": {"name": "ai-generation", "color": "e4e669"},
    "ops": {"name": "ops", "color": "ededed"},
    "content": {"name": "content", "color": "7057ff"},
    "fix": {"name": "fix", "color": "d73a4a"},
}


def _get_token() -> str:
    for line in (
        (ROOT / ".env.local").read_text().splitlines()
        if (ROOT / ".env.local").exists()
        else []
    ):
        if line.startswith("GITHUB_TOKEN="):
            return line.split("=", 1)[1].strip()
    return os.environ.get("GITHUB_TOKEN", "")


def _headers() -> dict:
    token = _get_token()
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _ensure_labels(labels: list[str]) -> None:
    """Create missing labels in the repo."""
    import requests

    existing_r = requests.get(
        f"https://api.github.com/repos/{GH_REPO}/labels",
        headers=_headers(),
        timeout=10,
    )
    existing_names = {l["name"] for l in existing_r.json()} if existing_r.ok else set()
    for label in labels:
        if label not in LABEL_MAP:
            continue
        info = LABEL_MAP[label]
        if info["name"] not in existing_names:
            requests.post(
                f"https://api.github.com/repos/{GH_REPO}/labels",
                headers=_headers(),
                json=info,
                timeout=10,
            )


def _existing_titles() -> set[str]:
    """Fetch open issue titles to avoid duplicates."""
    import requests

    titles = set()
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/repos/{GH_REPO}/issues",
            headers=_headers(),
            params={"state": "open", "per_page": 100, "page": page},
            timeout=15,
        )
        items = r.json() if r.ok else []
        if not items:
            break
        titles.update(i["title"] for i in items)
        if len(items) < 100:
            break
        page += 1
    return titles


def create_issue(
    title: str,
    body: str,
    labels: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    import requests

    if dry_run:
        return {"dry_run": True, "title": title, "labels": labels}
    _ensure_labels(labels or [])
    label_names = [LABEL_MAP.get(l, {}).get("name", l) for l in (labels or [])]
    r = requests.post(
        GH_API,
        headers=_headers(),
        json={"title": title, "body": body, "labels": label_names},
        timeout=15,
    )
    return r.json()


def _tasks_from_tasks_dir() -> list[dict]:
    tasks_dir = ROOT / "tasks"
    if not tasks_dir.exists():
        return []
    items = []
    for f in sorted(tasks_dir.glob("*.json")):
        if "issued" in f.name:
            continue
        try:
            data = json.loads(f.read_text())
            data["_source_file"] = str(f)
            items.append(data)
        except Exception:
            pass
    for f in sorted(tasks_dir.glob("*.md")):
        items.append(
            {
                "title": f.stem.replace("-", " ").replace("_", " "),
                "body": f.read_text()[:500],
                "labels": ["enhancement"],
                "_source_file": str(f),
            }
        )
    return items


def _tasks_from_memory(min_priority: int = 7) -> list[dict]:
    try:
        sys.path.insert(0, str(ROOT))
        from memory import get_memory

        mem = get_memory()
        rows = mem._db.execute(
            "SELECT description, priority, category FROM tasks WHERE status='pending' AND priority>=? ORDER BY priority DESC LIMIT 20",
            (min_priority,),
        ).fetchall()
        return [
            {
                "title": f"[{row[2]}] {row[0][:80]}",
                "body": row[0],
                "labels": [row[2] if row[2] in LABEL_MAP else "enhancement"],
                "_source": "memory",
            }
            for row in rows
        ]
    except Exception:
        return []


def _tasks_from_todo() -> list[dict]:
    todo = ROOT / "todo.md"
    if not todo.exists():
        return []
    items = []
    for line in todo.read_text().splitlines():
        line = line.strip()
        if line.startswith("- [ ]"):
            text = line[5:].strip()
            if len(text) > 5:
                label = (
                    "bug"
                    if any(w in text.lower() for w in ["fix", "error", "crash", "bug"])
                    else "enhancement"
                )
                items.append({"title": text[:80], "body": text, "labels": [label]})
    return items


def run(dry_run: bool = False, limit: int = 10, source: str = "all") -> list[dict]:
    tasks = []
    if source in ("all", "tasks"):
        tasks += _tasks_from_tasks_dir()
    if source in ("all", "memory"):
        tasks += _tasks_from_memory()
    if source in ("all", "todo"):
        tasks += _tasks_from_todo()

    if not tasks:
        return [{"message": "No pending tasks found"}]

    # De-duplicate by title
    existing = _existing_titles()
    results = []
    issued_dir = ROOT / "tasks" / "issued"
    issued_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks[:limit]:
        title = task.get("title", "Untitled task")
        if title in existing:
            results.append({"skipped": True, "reason": "already open", "title": title})
            continue
        body = task.get("body", title)
        labels = task.get("labels", ["enhancement"])
        result = create_issue(title, body, labels, dry_run=dry_run)
        result["title"] = title
        results.append(result)
        existing.add(title)
        # Move task file to issued/
        if not dry_run and "_source_file" in task:
            src = Path(task["_source_file"])
            if src.exists():
                src.rename(issued_dir / src.name)
        # Gentle rate limit
        if not dry_run:
            time.sleep(0.5)

    return results


def main():
    dry_run = "--dry-run" in sys.argv
    limit = 10
    source = "all"
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        if arg == "--source" and i + 1 < len(sys.argv):
            source = sys.argv[i + 1]

    results = run(dry_run=dry_run, limit=limit, source=source)
    for r in results:
        if r.get("dry_run"):
            print(f"  [DRY-RUN] Would create: {r['title']}")
        elif r.get("skipped"):
            print(f"  [SKIP]    {r['title']} (already open)")
        elif r.get("html_url"):
            print(f"  [CREATED] {r['html_url']}")
        elif r.get("message"):
            print(f"  [INFO]    {r['message']}")
        else:
            print(f"  [ERROR]   {r}")


if __name__ == "__main__":
    main()
