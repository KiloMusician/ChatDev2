#!/usr/bin/env python3
"""Cross-repo navigator — enable seamless jumping between NuSyQ-Hub, SimulatedVerse, NuSyQ.

Usage:
  python scripts/cross_repo_navigator.py hub|simverse|root [--pwd]
  python scripts/cross_repo_navigator.py list
  python scripts/cross_repo_navigator.py current

If --pwd is passed, prints the repo root path (suitable for eval/cd).
Otherwise, prints a navigational summary.
"""

import sys
from pathlib import Path

# Repo roots (relative to script location or absolute)
REPOS = {
    "hub": Path(__file__).resolve().parent.parent,  # NuSyQ-Hub
    "simverse": Path(__file__).resolve().parent.parent.parent / "SimulatedVerse" / "SimulatedVerse",
    "root": Path(__file__).resolve().parent.parent.parent.parent / "NuSyQ",
}

# Aliases
ALIASES = {
    "h": "hub",
    "s": "simverse",
    "r": "root",
    "nusyq-hub": "hub",
    "simulatedverse": "simverse",
    "nusyq": "root",
}


def normalize_repo_name(name: str) -> str | None:
    """Resolve repo name or alias to canonical name."""
    name_lower = name.lower()
    if name_lower in REPOS:
        return name_lower
    if name_lower in ALIASES:
        return ALIASES[name_lower]
    return None


def cmd_list() -> int:
    """List all repositories."""
    print("Available repositories:")
    for name, path in sorted(REPOS.items()):
        status = "✓" if path.exists() else "✗"
        print(f"  {status} {name:12} → {path}")
    return 0


def cmd_current() -> int:
    """Show current repository."""
    cwd = Path.cwd()
    for name, repo_path in sorted(REPOS.items()):
        try:
            if cwd == repo_path or cwd.is_relative_to(repo_path):
                print(f"Current: {name} ({repo_path})")
                return 0
        except ValueError:
            # is_relative_to not available in older Python; use string comparison
            if str(cwd).startswith(str(repo_path)):
                print(f"Current: {name} ({repo_path})")
                return 0
    print(f"Current: unknown ({cwd})")
    return 0


def cmd_navigate(repo_name: str, pwd_only: bool = False) -> int:
    """Navigate to a repository."""
    canonical = normalize_repo_name(repo_name)
    if not canonical:
        print(f"❌ Unknown repository: {repo_name}")
        print("   Valid repos: hub, simverse, root (or h, s, r)")
        return 1

    repo_path = REPOS[canonical]
    if not repo_path.exists():
        print(f"❌ Repository path does not exist: {repo_path}")
        return 1

    if pwd_only:
        # Print path for shell evaluation (suitable for: cd $(python ... --pwd))
        print(str(repo_path))
    else:
        # Print navigational info
        print(f"🗂️  Repository: {canonical}")
        print(f"   Path: {repo_path}")
        # Check if it's a git repo
        if (repo_path / ".git").exists():
            import subprocess

            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0:
                    branch = result.stdout.strip()
                    print(f"   Branch: {branch}")
            except Exception:
                pass
        print(f"\n💡 To navigate in shell, run: cd {repo_path}")
    return 0


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Cross-Repo Navigator")
        print("Usage:")
        print("  python scripts/cross_repo_navigator.py hub|simverse|root [--pwd]")
        print("  python scripts/cross_repo_navigator.py list")
        print("  python scripts/cross_repo_navigator.py current")
        return 0

    action = sys.argv[1]

    if action == "list":
        return cmd_list()
    elif action == "current":
        return cmd_current()
    else:
        pwd_only = "--pwd" in sys.argv[2:]
        return cmd_navigate(action, pwd_only=pwd_only)


if __name__ == "__main__":
    sys.exit(main())
