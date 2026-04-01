#!/usr/bin/env bash
set -euo pipefail

# ==== CONFIG ===============================================================
: "${DRY_RUN:=1}"                   # 1=dry-run, 0=apply
: "${WRITE_HINTS:=1}"               # write hints into ./_reports
: "${MAX_FILE_BYTES:=800000}"       # skip huge binaries
: "${ENABLE_RENAMES:=1}"            # allow rename pass (updates imports/paths)
: "${ENABLE_LINTERS:=1}"            # run local linters/formatters when present
: "${ENABLE_TESTS:=1}"              # run tests if configured
: "${ENABLE_OLLAMA:=0}"             # allow local LLM (Ollama) for tricky rewrites
: "${TOKEN_BUDGET:=0}"              # hard budget for remote AI; keep at 0
: "${RENAME_STYLE:=slug}"           # 'slug' or 'descriptive'
: "${BRANCH:=spree/$(date +%Y%m%d-%H%M)}"
# ===========================================================================

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

mkdir -p _reports spree_cache ops/logs

echo "==> Starting spree on branch: $BRANCH"
git checkout -b "$BRANCH" >/dev/null 2>&1 || git checkout "$BRANCH"

# 0) Baseline sanity snapshot
git add -A && git commit -m "chore(spree): baseline snapshot" || true

# 1) Inventory (fd+rg recommended, else find/grep)
if command -v fd >/dev/null; then
  fd -H -t f -a > spree_cache/files.all
else
  find . -type f -not -path "./.git/*" -print > spree_cache/files.all
fi

# 2) Classify (placeholders, empty, duplicates, broken, typos, orphans)
python3 ops/tools/index_repo.py --files spree_cache/files.all --out _reports/index.json

# 3) Duplicate detection (hash + near-dup via shingles)
python3 ops/tools/find_duplicates.py --index _reports/index.json --out _reports/duplicates.json

# 4) Placeholder/empty/broken markers
python3 ops/tools/find_placeholders.py --index _reports/index.json --out _reports/placeholders.json

# 5) Static checks (local first)
if [ "$ENABLE_LINTERS" = "1" ]; then
  bash ops/tools/run_linters.sh | tee _reports/linters.log || true
fi

# 6) Rename pass (safe, updates imports/refs)
if [ "$ENABLE_RENAMES" = "1" ]; then
  python3 ops/tools/smart_rename.py \
    --index _reports/index.json \
    --duplicates _reports/duplicates.json \
    --style "$RENAME_STYLE" \
    --dry-run "$DRY_RUN" \
    --out _reports/renames.json
  # Apply renames + reference updates
  python3 ops/tools/update_references.py --plan _reports/renames.json --dry-run "$DRY_RUN"
fi

# 7) Orphan + broken import resolution
python3 ops/tools/fix_orphans.py --index _reports/index.json --dry-run "$DRY_RUN" \
  --out _reports/orphan_fixes.json || true

# 8) Comment inject (explain decisions inline minimally)
python3 ops/tools/annotate_changes.py --plans _reports/*.json --dry-run "$DRY_RUN"

# 9) Tests (if present)
if [ "$ENABLE_TESTS" = "1" ]; then
  bash ops/tools/run_tests.sh | tee _reports/tests.log || true
fi

# 10) Cascade (plan next passes, zero-token)
python3 ops/tools/cascade_event.py --mode "post-spree" --budget "$TOKEN_BUDGET" \
  --out _reports/cascade_next.yml

# 11) Commit
git add -A
git commit -m "refactor(spree): consolidate, rename, update refs; docs & hints" || true

echo "==> Spree complete. Dry-run: $DRY_RUN | Reports in ./_reports"
echo "==> Review commits, then merge when happy."