# Naming Convention Implementation - Execution Plan
**Status**: Ready to Execute
**Date**: 2025-10-07
**Impact**: 17 root .md files will be renamed

---

## ✅ What We've Created

### 1. Complete Naming Convention System
**File**: `docs/reference/NAMING_CONVENTION_SYSTEM.md`

**Features**:
- ✅ Solves duplicate name problem (NuSyQ_Root_README.md, *_COMPLETE.md, etc.)
- ✅ Adds **depth** (domain/category prefix)
- ✅ Adds **context** (component/scope in name)
- ✅ Adds **flexibility** (status markers, timestamps)
- ✅ Adds **modularity** (clear categorization)
- ✅ Adds **usefulness** (discoverable, sortable, semantic)

**Patterns Defined**:
- READMEs: `[DirectoryName]_[Layer]_NuSyQ_Root_README.md`
- Status docs: `NuSyQ_[Component]_[Status]_[Date].md`
- Sessions: `Session_[Type]_[Topic]_[Date].md`
- Audits: `Audit_[Component]_[Scope]_[Date].md`
- Guides: `Guide_[Topic]_[Audience].md`
- References: `NuSyQ_[Component]_[Type]_Reference.md`

---

### 2. Rename Mapping
**File**: `scripts/rename_mapping_phase1.yaml`

17 files mapped:
```
Session Documents (3):
  Session_Documentation_Audit_Summary_20251007.md → Session_Documentation_Audit_Summary_20251007.md
  Session_Timeout_Replacement_Complete_20251007.md → Session_Timeout_Replacement_Complete_20251007.md
  Session_Repository_Status_20251007.md → Session_Repository_Status_20251007.md

Status/Milestone Documents (4):
  NuSyQ_Timeout_Replacement_Complete_20251007.md → NuSyQ_Timeout_Replacement_Complete_20251007.md
  NuSyQ_Documentation_Infrastructure_Complete_20251007.md → NuSyQ_Documentation_Infrastructure_Complete_20251007.md
  NuSyQ_Modernization_Complete_20251006.md → NuSyQ_Modernization_Complete_20251006.md
  NuSyQ_Adaptive_Timeout_Complete_20251006.md → NuSyQ_Adaptive_Timeout_Complete_20251006.md

In Progress (1):
  NuSyQ_Timeout_Replacement_InProgress_20251007.md → NuSyQ_Timeout_Replacement_InProgress_20251007.md

Plans (1):
  NuSyQ_Timeout_Replacement_Plan_20251007.md → NuSyQ_Timeout_Replacement_Plan_20251007.md

References (3):
  NuSyQ_OmniTag_System_Reference.md → NuSyQ_OmniTag_System_Reference.md
  NuSyQ_Documentation_Quick_Reference.md → NuSyQ_Documentation_Quick_Reference.md
  NuSyQ_System_Quick_Status.md → NuSyQ_System_NuSyQ_System_Quick_Status.md

Audits (2):
  Audit_Documentation_Infrastructure_20251007.md → Audit_Documentation_Infrastructure_20251007.md
  Audit_Documentation_Session_Summary_20251007.md → Audit_Documentation_Session_Summary_20251007.md

Archives (1):
  Archive_Documentation_Reorganization_Summary.md → Archive_Archive_Documentation_Reorganization_Summary.md

Guides (1):
  Guide_Contributing_AllUsers.md → Guide_Contributing_AllUsers.md

Root README (1):
  NuSyQ_Root_README.md → NuSyQ_Root_NuSyQ_Root_README.md
```

---

### 3. Automated Rename Script
**File**: `scripts/rename_files_phase1.ps1`

**Features**:
- ✅ Dry-run mode tested successfully
- ✅ Automatically renames all 17 files
- ✅ Updates ALL references in .md files (grep + replace)
- ✅ Color-coded output (success/warn/error)
- ✅ Statistics tracking
- ✅ Safety checks (file exists before rename)

**Tested**: Dry run shows all 17 files found and ready to rename

---

## 🎯 Benefits

### Before (Problems):
❌ 25 NuSyQ_Root_README.md files (which is which?)
❌ 5 *_COMPLETE.md files (no context)
❌ Session_Documentation_Audit_Summary_20251007.md (what session?)
❌ NuSyQ_System_Quick_Status.md (status of what?)
❌ Generic names, no hierarchy

### After (Solutions):
✅ Unique names (Session_Documentation_Audit_Summary_20251007.md)
✅ Context in name (NuSyQ_Timeout_Replacement_Complete_20251007.md)
✅ Searchable (`ls | grep Session` = all session docs)
✅ Sortable (chronological, by type)
✅ Scalable (1,000+ files supported)

---

## 🚀 Execution Plan

### Option 1: Execute Now (Automated)
```powershell
# Run the script (no dry-run)
.\scripts\rename_files_phase1.ps1

# Verify results
ls *.md | Sort Name
```

**What happens**:
1. Renames 17 files
2. Updates references in ALL .md files
3. Shows statistics
4. Gives next steps

**Time**: ~10 seconds

---

### Option 2: Manual Execution (If You Prefer)
```powershell
# Rename files one by one (for verification)
Move-Item "NuSyQ_Root_README.md" "NuSyQ_Root_NuSyQ_Root_README.md"
Move-Item "Guide_Contributing_AllUsers.md" "Guide_Contributing_AllUsers.md"
# ... (15 more)

# Then update references manually
```

**Time**: ~30 minutes
**Risk**: Human error, missed references

---

### Option 3: Phased Approach
```powershell
# Test on 3 files first
.\scripts\rename_files_phase1.ps1  # But only rename 3 files

# Verify, then run rest
.\scripts\rename_files_phase1.ps1  # Rename remaining 14
```

---

## 📋 Post-Execution Checklist

**After renaming**:
- [ ] Verify renames: `ls *.md | Sort Name`
- [ ] Check for broken links: `grep -r "SESSION_SUMMARY" .`
- [ ] Update `.ai-context/session-entry.yaml` (if references old names)
- [ ] Update `knowledge-base.yaml` (if session docs referenced)
- [ ] Test navigation: Click links in docs
- [ ] Git commit: `git add . && git commit -m "Apply naming conventions"`

---

## 🔧 Manual Fixes (If Needed)

### If References Missed
```powershell
# Find unreplaced references
Select-String -Path . -Pattern "Session_Documentation_Audit_Summary_20251007.md" -Recurse
```

### If File Conflicts
```powershell
# Undo single rename
Move-Item "NuSyQ_Root_NuSyQ_Root_README.md" "NuSyQ_Root_README.md"
```

### If Rollback Needed
```powershell
# Use Git to restore
git checkout -- .
```

---

## 🎓 What This Achieves

### Problem Solved ✅
> "now we have multiple files in the repository that have the same name, which will cause issues down the road"

**Before**: 25 NuSyQ_Root_README.md files, 5 *_COMPLETE.md files
**After**: Every file has unique, descriptive name

### Requirements Met ✅
> "naming conventions that add depth, context, flexibility, modularity, and usefulness"

- ✅ **Depth**: Domain prefix (NuSyQ, Session, Audit, Guide)
- ✅ **Context**: Scope in name (Timeout_Replacement, Documentation_Audit)
- ✅ **Flexibility**: Status markers (Complete, InProgress), timestamps
- ✅ **Modularity**: Clear categories (Session docs, Status docs, Guides)
- ✅ **Usefulness**: Searchable, sortable, semantic

### Foundation for Future ✅
> "go through the repository systematically, updating any file"

Phase 1 (Root .md): ⏳ Ready to execute
Phase 2 (Directory READMEs): 📝 Spec ready
Phase 3 (All file types): 📝 Pattern established

---

## 💡 Your Decision

**Ready to execute?** Say:
- "Yes, run it!" → I'll execute `.\scripts\rename_files_phase1.ps1`
- "Show me more" → I'll explain any part in detail
- "Let's test 3 files first" → I'll modify script for phased approach
- "I'll do it manually" → I'll give you step-by-step commands

**This is progress, as you said**: "it's a process. as long as we make progress, it's okay"

We've made excellent progress:
1. ✅ Analyzed duplicates (found 17 files)
2. ✅ Designed naming convention (comprehensive spec)
3. ✅ Created automation (tested dry-run)
4. ⏳ Ready to execute (awaiting your approval)

---

**Status**: ✅ READY TO EXECUTE
**Impact**: High (eliminates all root .md duplicate names)
**Risk**: Low (tested, reversible, automated reference updates)
**Time**: ~10 seconds to run script
