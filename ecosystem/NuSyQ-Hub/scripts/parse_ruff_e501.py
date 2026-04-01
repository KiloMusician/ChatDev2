import json
import re
from collections import Counter
from pathlib import Path

input_file = Path("ruff_e501.txt")
output_file = Path("ruff_e501_summary.json")

pattern = re.compile(r"-->\s*(.+?):\d+:\d+")

counts = Counter()
if not input_file.exists():
    print("ruff_e501.txt not found")
    raise SystemExit(1)

# Read raw bytes and detect UTF-16 BOM (many Windows tools emit UTF-16). Decode accordingly.
raw = input_file.read_bytes()
enc = "utf-8"
if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
    enc = "utf-16"
text = raw.decode(enc, errors="replace")
for line in text.splitlines():
    m = pattern.search(line)
    if m:
        p = m.group(1)
        p = p.replace("\\", "/")
        try:
            norm = Path(p).as_posix()
        except Exception:
            norm = p
        counts[norm] += 1

summary = counts.most_common()
with output_file.open("w", encoding="utf-8") as out:
    json.dump(summary, out, indent=2)

# Print top 30
for i, (file, c) in enumerate(summary[:30], 1):
    print(f"{i:2d}. {file} — {c}")

print(f"\nTotal distinct files: {len(counts)}")
print(f"Summary written to: {output_file}")
