#!/bin/bash
# ΞNuSyQ Consolidation Rollback Script
# Generated: 2025-08-27T16:55:17.542673

set -e

echo "🔄 Rolling back consolidation changes..."

# Restore from backup
if [ -d ".ops/backups/20250827-165517" ]; then
    echo "📁 Restoring files from backup..."
    cp -r .ops/backups/20250827-165517/* . 2>/dev/null || true
fi

# Reset git to last good state (if commits were made)
echo "⏪ Resetting git state..."
git status --porcelain | wc -l > /tmp/git_changes
if [ $(cat /tmp/git_changes) -gt 0 ]; then
    git stash push -m "rollback-stash-20250827-165517" || true
fi

echo "✅ Rollback complete"
echo "💡 Check git log and restore any needed commits manually"
