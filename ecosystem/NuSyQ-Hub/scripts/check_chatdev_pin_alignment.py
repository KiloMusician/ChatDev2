"""Check dependency pin alignment between NuSyQ-Hub and ChatDev2.

This script compares requirements.txt files to identify version mismatches
and provides recommendations for alignment.
"""

import re
from pathlib import Path


def parse_requirement(line: str) -> tuple[str, str] | None:
    """Parse a requirement line into (package_name, version_spec)."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Match package name and version spec
    match = re.match(r"^([a-zA-Z0-9_-]+)\s*([><=!~]+.*)?$", line)
    if match:
        package = match.group(1).lower().replace("_", "-")
        version = match.group(2) or ""
        return (package, version)
    return None


def load_requirements(filepath: Path) -> dict[str, str]:
    """Load requirements from a file into a dict."""
    requirements = {}
    if not filepath.exists():
        print(f"⚠️  Warning: {filepath} not found")
        return requirements

    with open(filepath, encoding="utf-8") as f:
        for line in f:
            parsed = parse_requirement(line)
            if parsed:
                package, version = parsed
                requirements[package] = version

    return requirements


def compare_requirements(hub_reqs: dict[str, str], chatdev_reqs: dict[str, str]) -> None:
    """Compare requirements and report differences."""
    print("\n" + "=" * 80)
    print("🔍 CHATDEV2 DEPENDENCY PIN ALIGNMENT ANALYSIS")
    print("=" * 80 + "\n")

    # Find common packages
    common_packages = set(hub_reqs.keys()) & set(chatdev_reqs.keys())
    hub_only = set(hub_reqs.keys()) - set(chatdev_reqs.keys())
    chatdev_only = set(chatdev_reqs.keys()) - set(hub_reqs.keys())

    print("📊 Summary:")
    print(f"   Common packages: {len(common_packages)}")
    print(f"   Hub-only packages: {len(hub_only)}")
    print(f"   ChatDev-only packages: {len(chatdev_only)}\n")

    # Check version mismatches
    mismatches = []
    for package in sorted(common_packages):
        hub_ver = hub_reqs[package]
        chatdev_ver = chatdev_reqs[package]
        if hub_ver != chatdev_ver:
            mismatches.append((package, hub_ver, chatdev_ver))

    if mismatches:
        print("⚠️  VERSION MISMATCHES FOUND:\n")
        for package, hub_ver, chatdev_ver in mismatches:
            print(f"   {package:<30} Hub: {hub_ver:<20} ChatDev: {chatdev_ver}")
        print()
    else:
        print("✅ No version mismatches found in common packages\n")

    # Show ChatDev-specific packages (these might need to be added to Hub)
    if chatdev_only:
        print("📦 ChatDev-specific packages (consider adding to Hub):\n")
        for package in sorted(chatdev_only):
            print(f"   {package:<30} {chatdev_reqs[package]}")
        print()

    # Show Hub-specific packages (informational)
    if hub_only and len(hub_only) <= 20:
        print("📦 Hub-specific packages (first 20):\n")
        for package in sorted(list(hub_only)[:20]):
            print(f"   {package:<30} {hub_reqs[package]}")
        print()

    # Generate recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80 + "\n")

    if mismatches:
        print("1. Resolve version mismatches:")
        print("   Consider using the more restrictive version or upgrading to latest compatible\n")

    critical_packages = ["openai", "tiktoken", "flask", "flask-socketio", "requests", "tenacity"]
    critical_mismatches = [(p, h, c) for p, h, c in mismatches if p in critical_packages]

    if critical_mismatches:
        print("⚠️  CRITICAL: These packages are core to ChatDev integration:\n")
        for package, hub_ver, chatdev_ver in critical_mismatches:
            print(f"   {package}: Hub={hub_ver}, ChatDev={chatdev_ver}")
        print()


def main() -> None:
    """Main execution."""
    # Define paths
    hub_root = Path(__file__).parent.parent
    chatdev_root = Path("C:/Users/keath/NuSyQ/ChatDev")

    hub_reqs_file = hub_root / "requirements.txt"
    chatdev_reqs_file = chatdev_root / "requirements.txt"

    print(f"📁 Hub requirements: {hub_reqs_file}")
    print(f"📁 ChatDev requirements: {chatdev_reqs_file}\n")

    # Load requirements
    hub_reqs = load_requirements(hub_reqs_file)
    chatdev_reqs = load_requirements(chatdev_reqs_file)

    # Compare
    compare_requirements(hub_reqs, chatdev_reqs)

    print("\n✨ Analysis complete!")


if __name__ == "__main__":
    main()
