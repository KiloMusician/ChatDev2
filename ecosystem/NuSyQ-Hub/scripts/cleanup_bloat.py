"""cleanup_bloat.py — NuSyQ-Hub report/log/prototype cleanup utility

Removes or archives obsolete, incomplete, or excessive files from reports, logs, prototypes, and session directories.
- Keeps only the most recent N reports/logs per type
- Moves old/incomplete prototypes to an archive
- Optionally deletes placeholder/stub files
"""

import shutil
from pathlib import Path

# Configuration
REPORTS_DIR = Path("state/reports")
LOGS_DIR = Path("logs/terminals")
PROTOTYPES_DIRS = [
    Path("prototypes"),
    Path("../NuSyQ/ChatDev/WareHouse"),
    Path("../SimulatedVerse/testing_chamber"),
]
SESSION_LOGS_DIR = Path("docs/Agent-Sessions")
ARCHIVE_DIR = Path("archive/obsolete")
MAX_REPORTS = 10
MAX_LOGS = 10


def cleanup_dir(directory, pattern, keep=MAX_REPORTS):
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files[keep:]:
        print(f"Archiving {f}")
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(f), ARCHIVE_DIR / f.name)


def cleanup_reports():
    if not REPORTS_DIR.exists():
        return
    cleanup_dir(REPORTS_DIR, "*.md", keep=MAX_REPORTS)
    cleanup_dir(REPORTS_DIR, "*.json", keep=MAX_REPORTS)


def cleanup_logs():
    if not LOGS_DIR.exists():
        return
    cleanup_dir(LOGS_DIR, "*.log", keep=MAX_LOGS)


def cleanup_prototypes():
    for d in PROTOTYPES_DIRS:
        if d.exists():
            for item in d.iterdir():
                if item.is_dir() and ("incomplete" in item.name or "stub" in item.name or "test" in item.name):
                    print(f"Archiving prototype {item}")
                    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(item), ARCHIVE_DIR / item.name)


def cleanup_sessions():
    if not SESSION_LOGS_DIR.exists():
        return
    cleanup_dir(SESSION_LOGS_DIR, "SESSION_*.md", keep=MAX_REPORTS)


def main():
    print("--- NuSyQ-Hub Cleanup Utility ---")
    cleanup_reports()
    cleanup_logs()
    cleanup_prototypes()
    cleanup_sessions()
    print("Cleanup complete. Archived files are in:", ARCHIVE_DIR)


if __name__ == "__main__":
    main()
