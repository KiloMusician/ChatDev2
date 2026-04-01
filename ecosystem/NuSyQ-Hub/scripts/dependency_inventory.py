#!/usr/bin/env python3
"""Generate an up-to-date dependency inventory for NuSyQ repositories."""

from __future__ import annotations

import datetime
import json
import re

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - Py3.10 fallback
    import tomli as tomllib  # type: ignore
from collections import Counter, OrderedDict
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).parent.parent
INVENTORY_PATH = ROOT / "state" / "reports" / "dependency_inventory.md"


# Preserve order while counting occurrences
def _count_preserving_order(items: list[str]) -> OrderedDict[str, int]:
    counts: OrderedDict[str, int] = OrderedDict()
    for item in items:
        if not item:
            continue
        counts[item] = counts.get(item, 0) + 1
    return counts


_VERSION_SPLIT = re.compile(r"[\\s<>=!~;,\\[]")


def _normalize_dep_name(raw: str) -> str:
    """Strip version specifiers / markers from a dependency string."""
    raw = raw.strip().strip("'\"")
    if not raw:
        return ""
    # First, try robust parsing
    try:
        return Requirement(raw).name
    except Exception:
        pass

    # drop environment markers and extras
    raw = raw.split(";")[0]
    raw = raw.split("[")[0]
    parts = _VERSION_SPLIT.split(raw, maxsplit=1)
    token = parts[0] if parts else raw
    # fallback: grab first package-like token
    m = re.search(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", token)
    return m.group(0) if m else ""


def parse_pyproject() -> list[str]:
    path = ROOT / "pyproject.toml"
    if not path.exists():
        return []
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    deps: list[str] = []

    def _add_entries(entries):
        if isinstance(entries, dict):
            for key, value in entries.items():
                deps.append(_normalize_dep_name(key))
                # Optional/extra dependency values can be lists of strings
                if isinstance(value, list):
                    for item in value:
                        deps.append(_normalize_dep_name(str(item)))

    project = data.get("project", {})
    poetry = data.get("tool", {}).get("poetry", {})

    # Core + dev dependencies
    for section in (project, poetry):
        for key in ("dependencies", "dev-dependencies"):
            _add_entries(section.get(key))

    # PEP 621 optional-dependencies and Poetry extras
    _add_entries(project.get("optional-dependencies"))
    _add_entries(poetry.get("extras"))

    return deps


def parse_requirements() -> list[str]:
    files = sorted(ROOT.glob("requirements*.txt"))
    deps = []
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            deps.append(_normalize_dep_name(line))
    return deps


def parse_package_json() -> list[str]:
    path = ROOT / "package.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    deps = []
    for key in ("dependencies", "devDependencies"):
        section = data.get(key, {})
        if isinstance(section, dict):
            deps.extend(section.keys())
    return deps


def generate_report():
    py_deps = _count_preserving_order(parse_pyproject() + parse_requirements())
    node_deps = Counter(parse_package_json())
    timestamp = datetime.datetime.now().isoformat()

    lines = [
        "# Dependency Inventory",
        "",
        f"*Generated on {timestamp}*",
        "",
        "## Python Dependencies (derived from `pyproject.toml` + `requirements*.txt`)",
    ]

    if py_deps:
        for name, count in py_deps.items():
            lines.append(f"- `{name}` (mentioned {count} times across manifests)")
    else:
        lines.append("- No Python dependencies detected.")

    lines.append("")
    lines.append("## Node / JS Dependencies (derived from `package.json`)")
    if node_deps:
        for name, _count in node_deps.most_common():
            lines.append(f"- `{name}` (declared in package.json)")
    else:
        lines.append("- No Node dependencies detected.")

    lines.append("")
    lines.append("## Notes")
    lines.append("- The dependency order mirrors the order listed in the manifest files.")
    lines.append("- Use this inventory when auditing unused packages or identifying bottlenecks.")
    lines.append("- `pyproject.toml` is authoritative for installations that support PEP 621.")

    INVENTORY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote dependency inventory with {len(py_deps)} Python and {len(node_deps)} Node deps.")


if __name__ == "__main__":
    generate_report()
