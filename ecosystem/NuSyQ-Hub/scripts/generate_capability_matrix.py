#!/usr/bin/env python3
"""Generate comprehensive capability matrix across all modules in NuSyQ-Hub."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def analyze_modules() -> dict[str, Any]:
    """Analyze all modules in src/ directory."""
    modules: dict[str, dict[str, str]] = {}
    src_path = Path("src")

    if not src_path.exists():
        return modules

    # Walk through src directory
    for py_file in src_path.rglob("*.py"):
        # Skip __pycache__ and tests
        if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
            continue

        # Get relative path
        rel_path = py_file.relative_to(src_path)
        module_name = str(rel_path).replace("\\", "/").replace(".py", "")

        # Read file to gather info
        try:
            with open(py_file) as f:
                content = f.read()

            # Determine attributes
            has_tests = (Path("tests") / f"test_{py_file.stem}.py").exists() or (
                Path("tests") / rel_path.parent / f"test_{py_file.stem}.py"
            ).exists()
            has_docstring = '"""' in content or "'''" in content
            has_type_hints = "->" in content or (": " in content and "def " in content)
            has_async = "async def" in content
            is_documented = "Args:" in content or "Returns:" in content

            modules[module_name] = {
                "status": "Active" if has_docstring else "Partial",
                "tested": "Yes" if has_tests else "No",
                "documented": "Yes" if is_documented else "No",
                "async": "Yes" if has_async else "No",
                "type_hints": "Yes" if has_type_hints else "No",
                "file_path": str(rel_path),
            }

        except Exception:
            modules[module_name] = {
                "status": "Error reading",
                "tested": "Unknown",
                "documented": "Unknown",
                "async": "Unknown",
                "type_hints": "Unknown",
                "file_path": str(rel_path),
            }

    return modules


def generate_capability_matrix() -> str:
    """Generate markdown capability matrix."""
    modules = analyze_modules()

    if not modules:
        return "# Capability Matrix\n\nNo modules found in src/ directory.\n"

    # Sort modules by name
    sorted_modules = sorted(modules.items())

    content = f"""# NuSyQ-Hub Capability Matrix

**Generated:** {datetime.now().isoformat()}

**Total Modules:** {len(modules)}

## Legend

- ✓ = Yes / Present
- ✗ = No / Absent
- ? = Unknown

## Module Inventory

| Module | Status | Tests | Documented | Async | Type Hints |
|--------|--------|-------|------------|-------|-----------|
"""

    for module_name, attrs in sorted_modules:
        status_icon = "✓" if attrs["status"] == "Active" else "⚠"
        tested_icon = "✓" if attrs["tested"] == "Yes" else "✗"
        documented_icon = "✓" if attrs["documented"] == "Yes" else "✗"
        async_icon = "✓" if attrs["async"] == "Yes" else "✗"
        types_icon = "✓" if attrs["type_hints"] == "Yes" else "✗"

        content += f"| `{module_name}` | {status_icon} {attrs['status']} | {tested_icon} | {documented_icon} | {async_icon} | {types_icon} |\n"

    # Summary statistics
    total = len(modules)
    active = sum(1 for m in modules.values() if m["status"] == "Active")
    tested = sum(1 for m in modules.values() if m["tested"] == "Yes")
    documented = sum(1 for m in modules.values() if m["documented"] == "Yes")
    async_modules = sum(1 for m in modules.values() if m["async"] == "Yes")
    typed = sum(1 for m in modules.values() if m["type_hints"] == "Yes")

    content += f"""

## Summary Statistics

- **Total Modules:** {total}
- **Active Status:** {active} ({100 * active // total}%)
- **With Tests:** {tested} ({100 * tested // total}%)
- **Documented:** {documented} ({100 * documented // total}%)
- **Async Support:** {async_modules} ({100 * async_modules // total}%)
- **Type Hints:** {typed} ({100 * typed // total}%)

## Key Directories

"""

    # Group by directory
    dirs: dict[str, int] = {}
    for module_name in modules:
        dir_name = module_name.split("/")[0] if "/" in module_name else "root"
        dirs[dir_name] = dirs.get(dir_name, 0) + 1

    for dir_name in sorted(dirs.keys()):
        content += f"- **{dir_name}:** {dirs[dir_name]} modules\n"

    content += """

## Quality Score

**Module Quality Matrix (Module Health):**
- 🟢 **Green:** Fully documented, tested, type-hinted, active status
- 🟡 **Yellow:** Partially documented or tested
- 🔴 **Red:** Minimal documentation or tests

## Next Steps

1. Prioritize documenting modules marked ⚠ (Partial status)
2. Add tests for modules with ✗ in Tests column
3. Add type hints to modules missing them
4. Archive or integrate duplicate/unused modules

---

See [INVESTIGATION_INVENTORY_20260110.md](INVESTIGATION_INVENTORY_20260110.md) for full system overview.
"""

    return content


def save_capability_matrix(content: str) -> None:
    """Save capability matrix to file."""
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    matrix_file = docs_dir / "CAPABILITY_MATRIX.md"
    with open(matrix_file, "w") as f:
        f.write(content)

    print(f"✓ Capability matrix saved: {matrix_file}")

    # Also save JSON version for programmatic access
    modules = analyze_modules()
    receipt_dir = Path("state/receipts/capability")
    receipt_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt_file = receipt_dir / f"matrix_{timestamp_str}.json"

    with open(receipt_file, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_modules": len(modules),
                "modules": modules,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"✓ Receipt saved: {receipt_file}")


def print_summary(content: str) -> None:
    """Print capability matrix summary."""
    lines = content.split("\n")
    # Print title and stats
    print("\n" + "=" * 80)
    for _i, line in enumerate(lines[:30]):
        if "---" in line:
            break
        print(line)
    print("=" * 80 + "\n")


if __name__ == "__main__":
    matrix = generate_capability_matrix()
    print_summary(matrix)
    save_capability_matrix(matrix)
