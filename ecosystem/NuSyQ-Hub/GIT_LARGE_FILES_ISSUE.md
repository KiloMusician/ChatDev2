# Git Large Files Issue - Action Required

**Date**: December 16, 2025
**Status**: 🔴 **BLOCKING PUSH TO REMOTE**

---

## Problem

Cannot push commits to GitHub due to large files in git history:
- `COMPLETE_FUNCTION_REGISTRY.md` (50.50 MB)
- `function_registry_data.json` (409.81 MB)

These files were committed in earlier history (commit `98547cb`) and exceed GitHub's limits.

---

## Impact

- ✅ **Local development**: Can continue normally
- ✅ **Local commits**: Working fine
- ❌ **Push to remote**: Blocked
- ❌ **Collaboration**: Cannot share changes
- ❌ **Backup**: Remote not updated

---

## Solutions

### Option A: BFG Repo-Cleaner (Recommended)
```bash
# Install BFG
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Clean repository
java -jar bfg.jar --delete-files COMPLETE_FUNCTION_REGISTRY.md
java -jar bfg.jar --delete-files function_registry_data.json

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: rewrites history)
git push origin codex/add-friendly-diagnostics-ci --force
```

### Option B: git filter-branch
```bash
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch COMPLETE_FUNCTION_REGISTRY.md function_registry_data.json" \
  --prune-empty --tag-name-filter cat -- --all

git push origin codex/add-friendly-diagnostics-ci --force
```

### Option C: New Clean Branch (Safest)
```bash
# Create new branch from current state
git checkout -b codex/clean-branch

# Ensure large files are gitignored
echo "COMPLETE_FUNCTION_REGISTRY.md" >> .gitignore
echo "function_registry_data.json" >> .gitignore
echo "**/function_registry*.json" >> .gitignore

# Commit gitignore
git add .gitignore
git commit -m "Add large files to gitignore"

# Push new clean branch
git push origin codex/clean-branch
```

---

## Current Workaround

**For now, continuing with local development**:
- All work is committed locally
- Proceeding with Phases 2-3
- Will resolve git issue before final push

**Files added to .gitignore**:
- `COMPLETE_FUNCTION_REGISTRY.md`
- `function_registry_data.json`
- `**/function_registry*.json`

---

## Action Required

**Before final deployment:**
1. Choose solution (Option C recommended for safety)
2. Execute cleanup
3. Verify push works
4. Update remote branch

**Alternative**: If these registry files are needed, consider:
- Moving to Git LFS (Large File Storage)
- Storing in separate data repository
- Using external storage (S3, Azure Blob, etc.)

---

## Notes

- Local repository is clean and functional
- All recent work (Batches 1-6) committed locally
- Development can continue uninterrupted
- This only affects remote synchronization

---

**Status**: Documented, workaround in place, can proceed with development
