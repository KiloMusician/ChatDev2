# NuSyQ Naming Convention - Phase 1 Renaming Script
# Purpose: Systematically rename root .md files per new convention
# Date: 2025-10-07
# Usage: .\scripts\rename_files_phase1.ps1 [-DryRun] [-Verbose]

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

# Color output functions
function Write-Success { param($msg) Write-Host $msg -ForegroundColor Green }
function Write-Info { param($msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Warn { param($msg) Write-Host $msg -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host $msg -ForegroundColor Red }

# Rename mapping (from rename_mapping_phase1.yaml)
$renames = @{
    # Session Documents
    "SESSION_SUMMARY_2025-10-07.md" = "Session_Documentation_Audit_Summary_20251007.md"
    "SESSION_COMPLETE_TIMEOUT_REPLACEMENT.md" = "Session_Timeout_Replacement_Complete_20251007.md"
    "REPOSITORY_STATUS_2025-10-07.md" = "Session_Repository_Status_20251007.md"

    # Status/Milestone Documents
    "TIMEOUT_REPLACEMENT_COMPLETE.md" = "NuSyQ_Timeout_Replacement_Complete_20251007.md"
    "DOCUMENTATION_INFRASTRUCTURE_COMPLETE.md" = "NuSyQ_Documentation_Infrastructure_Complete_20251007.md"
    "MODERNIZATION_COMPLETE.md" = "NuSyQ_Modernization_Complete_20251006.md"
    "ADAPTIVE_TIMEOUT_COMPLETE.md" = "NuSyQ_Adaptive_Timeout_Complete_20251006.md"

    # In Progress Documents
    "TIMEOUT_REPLACEMENT_PROGRESS.md" = "NuSyQ_Timeout_Replacement_InProgress_20251007.md"

    # Plan Documents
    "SYSTEMATIC_TIMEOUT_REPLACEMENT_PLAN.md" = "NuSyQ_Timeout_Replacement_Plan_20251007.md"

    # Reference Documents
    "OMNITAG_SYSTEM_SUMMARY.md" = "NuSyQ_OmniTag_System_Reference.md"
    "QUICK_REFERENCE_DOCUMENTATION.md" = "NuSyQ_Documentation_Quick_Reference.md"
    "QUICK_STATUS.md" = "NuSyQ_System_Quick_Status.md"

    # Audit Documents
    "REPOSITORY_DOCUMENTATION_AUDIT.md" = "Audit_Documentation_Infrastructure_20251007.md"
    "DOCUMENTATION_SESSION_SUMMARY.md" = "Audit_Documentation_Session_Summary_20251007.md"

    # Archive Documents
    "DOCUMENTATION_REORGANIZATION_SUMMARY.md" = "Archive_Documentation_Reorganization_Summary.md"

    # Guide Documents
    "CONTRIBUTING.md" = "Guide_Contributing_AllUsers.md"

    # Root README
    "README.md" = "NuSyQ_Root_README.md"
}

# Header
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Info "  NuSyQ Naming Convention - Phase 1: Root .md Files"
Write-Info "═══════════════════════════════════════════════════════════════"
if ($DryRun) {
    Write-Warn "  DRY RUN MODE - No files will be modified"
}
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Host ""

$successCount = 0
$skipCount = 0
$errorCount = 0

# Phase 1: Rename Files
Write-Info "[Phase 1] Renaming Files..."
Write-Host ""

foreach ($old in $renames.Keys) {
    $new = $renames[$old]

    if ($Verbose) {
        Write-Info "  Checking: $old"
    }

    if (Test-Path $old) {
        if ($DryRun) {
            Write-Warn "  [DRY RUN] Would rename: $old → $new"
        } else {
            try {
                Move-Item $old $new -ErrorAction Stop
                Write-Success "  ✓ Renamed: $old → $new"
                $successCount++
            } catch {
                Write-Err "  ✗ ERROR renaming $old : $_"
                $errorCount++
            }
        }
    } else {
        if ($Verbose) {
            Write-Warn "  ⊘ SKIP (not found): $old"
        }
        $skipCount++
    }
}

Write-Host ""
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Info "  Phase 1 Summary"
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Success "  ✓ Renamed: $successCount files"
Write-Warn "  ⊘ Skipped: $skipCount files (not found)"
if ($errorCount -gt 0) {
    Write-Err "  ✗ Errors: $errorCount files"
}
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Host ""

# Phase 2: Update References (only if not dry run and renames succeeded)
if (-not $DryRun -and $successCount -gt 0) {
    Write-Info "[Phase 2] Updating references in all .md files..."
    Write-Host ""

    $mdFiles = Get-ChildItem -Recurse -Filter "*.md" -File
    $totalUpdates = 0

    foreach ($file in $mdFiles) {
        $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { continue }

        $originalContent = $content

        # Replace all old references with new ones
        foreach ($old in $renames.Keys) {
            $new = $renames[$old]
            $content = $content -replace [regex]::Escape($old), $new
        }

        if ($content -ne $originalContent) {
            Set-Content $file.FullName $content
            Write-Success "  ✓ Updated references in: $($file.FullName)"
            $totalUpdates++
        }
    }

    Write-Host ""
    Write-Info "═══════════════════════════════════════════════════════════════"
    Write-Success "  ✓ Updated $totalUpdates files with new references"
    Write-Info "═══════════════════════════════════════════════════════════════"
}

# Final instructions
Write-Host ""
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Info "  Next Steps"
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Host "  1. Verify renames with: ls *.md | Sort Name"
Write-Host "  2. Check for broken links: grep -r '\.md' . | grep -v '.venv'"
Write-Host "  3. Update .ai-context/ files if needed"
Write-Host "  4. Update knowledge-base.yaml if session docs renamed"
Write-Host "  5. Run Phase 2 (directory READMEs) when ready"
Write-Info "═══════════════════════════════════════════════════════════════"
Write-Host ""

if ($DryRun) {
    Write-Warn "This was a DRY RUN. Run without -DryRun to apply changes."
} else {
    Write-Success "Phase 1 complete! Files renamed and references updated."
}
