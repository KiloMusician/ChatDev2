<!--
╔══════════════════════════════════════════════════════════════════════════╗
║ ΞNuSyQ OmniTag Metadata                                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║ FILE-ID: nusyq.docs.reference.naming-conventions                        ║
║ TYPE: Markdown Document                                                 ║
║ STATUS: Production                                                      ║
║ VERSION: 1.0.0                                                          ║
║ TAGS: [documentation, standards, naming, conventions, architecture]     ║
║ CONTEXT: Σ∆ (Meta Layer)                                               ║
║ AGENTS: [AllAgents]                                                     ║
║ DEPS: [OMNITAG_SPECIFICATION.md, FILE_ORGANIZATION_STRATEGY.md]        ║
║ INTEGRATIONS: [ΞNuSyQ-Framework]                                        ║
║ CREATED: 2025-10-07                                                     ║
║ UPDATED: 2025-10-07                                                     ║
║ AUTHOR: Claude Code                                                     ║
║ STABILITY: High (Production Ready)                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
-->

# NuSyQ Naming Convention System
## Comprehensive File, Directory, and Sector Naming Standards

**Version**: 1.0.0
**Status**: Active Standard
**Last Updated**: 2025-10-07
**Purpose**: Eliminate duplicate names, add depth/context, enable scalability

---

## 🎯 Problem Statement

**Current Issues**:
- ✅ **25 NuSyQ_Root_README.md files** (confusing which is which)
- ✅ **5 *_COMPLETE.md files** in root (no differentiation)
- ✅ **Multiple *_SUMMARY.md files** (unclear scope)
- ⚠️ **No systematic naming for status docs** (complete, summary, audit, etc.)

**Goal**: Create **unique, contextual, hierarchical** names that:
1. Add depth (domain, category, status, timestamp)
2. Prevent collisions (no duplicate names anywhere)
3. Enable discovery (semantic search via name)
4. Support modularity (clear file relationships)
5. Scale gracefully (new files fit pattern)

---

## 📋 Naming Convention Structure

### Core Pattern

```
[DOMAIN]_[CATEGORY]_[COMPONENT]_[STATUS]_[TIMESTAMP].ext

Components (all optional except COMPONENT):
- DOMAIN: nusyq, docs, config, test, etc.
- CATEGORY: session, audit, guide, reference, etc.
- COMPONENT: specific subject (timeout, documentation, agents)
- STATUS: complete, inprogress, draft, archived
- TIMESTAMP: YYYYMMDD or YYYYMMDD-HHMM for sessions
```

### Examples

**BEFORE** (Ambiguous):
- `NuSyQ_Root_README.md` (which one?)
- `NuSyQ_Timeout_Replacement_Complete_20251007.md` (what domain?)
- `Session_Documentation_Audit_Summary_20251007.md` (what session?)

**AFTER** (Clear):
- `NuSyQ_Root_NuSyQ_Root_README.md` (root README)
- `Config_Core_NuSyQ_Root_README.md` (config directory README)
- `NuSyQ_Timeout_Replacement_Complete_20251007.md`
- `Session_Documentation_Audit_Summary_20251007.md`

---

## 📂 File Type Naming Patterns

### 1. README Files (Directory Documentation)

**Pattern**: `[DirectoryName]_[Layer]_NuSyQ_Root_README.md`

```
Root Level:
  NuSyQ_Root_NuSyQ_Root_README.md                      (was: NuSyQ_Root_README.md)

Directory Level:
  Config_Core_NuSyQ_Root_README.md                     (was: config/NuSyQ_Root_README.md)
  Scripts_Automation_NuSyQ_Root_README.md              (was: scripts/NuSyQ_Root_README.md)
  Tests_QA_NuSyQ_Root_README.md                        (was: tests/NuSyQ_Root_README.md)
  Examples_Demos_NuSyQ_Root_README.md                  (was: examples/NuSyQ_Root_README.md)
  State_Persistence_NuSyQ_Root_README.md               (was: State/NuSyQ_Root_README.md)
  Docs_Navigation_INDEX.md                  (was: docs/INDEX.md)
  MCP_Server_Integration_NuSyQ_Root_README.md          (was: mcp_server/NuSyQ_Root_README.md)
  ChatDev_Framework_NuSyQ_Root_README.md               (was: ChatDev/NuSyQ_Root_README.md)
  Godot_Integration_NuSyQ_Root_README.md               (was: GODOT/NuSyQ_Root_README.md)
```

**Rule**: READMEs stay IN their directories but get unique names

---

### 2. Status/Milestone Documents

**Pattern**: `[Domain]_[Component]_[Status]_[Date].md`

```
Implementation Complete:
  NuSyQ_Timeout_Replacement_Complete_20251007.md
    (was: NuSyQ_Timeout_Replacement_Complete_20251007.md)

  NuSyQ_Documentation_Infrastructure_Complete_20251007.md
    (was: NuSyQ_Documentation_Infrastructure_Complete_20251007.md)

  NuSyQ_Modernization_Complete_20251006.md
    (was: NuSyQ_Modernization_Complete_20251006.md)

In Progress:
  NuSyQ_Timeout_Replacement_InProgress_20251007.md
    (was: NuSyQ_Timeout_Replacement_InProgress_20251007.md)

Plans:
  NuSyQ_Timeout_Replacement_Plan_20251007.md
    (was: NuSyQ_Timeout_Replacement_Plan_20251007.md)
```

**Status Values**:
- `Complete` - Finished work
- `InProgress` - Active work
- `Plan` - Planning document
- `Draft` - Early stage
- `Archived` - Historical record

---

### 3. Session Documents

**Pattern**: `Session_[Type]_[Topic]_[Date].md` OR `Session_[Topic]_[Type]_[Date].md`

```
Summaries:
  Session_Documentation_Audit_Summary_20251007.md
    (was: Session_Documentation_Audit_Summary_20251007.md)

  Session_Documentation_Audit_Complete_20251007.md
    (was: Session_Timeout_Replacement_Complete_20251007.md)

Status Reports:
  Session_Repository_Status_20251007.md
    (was: Session_Repository_Status_20251007.md)
```

**Session Types**:
- `Summary` - Overview of session work
- `Complete` - Session completion report
- `Status` - Status snapshot
- `Audit` - Audit/analysis session
- `Implementation` - Implementation session

---

### 4. Reference Documents

**Pattern**: `[Domain]_[Component]_[Type]_Reference.md`

```
System References:
  NuSyQ_OmniTag_System_Reference.md
    (was: NuSyQ_OmniTag_System_Reference.md)

  NuSyQ_Naming_Convention_Reference.md
    (this document)

Quick References:
  NuSyQ_Documentation_Quick_Reference.md
    (was: NuSyQ_Documentation_Quick_Reference.md)

  NuSyQ_System_NuSyQ_System_Quick_Status.md
    (was: NuSyQ_System_Quick_Status.md)
```

---

### 5. Audit/Analysis Documents

**Pattern**: `Audit_[Component]_[Scope]_[Date].md`

```
Audits:
  Audit_Documentation_Infrastructure_20251007.md
    (was: Audit_Documentation_Infrastructure_20251007.md)

  Audit_Repository_Health_20251007.md

  Audit_Code_Quality_20251006.md
```

---

### 6. Contributing/Guide Documents

**Pattern**: `Guide_[Topic]_[Audience].md` OR `[Domain]_[Topic]_Guide.md`

```
Guides:
  Guide_Contributing_AllUsers.md
    (was: Guide_Contributing_AllUsers.md)

  Guide_ChatDev_Integration.md
    (was: NUSYQ_CHATDEV_GUIDE.md)

Archives:
  Archive_Improvements_Summary.md
    (was: ARCHIVE_IMPROVEMENTS_SUMMARY.md)

  Archive_Archive_Documentation_Reorganization_Summary.md
    (was: Archive_Documentation_Reorganization_Summary.md)
```

---

## 🗂️ Directory Naming Patterns

### Current Directories (Keep As-Is - Already Good)

```
✅ config/           - Short, clear, standard
✅ scripts/          - Standard
✅ tests/            - Standard
✅ examples/         - Standard
✅ docs/             - Standard
✅ mcp_server/       - Descriptive, clear
✅ ChatDev/          - External submodule
✅ GODOT/            - External integration
```

### Subdirectory Patterns

**Pattern**: `[parent]_[specific_purpose]` OR just `[specific_purpose]`

```
docs/ subdirectories:
  docs/guides/           ✅ Clear
  docs/reference/        ✅ Clear
  docs/sessions/         ✅ Clear
  docs/archive/          ✅ Clear (if created)

config/ subdirectories (if needed):
  config/agents/         - Agent configurations
  config/templates/      - Config templates
  config/schemas/        - Validation schemas

tests/ subdirectories:
  tests/integration/     ✅ Already clear
  tests/unit/            - If needed
  tests/e2e/             - If needed
```

---

## 🏷️ OmniTag FILE-ID Mapping

**FILE-ID should match filename pattern**:

```
Filename: NuSyQ_Timeout_Replacement_Complete_20251007.md
FILE-ID:  nusyq.docs.session.timeout-replacement-complete-20251007

Filename: Config_Core_NuSyQ_Root_README.md
FILE-ID:  nusyq.docs.directory.config-core-readme

Filename: Guide_Contributing_AllUsers.md
FILE-ID:  nusyq.docs.guide.contributing-allusers
```

**Pattern**: `nusyq.[category].[type].[component-from-filename]`

---

## 📊 Renaming Strategy (Phased Approach)

### Phase 1: Root-Level .md Files (FIRST PRIORITY)

**Target**: 30+ root-level .md files

**Process**:
1. List all root .md files
2. Categorize (status, session, audit, guide, reference)
3. Apply naming convention
4. Update all references (grep for old names)
5. Test (verify no broken links)

**Example Renames**:
```powershell
# Session documents
Session_Documentation_Audit_Summary_20251007.md
  → Session_Documentation_Audit_Summary_20251007.md

Session_Timeout_Replacement_Complete_20251007.md
  → Session_Timeout_Replacement_Complete_20251007.md

Session_Repository_Status_20251007.md
  → Session_Repository_Status_20251007.md

# Status documents
NuSyQ_Timeout_Replacement_Complete_20251007.md
  → NuSyQ_Timeout_Replacement_Complete_20251007.md

NuSyQ_Documentation_Infrastructure_Complete_20251007.md
  → NuSyQ_Documentation_Infrastructure_Complete_20251007.md

NuSyQ_Modernization_Complete_20251006.md
  → NuSyQ_Modernization_Complete_20251006.md

# Reference documents
NuSyQ_OmniTag_System_Reference.md
  → NuSyQ_OmniTag_System_Reference.md

NuSyQ_Documentation_Quick_Reference.md
  → NuSyQ_Documentation_Quick_Reference.md

NuSyQ_System_Quick_Status.md
  → NuSyQ_System_NuSyQ_System_Quick_Status.md

# Guides
Guide_Contributing_AllUsers.md
  → Guide_Contributing_AllUsers.md

NUSYQ_CHATDEV_GUIDE.md
  → Guide_ChatDev_Integration.md

# Audits
Audit_Documentation_Infrastructure_20251007.md
  → Audit_Documentation_Infrastructure_20251007.md

# Plans/Progress
NuSyQ_Timeout_Replacement_InProgress_20251007.md
  → NuSyQ_Timeout_Replacement_InProgress_20251007.md

NuSyQ_Timeout_Replacement_Plan_20251007.md
  → NuSyQ_Timeout_Replacement_Plan_20251007.md

# Archives
ARCHIVE_IMPROVEMENTS_SUMMARY.md
  → Archive_Improvements_Summary_20251006.md

Archive_Documentation_Reorganization_Summary.md
  → Archive_Documentation_Reorganization_Summary_20251006.md
```

---

### Phase 2: Directory README Files (SECOND PRIORITY)

**Keep READMEs IN directories** but rename for uniqueness:

```powershell
# Rename IN PLACE (stay in directories)
config/NuSyQ_Root_README.md
  → config/Config_Core_NuSyQ_Root_README.md

scripts/NuSyQ_Root_README.md
  → scripts/Scripts_Automation_NuSyQ_Root_README.md

tests/NuSyQ_Root_README.md
  → tests/Tests_QA_NuSyQ_Root_README.md

examples/NuSyQ_Root_README.md
  → examples/Examples_Demos_NuSyQ_Root_README.md

State/NuSyQ_Root_README.md
  → State/State_Persistence_NuSyQ_Root_README.md

mcp_server/NuSyQ_Root_README.md
  → mcp_server/MCP_Server_Integration_NuSyQ_Root_README.md

# Root README needs context too
NuSyQ_Root_README.md
  → NuSyQ_Root_NuSyQ_Root_README.md
```

**Update references in**:
- All .md files that link to READMEs
- docs/INDEX.md (navigation hub)
- `.ai-context/` files

---

### Phase 3: Python Files (If Needed)

**Current Python files are fine** (no duplicates detected):
- `config/multi_agent_session.py` ✅
- `config/ai_council.py` ✅
- `scripts/search_omnitags.py` ✅

**Only rename if**:
- Duplicate names appear
- Module imports break
- Clarity severely lacking

---

### Phase 4: Update All References

**Tools**:
```powershell
# Find all references to old name
grep -r "old_filename.md" .

# PowerShell equivalent
Select-String -Path . -Pattern "old_filename.md" -Recurse
```

**Files to check**:
- All .md files (links, references)
- Python files (docstrings, comments)
- .ai-context/ files (session history)
- knowledge-base.yaml (session logs)
- docs/INDEX.md (navigation)

---

## 🔧 Implementation Tools

### Renaming Script Template

```powershell
# scripts/rename_files_systematic.ps1

# Phase 1: Root .md files
$renames = @{
    "Session_Documentation_Audit_Summary_20251007.md" = "Session_Documentation_Audit_Summary_20251007.md"
    "NuSyQ_Timeout_Replacement_Complete_20251007.md" = "NuSyQ_Timeout_Replacement_Complete_20251007.md"
    # ... more mappings
}

foreach ($old in $renames.Keys) {
    $new = $renames[$old]
    if (Test-Path $old) {
        Write-Host "Renaming: $old → $new" -ForegroundColor Green
        Move-Item $old $new
    }
}

# Update references
foreach ($file in Get-ChildItem -Recurse -Filter "*.md") {
    foreach ($old in $renames.Keys) {
        $new = $renames[$old]
        (Get-Content $file.FullName) -replace [regex]::Escape($old), $new | Set-Content $file.FullName
    }
}
```

---

## 📋 Validation Checklist

**After each rename**:
- [ ] File renamed successfully
- [ ] All references updated (grep verification)
- [ ] Links work in .md files
- [ ] OmniTag FILE-ID updated (if file is tagged)
- [ ] docs/INDEX.md updated
- [ ] .ai-context/ updated (if referenced)
- [ ] knowledge-base.yaml updated (if session doc)
- [ ] Git status clean (no broken files)

---

## 🎯 Benefits

### 1. Uniqueness ✅
- No more "which NuSyQ_Root_README.md?"
- No more "which COMPLETE.md?"
- Every file has unique, searchable name

### 2. Depth/Context ✅
- Filename tells domain (NuSyQ, Session, Audit, Guide)
- Filename tells category (Complete, InProgress, Plan)
- Filename tells date (20251007)

### 3. Scalability ✅
- New files fit pattern automatically
- Pattern supports 1,000+ files
- Sorting by name = logical grouping

### 4. Discovery ✅
- `ls | grep Session` → all session docs
- `ls | grep Complete` → all completion reports
- `ls | grep 20251007` → all Oct 7 docs

### 5. Modularity ✅
- Clear file relationships
- Parent-child linkages obvious
- Dependencies traceable

---

## 📝 Naming Convention Decision Tree

```
Is this a README file?
├─ Yes → [DirectoryName]_[Layer]_NuSyQ_Root_README.md (IN directory)
└─ No → Is this a status/milestone doc?
    ├─ Yes → NuSyQ_[Component]_[Status]_[Date].md
    └─ No → Is this a session doc?
        ├─ Yes → Session_[Type]_[Topic]_[Date].md
        └─ No → Is this an audit?
            ├─ Yes → Audit_[Component]_[Scope]_[Date].md
            └─ No → Is this a guide?
                ├─ Yes → Guide_[Topic]_[Audience].md
                └─ No → Is this a reference?
                    ├─ Yes → NuSyQ_[Component]_[Type]_Reference.md
                    └─ No → Custom pattern (document in this spec)
```

---

## 🚀 Next Steps

### Immediate (Today)
1. Create `scripts/rename_files_systematic.ps1`
2. Generate full rename mapping (all root .md files)
3. Test on 2-3 files first
4. Verify references update correctly

### Short-Term (This Week)
5. Rename all root .md files (Phase 1)
6. Rename directory READMEs (Phase 2)
7. Update all references
8. Validate with grep

### Long-Term (This Month)
9. Document any edge cases
10. Update OmniTags for renamed files
11. Create naming validator script
12. Add pre-commit hook (enforce naming)

---

## 📞 Maintenance

**Owner**: Claude Code (GitHub Copilot)
**Status**: Active Standard
**Review Cycle**: Quarterly or when pattern breaks

**When to update this spec**:
- New file type appears
- Pattern collision found
- Community feedback
- Scalability issues

---

**Status**: ✅ SPECIFICATION COMPLETE
**Implementation**: ⏳ PENDING (ready to execute)
**Impact**: High (eliminates all duplicate names)

---

## Appendix: Full Rename Mapping (Root Level)

See `scripts/rename_mapping_phase1.yaml` for complete list.
