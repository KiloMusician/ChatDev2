"""
Workaround script for pytest 8.4.2 Windows file handle bug.
Runs tests file-by-file to avoid terminal writer crashes.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run all test files individually."""
    tests_dir = Path(__file__).parent / "tests"
    test_files = sorted(tests_dir.glob("test_*.py"))

    if not test_files:
        print("No test files found!")
        return 1

    print(f"Found {len(test_files)} test files\n")

    failed_files = []
    passed_count = 0
    failed_count = 0

    for test_file in test_files:
        print(f"\n{'=' * 70}")
        print(f"Running: {test_file.name}")
        print("=" * 70)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(test_file),
                "-p",
                "no:cacheprovider",
                "-p",
                "no:capture",
                "-v",
                "--tb=short",
            ],
            capture_output=False,
            check=False,
        )

        if result.returncode == 0:
            passed_count += 1
            print(f"\n✓ {test_file.name} PASSED")
        else:
            failed_count += 1
            failed_files.append(test_file.name)
            print(f"\n✗ {test_file.name} FAILED")

    print(f"\n\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    print(f"Total test files: {len(test_files)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")

    if failed_files:
        print("\nFailed files:")
        for f in failed_files:
            print(f"  - {f}")
        return 1

    print("\n✓ All test files passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
