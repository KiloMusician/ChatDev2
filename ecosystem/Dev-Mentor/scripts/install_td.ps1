# install_td.ps1 — Install 'td' command for PowerShell + CMD (Windows)
# ─────────────────────────────────────────────────────────────────────────────
# Installs td.ps1 and td.cmd into $HOME\bin and adds them to the user PATH.
#
# Usage:
#   .\scripts\install_td.ps1
#   .\scripts\install_td.ps1 -Uninstall
#   .\scripts\install_td.ps1 -Check
# ─────────────────────────────────────────────────────────────────────────────
param(
    [switch]$Uninstall,
    [switch]$Check
)

$ErrorActionPreference = "Stop"

# Resolve repo root from this script's location
$RepoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$UserBin  = Join-Path $HOME "bin"
$PSScriptsDir = Join-Path $HOME "Documents\WindowsPowerShell\Scripts"
$PS7ScriptsDir = Join-Path $HOME "Documents\PowerShell\Scripts"

function Write-Ok($s)   { Write-Host "  $([char]0x2713) $s" -ForegroundColor Green }
function Write-Warn($s) { Write-Host "  ! $s"              -ForegroundColor Yellow }
function Write-Info($s) { Write-Host "  . $s"              -ForegroundColor Cyan }
function Write-Hr       { Write-Host ("  " + ("─" * 52))   -ForegroundColor DarkGray }

Write-Host ""
Write-Host "  ◈ TERMINAL DEPTHS — Launcher Installer (Windows)" -ForegroundColor Magenta
Write-Hr

# ── Sentinel file ─────────────────────────────────────────────────────────────
$SentinelFile = Join-Path $RepoRoot ".td_repo"

# ── Check mode ────────────────────────────────────────────────────────────────
if ($Check) {
    $dest = Join-Path $UserBin "td.ps1"
    if (Test-Path $dest) {
        Write-Ok "'td.ps1' is installed at $dest"
    } else {
        Write-Warn "'td' is NOT installed"
        Write-Info "Run: .\scripts\install_td.ps1"
    }
    Write-Host ""
    exit 0
}

# ── Uninstall mode ────────────────────────────────────────────────────────────
if ($Uninstall) {
    foreach ($p in @(
        "$UserBin\td.ps1", "$UserBin\td.cmd",
        "$PSScriptsDir\td.ps1", "$PS7ScriptsDir\td.ps1"
    )) {
        if (Test-Path $p) { Remove-Item $p; Write-Ok "Removed: $p" }
    }
    if (Test-Path $SentinelFile) { Remove-Item $SentinelFile; Write-Ok "Removed sentinel" }
    Write-Info "Uninstall complete."
    Write-Host ""; exit 0
}

# ── Install ───────────────────────────────────────────────────────────────────

# Write sentinel
$RepoRoot | Out-File -FilePath $SentinelFile -Encoding utf8 -NoNewline
Write-Ok "Sentinel: $SentinelFile"

# Create UserBin dir
if (-not (Test-Path $UserBin)) { New-Item -ItemType Directory -Path $UserBin | Out-Null }

# PowerShell wrapper
$PS1Content = @"
# td.ps1 — Terminal Depths Launcher (auto-installed by install_td.ps1)
`$TDRepo = "$RepoRoot"
`$PythonExe = if (Get-Command 'python3' -ErrorAction SilentlyContinue) { 'python3' } else { 'python' }
& `$PythonExe "`$TDRepo\scripts\td.py" @Args
exit `$LASTEXITCODE
"@

$ps1Dest = Join-Path $UserBin "td.ps1"
$PS1Content | Out-File -FilePath $ps1Dest -Encoding utf8
Write-Ok "Installed: $ps1Dest"

# CMD wrapper
$CmdContent = @"
@echo off
set "TD_REPO=$RepoRoot"
where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 "%TD_REPO%\scripts\td.py" %*
) else (
    python "%TD_REPO%\scripts\td.py" %*
)
"@

$cmdDest = Join-Path $UserBin "td.cmd"
$CmdContent | Out-File -FilePath $cmdDest -Encoding ascii
Write-Ok "Installed: $cmdDest"

# Copy to PowerShell Script dirs
foreach ($psdir in @($PSScriptsDir, $PS7ScriptsDir)) {
    if (-not (Test-Path $psdir)) { New-Item -ItemType Directory -Path $psdir -Force | Out-Null }
    $PS1Content | Out-File -FilePath "$psdir\td.ps1" -Encoding utf8
    Write-Ok "PS Scripts: $psdir\td.ps1"
}

# Update user PATH if UserBin not already there
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($CurrentPath -notlike "*$UserBin*") {
    [Environment]::SetEnvironmentVariable("PATH", "$CurrentPath;$UserBin", "User")
    Write-Ok "Added $UserBin to user PATH"
    Write-Warn "Restart your terminal for PATH to take effect"
} else {
    Write-Info "$UserBin already in PATH"
}

Write-Hr
Write-Host ""
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Usage anywhere:"
Write-Host "    td                — enter Terminal Depths      (PowerShell / CMD)"
Write-Host "    td play           — terminal REPL (no browser)"
Write-Host "    td status         — server health"
Write-Host "    td open           — open in browser"
Write-Host "    td surfaces       — map all surfaces"
Write-Host "    td install        — re-run installer"
Write-Host ""
Write-Host "  For Git Bash / WSL, use the bash installer:" -ForegroundColor DarkGray
Write-Host "    bash scripts/install_td.sh" -ForegroundColor DarkGray
Write-Host ""
