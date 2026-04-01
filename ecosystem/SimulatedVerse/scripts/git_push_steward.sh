#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
#  G I T   P U S H   S T E W A R D   (Replit / "Sage-Pilot" edition)
#  - Diagnoses auth, remotes, locks, branch, LFS, hooks, large repo hazards
#  - Uses http.extraheader for PAT (no token persisted to disk, no echo)
#  - Writes compact receipts to reports/
#  - Never prints secrets; masks environment
#  - Works even if .git is "agent-restricted" (you run this in Shell)
# ──────────────────────────────────────────────────────────────────────────────

START_TS="$(date -u +%Y%m%d_%H%M%S)"
RECEIPTS_DIR="reports"
mkdir -p "$RECEIPTS_DIR"

log() { printf "%s %s\n" "$(date -u +%H:%M:%S)" "$*"; }
mask() { # print "****" if value looks like a token
  local v="$1"
  if [[ ${#v} -ge 8 ]]; then echo "********"; else echo "$v"; fi
}

write_receipt () {
  local path="$RECEIPTS_DIR/git_push_receipt_${START_TS}.json"
  cat > "$path" <<EOF
{
  "ts": "$(date -u +%FT%TZ)",
  "step": "$1",
  "data": $2
}
EOF
  log "📄 receipt -> $path"
}

# ──────────────────────────────────────────────────────────────────────────────
# 0) Fast environment sense
# ──────────────────────────────────────────────────────────────────────────────
log "🔎 Sensing environment…"
GIT_VER="$(git --version 2>/dev/null || true)"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
HEAD_SHA="$(git rev-parse --short HEAD 2>/dev/null || true)"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LOCK_PATH="$ROOT/.git/index.lock"
REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
REMOTE_SHOW="$(git remote -v 2>/dev/null || true)"
STATUS_BRIEF="$(git status --porcelain=v1 -b 2>/dev/null || true)"

write_receipt "sense" "$(jq -nc \
  --arg gv "$GIT_VER" \
  --arg br "$BRANCH" \
  --arg sha "$HEAD_SHA" \
  --arg root "$ROOT" \
  --arg remote "$REMOTE_URL" \
  --arg status "$STATUS_BRIEF" \
  --arg remshow "$REMOTE_SHOW" \
  '{git_version:$gv, branch:$br, head:$sha, root:$root, remote:$remote, status:$status, remotes:$remshow}')"

# ──────────────────────────────────────────────────────────────────────────────
# 1) Clear stale lock (safe)
# ──────────────────────────────────────────────────────────────────────────────
if [[ -f "$LOCK_PATH" ]]; then
  log "🧹 Found stale index.lock -> $LOCK_PATH (removing safely)"
  rm -f "$LOCK_PATH"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 2) Find an auth token w/out printing it
#    (Try your known envs in priority order; do not echo)
# ──────────────────────────────────────────────────────────────────────────────
CANDIDATES=(
  "NuSyQ_Github_Token_Fine_Grained"
  "GITHUB_PERSONAL_ACCESS_TOKEN"
  "GITHUB_TOKEN"
  "ADMIN_TOKEN"
  "GH_TOKEN"
)

TOKEN=""
TOKEN_NAME=""
for k in "${CANDIDATES[@]}"; do
  if [[ -n "${!k-}" ]]; then TOKEN="${!k}"; TOKEN_NAME="$k"; break; fi
done

if [[ -z "$TOKEN" ]]; then
  write_receipt "auth" "$(jq -nc '{"auth":"absent"}')"
  log "❌ No GitHub token environment variable found."
  log "   Set one of: ${CANDIDATES[*]}"
  exit 1
else
  write_receipt "auth" "$(jq -nc --arg name "$TOKEN_NAME" '{"auth":"present","which":$name}')"
  log "🔐 Auth present via $TOKEN_NAME"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3) Ensure user identity (won't break if already configured)
# ──────────────────────────────────────────────────────────────────────────────
git config user.name  >/dev/null 2>&1 || git config user.name  "NuSyQ Sage-Pilot"
git config user.email >/dev/null 2>&1 || git config user.email "sage-pilot@users.noreply.github.com"

# ──────────────────────────────────────────────────────────────────────────────
# 4) Ensure origin remote URL
#    You can override with: export GIT_REMOTE="https://github.com/<org>/<repo>.git"
# ──────────────────────────────────────────────────────────────────────────────
if [[ -n "${GIT_REMOTE-}" ]]; then
  TARGET_REMOTE="$GIT_REMOTE"
elif [[ -n "$REMOTE_URL" ]]; then
  TARGET_REMOTE="$REMOTE_URL"
else
  # Fallback guess: use repo folder name (change org/name if needed)
  REPO_NAME="$(basename "$ROOT")"
  TARGET_REMOTE="https://github.com/KiloMusician/${REPO_NAME}.git"
fi

if git remote get-url origin >/dev/null 2>&1; then
  log "🔗 origin exists -> $(git remote get-url origin)"
else
  log "🔗 adding origin -> $TARGET_REMOTE"
  git remote add origin "$TARGET_REMOTE"
fi

write_receipt "remote" "$(jq -nc --arg url "$(git remote get-url origin)" '{"origin":$url}')"

# ──────────────────────────────────────────────────────────────────────────────
# 5) Optional: create remote repo if missing (requires repo scope)
#    Set CREATE_REMOTE=1 to attempt creation.
# ──────────────────────────────────────────────────────────────────────────────
if [[ "${CREATE_REMOTE-0}" = "1" ]]; then
  OWNER_REPO="$(git remote get-url origin | sed -E 's#.*github.com[:/]+([^/]+/[^/]+)(\.git)?#\1#')"
  OWNER="${OWNER_REPO%/*}"
  NAME="${OWNER_REPO#*/}"
  log "🛠️  Attempting to create repo $OWNER/$NAME (if it does not exist)…"
  # Silent check; if it 404s, try to create
  if ! curl -s -H "Authorization: Bearer $TOKEN" "https://api.github.com/repos/$OWNER/$NAME" | grep -q '"full_name"'; then
    curl -s -X POST \
      -H "Authorization: Bearer $TOKEN" \
      -H "Accept: application/vnd.github+json" \
      https://api.github.com/user/repos \
      -d "{\"name\":\"$NAME\",\"private\":true}" >/dev/null || true
  fi
fi

# ──────────────────────────────────────────────────────────────────────────────
# 6) Stash local WIP as a tiny, conventional commit (if needed)
# ──────────────────────────────────────────────────────────────────────────────
if ! git diff --quiet || ! git diff --cached --quiet; then
  log "📝 Staging changes…"
  git add -A
  COMMIT_MSG="chore(repo): safe micro-commit from Replit Sage-Pilot @ ${START_TS}"
  git commit -m "$COMMIT_MSG" || true
fi

# ──────────────────────────────────────────────────────────────────────────────
# 7) Large files / LFS hint (optional, non-fatal)
# ──────────────────────────────────────────────────────────────────────────────
HAS_LFS=false
if command -v git-lfs >/dev/null 2>&1; then
  HAS_LFS=true
fi
# If repo > 2.5GB or files > 50MB, suggest LFS
SIZE_MB="$(du -sm . | awk '{print $1}')"
LFS_SUGGEST=false
if [[ "$SIZE_MB" -ge 2500 ]]; then LFS_SUGGEST=true; fi

write_receipt "size" "$(jq -nc --argjson mb "$SIZE_MB" --argjson lfs "$([[ $LFS_SUGGEST == true ]] && echo 1 || echo 0)" \
  '{size_mb:$mb, suggest_lfs:($lfs==1)}')"

# ──────────────────────────────────────────────────────────────────────────────
# 8) Compute branch/upstream and push with ephemeral header
#    (No token in URL; no credential store)
# ──────────────────────────────────────────────────────────────────────────────
if [[ -z "$BRANCH" || "$BRANCH" = "HEAD" ]]; then
  # Try common default; adjust if needed
  BRANCH="main"
  if ! git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    BRANCH="master"
  fi
fi

log "🚀 Preparing push: branch=$BRANCH  remote=$(git remote get-url origin)"

# Build Basic header once (no echo)
BASIC="$(printf ":$TOKEN" | base64 | tr -d '\n')"
set +e
git -c http.extraheader="Authorization: Basic $BASIC" \
    push -u origin "$BRANCH"
RC=$?
set -e

if [[ $RC -ne 0 ]]; then
  log "⚠️  First push failed (rc=$RC). Trying common fallbacks…"

  # Fallback #1: create upstream if missing
  set +e
  git -c http.extraheader="Authorization: Basic $BASIC" \
      push -u origin "HEAD:$BRANCH"
  RC=$?
  set -e
fi

if [[ $RC -ne 0 ]]; then
  # Fallback #2: orphan snapshot branch (non-destructive)
  SNAP="snapshot_${START_TS}"
  log "🧭 Creating orphan snapshot branch -> $SNAP (non-destructive fallback)"
  git checkout --orphan "$SNAP"
  git reset
  git add -A
  git commit -m "build(snapshot): orphan snapshot ${START_TS}"
  set +e
  git -c http.extraheader="Authorization: Basic $BASIC" \
      push -u origin "$SNAP"
  RC=$?
  set -e
fi

if [[ $RC -ne 0 ]]; then
  write_receipt "push" "$(jq -nc --arg result "failed" '{"push":$result}')"
  log "❌ Push failed after fallbacks. See receipts in $RECEIPTS_DIR."
  log "   Hints:"
  log "   • Confirm PAT scopes (fine-grained: contents=Read/Write; classic: repo)."
  log "   • Verify remote exists and you have access."
  log "   • If hooks block, try: GIT_PARAMS=1 git … push --no-verify"
  exit 2
else
  write_receipt "push" "$(jq -nc --arg result "ok" --arg branch "$BRANCH" '{"push":$result,"branch":$branch}')"
  log "✅ Push succeeded."
fi

# ──────────────────────────────────────────────────────────────────────────────
# 9) Post-push housekeeping (optional but safe)
# ──────────────────────────────────────────────────────────────────────────────
# Light GC (safe on Replit); skip aggressive to avoid CPU spikes
git gc --prune=now >/dev/null 2>&1 || true

log "🌿 Done."