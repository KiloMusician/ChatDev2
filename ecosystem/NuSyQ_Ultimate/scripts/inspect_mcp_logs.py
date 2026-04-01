import glob
import os


def tail_lines(path, n=200):
    try:
        with open(path, "rb") as f:
            data = f.read().splitlines()
            lines = data[-n:]
            for b in lines:
                try:
                    print(b.decode("utf-8", errors="replace"))
                except (AttributeError, TypeError):
                    print(b)
    except (OSError, UnicodeDecodeError, ValueError, TypeError) as e:
        print(f"-- ERROR reading {path}: {e}")


paths = glob.glob("**/*mcp*", recursive=True)
files = [p for p in paths if os.path.isfile(p)]
if not files:
    print("NO_MCP_FILES")
else:
    for f in sorted(files):
        print("=== FILE:", f)
        tail_lines(f)
        print("\n")
