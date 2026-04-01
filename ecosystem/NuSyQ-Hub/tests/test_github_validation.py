#!/usr/bin/env python3
"""Simple GitHub Validation Test Runner.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import sys
from pathlib import Path

# Add src utils to path
repo_root = Path(__file__).parent.parent
sys.path.append(str(repo_root / "src" / "utils"))

try:
    from github_validation_suite import GitHubIntegrationValidationSuite

    print("🔧 Running GitHub Integration Validation...")

    validator = GitHubIntegrationValidationSuite()
    results = validator.run_comprehensive_validation()

    print("\n📊 Validation Complete!")
    print(f"   Overall Score: {results.get('overall_score', 0):.1f}/100")
    print(f"   Status: {results.get('overall_status', 'unknown').replace('_', ' ').title()}")
    print(f"   Recommendations: {len(results.get('recommendations', []))}")

    # Create report
    report_path = validator.create_validation_summary_report()
    print(f"   Report: {report_path}")

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Validation error: {e}")
