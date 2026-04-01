<#
.SYNOPSIS
    Build the NuSyQ-Hub Docker image using a sanitized context inside WSL2.

.DESCRIPTION
    Works around Windows permission denial on config/.secure by:
      * Generating sanitized build context (scripts/create_sanitized_context.py)
      * Invoking docker build from WSL (Ubuntu default) against that context
      * Tagging image with provided tag (default: v1.0.0) and git short SHA if available

.PARAMETER Tag
    Base tag to apply to the built image (default v1.0.0)

.EXAMPLE
    ./scripts/wsl_build.ps1 -Tag v1.1.0

#>
param(
    [string]$Tag = "v1.0.0"
)

Write-Host "🔧 Generating sanitized build context..." -ForegroundColor Cyan
python scripts/create_sanitized_context.py || exit $LASTEXITCODE

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    Write-Error "WSL not available. Install WSL2 or run build manually with sanitized context."
    exit 1
}

$gitSha = "unknown"
try { $gitSha = (git rev-parse --short HEAD).Trim() } catch { }
$fullTag = "nusyq-hub:$Tag-$gitSha"
Write-Host "🐧 Building inside WSL2 with tag $fullTag" -ForegroundColor Cyan

# Convert path for WSL (assumes default mounting at /mnt/c)
$winPath = (Get-Location).Path
$wslPath = "/mnt/" + $winPath.Substring(0,1).ToLower() + $winPath.Substring(2).Replace("\\","/")
$contextPath = "$wslPath/.sanitized_build_context"

wsl -e bash -lc "cd '$contextPath' && docker build -t '$fullTag' ." || exit $LASTEXITCODE

Write-Host "✅ WSL build complete: $fullTag" -ForegroundColor Green
