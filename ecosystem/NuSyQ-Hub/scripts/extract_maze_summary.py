import json
from pathlib import Path

log = Path("logs")
files = sorted(log.glob("maze_summary_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
if not files:
    print("No maze_summary_*.json files found in logs/")
    raise SystemExit(1)
path = files[0]
print("Using summary:", path)
# We'll stream-read the file to find top-level keys without loading entire huge file
# But to get "errors" and top files we can try incremental parsing using json.load but limit memory by reading smaller chunks
# Simpler: read the first 10MB and look for '"errors"' and '"files"' occurrences; if not found, fallback to skipping

chunk_size = 10 * 1024 * 1024
with path.open("r", encoding="utf-8", errors="replace") as fh:
    s = fh.read(chunk_size)
# find "errors":
if '"errors"' in s:
    try:
        # attempt to parse the errors array by finding the position of '"errors"'
        idx = s.index('"errors"')
        # find the start of the array
        arr_start = s.index("[", idx)
        # naive find of closing bracket - count brackets
        depth = 0
        for i in range(arr_start, len(s)):
            if s[i] == "[":
                depth += 1
            elif s[i] == "]":
                depth -= 1
                if depth == 0:
                    arr_end = i + 1
                    break
        errors_json = s[arr_start:arr_end]
        errors = json.loads(errors_json)
        print("Errors count:", len(errors))
        print("\nSample errors (first 20):")
        for e in errors[:20]:
            print("-", e)
    except Exception as e:
        print("Failed to extract errors safely:", e)
else:
    print('No "errors" key found in initial chunk.')

# Find top files by scanning for '"files"' key and then list file paths keys if possible
if '"files"' in s:
    try:
        idx = s.index('"files"')
        obj_start = s.index("{", idx)
        # find approximate end of files object by finding a closing '}\n    ,"errors"' pattern
        # This is brittle; instead we'll search for '"errors"' after obj_start and cut before it
        err_idx = s.find('"errors"', obj_start)
        if err_idx != -1:
            files_obj_text = s[obj_start:err_idx]
            # naive extract of keys
            import re

            keys = re.findall(r'"(C:[^"\\]+|src\\[^"\\]+|[\w\/.-]+\.py)"\s*:\s*\[', files_obj_text)
            print("\nDiscovered file keys sample (first 30):")
            for k in keys[:30]:
                print("-", k)
        else:
            print('Could not find "errors" after "files" in initial chunk; skipping file-key extraction')
    except Exception as e:
        print("Failed to extract files safely:", e)
else:
    print('No "files" key found in initial chunk.')

print("\nDone.")
