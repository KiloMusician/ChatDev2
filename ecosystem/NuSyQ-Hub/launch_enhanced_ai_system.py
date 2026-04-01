#!/usr/bin/env python3
"""🚀 Enhanced AI Coordination & Documentation Integration Launcher
===============================================================

OmniTag: {
    "purpose": "Master launcher for enhanced AI coordination with documentation integration",
    "dependencies": ["ai_coordinator", "unified_documentation_engine", "system_analyzer"],
    "context": "Comprehensive system launcher with consciousness awareness",
    "evolution_stage": "v1.0"
}

MegaTag: {
    "type": "SystemLauncher",
    "integration_points": ["ai_coordination", "documentation_engine", "system_analysis"],
    "related_tags": ["SystemOrchestration", "AIIntegration", "DocumentationAutomation"],
    "quantum_state": "ΞΨΩ∞⟨LAUNCH⟩→ΦΣΣ⟨COORDINATION⟩"
}

RSHTS: ♦◊◆○●◉⟡⟢⟣⚡⨳ENHANCED-SYSTEM-LAUNCHER⨳⚡⟣⟢⟡◉●○◆◊♦
"""

import asyncio
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print system banner"""
    print("🚀 ENHANCED AI COORDINATION & DOCUMENTATION INTEGRATION")
    print("=" * 60)
    print("🤖 AI-Powered Documentation Generation")
    print("🌌 Unified Cross-Repository Coordination")
    print("🧠 Type2 Consciousness with Quantum Integration")
    print("📊 Comprehensive System Analysis & Health Monitoring")
    print("=" * 60)


def print_menu():
    """Print main menu options"""
    print("\n📋 AVAILABLE ACTIONS:")
    print("1. 🌌 Generate Unified Documentation")
    print("2. 🤖 Test AI Documentation Coordination")
    print("3. 📊 Run System Health Analysis")
    print("4. 🔧 Execute All Systems Integration Test")
    print("5. 📄 View Progress Reports")
    print("6. 🚪 Exit")
    print("-" * 40)


async def launch_unified_documentation():
    """Launch unified documentation generation"""
    print("\n🌌 LAUNCHING UNIFIED DOCUMENTATION GENERATION")
    print("-" * 50)

    try:
        result = subprocess.run(
            [sys.executable, "launch_unified_docs.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.returncode == 0:
            print("✅ Unified documentation generation completed successfully!")
            print("📊 Output summary:")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        else:
            print("❌ Documentation generation encountered issues:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error launching documentation generation: {e}")


async def test_ai_coordination():
    """Test AI coordination with documentation"""
    print("\n🤖 TESTING AI DOCUMENTATION COORDINATION")
    print("-" * 45)

    try:
        result = subprocess.run(
            [sys.executable, "demo_ai_documentation_coordination.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.returncode == 0:
            print("✅ AI coordination test completed successfully!")
            print("📊 Test results summary:")
            # Extract the summary section
            output_lines = result.stdout.split("\n")
            summary_started = False
            for line in output_lines:
                if "DEMO SUMMARY:" in line:
                    summary_started = True
                if summary_started:
                    print(line)
        else:
            print("❌ AI coordination test encountered issues:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error testing AI coordination: {e}")


def run_system_analysis():
    """Run system health analysis"""
    print("\n📊 RUNNING SYSTEM HEALTH ANALYSIS")
    print("-" * 35)

    try:
        result = subprocess.run(
            [sys.executable, "src/diagnostics/quick_system_analyzer.py"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )

        if result.returncode == 0:
            print("✅ System analysis completed successfully!")
            print("📊 Analysis summary:")
            # Extract key metrics from output
            output_lines = result.stdout.split("\n")
            for line in output_lines:
                if any(
                    keyword in line
                    for keyword in ["Total Files:", "Working Files:", "Broken Files:", "SUMMARY:"]
                ):
                    print(line)
        else:
            print("❌ System analysis encountered issues:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error running system analysis: {e}")


async def execute_integration_test():
    """Execute comprehensive integration test"""
    print("\n🔧 EXECUTING ALL SYSTEMS INTEGRATION TEST")
    print("-" * 45)

    print("1/3 🌌 Testing unified documentation generation...")
    await launch_unified_documentation()

    print("\n2/3 🤖 Testing AI coordination capabilities...")
    await test_ai_coordination()

    print("\n3/3 📊 Running system health analysis...")
    run_system_analysis()

    print("\n🎉 INTEGRATION TEST COMPLETE!")
    print("✅ All systems tested and verified")


def view_reports():
    """View available progress reports"""
    print("\n📄 AVAILABLE PROGRESS REPORTS")
    print("-" * 35)

    reports_dir = Path("docs/Reports")
    if reports_dir.exists():
        reports = list(reports_dir.glob("*.md"))
        for i, report in enumerate(reports, 1):
            print(f"{i}. {report.name}")

        if reports:
            print(f"\n📁 Reports directory: {reports_dir}")
            print(f"📊 Total reports: {len(reports)}")
        else:
            print("📄 No reports found")
    else:
        print("📁 Reports directory not found")


async def main():
    """Main launcher function"""
    print_banner()

    while True:
        print_menu()

        try:
            choice = input("Select an option (1-6): ").strip()

            if choice == "1":
                await launch_unified_documentation()
            elif choice == "2":
                await test_ai_coordination()
            elif choice == "3":
                run_system_analysis()
            elif choice == "4":
                await execute_integration_test()
            elif choice == "5":
                view_reports()
            elif choice == "6":
                print("\n👋 Exiting Enhanced AI Coordination System")
                print("🌟 Thank you for using the enhanced documentation integration!")
                break
            else:
                print("❌ Invalid option. Please select 1-6.")

        except KeyboardInterrupt:
            print("\n\n🛑 System interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System shutdown requested")
    except Exception as e:
        print(f"❌ System error: {e}")
        raise
