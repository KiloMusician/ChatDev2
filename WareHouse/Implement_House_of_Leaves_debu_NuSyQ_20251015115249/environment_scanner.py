"""Placeholder environment scanner."""

def scan_repo(path: str) -> dict[str, str]:
    return {"path": path, "status": "placeholder scan", "issues": "none"}


def main() -> None:
    print(scan_repo("./"))


if __name__ == "__main__":
    main()
