from pathlib import Path

OLD_PREFIX = r"C:\Users\malik\Desktop\Legacy\NuSyQ-Hub"
TARGET_DIRS = ["state/reports", "docs/Reports", "state/receipts", "logs"]
EXTENSIONS = {".md", ".json", ".txt", ".log"}
MAX_FILE_SIZE = 2_000_000  # skip files larger than ~2MB


def rewrite_file(path: Path, replacement: str) -> int:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if OLD_PREFIX not in text:
        return 0

    updated = text.replace(OLD_PREFIX, replacement)
    path.write_text(updated, encoding="utf-8")
    return text.count(OLD_PREFIX)


def iter_targets(root: Path):
    for dir_name in TARGET_DIRS:
        target_dir = root / dir_name
        if not target_dir.exists():
            continue
        for path in target_dir.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in EXTENSIONS:
                continue
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            yield path


def main() -> None:
    root = Path.cwd()
    replacement = str(root)
    total = 0

    for target in iter_targets(root):
        count = rewrite_file(target, replacement)
        if count:
            print(f"Updated {count} stale paths in {target.relative_to(root)}")
            total += count

    if total == 0:
        print("No stale absolute paths found.")
    else:
        print(f"Replaced {total} stale references with {replacement}")


if __name__ == "__main__":
    main()
