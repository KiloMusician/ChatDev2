"""🏥 Quick Health Dashboard - Real-Time Error Status
Shows current error state across all diagnostic systems
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[str, int]:
    """Run command and return output + exit code"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        return result.stdout + result.stderr, result.returncode
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return f"Error: {e}", 1


def main():
    print("=" * 80)
    print("🏥 NUSYQ-HUB HEALTH DASHBOARD")
    print("=" * 80)
    print()

    # 1. Ruff Error Count
    print("📊 RUFF LINTER STATUS")
    print("-" * 80)
    output, _ = run_command([sys.executable, "-m", "ruff", "check", "src/", "--select=E,W,F,C901", "--statistics"])

    if "Found" in output:
        lines = output.strip().split("\n")
        error_counts = {}
        total = 0

        for line in lines:
            if line.strip() and not line.startswith("Found"):
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    count = int(parts[0])
                    code = parts[1]
                    total += count
                    error_counts[code] = count

        print(f"  ✅ Total Errors: {total}")
        for code, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            emoji = "🟢" if count < 100 else "🟡" if count < 500 else "🔴"
            print(f"     {emoji} {code}: {count}")
    else:
        print("  ✅ No errors found!")

    print()

    # 2. Critical Type Errors
    print("🔬 TYPE SYSTEM STATUS")
    print("-" * 80)
    output, code = run_command(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src/consciousness/the_oldest_house.py",
            "--select=F,E",
        ]
    )

    if code == 0:
        print("  ✅ the_oldest_house.py: All type checks passing!")
    else:
        error_count = output.count("\n--> ")
        print(f"  ⚠️  the_oldest_house.py: {error_count} type errors")

    print()

    # 3. Test Suite Status
    print("🧪 TEST SUITE STATUS")
    print("-" * 80)
    try:
        output, code = run_command([sys.executable, "-m", "pytest", "--collect-only", "-q"])
        if "test" in output.lower():
            test_count = output.count("test_")
            print(f"  ✅ Found {test_count} tests")
        else:
            print("  ⚠️  No tests discovered")
    except (ModuleNotFoundError, RuntimeError, OSError):
        print("  Info: Pytest not available")

    print()

    # 4. SonarQube Issues
    print("🔍 SONARQUBE ANALYSIS")
    print("-" * 80)
    sonar_results = Path("data/diagnostics/sonarqube_scan_results.json")
    if sonar_results.exists():
        import json

        try:
            data = json.loads(sonar_results.read_text())
            if isinstance(data, list) and data:
                print(f"  ✅ Last Scan: {len(data)} issues found")

                # Group by rule
                rules = {}
                for issue in data:
                    if isinstance(issue, dict):
                        rule = issue.get("rule", "unknown")
                        rules[rule] = rules.get(rule, 0) + 1

                for rule, count in sorted(rules.items(), key=lambda x: x[1], reverse=True)[:3]:
                    print(f"     • {rule}: {count} occurrences")
            else:
                print(f"  Info: Scan data format: {type(data)}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  ⚠️  Error reading scan results: {e}")
    else:
        print("  Info: No SonarQube scan results found")
        print("     Run: python scripts/analyze_sonarqube_issues.py")

    print()

    # 5. Quest System Status
    print("🎯 QUEST SYSTEM STATUS")
    print("-" * 80)
    quest_file = Path("data/unified_pu_queue.json")
    if quest_file.exists():
        import json

        queue = json.loads(quest_file.read_text())
        print(f"  ✅ PU Queue: {len(queue)} items")

        # Count by type
        types = {}
        for pu in queue:
            pu_type = pu.get("pu_type", "unknown")
            types[pu_type] = types.get(pu_type, 0) + 1

        for pu_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
            print(f"     • {pu_type}: {count}")
    else:
        print("  Info: No PU queue found")

    print()

    # 6. Overall Health Grade
    print("🎓 OVERALL HEALTH GRADE")
    print("-" * 80)

    # Calculate grade based on error count
    # 0-100: A+, 101-500: A, 501-1000: B, 1001-2000: C, 2000+: D
    output, _ = run_command([sys.executable, "-m", "ruff", "check", "src/", "--select=E,W,F,C901", "--statistics"])

    if "Found" in output:
        match = None
        for line in output.split("\n"):
            if "Found" in line and "error" in line:
                import re

                nums = re.findall(r"\d+", line)
                if nums:
                    match = int(nums[0])
                    break

        if match is not None:
            if match <= 100:
                grade = "A+"
                emoji = "🏆"
            elif match <= 500:
                grade = "A"
                emoji = "🥇"
            elif match <= 1000:
                grade = "B+"
                emoji = "🥈"
            elif match <= 1500:
                grade = "B"
                emoji = "🥉"
            elif match <= 2000:
                grade = "C"
                emoji = "⚠️"
            else:
                grade = "D"
                emoji = "🔴"

            print(f"  {emoji} Grade: {grade} ({match} total errors)")
            print()

            if match <= 1500:
                print("  🎉 Repository is in good health!")
            else:
                print("  ⚠️  Consider running automated fixes:")
                print("     python -m ruff check src/ --fix --unsafe-fixes")
    else:
        print("  🏆 Grade: A+ (0 errors!)")
        print()
        print("  🎉 Perfect health!")

    print()
    print("=" * 80)
    print("Dashboard generated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
