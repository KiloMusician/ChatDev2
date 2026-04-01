# Git Workflow Guide for NuSyQ-Hub

## Overview
This guide provides simple, practical Git commands for working with the NuSyQ-Hub repository and resolving common issues.

## Repository Status (December 23, 2025)

### Recent Major Changes
- **Large Files Removed**: Cleaned 409MB+ files from Git history using git-filter-repo
- **Master Branch**: Force-pushed with cleaned history
- **Current Status**: All repositories synced with GitHub

### Files Added to .gitignore
```
# Large generated files (too big for GitHub)
function_registry_data.json
COMPLETE_FUNCTION_REGISTRY.md
```

## Common Git Operations

### 1. Check Repository Status
```bash
# See what files are changed
git status

# See current branch
git branch

# See recent commits
git log --oneline -10
```

### 2. Committing Changes
```bash
# Add specific files
git add file1.py file2.py

# Add all changes
git add .

# Commit with message
git commit -m "Your descriptive commit message"

# Commit using our template
git commit -m "$(cat <<'EOF'
Brief description of changes

Detailed explanation of what changed and why.

🤖 Generated with Claude Code (https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 3. Pushing to GitHub
```bash
# Push current branch
git push origin BRANCH_NAME

# Push and set upstream (first time)
git push -u origin BRANCH_NAME

# Force push (use carefully!)
git push origin BRANCH_NAME --force
```

### 4. Pulling from GitHub
```bash
# Pull latest changes from current branch
git pull

# Pull from specific branch
git pull origin master

# Fetch without merging
git fetch origin
```

### 5. Branch Management
```bash
# List all branches
git branch -a

# Create new branch
git checkout -b new-branch-name

# Switch to existing branch
git checkout branch-name

# Delete local branch
git branch -d branch-name

# Delete remote branch
git push origin --delete branch-name
```

### 6. Syncing Forks/Remotes
```bash
# Add upstream remote (if forked)
git remote add upstream https://github.com/ORIGINAL_OWNER/REPO.git

# Fetch from upstream
git fetch upstream

# Merge upstream changes
git merge upstream/master
```

## Troubleshooting Common Issues

### Issue: "File is too large" (> 100MB)

**Solution 1: Add to .gitignore**
```bash
# Add file to .gitignore
echo "large_file.json" >> .gitignore
git add .gitignore
git commit -m "Add large file to .gitignore"
```

**Solution 2: Remove from Git history (if already committed)**
```bash
# Install git-filter-repo
python -m pip install git-filter-repo

# Remove file from entire history
git filter-repo --path large_file.json --invert-paths --force

# Add back remote and force push
git remote add origin https://github.com/KiloMusician/NuSyQ-Hub.git
git push origin BRANCH_NAME --force
```

### Issue: Merge Conflicts

**Solution:**
```bash
# See conflicted files
git status

# Option 1: Keep your changes
git checkout --ours path/to/file

# Option 2: Keep their changes
git checkout --theirs path/to/file

# Option 3: Edit manually, then:
git add path/to/file

# Complete the merge
git commit
```

### Issue: Untracked Files Blocking Operations

**Solution:**
```bash
# Remove specific untracked file
rm -f path/to/file

# Remove all untracked files (CAREFUL!)
git clean -fd

# Preview what would be removed
git clean -fd --dry-run
```

### Issue: Diverged History After Rewrite

**Solution:**
```bash
# If you've rewritten history (like with git-filter-repo)
# and need to sync branches:

# Force update local branch to match remote
git fetch origin
git reset --hard origin/master

# Or force push if local is correct
git push origin master --force
```

### Issue: Stash Conflicts

**Solution:**
```bash
# Save changes temporarily
git stash

# Do your operation (checkout, merge, etc.)

# Apply stash back
git stash pop

# If conflicts, either resolve or drop stash
git stash drop
```

## Best Practices

### 1. Commit Messages
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed explanation
- Reference issues/PRs if applicable
- Include co-author credits when working with AI

### 2. Before Pushing
```bash
# Always check what you're pushing
git status
git diff
git log origin/BRANCH..HEAD --oneline
```

### 3. Working with Large Files
- Use .gitignore to exclude large generated files
- Consider Git LFS for large binary files
- Keep function registries and generated docs out of Git

### 4. Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `codex/description` - AI-assisted development

### 5. Regular Syncing
```bash
# Daily workflow
git fetch origin
git pull origin master
# Work on your changes
git add .
git commit -m "Description"
git push origin your-branch
```

## NuSyQ-Hub Specific Commands

### Check All Three Repositories
```bash
# From NuSyQ-Hub root
git status
cd ../SimulatedVerse && git status
cd ../NuSyQ && git status
```

### Sync All Repositories
```bash
# NuSyQ-Hub
cd c:/Users/keath/Desktop/Legacy/NuSyQ-Hub
git pull origin master
git push origin master

# SimulatedVerse (if it exists)
cd c:/Users/keath/Desktop/Legacy/SimulatedVerse
git pull origin main
git push origin main

# NuSyQ Root (if it exists)
cd c:/Users/keath/Desktop/Legacy/NuSyQ
git pull origin master
git push origin master
```

## Emergency Recovery

### Undo Last Commit (Not Pushed)
```bash
# Keep changes in working directory
git reset --soft HEAD~1

# Discard changes completely
git reset --hard HEAD~1
```

### Undo Force Push (If Needed)
```bash
# Find the old commit
git reflog

# Reset to old commit
git reset --hard OLD_COMMIT_HASH

# Force push back
git push origin master --force
```

### Recover Deleted Branch
```bash
# Find the commit
git reflog

# Recreate branch
git checkout -b recovered-branch COMMIT_HASH
```

## Quick Reference Card

```bash
# Status
git status              # What's changed
git branch             # What branch am I on
git log --oneline -5   # Recent commits

# Save Work
git add .              # Stage all changes
git commit -m "msg"    # Commit
git push               # Push to GitHub

# Get Updates
git fetch              # Download updates
git pull               # Download and merge
git pull --rebase      # Download and replay

# Branches
git checkout -b new    # Create branch
git checkout existing  # Switch branch
git branch -d old      # Delete branch

# Emergency
git stash              # Save work temporarily
git reset --hard       # Discard all changes
git reflog             # Find lost commits
```

## Getting Help

### Git Documentation
```bash
# Help for any command
git help COMMAND
git COMMAND --help

# Examples
git help commit
git help push
```

### Repository Issues
If you encounter persistent Git issues:
1. Check [GitHub Issues](https://github.com/KiloMusician/NuSyQ-Hub/issues)
2. Ask Claude Code for assistance
3. Consult Git documentation: https://git-scm.com/doc

## Glossary

- **Repository**: The project folder tracked by Git
- **Commit**: A saved snapshot of your changes
- **Branch**: An independent line of development
- **Remote**: The GitHub copy of your repository
- **Origin**: The default name for your GitHub remote
- **HEAD**: Pointer to your current commit
- **Staging**: Preparing files for commit (git add)
- **Push**: Send commits to GitHub
- **Pull**: Get commits from GitHub
- **Fetch**: Download commits without merging
- **Merge**: Combine branches
- **Rebase**: Replay commits on top of another branch
- **Stash**: Temporary storage for changes
- **Conflict**: When Git can't automatically merge changes
- **Force Push**: Overwrite remote history (use carefully!)

---

**Last Updated**: December 23, 2025
**Repository**: NuSyQ-Hub
**Maintainer**: KiloMusician
**Contributors**: Claude Sonnet 4.5
