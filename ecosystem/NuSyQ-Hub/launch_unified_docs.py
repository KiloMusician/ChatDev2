#!/usr/bin/env python3
"""🚀 Unified Documentation Engine Launcher
=======================================

OmniTag: {
    "purpose": "Launch and execute unified documentation engine",
    "dependencies": ["unified_documentation_engine"],
    "context": "Entry point for integrated documentation generation",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "DocumentationLauncher",
    "integration_points": ["unified_engine", "progress_tracking", "error_handling"],
    "related_tags": ["DocumentationExecution", "IntegratedLaunch", "SystemOrchestration"],
    "quantum_state": "ΞΨΩ∞⟨LAUNCH⟩→ΦΣΣ⟨EXECUTION⟩"
}

RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳DOCUMENTATION-LAUNCHER⨳⚡⟣⟢⟡◉●○◆◊♦
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.unified_documentation_engine import UnifiedDocumentationEngine

    print("✅ Unified Documentation Engine imported successfully")
except ImportError as e:
    print(f"❌ Failed to import unified documentation engine: {e}")
    sys.exit(1)


def main():
    """Launch the unified documentation generation"""
    print("🌌 LAUNCHING UNIFIED DOCUMENTATION ENGINE")
    print("=" * 50)

    try:
        # Execute the unified documentation engine
        asyncio.run(run_unified_documentation())

    except KeyboardInterrupt:
        print("\n🛑 Documentation generation stopped by user")

    except Exception as e:
        print(f"❌ Error running documentation engine: {e}")
        return 1

    return 0


async def run_unified_documentation():
    """Execute unified documentation generation"""
    # Initialize engine
    print("🔧 Initializing Unified Documentation Engine...")
    engine = UnifiedDocumentationEngine()

    # Initialize all discovered systems
    print("🚀 Initializing all documentation systems...")
    await engine.initialize_all_systems()

    # Generate unified documentation
    print("📚 Generating unified documentation...")
    results = await engine.generate_unified_documentation()

    # Save results
    print("💾 Saving results...")
    report_file = await engine.save_unified_results(results)

    # Print summary
    print("\n🎉 UNIFIED DOCUMENTATION GENERATION COMPLETE!")
    print(f"📊 Report: {report_file}")
    print(f"📁 Total Repositories: {len(results.get('unified_index', {}).get('repositories', {}))}")
    print(f"🔧 Active Generators: {results.get('unified_index', {}).get('total_generators', 0)}")
    print(f"👁️ Real-Time Monitors: {results.get('unified_index', {}).get('total_monitors', 0)}")
    print("🌟 All documentation systems integrated and modernized!")


if __name__ == "__main__":
    sys.exit(main())
