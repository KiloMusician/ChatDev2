"""Fix hardcoded Ollama host references across the NuSyQ-Hub repository.
Replaces any hardcoded "http://localhost:11434" with configured host from config/settings.json.
"""

import json
import re
from pathlib import Path


def main():
    repo_root = Path(__file__).parent.parent
    config_file = repo_root / "config" / "settings.json"
    config = json.loads(config_file.read_text(encoding="utf-8"))
    ollama_host = config.get("ollama", {}).get("host", "http://localhost:11434")

    # catch both original and fallback ports 11434 and 11435
    pattern = re.compile(r"http://localhost:1143[45]")
    replacements = []

    for filepath in repo_root.rglob("*.py"):
        try:
            text = filepath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip files that aren’t UTF-8 text
            continue
        # Replace any hardcoded localhost ports 11434 or 11435
        if pattern.search(text):
            new_text = pattern.sub(ollama_host, text)
            try:
                filepath.write_text(new_text, encoding="utf-8")
                replacements.append(str(filepath.relative_to(repo_root)))
            except (OSError, PermissionError):
                # Could not write file, skip
                continue

    if replacements:
        print("Replaced host in files:")
        for f in replacements:
            print(" -", f)
    else:
        print("No hardcoded references found.")


if __name__ == "__main__":
    main()
