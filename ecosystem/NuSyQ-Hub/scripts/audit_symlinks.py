#!/usr/bin/env python3
"""Audit symlinks and cross-repo dependencies across all three repos."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def find_symlinks(repo_path: Path) -> list[dict[str, str]]:
    """Find all symlinks in a repository."""
    symlinks: list[dict[str, str]] = []

    try:
        # PowerShell command to find symlinks and junctions
        result = subprocess.run(
            [
                "powershell",
                "-Command",
                f"Get-ChildItem -Path '{repo_path}' -Recurse -ErrorAction SilentlyContinue | "
                "Where-Object {$_.LinkType -like '*Link*' -or $_.LinkType -like '*Junction*'} | "
                "Select-Object FullName, LinkType",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")[3:]  # Skip header
            for line in lines:
                if line.strip():
                    symlinks.append({"path": line.strip(), "type": "symlink/junction"})

    except Exception:
        # Fallback: look for .lnk files
        for lnk_file in repo_path.rglob("*.lnk"):
            symlinks.append({"path": str(lnk_file), "type": "lnk_file"})

    return symlinks


def audit_symlinks() -> dict[str, Any]:
    """Audit symlinks across all three repos."""
    audit = {
        "timestamp": datetime.now().isoformat(),
        "repos": {},
        "cross_repo_dependencies": [],
        "summary": "",
    }

    # Define repos
    repos = {
        "NuSyQ-Hub": Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub"),
        "SimulatedVerse": Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse"),
        "NuSyQ": Path("C:/Users/keath/NuSyQ"),
    }

    for repo_name, repo_path in repos.items():
        if not repo_path.exists():
            audit["repos"][repo_name] = {
                "path": str(repo_path),
                "exists": False,
                "symlinks": [],
            }
            continue

        symlinks = find_symlinks(repo_path)
        audit["repos"][repo_name] = {
            "path": str(repo_path),
            "exists": True,
            "symlink_count": len(symlinks),
            "symlinks": symlinks,
        }

        # Check for cross-repo references
        for symlink in symlinks:
            for other_repo_name, other_path in repos.items():
                if other_repo_name != repo_name:
                    if str(other_path) in symlink.get("path", ""):
                        audit["cross_repo_dependencies"].append(
                            {
                                "from": repo_name,
                                "to": other_repo_name,
                                "symlink": symlink["path"],
                            }
                        )

    # Summary
    total_symlinks = sum(len(v.get("symlinks", [])) for v in audit["repos"].values())
    audit["summary"] = f"Found {total_symlinks} symlinks across {len(repos)} repos"

    return audit


def save_audit_report(audit: dict[str, Any]) -> None:
    """Save audit report."""
    report_path = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/docs/CROSS_REPO_DEPENDENCIES.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Create markdown report
    content = f"""# Cross-Repository Dependencies Audit

**Generated:** {audit["timestamp"]}

## Summary

{audit["summary"]}

## Repository Analysis

"""

    for repo_name, repo_info in audit["repos"].items():
        content += f"\n### {repo_name}\n"
        content += f"- **Path:** `{repo_info['path']}`\n"
        content += f"- **Exists:** {'✓' if repo_info['exists'] else '❌'}\n"

        if repo_info["exists"]:
            content += f"- **Symlinks Found:** {repo_info.get('symlink_count', 0)}\n"

            if repo_info.get("symlinks"):
                content += "\n**Symlinks:**\n"
                for symlink in repo_info["symlinks"]:
                    content += f"  - `{symlink['path']}` ({symlink['type']})\n"

    if audit["cross_repo_dependencies"]:
        content += "\n## Cross-Repository Dependencies\n"
        for dep in audit["cross_repo_dependencies"]:
            content += f"- **{dep['from']}** → **{dep['to']}**\n"
            content += f"  - Symlink: `{dep['symlink']}`\n"
    else:
        content += "\n## Cross-Repository Dependencies\n\nNone found. Repos are independent.\n"

    with open(report_path, "w") as f:
        f.write(content)

    print(f"✓ Audit report saved: {report_path}")

    # Also save JSON receipt
    receipt_dir = Path("C:/Users/keath/Desktop/Legacy/NuSyQ-Hub/state/receipts/audit")
    receipt_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = receipt_dir / f"symlink_audit_{timestamp_str}.json"

    with open(receipt_file, "w") as f:
        json.dump(audit, f, indent=2, default=str)

    print(f"✓ Receipt saved: {receipt_file}")


def print_audit_summary(audit: dict[str, Any]) -> None:
    """Print audit summary."""
    print("\n" + "=" * 80)
    print("SYMLINK & CROSS-REPO DEPENDENCY AUDIT")
    print("=" * 80)
    print(f"\n{audit['summary']}")

    print("\nRepository Status:")
    for repo_name, repo_info in audit["repos"].items():
        status = "✓" if repo_info["exists"] else "❌"
        symlinks = repo_info.get("symlink_count", 0)
        print(f"  {status} {repo_name}: {symlinks} symlinks")
        if repo_info.get("symlinks"):
            for symlink in repo_info["symlinks"][:3]:  # Show first 3
                print(f"     - {symlink['path'][:60]}...")

    if audit["cross_repo_dependencies"]:
        print("\nCross-Repo Dependencies Detected:")
        for dep in audit["cross_repo_dependencies"]:
            print(f"  • {dep['from']} → {dep['to']}")
    else:
        print("\n✓ No cross-repository symlinks detected. Repos are independent.")


if __name__ == "__main__":
    audit = audit_symlinks()
    print_audit_summary(audit)
    save_audit_report(audit)
