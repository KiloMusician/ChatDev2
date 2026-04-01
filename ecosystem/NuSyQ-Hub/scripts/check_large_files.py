"""Fail CI if any committed file exceeds size threshold.

Usage: python scripts/check_large_files.py --threshold-mb 5
"""

import argparse
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--threshold-mb", type=int, default=5)
args = parser.parse_args()

threshold = args.threshold_mb * 1024 * 1024

repo = Path(".")
# check tracked files
files = (p for p in repo.rglob("*") if p.is_file())
large = []
for f in files:
    try:
        size = f.stat().st_size
        if size > threshold:
            large.append((f, size))
    except Exception:
        continue

if large:
    print("Found large files:")
    for f, s in sorted(large, key=lambda x: -x[1]):
        print(f" - {f} ({s / 1024 / 1024:.2f} MB)")
    print("Failing CI due to large files. Consider Git LFS or external storage.")
    sys.exit(2)

print("No large files found")
sys.exit(0)
