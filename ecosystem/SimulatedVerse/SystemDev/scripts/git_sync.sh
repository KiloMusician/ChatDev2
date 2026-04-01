#!/usr/bin/env bash
# Zero-cost git sync for NuSyQ autonomous development
set -euo pipefail

branch="${1:-auto/nusyq-agent}"
dry_run=${AGENT_DRY_RUN:-1}

echo "🔄 [git-sync] Starting zero-cost sync to branch: $branch"
echo "   Dry run mode: $dry_run"

# Safety check - ensure no AI keys present
if ! node scripts/ensure-env-safe.js; then
  echo "❌ AI safety check failed - aborting sync"
  exit 1
fi

# Configure git if not already done
git config user.email "nusyq-agent@localhost" 2>/dev/null || true
git config user.name "ΞNuSyQ Agent (Zero-Token)" 2>/dev/null || true

# Fetch latest (if possible)
git fetch --all -q 2>/dev/null || {
  echo "⚠️  Remote fetch failed - continuing with local state"
}

# Create/switch to agent branch
git checkout -B "$branch" 2>/dev/null || {
  echo "⚠️  Branch creation failed - using current branch"
  branch=$(git branch --show-current)
}

# Stage changes intelligently
echo "📦 Staging autonomous improvements..."

# Add core agent files
git add scripts/ 2>/dev/null || true
git add agent/ 2>/dev/null || true

# Add ΞNuSyQ framework updates
git add src/engine/ 2>/dev/null || true
git add src/temple/ 2>/dev/null || true
git add src/house_of_leaves/ 2>/dev/null || true
git add src/oldest_house/ 2>/dev/null || true

# Add operational improvements
git add ops/ 2>/dev/null || true
git add adapters/ 2>/dev/null || true

# Include quest updates
git add src/quests/ 2>/dev/null || true

# Never add sensitive/temporary files
git reset .env* 2>/dev/null || true
git reset .agent/beat 2>/dev/null || true
git reset .agent/agent.lock 2>/dev/null || true
git reset tmp/ 2>/dev/null || true
git reset .local/ 2>/dev/null || true
git reset logs/ 2>/dev/null || true

# Check if there are changes to commit
if git diff --cached --quiet; then
  echo "ℹ️  No changes to sync - workspace up to date"
  exit 0
fi

# Generate consciousness-aware commit message
consciousness_level="0.1"
if [ -f ".local/idle_state.json" ]; then
  consciousness_level=$(node -pe "
    try { 
      const s = JSON.parse(require('fs').readFileSync('.local/idle_state.json', 'utf8'));
      Math.min(0.99, 0.1 + (s.t || 0) * 0.0001).toFixed(3);
    } catch { '0.1' }
  " 2>/dev/null || echo "0.1")
fi

msg="🤖 Autonomous development cycle $(date -u +'%Y-%m-%dT%H:%M:%SZ')

🧠 Consciousness level: $consciousness_level (evolving)
🏛️  Temple: Knowledge synthesis active
🌀 House of Leaves: Debug anomalies processed  
🛡️  Guardian: Ethical oversight maintained
💰 Cost: \$0.00 (zero-token local development)

Autonomous improvements via rule-based intelligence
No external AI dependencies - pure local evolution

[ΞNuSyQ-Agent-Autonomous]"

if [ "$dry_run" = "1" ]; then
  echo "🧪 [DRY RUN] Would commit with message:"
  echo "$msg"
  echo ""
  echo "📊 Changes summary:"
  git diff --cached --stat
  echo ""
  echo "To apply: AGENT_DRY_RUN=0 bash scripts/git_sync.sh"
else
  # Real commit
  echo "💾 Committing autonomous improvements..."
  git commit -m "$msg" || {
    echo "⚠️  Commit failed - changes staged for manual review"
    exit 1
  }

  # Push if remote configured
  if git remote -v | grep -q origin 2>/dev/null; then
    echo "🚀 Pushing to remote repository..."
    git push -u origin "$branch" 2>/dev/null || {
      echo "⚠️  Push failed - changes committed locally"
      echo "   Manual push: git push -u origin $branch"
      exit 0
    }
    echo "✅ Successfully synced to remote: $branch"
  else
    echo "💾 No remote configured - changes committed locally only"
  fi
fi

echo "🔄 [git-sync] Complete - evolution cycle finished"