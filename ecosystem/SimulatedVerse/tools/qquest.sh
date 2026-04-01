#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
OUT="${2:-.qquest}"
mkdir -p "$OUT"

echo "== Query-Quest: static sweep =="

# Check for required tools and provide alternatives
if ! command -v rg >/dev/null; then
    echo "Warning: ripgrep (rg) not found. Install with: brew install ripgrep"
    touch "$OUT/placeholders_and_spinloops.txt"
else
    # 1) Obvious footguns / placeholders - Fixed regex patterns
    rg -n --hidden -S --no-ignore -g '!node_modules' -g '!build' -g '!.git' \
      'TODO|FIXME|XXX|HACK|WIP|TBD|PLACEHOLDER|MOCK|FAKE|DUMMY|console\.log\(|print\(|debugger|while\s*\(\s*true\s*\)|for\s*\(\s*;;\s*\)|process\.exit\(' \
      "$ROOT" | tee "$OUT/placeholders_and_spinloops.txt" || touch "$OUT/placeholders_and_spinloops.txt"
fi

# 2) Duplicates by fingerprint - Handle missing fd
if command -v fd >/dev/null; then
    FD_CMD="fd"
elif command -v fdfind >/dev/null; then
    FD_CMD="fdfind"
else
    echo "Warning: fd/fdfind not found. Using find as fallback"
    FD_CMD="find"
fi

if [ "$FD_CMD" = "find" ]; then
    find "$ROOT" -type f ! -path "*/node_modules/*" ! -path "*/build/*" ! -path "*/.git/*" \
      | xargs -I{} sh -c 'printf "%s  " "{}"; shasum "{}" 2>/dev/null | cut -d" " -f1' \
      | sort -k2 \
      | awk '{if($2==p){print prev"\n"$0"\n"}; p=$2; prev=$0}' \
      | tee "$OUT/duplicate_hashes.txt" || touch "$OUT/duplicate_hashes.txt"
else
    $FD_CMD -H -t f . "$ROOT" \
      | grep -v -E '/(node_modules|build|dist|.git)/' \
      | xargs -I{} sh -c 'printf "%s  " "{}"; shasum "{}" 2>/dev/null | cut -d" " -f1' \
      | sort -k2 \
      | awk '{if($2==p){print prev"\n"$0"\n"}; p=$2; prev=$0}' \
      | tee "$OUT/duplicate_hashes.txt" || touch "$OUT/duplicate_hashes.txt"
fi

# 3) Broken imports / dead paths (TS/JS/Python/Godot/Unity-ish)
if command -v rg >/dev/null; then
    rg -n --hidden -S --no-ignore -g '!node_modules' -g '!build' -g '!.git' \
      'from\s+["\x27]\.[^"\x27]+["\x27]|import\s+.+\s+from\s+["\x27]\.[^"\x27]+["\x27]|load\(["\x27]res://[^"\x27]+["\x27]\)' \
      "$ROOT" \
    | awk -F: 'BEGIN{OFS=":"}{print $1,$2,$3}' \
    | tee "$OUT/suspect_imports.txt" || touch "$OUT/suspect_imports.txt"
else
    touch "$OUT/suspect_imports.txt"
fi

# 4) CSS/UX: "looks like a button" but not clickable
if command -v rg >/dev/null; then
    rg -n --hidden -S --no-ignore -g '!node_modules' -g '!build' -g '!.git' \
      '<div[^>]*(btn|button|primary|secondary)[^>]*>|class(Name)?=.*(btn|button|cta|primary|secondary).*' \
      "$ROOT" | tee "$OUT/looks_like_button.txt" || touch "$OUT/looks_like_button.txt"
else
    touch "$OUT/looks_like_button.txt"
fi

# 5) eslint/ruff/mypy/bandit/radon (fast config-less)
if command -v eslint >/dev/null; then
  eslint . --max-warnings=0 || true
fi
if command -v ruff >/dev/null; then
  ruff check . --output-format=github || true
fi
if command -v mypy >/dev/null; then
  mypy --ignore-missing-imports || true
fi
if command -v bandit >/dev/null; then
  bandit -q -r . || true
fi
if command -v radon >/dev/null; then
  radon cc -s -n D . | tee "$OUT/code_complexity.txt" || true
fi

# 6) Project graphs (bottlenecks via fan-in / fan-out)
if command -v python3 >/dev/null; then
    python3 - <<'PY' "$ROOT" "$OUT"
import os, re, sys, json, pathlib, collections
try:
    root, out = sys.argv[1], sys.argv[2]
    edges = []
    imp = re.compile(r'(?:from|import)\s+([a-zA-Z0-9_\.]+)')
    for p in pathlib.Path(root).rglob('*.py'):
        if any(s in p.parts for s in ('.git','node_modules','dist','build')): continue
        try:
            txt = p.read_text('utf-8',errors='ignore')
        except: 
            continue
        for m in imp.findall(txt):
            edges.append([str(p), m])
    G = collections.defaultdict(lambda: {'in':0,'out':0})
    for a,b in edges: 
        G[a]['out']+=1; G[b]['in']+=1
    hot = sorted(G.items(), key=lambda kv:(-kv[1]['in']-kv[1]['out']))[:32]
    pathlib.Path(out,'python_hotspots.json').write_text(json.dumps(hot,indent=2))
    print("Hotspots written:", pathlib.Path(out,'python_hotspots.json'))
except Exception as e:
    print(f"Python analysis failed: {e}")
    with open(f"{out}/python_hotspots.json", "w") as f:
        f.write("[]")
PY
else
    echo "[]" > "$OUT/python_hotspots.json"
fi

# 7) KPulse-specific checks
echo "== KPulse-specific checks =="

# Interactive affordances without handlers
if command -v rg >/dev/null; then
    rg -n '<(div|span|i|svg)[^>]*(btn|button|cta|pill|chip)[^>]*>' -g '!node_modules' "$ROOT" \
    | rg -v 'onClick=|@click=|bind:tap|href=' > "$OUT/affordances_without_actions.txt" || touch "$OUT/affordances_without_actions.txt"

    # Loading bars present & wired
    rg -n 'Progress(Bar|Spinner|Circle)|aria-busy|role="progressbar"' -g '!node_modules' "$ROOT" \
      > "$OUT/progress_components.txt" || touch "$OUT/progress_components.txt"
    rg -n 'setProgress\(|progress\.(set|update)|dispatch\(.+PROGRESS' -g '!node_modules' "$ROOT" \
      > "$OUT/progress_wiring.txt" || touch "$OUT/progress_wiring.txt"

    # Endless loop detectors
    rg -n 'for\s*\(;;\)|while\s*\(true\)|while\s+True' -g '!node_modules' "$ROOT" > "$OUT/loops.txt" || touch "$OUT/loops.txt"
    rg -n 'requestAnimationFrame\([^)]*\)' -g '!node_modules' "$ROOT" \
      | rg -v 'cancelAnimationFrame|throttle|debounce' >> "$OUT/loops.txt" || true

    # Broken routes (web)
    if [ -d "public" ]; then
        rg -n 'path:\s*["'\'']/[^"'\'']*["'\'']' src 2>/dev/null | cut -d'"' -f2 \
          | while read p; do [ -d "public$p" -o -f "public$p" ] || echo "$p"; done \
          > "$OUT/missing_routes.txt" || touch "$OUT/missing_routes.txt"
    fi

    # Godot/Python bottlenecks
    rg -n 'process\(|_physics_process\(|_process\(' -g '*.gd' "$ROOT" > "$OUT/godot_ticks.txt" || touch "$OUT/godot_ticks.txt"
    rg -n 'time\.sleep\(|await asyncio\.sleep\(\s*0\s*\)' -g '*.py' "$ROOT" > "$OUT/sleeps.txt" || touch "$OUT/sleeps.txt"
else
    # Create empty files if rg is not available
    touch "$OUT/affordances_without_actions.txt" "$OUT/progress_components.txt" "$OUT/progress_wiring.txt" "$OUT/loops.txt" "$OUT/godot_ticks.txt" "$OUT/sleeps.txt" "$OUT/missing_routes.txt"
fi

echo "== Done =="
echo "Reports saved to: $OUT/"
echo "Priority order: loops.txt, placeholders_and_spinloops.txt, affordances_without_actions.txt"