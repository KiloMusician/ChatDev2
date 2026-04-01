#!/usr/bin/env bash
set -euo pipefail

# --- Zeta env bootstrap (quiet) ---
need() { command -v "$1" >/dev/null 2>&1 || return 1; }
if ! need rg; then nix-env -iA nixpkgs.ripgrep >/dev/null 2>&1 || true; fi
if ! need fd; then nix-env -iA nixpkgs.fd >/dev/null 2>&1 || true; fi
if ! need jq; then nix-env -iA nixpkgs.jq >/dev/null 2>&1 || true; fi
if ! need yq; then nix-env -iA nixpkgs.yq-go >/dev/null 2>&1 || true; fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
OUTDIR="$ROOT/reports/chatdev_audit"
mkdir -p "$OUTDIR"

STAMP="$(date +%Y%m%d-%H%M%S)"
MD="$OUTDIR/quick_${STAMP}.md"

# Patterns to detect ChatDev presence
PATTERN='chatdev|ChatDev|chat-dev|chat_dev|chat dev|chat-dev.yaml|chatdev.yml|team.yml|agents/team|chatdev.config'

echo "# ChatDev Quick Audit ($STAMP)" > "$MD"
echo "" >> "$MD"

# Count references (fallback to grep if rg missing)
if need rg; then
  echo "## Reference counts" >> "$MD"
  rg -n --glob '!node_modules/**' --glob '!.git/**' --hidden -S "$PATTERN" | tee "$OUTDIR/quick_hits_${STAMP}.txt" \
    | awk -F: '{print $1}' | sort | uniq -c | sort -nr \
    | awk '{printf "- %s × %s\n",$1,$2}' >> "$MD" || true
else
  echo "## Reference counts (grep fallback)" >> "$MD"
  grep -RIn --exclude-dir={.git,node_modules} -E "$PATTERN" . | tee "$OUTDIR/quick_hits_${STAMP}.txt" \
    | awk -F: '{print $1}' | sort | uniq -c | sort -nr \
    | awk '{printf "- %s × %s\n",$1,$2}' >> "$MD" || true
fi

echo "" >> "$MD"
echo "## Config files detected" >> "$MD"
find . -maxdepth 4 -type f \( -name "chatdev.yml" -o -name "chatdev.yaml" -o -name "chatdev.config.*" -o -path "*/agents/team.yml" \) \
  | sed 's#^\./##' | sort | awk '{print "- " $0}' >> "$MD" || true

echo "" >> "$MD"
echo "## Package hints" >> "$MD"
if [ -f package.json ]; then
  jq -r '.dependencies,.devDependencies|keys[]?' package.json 2>/dev/null \
    | grep -i chatdev | sed 's/^/- npm: /' >> "$MD" || true
fi
if [ -f pyproject.toml ]; then
  grep -E 'chatdev|ChatDev' pyproject.toml | sed 's/^/- py: /' >> "$MD" || true
fi
if [ -f requirements.txt ]; then
  grep -i chatdev requirements.txt | sed 's/^/- py: /' >> "$MD" || true
fi

echo "" >> "$MD"
echo "## CLI presence" >> "$MD"
if command -v chatdev >/dev/null 2>&1; then
  echo "- chatdev: FOUND" >> "$MD"
else
  echo "- chatdev: not found (ok if using embedded runner)" >> "$MD"
fi

echo "" >> "$MD"
echo "## Suggested next steps" >> "$MD"
echo "- Run deep audit: python3 scripts/zeta/audit_chatdev.py" >> "$MD"
echo "- If missing configs, scaffold chatdev.yml + agents/team.yml (Ollama local)." >> "$MD"

ln -sf "$MD" "$OUTDIR/LATEST.md"
echo "::SUMMARY::$MD"
echo "Wrote $MD"