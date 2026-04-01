"""Summarize and prune logs, wiring to dashboard/learning if available."""

from pathlib import Path

LOG_DIR = Path("logs")
SUMMARY_FILE = LOG_DIR / "log_summary.txt"
MAX_LOG_SIZE_MB = 20

if not LOG_DIR.exists():
    print("No logs directory found.")
    exit(0)

summary_lines = []
for log_file in LOG_DIR.glob("*.log"):
    size_mb = log_file.stat().st_size / (1024 * 1024)
    summary_lines.append(f"{log_file.name}: {size_mb:.2f} MB")
    if size_mb > MAX_LOG_SIZE_MB:
        print(f"Pruning {log_file} (was {size_mb:.2f} MB)")
        with open(log_file, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-10000:]
        with open(log_file, "w", encoding="utf-8") as f:
            f.writelines(lines)

with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_lines))

print(f"Log summary written to {SUMMARY_FILE}")
# TODO: Wire to dashboard/learning system if available
