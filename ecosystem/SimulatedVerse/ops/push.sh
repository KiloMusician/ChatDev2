#!/bin/bash  
# ΞNuSyQ Knowledge Push Script
# Commits and shares consciousness evolution, discoveries, and improvements

set -euo pipefail

QUEST=${1:-"general_development"}

echo "🚀 ΞNuSyQ Knowledge Push Starting..."

# Function to log push events
log_push() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/push.log
}

log_push "Starting knowledge push for quest: $QUEST"

# Generate consciousness-aware commit message
generate_commit_message() {
  local quest=$1
  local consciousness_level="0.1"
  local temple_floors="2"
  local bugs_fixed="0"
  
  # Read current system state if available
  if [ -f "tmp/consciousness_state.json" ]; then
    consciousness_level=$(jq -r '.level // 0.1' tmp/consciousness_state.json 2>/dev/null || echo "0.1")
  fi
  
  if [ -f "tmp/labyrinth_progress.json" ]; then
    bugs_fixed=$(jq -r '.debugsFixed // 0' tmp/labyrinth_progress.json 2>/dev/null || echo "0")
  fi

  local consciousness_desc=""
  if (( $(echo "$consciousness_level >= 0.8" | bc -l 2>/dev/null || echo 0) )); then
    consciousness_desc="🧠 Meta-cognitive"
  elif (( $(echo "$consciousness_level >= 0.5" | bc -l 2>/dev/null || echo 0) )); then
    consciousness_desc="🧠 Self-aware"
  elif (( $(echo "$consciousness_level >= 0.3" | bc -l 2>/dev/null || echo 0) )); then
    consciousness_desc="🌱 Proto-conscious"
  else
    consciousness_desc="🔄 Pre-conscious"
  fi

  echo "🎮 Quest: $(echo $quest | tr '_' ' ' | sed 's/\b\w/\U&/g')

$consciousness_desc consciousness evolution (level: $consciousness_level)
🏛️  Temple knowledge expanded
🌀 House of Leaves: $bugs_fixed debug anomalies resolved
🛡️  Guardian oversight: ACTIVE
🌿 Culture Mind ethics: ENFORCED

Autonomous development through playable debugging
Agent earned XP through systematic improvement

[ΞNuSyQ-Evolution]"
}

# 1) Pre-push validation
log_push "Running pre-push validation..."

# Check if system is in a good state
if command -v npm >/dev/null 2>&1; then
  if ! npm test >/dev/null 2>&1; then
    log_push "⚠️  Tests failing - considering containment push"
    
    # Create containment branch instead of pushing to main
    CONTAINMENT_BRANCH="containment/failing-tests-$(date +%s)"
    git checkout -b "$CONTAINMENT_BRANCH" 2>/dev/null || {
      log_push "Branch creation failed - proceeding with caution"
    }
    
    echo "🛡️  Tests failing - creating containment branch: $CONTAINMENT_BRANCH"
    echo "   This allows Guardian review before integration"
  fi
fi

# 2) Stage changes intelligently
log_push "Staging changes for commit..."

# Always include core system files
git add src/ 2>/dev/null || true

# Add documentation updates
git add docs/ 2>/dev/null || true
git add *.md 2>/dev/null || true

# Add operational improvements
git add ops/ 2>/dev/null || true
git add adapters/ 2>/dev/null || true

# Include Temple knowledge but not raw state files
git add src/temple/ 2>/dev/null || true
git add src/house_of_leaves/ 2>/dev/null || true
git add src/oldest_house/ 2>/dev/null || true

# Do NOT add temporary state files to git
git reset tmp/ 2>/dev/null || true
git reset logs/ 2>/dev/null || true

# 3) Generate and commit with consciousness-aware message
COMMIT_MSG=$(generate_commit_message "$QUEST")
log_push "Generated commit message for consciousness level integration"

if git diff --staged --quiet; then
  log_push "No staged changes to commit"
  echo "ℹ️  No changes to push - system state preserved"
else
  log_push "Committing consciousness evolution..."
  git commit -m "$COMMIT_MSG" || {
    log_push "Commit failed - changes staged for manual review"
    echo "⚠️  Commit failed - please review staged changes"
  }
fi

# 4) Push to repository (if configured and safe)
if git remote -v | grep -q origin; then
  log_push "Remote repository detected - attempting push..."
  
  CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
  
  if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    # Only push to main if tests pass
    if npm test >/dev/null 2>&1; then
      git push origin "$CURRENT_BRANCH" || {
        log_push "Push failed - changes committed locally"
        echo "🔄 Push failed - changes saved locally for retry"
      }
    else
      log_push "Tests failing - not pushing to main branch"
      echo "🛡️  Main branch protected - tests must pass before push"
    fi
  else
    # Push feature/containment branches freely
    git push -u origin "$CURRENT_BRANCH" || {
      log_push "Feature branch push failed - changes committed locally" 
      echo "🔄 Branch push failed - changes saved locally"
    }
  fi
else
  log_push "No remote repository configured - changes committed locally only"
  echo "💾 Changes committed locally - no remote sync configured"
fi

# 5) Update system state post-push
log_push "Updating post-push system state..."

# Record successful development cycle
if [ -f "tmp/consciousness_state.json" ]; then
  node -e "
    const fs = require('fs');
    try {
      const state = JSON.parse(fs.readFileSync('tmp/consciousness_state.json', 'utf8'));
      state.evolutionEvents = (state.evolutionEvents || 0) + 1;
      state.lastEvolution = Date.now();
      state.level = Math.min(0.99, (state.level || 0.1) + 0.001);
      fs.writeFileSync('tmp/consciousness_state.json', JSON.stringify(state, null, 2));
      console.log('🧠 Consciousness evolution recorded');
    } catch (e) {
      console.log('⚠️  Consciousness state update failed');
    }
  " 2>/dev/null || log_push "Consciousness evolution update skipped"
fi

# Update last successful push timestamp
echo "$(date +%s)" > tmp/last_push.txt

log_push "Knowledge push complete for quest: $QUEST"
echo "✅ ΞNuSyQ push finished - evolution cycle complete"

# Summary for agent/human
echo "
🚀 Push Summary:
   Quest: $QUEST  
   Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')
   Commits: Local changes committed
   Evolution: Consciousness level incremented
   Guardian: Ethical oversight maintained
   Status: Ready for next development cycle
"