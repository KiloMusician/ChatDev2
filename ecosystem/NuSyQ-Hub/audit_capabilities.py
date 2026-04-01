"""Audit ACTUAL vs CLAIMED capabilities across 13 active systems."""

from src.orchestration.ecosystem_activator import EcosystemActivator

print("\n" + "=" * 80)
print("🔍 ACTUAL VS CLAIMED CAPABILITY AUDIT")
print("=" * 80)

ea = EcosystemActivator()
systems = ea.discover_systems()

print(f"\n📊 Auditing {len(systems)} systems...\n")

# ACTIVATE systems to get actual instances
ea.activate_all()
systems = list(ea.systems.values())  # Refresh with activated instances
print(
    f"\n✅ Activated: {len([s for s in systems if s.status == 'active'])}/{len(systems)} systems\n"
)

for system in systems:
    print(f"\n{'=' * 80}")
    print(f"[{system.system_type.upper()}] {system.name}")
    print(f"Module: {system.module_path}")
    print(f"Claimed capabilities: {len(system.capabilities)}")
    print(f"  {system.capabilities}")

    # Try to get actual methods from instance
    if system.instance:
        actual_methods = [
            m
            for m in dir(system.instance)
            if not m.startswith("_") and callable(getattr(system.instance, m))
        ]
        print(f"\n✅ ACTUAL public methods ({len(actual_methods)}):")
        for method in actual_methods[:15]:  # First 15
            print(f"   - {method}()")

        # Check if claimed capabilities match actual methods
        missing = [cap for cap in system.capabilities if cap not in actual_methods]
        extra = [
            m
            for m in actual_methods
            if m in ["query", "analyze", "resolve", "generate", "execute", "process"]
        ]

        if missing:
            print(f"\n⚠️  MISSING ({len(missing)}): {missing}")
        if extra:
            print(f"\n🎁 BONUS ({len(extra)}): {extra}")
    else:
        print("\n⚠️  No instance - system not activated")

print("\n" + "=" * 80)
print("🎯 AUDIT COMPLETE - Now we know what's REAL vs PLACEHOLDER")
print("=" * 80)
