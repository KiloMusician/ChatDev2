#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean up git state and commit infrastructure changes in logical groups.

.DESCRIPTION
    This script helps organize the 350+ uncommitted files into logical commits:
    1. Add updated .gitignore
    2. Move test files to correct locations
    3. Commit infrastructure (testing chamber, temple, automation)
    4. Commit tests
    5. Commit documentation
    6. Commit configuration

    Auto-generated diagnostic files are ignored per .gitignore.

.PARAMETER DryRun
    Show what would be committed without actually committing.

.PARAMETER SkipPush
    Skip pushing to remote after commits.
#>

param(
    [switch]$DryRun,
    [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
$repoRoot = "c:\Users\keath\Desktop\Legacy\NuSyQ-Hub"

Write-Host "🧹 NuSyQ-Hub Git Cleanup & Commit Script" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Set-Location -LiteralPath $repoRoot

# Check git status
Write-Host "📊 Current Git Status:" -ForegroundColor Yellow
git status --short | Select-Object -First 20
$totalChanges = (git status --short | Measure-Object).Count
Write-Host "`nTotal files changed: $totalChanges`n" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "🔍 DRY RUN MODE - No changes will be committed`n" -ForegroundColor Magenta
}

# Step 1: Add .gitignore
Write-Host "Step 1: Add updated .gitignore" -ForegroundColor Green
if ($DryRun) {
    git diff .gitignore
} else {
    git add .gitignore
    git commit -m "chore: Update gitignore for auto-generated files and diagnostics" -m "Excludes system health assessments, diagnostic scripts, and auto-generated data"
    Write-Host "✅ Committed .gitignore" -ForegroundColor Green
}

# Step 2: Move test file to correct location
Write-Host "`nStep 2: Move test_multi_ai_orchestrator.py to tests/" -ForegroundColor Green
if (Test-Path "test_multi_ai_orchestrator.py") {
    if ($DryRun) {
        Write-Host "Would move: test_multi_ai_orchestrator.py -> tests/" -ForegroundColor Yellow
    } else {
        git mv test_multi_ai_orchestrator.py tests/
        git commit -m "test: Move orchestrator test to tests/ directory"
        Write-Host "✅ Moved and committed test file" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  test_multi_ai_orchestrator.py not found or already moved" -ForegroundColor Yellow
}

# Step 3: Commit infrastructure
Write-Host "`nStep 3: Commit infrastructure (testing chamber, temple, automation)" -ForegroundColor Green
$infraFiles = @(
    "testing_chamber/"
    "src/main.py"
    "src/automation/"
    "src/evolution/"
    "src/consciousness/temple_of_knowledge/"
    "src/orchestration/chamber_promotion_manager.py"
    "src/real_time_context_monitor.py"
    "src/unified_documentation_engine.py"
    "initialize_temple_and_monitor.py"
    "ollama_port_standardizer.py"
    "pytest.ini"
)

$existingInfra = $infraFiles | Where-Object { Test-Path $_ }
if ($existingInfra.Count -gt 0) {
    if ($DryRun) {
        Write-Host "Would add:" -ForegroundColor Yellow
        $existingInfra | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    } else {
        git add $existingInfra
        git commit -m "feat: Add testing chamber, temple, and automation infrastructure" -m "- Testing chamber with promotion workflow
- Temple of Knowledge consciousness system
- Automation and evolution modules
- Real-time context monitoring
- Unified documentation engine
- Ollama port standardization
- Pytest configuration"
        Write-Host "✅ Committed infrastructure files" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  No infrastructure files found to commit" -ForegroundColor Yellow
}

# Step 4: Commit tests
Write-Host "`nStep 4: Commit test files" -ForegroundColor Green
$testFiles = @(
    "tests/test_temple_and_monitor.py"
    "tests/test_ai_coordinator_generated.py"
    "tests/test_multi_ai_orchestrator.py"
)

$existingTests = $testFiles | Where-Object { Test-Path $_ }
if ($existingTests.Count -gt 0) {
    if ($DryRun) {
        Write-Host "Would add:" -ForegroundColor Yellow
        $existingTests | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    } else {
        git add $existingTests
        git commit -m "test: Add comprehensive test coverage for temple and coordinator" -m "- Temple of Knowledge and Enhanced Monitor tests
- AI coordinator generated tests
- Multi-AI orchestrator tests"
        Write-Host "✅ Committed test files" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  No test files found to commit" -ForegroundColor Yellow
}

# Step 5: Commit documentation
Write-Host "`nStep 5: Commit documentation" -ForegroundColor Green
$docFiles = @(
    "docs/PHASE_1_DEBUGGING_COMPLETE.md"
    "docs/PHASE_2_CONFIG_FIXES_COMPLETE.md"
    "docs/COMPLETE_GATED_TOOLS_ACTIVATION_REPORT.md"
    "docs/AUTONOMOUS_SYSTEM_DEPLOYMENT_SUMMARY.md"
    "docs/TEMPLE_AND_MONITOR_IMPLEMENTATION_SUMMARY.md"
    "docs/TESTING_CHAMBER_QUICK_REFERENCE.md"
    "docs/QUICK_START_TEMPLE_MONITOR.md"
    "docs/AUTONOMOUS_SYSTEM_SUCCESS_SUMMARY.md"
    "docs/AUTONOMOUS_MONITOR_DEPLOYMENT_SUCCESS.md"
    "docs/CODE_QUALITY_REMEDIATION_REPORT.md"
    "docs/COMPREHENSIVE_MODERNIZATION_AUDIT.md"
    "docs/OPTION_5_AUTONOMOUS_SYSTEM_PROPOSAL.md"
    "docs/SYSTEMATIC_DEBUGGING_REPORT.md"
    ".github/copilot-instructions.md"
    ".vscode/copilot-config.json"
    "COMPREHENSIVE_WORK_BACKLOG.md"
    "MASTER_REPOSITORY_INVENTORY.md"
    "REPOSITORY_WORK_SUMMARY.md"
    "THREE_REPOSITORY_INTEGRATION_MASTER_PLAN.md"
    "THEATER_SCORE_CLARIFICATION.md"
    "GIT_AND_EXTENSION_AUDIT.md"
)

$existingDocs = $docFiles | Where-Object { Test-Path $_ }
if ($existingDocs.Count -gt 0) {
    if ($DryRun) {
        Write-Host "Would add $($existingDocs.Count) documentation files" -ForegroundColor Yellow
    } else {
        git add $existingDocs
        git commit -m "docs: Add phase reports, system documentation, and Copilot config" -m "- Phase 1 & 2 completion reports
- Gated tools activation documentation
- Autonomous system deployment summaries
- Temple and testing chamber guides
- Git and extension audit
- Repository integration planning
- Copilot instructions and configuration"
        Write-Host "✅ Committed documentation files" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  No documentation files found to commit" -ForegroundColor Yellow
}

# Step 6: Commit configuration
Write-Host "`nStep 6: Commit configuration files" -ForegroundColor Green
$configFiles = @(
    "config/sector_definitions.yaml"
    "config/service_urls.json"
    "data/autonomous_monitor_config.json"
    "data/unified_pu_queue.json"
)

$existingConfig = $configFiles | Where-Object { Test-Path $_ }
if ($existingConfig.Count -gt 0) {
    if ($DryRun) {
        Write-Host "Would add:" -ForegroundColor Yellow
        $existingConfig | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    } else {
        git add $existingConfig
        git commit -m "config: Add sector definitions and service configuration" -m "- Sector definitions for autonomous monitoring
- Service URLs configuration
- Autonomous monitor config
- Unified PU queue data"
        Write-Host "✅ Committed configuration files" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  No configuration files found to commit" -ForegroundColor Yellow
}

# Step 7: Show what's left uncommitted (should be mostly modified files from Phase 1 & 2)
Write-Host "`nStep 7: Remaining uncommitted changes" -ForegroundColor Green
$remainingChanges = git status --short
$remainingCount = ($remainingChanges | Measure-Object).Count

if ($remainingCount -gt 0) {
    Write-Host "There are $remainingCount remaining changes:" -ForegroundColor Yellow
    Write-Host "These are likely the 237 modified files from Phase 1 & 2 automated fixes." -ForegroundColor Cyan
    Write-Host "You can commit these separately or use:" -ForegroundColor Cyan
    Write-Host "  git add -u  # Stage all modified tracked files" -ForegroundColor White
    Write-Host "  git commit -m 'refactor: Apply Phase 1 & 2 automated fixes'" -ForegroundColor White
} else {
    Write-Host "✅ All changes committed!" -ForegroundColor Green
}

# Step 8: Push to remote
if (-not $SkipPush -and -not $DryRun) {
    Write-Host "`nStep 8: Push to remote?" -ForegroundColor Green
    $push = Read-Host "Push to origin/codex/add-development-setup-instructions? (y/N)"
    if ($push -eq 'y' -or $push -eq 'Y') {
        git push origin codex/add-development-setup-instructions
        Write-Host "✅ Pushed to remote!" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Skipped push. You can push later with:" -ForegroundColor Yellow
        Write-Host "  git push origin codex/add-development-setup-instructions" -ForegroundColor White
    }
} elseif ($SkipPush) {
    Write-Host "`nSkipping push (--SkipPush flag)" -ForegroundColor Yellow
}

Write-Host "`n🎉 Git cleanup complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Summary
Write-Host "📊 Summary:" -ForegroundColor Cyan
git log --oneline -10
Write-Host "`nTo see full commit details: git log -5" -ForegroundColor Gray
Write-Host "To see what's still uncommitted: git status" -ForegroundColor Gray
