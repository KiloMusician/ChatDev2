#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
origin_url="$(git remote get-url origin 2>/dev/null || echo unknown)"
filemode="$(git config --get core.filemode || echo unset)"
untracked_cache="$(git config --get core.untrackedCache || echo unset)"
split_index="$(git config --get core.splitIndex || echo unset)"
many_files="$(git config --get feature.manyFiles || echo unset)"

echo "SimulatedVerse Git Boundary Check"
echo "================================"
echo "root:        $ROOT_DIR"
echo "branch:      $branch"
echo "origin:      $origin_url"
echo "filemode:    $filemode"
echo "untracked:   $untracked_cache"
echo "splitIndex:  $split_index"
echo "manyFiles:   $many_files"
echo

if [[ "$ROOT_DIR" == /mnt/c/* ]]; then
  echo "[note] repo is running from a Windows-mounted worktree under WSL."
  echo "       Slow 'git status' scans here are treated as filesystem friction, not proof of repo corruption."
else
  echo "[note] repo is not on /mnt/c; WSL mounted-worktree friction should be lower."
fi
echo

if command -v git-lfs >/dev/null 2>&1; then
  echo "[ok] git-lfs is available: $(command -v git-lfs)"
else
  echo "[warn] git-lfs is not available on PATH."
  echo "       This repo's pre-push / post-checkout / post-merge hooks expect git-lfs."
  echo "       Fix PATH or install git-lfs before treating hook failures as repo failures."
fi
echo

for hook in .git/hooks/pre-push .git/hooks/post-checkout .git/hooks/post-merge .git/hooks/post-commit; do
  [[ -f "$hook" ]] || continue
  if grep -q 'git lfs' "$hook"; then
    echo "[hook] $(basename "$hook"): git-lfs dependent"
  else
    echo "[hook] $(basename "$hook"): custom/non-lfs"
  fi
done
echo

echo "Recommended operator path:"
echo "1. Use 'npm run surfaces:ensure' for runtime recovery before broad investigation."
echo "2. Use Windows git or the workspace SCM truth command when WSL git status is slow."
echo "3. Treat missing git-lfs and mounted-worktree scan delay as environment issues first."
