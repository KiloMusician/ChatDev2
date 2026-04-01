#!/usr/bin/env python3
"""Zeta12 - Documentation Generator Entry Point

Scans the codebase for missing docstrings and generates a comprehensive report.
This is part of Phase 1 ZETA implementation.
"""

import os
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root))

try:
    from src.documentation_generator import DocumentationGenerator
except ImportError:
    from documentation_generator import DocumentationGenerator
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run Zeta12 documentation generator."""
    logger.info("🚀 ZETA12 - Documentation Generator Starting")
    logger.info("=" * 70)

    # Change to repo root (scripts/ -> NuSyQ-Hub/)
    _repo_root = Path(__file__).parent.parent
    os.chdir(_repo_root)

    # Create generator
    generator = DocumentationGenerator(["src"])

    # Scan modules
    logger.info("🔍 PHASE 1: Module Scanning")
    analyzers = generator.scan_modules()
    logger.info(f"✅ Found {len(analyzers)} modules to analyze")

    # Generate report
    logger.info("📊 PHASE 2: Analysis and Report Generation")
    report = generator.generate_report()

    # Export results
    logger.info("💾 PHASE 3: Exporting Results")
    export_path = "docs/reports/documentation_coverage.json"
    generator.export_report(export_path)

    # Print detailed findings
    logger.info("📈 PHASE 4: Summary and Recommendations")
    print("\n" + "=" * 70)
    print("🎯 ZETA12 DOCUMENTATION GENERATOR - RESULTS")
    print("=" * 70)

    summary = report["summary"]
    print("\n📊 Module Coverage:")
    print(f"  • Modules scanned: {report['total_modules']}")
    print(
        f"  • Total items found: {sum([summary['total_functions'], summary['total_classes'], summary['total_methods']])}"
    )

    print("\n📝 Function Documentation:")
    print(f"  • Documented: {summary['documented_functions']}/{summary['total_functions']}")
    print(f"  • Coverage: {summary.get('coverage', 'N/A')}")

    print("\n🏛️  Class Documentation:")
    print(f"  • Documented: {summary['documented_classes']}/{summary['total_classes']}")

    print("\n🔧 Method Documentation:")
    print(f"  • Documented: {summary['documented_methods']}/{summary['total_methods']}")

    print(f"\n📊 Overall Coverage: {summary['overall_coverage']}")
    print(f"⚠️  Items needing documentation: {summary['items_to_document']}")

    # Show top 10 modules with lowest coverage
    if report["modules"]:
        print("\n🚨 Top 10 Modules by Documentation Gaps:")
        modules_by_gaps = sorted(report["modules"], key=lambda x: x["functions"]["missing"], reverse=True)[:10]

        for i, module in enumerate(modules_by_gaps, 1):
            module_name = Path(module["module"]).name
            missing = module["functions"]["missing"]
            if missing > 0:
                print(f"  {i}. {module_name}: {missing} undocumented functions")

    # Show undocumented items if not too many
    undocumented = summary.get("undocumented_functions", [])
    if undocumented and len(undocumented) <= 20:
        print(f"\n📋 Undocumented Items ({len(undocumented)}):")
        for item in undocumented[:20]:
            module_rel = Path(item["module"]).name
            print(f"  • {module_rel}: {item['name']}() [line {item['line']}]")

    elif undocumented:
        print(f"\n📋 {len(undocumented)} items need documentation")
        print(f"   (See {export_path} for full list)")

    print("\n" + "=" * 70)
    print("✅ ZETA12 Complete - Report available at:")
    print(f"   {export_path}")
    print("=" * 70 + "\n")

    # Return appropriate exit code
    coverage_value = float(summary["overall_coverage"].rstrip("%")) if "%" in str(summary["overall_coverage"]) else 0
    if coverage_value < 60:
        logger.warning(f"⚠️  Current coverage is {summary['overall_coverage']} - below target of 60%")
        return 1
    else:
        logger.info(f"✅ Coverage target reached: {summary['overall_coverage']}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
