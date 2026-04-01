"""Quick check for latest ChatDev project status."""

from pathlib import Path

warehouse = Path("C:/Users/keath/NuSyQ/ChatDev/WareHouse")
projects = sorted(warehouse.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]

print("📦 Latest 3 ChatDev Projects:\n")
for i, proj in enumerate(projects, 1):
    files = list(proj.glob("**/*.py"))
    configs = list(proj.glob("*.json"))
    docs = list(proj.glob("*.md"))

    print(f"{i}. {proj.name}")
    print(f"   Modified: {proj.stat().st_mtime}")
    print(f"   Python files: {len(files)}")
    print(f"   Configs: {len(configs)}")
    print(f"   Docs: {len(docs)}")

    if files:
        print("   📄 Generated code:")
        for f in files[:5]:  # Show first 5
            print(f"      - {f.name} ({f.stat().st_size} bytes)")
    print()
