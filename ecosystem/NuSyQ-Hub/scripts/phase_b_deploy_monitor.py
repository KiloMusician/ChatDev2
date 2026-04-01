#!/usr/bin/env python3
"""Phase B: Production Deployment and Monitoring Script.

Sets up monitoring for ChatDev MCP resilience system.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.feature_flag_manager import is_feature_enabled
from src.resilience.mission_control_attestation import MissionControlReportBuilder


def check_feature_flags() -> dict:
    """Verify production feature flags enabled."""
    flags = {
        "chatdev_mcp_enabled": is_feature_enabled("chatdev_mcp_enabled"),
        "mission_control_enabled": is_feature_enabled("mission_control_enabled"),
    }
    return flags


def generate_culture_ship_report() -> dict | None:
    """Generate initial Culture Ship report."""
    try:
        builder = MissionControlReportBuilder()
        report = builder.build_report()

        # Save to standard location
        report_path = Path("state/reports/culture_ship_report.json")
        builder.save_report(report, report_path)

        return {
            "report_id": report.report_id,
            "timestamp": report.timestamp,
            "health_score": report.health_score,
            "audit_count": len(report.audit_summary),
            "patterns_count": len(report.patterns_observed),
            "violations_count": len(report.policy_violations),
            "lessons_count": len(report.lessons_learned),
            "report_path": str(report_path),
        }
    except Exception as e:
        return {"error": str(e)}


def check_monitoring_infrastructure() -> dict:
    """Verify monitoring directories and files exist."""
    base = Path("state")
    return {
        "audit_log": (base / "audit.jsonl").exists(),
        "checkpoints_dir": (base / "checkpoints").exists(),
        "attestations_dir": (base / "attestations").exists(),
        "reports_dir": (base / "reports").exists(),
        "sandbox_dir": (base / "sandbox").exists(),
    }


def main() -> None:
    """Run Phase B deployment monitoring."""
    print("\n" + "=" * 80)
    print("Phase B: Production Deployment & Monitoring")
    print("=" * 80 + "\n")

    # Step 1: Verify feature flags
    print("1️⃣  Checking feature flags...")
    flags = check_feature_flags()
    for flag, enabled in flags.items():
        status = "✅ ENABLED" if enabled else "❌ DISABLED"
        print(f"    {flag}: {status}")

    if not all(flags.values()):
        print("\n⚠️  Some feature flags are disabled. Enable them in config/feature_flags.json")

    # Step 2: Verify monitoring infrastructure
    print("\n2️⃣  Checking monitoring infrastructure...")
    infra = check_monitoring_infrastructure()
    for component, exists in infra.items():
        status = "✅ EXISTS" if exists else "⚠️  MISSING"
        print(f"    {component}: {status}")

    # Step 3: Generate Culture Ship report
    print("\n3️⃣  Generating Culture Ship report...")
    if flags.get("mission_control_enabled"):
        report_data = generate_culture_ship_report()
        if "error" in report_data:
            print(f"    ❌ Report generation failed: {report_data['error']}")
        else:
            print(f"    ✅ Report generated: {report_data['report_id']}")
            print(f"    📊 Health Score: {report_data['health_score']:.2f}")
            print(f"    📝 Audits: {report_data['audit_count']}")
            print(f"    🔍 Patterns: {report_data['patterns_count']}")
            print(f"    🎓 Lessons: {report_data['lessons_count']}")
            print(f"    💾 Saved to: {report_data['report_path']}")
    else:
        print("    ⏭️  Skipped (mission_control_enabled flag is off)")

    # Step 4: Summary and next steps
    print("\n" + "=" * 80)
    print("Phase B Deployment Status")
    print("=" * 80)

    if all(flags.values()):
        print("✅ Production configuration complete")
        print("\n📋 Next Steps:")
        print("   1. Monitor audit log growth: state/audit.jsonl")
        print("   2. Review Culture Ship reports: state/reports/culture_ship_report.json")
        print("   3. Watch checkpoint persistence: state/checkpoints/")
        print("   4. Check attestations: state/attestations/")
        print("\n🔄 To run ChatDev with resilience:")
        print("   from src.integration.chatdev_mcp_server import get_chatdev_mcp_server")
        print("   server = get_chatdev_mcp_server()")
        print('   result = await server.generate_project(task="...", model="...")')
    else:
        print("⚠️  Configuration incomplete - review feature flags above")

    print("\n")


if __name__ == "__main__":
    main()
