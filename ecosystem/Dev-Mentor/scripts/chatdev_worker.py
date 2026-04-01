#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from llm_client import LLMClient

try:
    import redis as _redis_lib
except Exception:  # pragma: no cover - import guard
    _redis_lib = None

QUEUE_PATH = BASE / "tasks" / "queue.json"
QUEUE_REL_PATH = QUEUE_PATH.relative_to(BASE).as_posix()
OUTPUT_DIR = BASE / "state" / "chatdev_output"
SERENA_CYCLE = BASE / "scripts" / "serena_cycle.py"
LOG_DIR = BASE / "var"
LOG_PATH = LOG_DIR / "chatdev_worker.log"
DEFAULT_POLL_SECONDS = 15
MAX_GENERATION_ATTEMPTS = 2
EXECUTION_RETRY_LIMIT = 2

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] CHATDEV_WORKER %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH),
    ],
)
log = logging.getLogger("chatdev_worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHATDEV_LLM_BACKEND = os.getenv("CHATDEV_LLM_BACKEND", "ollama")
CHATDEV_LLM_MODEL = os.getenv(
    "CHATDEV_LLM_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
)

if _redis_lib is not None:
    try:
        _redis = _redis_lib.from_url(REDIS_URL, decode_responses=True)
        _redis.ping()
    except Exception:
        _redis = None
else:
    _redis = None


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def slugify(text: str, limit: int = 48) -> str:
    compact = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return compact[:limit] or "task"


def load_queue() -> dict:
    if not QUEUE_PATH.exists():
        return {"updated_at": now_iso(), "source": "chatdev_worker", "tasks": []}
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(queue: dict) -> None:
    queue["updated_at"] = now_iso()
    QUEUE_PATH.write_text(json.dumps(queue, indent=2), encoding="utf-8")


def publish(channel: str, payload: dict) -> None:
    if _redis is None:
        return
    try:
        _redis.publish(channel, json.dumps({**payload, "_ts": now_iso()}))
    except Exception as exc:
        log.debug("Redis publish failed for %s: %s", channel, exc)


def select_tasks(queue: dict) -> list[dict]:
    selected: list[dict] = []
    for task in queue.get("tasks", []):
        if task.get("status") != "open":
            continue
        assignee = (task.get("assigned_to") or "").lower()
        category = (task.get("category") or "").lower()
        if assignee == "chatdev" or category == "hardening":
            selected.append(task)
    return selected


def update_task(task_id: str, **changes: object) -> dict | None:
    queue = load_queue()
    updated = None
    for task in queue.get("tasks", []):
        if task.get("id") == task_id:
            task.update(changes)
            updated = task
            break
    if updated is not None:
        save_queue(queue)
    return updated


def extract_target_path(task: dict) -> str | None:
    haystacks = [
        str(task.get("description") or ""),
        str(task.get("context") or ""),
        str(task.get("target") or ""),
        str(task.get("output") or ""),
    ]
    path_pattern = re.compile(
        r"([A-Za-z0-9_./-]+\.(?:py|ts|tsx|js|json|md|cs|xml|yml|yaml))"
    )
    for text in haystacks:
        match = path_pattern.search(text)
        if match:
            return match.group(1)
    description = (task.get("description") or "").lower()
    if "hub_health_probe" in description:
        return "scripts/hub_health_probe.py"
    return None


def refresh_serena(scope: str) -> dict:
    try:
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(SERENA_CYCLE),
                "--mode",
                "scoped",
                "--scope",
                scope,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(BASE),
            check=False,
        )
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr[-500:]}
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        return {"ok": True, "payload": payload}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def read_target(target_path: str | None) -> tuple[str | None, str]:
    if not target_path:
        return None, ""
    path = BASE / target_path
    if not path.exists() or not path.is_file():
        return target_path, ""
    return target_path, path.read_text(encoding="utf-8", errors="replace")


def read_related_tests(target_path: str | None) -> tuple[str | None, str]:
    if not target_path:
        return None, ""
    candidate = BASE / "tests" / f"test_{Path(target_path).stem}.py"
    if candidate.exists():
        relative = candidate.relative_to(BASE).as_posix()
        return relative, candidate.read_text(encoding="utf-8", errors="replace")
    return candidate.relative_to(BASE).as_posix(), ""


def build_prompt(
    task: dict,
    target_path: str | None,
    target_text: str,
    test_path: str | None,
    test_text: str,
    serena_summary: dict,
    previous_error: str | None = None,
) -> str:
    description = task.get("description", "")
    context = task.get("context", "")
    align = ((serena_summary.get("payload") or {}).get("align") or {}).get("score")
    drift = ((serena_summary.get("payload") or {}).get("drift") or {}).get(
        "signals", []
    )
    drift_excerpt = json.dumps(drift[:5], indent=2)
    target_block = target_text[:8000] if target_text else "(target file unavailable)"
    test_block = test_text[:4000] if test_text else "(no existing test file)"
    retry_block = (
        f"\nPrevious validation error:\n{previous_error}\n" if previous_error else ""
    )
    return (
        "You are ChatDev, a careful autonomous code-hardening worker inside Dev-Mentor.\n"
        "Return ONLY a unified diff patch. No prose, no markdown explanation, no code fences.\n\n"
        f"Task ID: {task.get('id')}\n"
        f"Priority: {task.get('priority')}\n"
        f"Description: {description}\n"
        f"Extra context: {context}\n"
        f"Target path: {target_path or 'unknown'}\n"
        f"Related test path: {test_path or 'unknown'}\n"
        f"Serena align score: {align}\n"
        f"Serena drift summary: {drift_excerpt}\n\n"
        "Hard requirements:\n"
        "- Focus only on the target task.\n"
        "- Output a valid unified diff beginning with `diff --git`.\n"
        "- Keep the patch small and targeted.\n"
        "- Add tests when appropriate.\n"
        "- Preserve existing `--once` behavior.\n"
        "- Make daemon mode graceful on SIGTERM.\n"
        "- Improve timeout/malformed-response handling with retry/backoff.\n"
        "- Ensure the module is safe to import.\n"
        f"{retry_block}\n"
        "Current target file:\n"
        f"{target_block}\n\n"
        "Current related test file:\n"
        f"{test_block}\n"
    )


def fallback_response(task: dict, target_path: str | None, serena_summary: dict) -> str:
    return (
        f"# Summary\n\n"
        f"Fallback ChatDev response for `{task.get('id')}` because no higher-quality model response was available.\n\n"
        f"# Proposed Changes\n\n"
        f"- Review `{target_path or 'target file'}` for import safety and side effects.\n"
        f"- Add daemon-mode signal handling and retry/backoff around network reads.\n"
        f"- Add focused pytest coverage for success and failure paths.\n"
        f"- Re-run Serena scoped walk after edits.\n\n"
        f"# Unified Diff\n\n"
        f"```diff\n"
        f"*** placeholder diff for {task.get('description')}\n"
        f"```\n\n"
        f"# Validation Steps\n\n"
        f"- `pytest tests/test_hub_health_probe.py`\n"
        f"- `python scripts/hub_health_probe.py --once`\n"
        f"- `timeout 5 python scripts/hub_health_probe.py --daemon`\n"
        f"- Inspect `state/serena_status.json` for drift after patching.\n"
    )


def extract_unified_diff(text: str) -> str:
    if not text:
        return ""
    fenced = re.search(r"```diff\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    raw = re.search(r"(^diff --git .*?$.*)", text, flags=re.DOTALL | re.MULTILINE)
    if raw:
        return raw.group(1).strip()
    simple = re.search(
        r"(^--- .*\n\+\+\+ .*\n(?:.*\n?)*)", text, flags=re.DOTALL | re.MULTILINE
    )
    if simple:
        return simple.group(1).strip()
    return ""


def build_hub_health_probe_rule_based_diff(
    target_path: str, target_text: str, test_path: str
) -> str:
    updated = target_text
    updated = updated.replace(
        "import argparse\n", "import argparse\nimport signal\nimport threading\n"
    )
    updated = updated.replace(
        "MAX_RESTARTS_PER_HOUR = 1\n",
        "MAX_RESTARTS_PER_HOUR = 1\nREAD_RETRIES = 3\nREAD_RETRY_BACKOFF_SECONDS = 0.5\n_STOP_EVENT = threading.Event()\n",
    )
    updated = updated.replace(
        'def _read_url(url: str, timeout: int = 5) -> dict | None:\n    try:\n        with urlopen(url, timeout=timeout) as response:\n            return json.loads(response.read().decode("utf-8"))\n    except Exception:\n        return None\n',
        'def _read_url(url: str, timeout: int = 5, attempts: int = READ_RETRIES) -> dict | None:\n    for attempt in range(max(1, attempts)):\n        try:\n            with urlopen(url, timeout=timeout) as response:\n                return json.loads(response.read().decode("utf-8"))\n        except Exception:\n            if attempt >= max(1, attempts) - 1:\n                return None\n            time.sleep(READ_RETRY_BACKOFF_SECONDS * (attempt + 1))\n    return None\n',
    )
    updated = updated.replace(
        'def main() -> int:\n    parser = argparse.ArgumentParser(description="Probe NuSyQ-Hub health and restart conservatively on sustained drift.")\n    parser.add_argument("--interval", type=int, default=30, help="Loop interval in seconds")\n    parser.add_argument("--once", action="store_true", help="Run a single probe and exit")\n    args = parser.parse_args()\n\n    state = ProbeState()\n    if args.once:\n        return probe_once(state)\n\n    while True:\n        probe_once(state)\n        time.sleep(args.interval)\n',
        'def _install_signal_handlers() -> None:\n    def _handle_signal(signum, frame):\n        _STOP_EVENT.set()\n\n    for sig in (signal.SIGINT, signal.SIGTERM):\n        try:\n            signal.signal(sig, _handle_signal)\n        except Exception:\n            continue\n\n\ndef run_daemon(interval: int, state: ProbeState) -> int:\n    _STOP_EVENT.clear()\n    _install_signal_handlers()\n    while not _STOP_EVENT.is_set():\n        probe_once(state)\n        if _STOP_EVENT.wait(interval):\n            break\n    return 0\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(description="Probe NuSyQ-Hub health and restart conservatively on sustained drift.")\n    parser.add_argument("--interval", type=int, default=30, help="Loop interval in seconds")\n    parser.add_argument("--once", action="store_true", help="Run a single probe and exit")\n    parser.add_argument("--daemon", action="store_true", help="Run continuously until signalled")\n    args = parser.parse_args(argv)\n\n    state = ProbeState()\n    if args.once:\n        return probe_once(state)\n\n    return run_daemon(args.interval, state)\n',
    )

    test_text = """from __future__ import annotations

import json
import threading
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.hub_health_probe as probe


def test_read_json_file_missing(tmp_path):
    assert probe._read_json_file(tmp_path / "missing.json") is None


def test_read_json_file_valid(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
    assert probe._read_json_file(path) == {"status": "ok"}


def test_read_url_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}

    class DummyResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"overall_status": "healthy"}'

    def fake_urlopen(url, timeout=5):
        calls["count"] += 1
        if calls["count"] < 2:
            raise OSError("temporary failure")
        return DummyResponse()

    monkeypatch.setattr(probe, "urlopen", fake_urlopen)
    monkeypatch.setattr(probe.time, "sleep", lambda *_: None)
    assert probe._read_url("http://example.test", attempts=2) == {"overall_status": "healthy"}


def test_main_once_calls_probe_once(monkeypatch):
    calls = {"count": 0}

    def fake_probe_once(state):
        calls["count"] += 1
        return 0

    monkeypatch.setattr(probe, "probe_once", fake_probe_once)
    assert probe.main(["--once"]) == 0
    assert calls["count"] == 1


def test_run_daemon_stops_on_signal(monkeypatch):
    stop_event = threading.Event()
    monkeypatch.setattr(probe, "_STOP_EVENT", stop_event)
    monkeypatch.setattr(probe, "_install_signal_handlers", lambda: None)

    calls = {"count": 0}

    def fake_probe_once(state):
        calls["count"] += 1
        stop_event.set()
        return 0

    monkeypatch.setattr(probe, "probe_once", fake_probe_once)
    assert probe.run_daemon(0, probe.ProbeState()) == 0
    assert calls["count"] == 1
"""

    main_diff = "".join(
        difflib.unified_diff(
            target_text.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{target_path}",
            tofile=f"b/{target_path}",
        )
    )
    test_diff = "".join(
        difflib.unified_diff(
            [],
            test_text.splitlines(keepends=True),
            fromfile="/dev/null",
            tofile=f"b/{test_path}",
        )
    )
    return (
        f"diff --git a/{target_path} b/{target_path}\n"
        f"{main_diff}"
        f"diff --git a/{test_path} b/{test_path}\n"
        f"new file mode 100644\n"
        f"{test_diff}"
    )


def parse_changed_paths(diff_text: str) -> list[str]:
    paths: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            if path != "/dev/null":
                paths.append(path)
    return list(dict.fromkeys(paths))


def tracked_in_git(path: str) -> bool:
    check = subprocess.run(
        ["git", "-C", str(BASE), "ls-files", "--error-unmatch", "--", path],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return check.returncode == 0


def revert_paths(paths: list[str]) -> None:
    tracked = [path for path in paths if tracked_in_git(path)]
    untracked = [path for path in paths if path not in tracked]
    if tracked:
        subprocess.run(
            ["git", "-C", str(BASE), "checkout", "--", *tracked],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    for relative in untracked:
        target = BASE / relative
        try:
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=True)
            elif target.exists():
                target.unlink()
        except Exception:
            continue


def apply_diff_to_worktree(diff_text: str) -> tuple[bool, str]:
    check = subprocess.run(
        ["git", "-C", str(BASE), "apply", "--check", "--recount", "-"],
        input=diff_text,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if check.returncode != 0:
        return (
            False,
            (check.stderr or check.stdout or "git apply --check failed").strip(),
        )

    apply_patch = subprocess.run(
        ["git", "-C", str(BASE), "apply", "--recount", "-"],
        input=diff_text,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if apply_patch.returncode != 0:
        return (
            False,
            (apply_patch.stderr or apply_patch.stdout or "git apply failed").strip(),
        )

    return True, "applied"


def select_test_targets(changed_paths: list[str]) -> list[str]:
    explicit_tests = [
        path
        for path in changed_paths
        if path.startswith("tests/") and path.endswith(".py")
    ]
    if explicit_tests:
        return explicit_tests

    candidates: list[str] = []
    for path in changed_paths:
        stem = Path(path).stem
        test_path = BASE / "tests" / f"test_{stem}.py"
        if test_path.exists():
            candidates.append(test_path.relative_to(BASE).as_posix())
    if candidates:
        return list(dict.fromkeys(candidates))

    tests_dir = BASE / "tests"
    if tests_dir.exists():
        return ["tests"]
    return []


def validate_diff(diff_text: str, task: dict) -> tuple[bool, str]:
    check = subprocess.run(
        ["git", "-C", str(BASE), "apply", "--check", "--recount", "-"],
        input=diff_text,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if check.returncode != 0:
        return (
            False,
            (check.stderr or check.stdout or "git apply --check failed").strip(),
        )

    changed_paths = parse_changed_paths(diff_text)
    if not changed_paths:
        return False, "No changed paths detected in diff"

    temp_dir = tempfile.mkdtemp(prefix="chatdev-validate-")
    try:
        for path in changed_paths:
            source = BASE / path
            destination = Path(temp_dir) / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                shutil.copy2(source, destination)

        apply_patch = subprocess.run(
            [
                "git",
                "apply",
                "--recount",
                "--unsafe-paths",
                "-p1",
                "--directory",
                temp_dir,
                "-",
            ],
            input=diff_text,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if apply_patch.returncode != 0:
            return (
                False,
                (
                    apply_patch.stderr or apply_patch.stdout or "git apply failed"
                ).strip(),
            )

        python_files = [path for path in changed_paths if path.endswith(".py")]
        if python_files:
            compile_cmd = ["python3", "-m", "py_compile", *python_files]
            compiled = subprocess.run(
                compile_cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if compiled.returncode != 0:
                return (
                    False,
                    (compiled.stderr or compiled.stdout or "py_compile failed").strip(),
                )

        if "tests/test_hub_health_probe.py" in changed_paths:
            test_env = os.environ.copy()
            test_env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
            tested = subprocess.run(
                [
                    "python3",
                    "-m",
                    "pytest",
                    "tests/test_hub_health_probe.py",
                    "-q",
                    "-s",
                ],
                cwd=temp_dir,
                env=test_env,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if tested.returncode != 0:
                return (
                    False,
                    (tested.stderr or tested.stdout or "pytest failed").strip(),
                )

        return True, "validation_ok"
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_tests_for_paths(changed_paths: list[str]) -> tuple[bool, str, list[str]]:
    targets = select_test_targets(changed_paths)
    if not targets:
        return True, "no_tests_found", []

    test_env = os.environ.copy()
    test_env.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    command = ["python3", "-m", "pytest", *targets, "-q", "-s"]
    tested = subprocess.run(
        command,
        cwd=str(BASE),
        env=test_env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    output = (tested.stdout or "") + (tested.stderr or "")
    return tested.returncode == 0, output.strip(), targets


def commit_paths(
    paths: list[str], task_id: str, *, include_queue: bool = False
) -> tuple[bool, str | None, str]:
    targets = list(dict.fromkeys(paths + ([QUEUE_REL_PATH] if include_queue else [])))
    if not targets:
        return False, None, "No changed paths to commit"

    added = subprocess.run(
        ["git", "-C", str(BASE), "add", "--", *targets],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if added.returncode != 0:
        return False, None, (added.stderr or added.stdout or "git add failed").strip()

    committed = subprocess.run(
        ["git", "-C", str(BASE), "commit", "-m", f"chatdev: complete {task_id}"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    output = ((committed.stdout or "") + (committed.stderr or "")).strip()
    if committed.returncode != 0:
        return False, None, output or "git commit failed"

    head = subprocess.run(
        ["git", "-C", str(BASE), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    commit_hash = head.stdout.strip() if head.returncode == 0 else None
    return True, commit_hash, output


def execute_diff(task: dict, diff_text: str) -> tuple[bool, dict]:
    changed_paths = parse_changed_paths(diff_text)
    if not changed_paths:
        return False, {"error": "No changed files in generated diff"}

    applied, apply_message = apply_diff_to_worktree(diff_text)
    if not applied:
        return False, {"error": apply_message, "changed_paths": changed_paths}

    tests_ok, test_output, test_targets = run_tests_for_paths(changed_paths)
    if not tests_ok:
        revert_paths(changed_paths)
        return False, {
            "error": test_output or "Tests failed",
            "changed_paths": changed_paths,
            "test_targets": test_targets,
        }

    return True, {
        "changed_paths": changed_paths,
        "test_targets": test_targets,
        "test_output": test_output,
    }


def generate_candidate_diff(
    task: dict,
    target_path: str | None,
    target_text: str,
    test_path: str | None,
    test_text: str,
    serena_summary: dict,
    feedback: str | None = None,
) -> tuple[str, dict]:
    llm = LLMClient(model=CHATDEV_LLM_MODEL, backend=CHATDEV_LLM_BACKEND)
    validation_errors: list[str] = [feedback] if feedback else []
    for _attempt in range(MAX_GENERATION_ATTEMPTS):
        prompt = build_prompt(
            task,
            target_path,
            target_text,
            test_path,
            test_text,
            serena_summary,
            previous_error=validation_errors[-1] if validation_errors else None,
        )
        try:
            output = llm.generate(
                prompt,
                system="You are a precise patch-oriented code hardening assistant. Return only a valid unified diff.",
                max_tokens=1800,
                temperature=0.1,
                cache=False,
            )
        except Exception as exc:
            validation_errors.append(f"Generation failed: {exc}")
            continue
        diff_text = extract_unified_diff(output.strip())
        if not diff_text:
            validation_errors.append("No unified diff found in model output")
            continue
        ok, message = validate_diff(diff_text, task)
        if ok:
            return diff_text, {
                "attempts": len(validation_errors) + 1,
                "validation": message,
                "fallback": False,
            }
        validation_errors.append(message)

    if target_path == "scripts/hub_health_probe.py" and target_text and test_path:
        diff_text = build_hub_health_probe_rule_based_diff(
            target_path, target_text, test_path
        )
        ok, message = validate_diff(diff_text, task)
        if ok:
            return diff_text, {
                "attempts": MAX_GENERATION_ATTEMPTS,
                "validation": message,
                "fallback": True,
                "fallback_reason": (
                    validation_errors[-1] if validation_errors else "model_unusable"
                ),
            }

    return "", {
        "attempts": MAX_GENERATION_ATTEMPTS,
        "validation": validation_errors[-1] if validation_errors else "no_output",
        "fallback": True,
        "fallback_reason": (
            validation_errors[-1] if validation_errors else "model_unusable"
        ),
    }


def generate_artifact(task: dict, feedback: str | None = None) -> tuple[str, dict]:
    target_path = extract_target_path(task)
    serena_scope = target_path or "scripts"
    serena_summary = refresh_serena(serena_scope)
    target_path, target_text = read_target(target_path)
    test_path, test_text = read_related_tests(target_path)

    diff_text, generation_meta = generate_candidate_diff(
        task,
        target_path,
        target_text,
        test_path,
        test_text,
        serena_summary,
        feedback=feedback,
    )

    if not diff_text:
        output = fallback_response(task, target_path, serena_summary)
    else:
        output = diff_text

    metadata = {
        "task_id": task.get("id"),
        "target_path": target_path,
        "test_path": test_path,
        "serena_ok": serena_summary.get("ok", False),
        "serena_align": ((serena_summary.get("payload") or {}).get("align") or {}).get(
            "score"
        ),
        "generated_at": now_iso(),
        **generation_meta,
    }
    return output, metadata


def write_artifact(task: dict, content: str, metadata: dict) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{stamp}_{task['id'].lower()}_{slugify(task.get('description', 'task'))}.md"
    path = OUTPUT_DIR / name
    payload = {
        "task": task,
        "metadata": metadata,
        "content": content,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def process_task(task_id: str, *, apply_mode: bool = False) -> dict:
    claimed = update_task(
        task_id, status="in_progress", started_at=now_iso(), worker="chatdev_worker"
    )
    if claimed is None:
        return {"ok": False, "error": f"Task {task_id} not found"}

    log.info("Processing %s: %s", task_id, claimed.get("description"))
    execution_feedback: str | None = None
    last_artifact_path: Path | None = None
    last_content = ""
    last_metadata: dict = {}

    for attempt in range(EXECUTION_RETRY_LIMIT + 1):
        content, metadata = generate_artifact(claimed, feedback=execution_feedback)
        metadata["execution_attempt"] = attempt + 1
        metadata["apply_mode"] = apply_mode
        artifact_path = write_artifact(claimed, content, metadata)
        last_artifact_path = artifact_path
        last_content = content
        last_metadata = metadata

        if not apply_mode:
            updated = update_task(
                task_id,
                status="completed",
                completed_at=now_iso(),
                output=str(artifact_path),
                output_preview=content[:500],
                worker="chatdev_worker",
            )
            result = {
                "ok": True,
                "task_id": task_id,
                "artifact": str(artifact_path),
                "task": updated or claimed,
            }
            publish("lattice.chatdev.complete", result)
            return result

        execution_ok, execution_meta = execute_diff(claimed, content)
        if execution_ok:
            metadata.update(execution_meta)
            updated = update_task(
                task_id,
                status="completed",
                completed_at=now_iso(),
                output=str(artifact_path),
                output_preview=content[:500],
                worker="chatdev_worker",
            )
            committed, commit_hash, commit_output = commit_paths(
                execution_meta.get("changed_paths", []),
                task.get("id", "task"),
                include_queue=True,
            )
            if not committed:
                revert_paths(execution_meta.get("changed_paths", []) + [QUEUE_REL_PATH])
                execution_feedback = commit_output or "Commit failed"
                log.warning(
                    "Commit failed for %s attempt %s: %s",
                    task_id,
                    attempt + 1,
                    execution_feedback,
                )
                last_metadata = {**metadata, "execution_error": execution_feedback}
                continue

            metadata.update(
                {"commit_hash": commit_hash, "commit_output": commit_output}
            )
            artifact_path.write_text(
                json.dumps(
                    {
                        "task": updated or claimed,
                        "metadata": metadata,
                        "content": content,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            result = {
                "ok": True,
                "task_id": task_id,
                "artifact": str(artifact_path),
                "commit_hash": commit_hash,
                "task": updated or claimed,
            }
            publish("lattice.chatdev.complete", result)
            return result

        execution_feedback = str(execution_meta.get("error") or "Execution failed")
        log.warning(
            "Execution failed for %s attempt %s: %s",
            task_id,
            attempt + 1,
            execution_feedback,
        )
        last_metadata = {**metadata, "execution_error": execution_feedback}

    if last_artifact_path is not None:
        last_artifact_path.write_text(
            json.dumps(
                {"task": claimed, "metadata": last_metadata, "content": last_content},
                indent=2,
            ),
            encoding="utf-8",
        )

    updated = update_task(
        task_id,
        status="failed",
        completed_at=now_iso(),
        output=str(last_artifact_path) if last_artifact_path else None,
        output_preview=last_content[:500],
        worker="chatdev_worker",
        error=str(
            last_metadata.get("execution_error")
            or last_metadata.get("validation")
            or "execution_failed"
        ),
    )
    result = {
        "ok": False,
        "task_id": task_id,
        "artifact": str(last_artifact_path) if last_artifact_path else None,
        "error": updated.get("error") if updated else "execution_failed",
        "task": updated or claimed,
    }
    publish("lattice.chatdev.failed", result)
    return result


def run_once(*, apply_mode: bool = False) -> int:
    queue = load_queue()
    tasks = select_tasks(queue)
    if not tasks:
        log.info("No ChatDev tasks ready.")
        return 0
    processed = 0
    for task in tasks:
        result = process_task(task["id"], apply_mode=apply_mode)
        if result.get("ok"):
            processed += 1
    return processed


def daemon_loop(poll_seconds: int, *, apply_mode: bool = False) -> None:
    log.info("ChatDev worker online. Polling %s every %ss", QUEUE_PATH, poll_seconds)
    publish(
        "lattice.chatdev.online",
        {"status": "starting", "queue": str(QUEUE_PATH), "apply_mode": apply_mode},
    )
    while True:
        try:
            processed = run_once(apply_mode=apply_mode)
            if processed:
                log.info("Processed %s task(s) this cycle", processed)
        except Exception as exc:
            log.exception("Worker cycle failed: %s", exc)
        time.sleep(poll_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real ChatDev task-consuming worker.")
    parser.add_argument("--daemon", action="store_true", help="Poll queue forever")
    parser.add_argument("--once", action="store_true", help="Run one queue scan")
    parser.add_argument("--task-id", help="Process a single task ID")
    parser.add_argument(
        "--apply", action="store_true", help="Apply, test, and commit validated diffs"
    )
    parser.add_argument(
        "--poll", type=int, default=DEFAULT_POLL_SECONDS, help="Queue poll interval"
    )
    args = parser.parse_args(argv)
    apply_mode = args.apply or os.environ.get("CHATDEV_APPLY_CHANGES", "").lower() in {
        "1",
        "true",
        "yes",
    }

    if args.task_id:
        result = process_task(args.task_id, apply_mode=apply_mode)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    if args.once:
        run_once(apply_mode=apply_mode)
        return 0
    if args.daemon:
        daemon_loop(args.poll, apply_mode=apply_mode)
        return 0

    log.info("No mode specified. Use --daemon, --once, or --task-id.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
