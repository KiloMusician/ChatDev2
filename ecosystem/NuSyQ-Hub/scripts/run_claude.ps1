param(
    [string]$Cmd,
    [string]$TempPath = "$env:LOCALAPPDATA\Temp",
    [switch]$PreflightOnly,
    [switch]$SkipPreflight
)

# Ensure TMP/TEMP point to a real temp directory so Claude and related tools
# that create many temporary files use the expected location.
if (-not (Test-Path -Path $TempPath)) {
    New-Item -ItemType Directory -Path $TempPath -Force | Out-Null
}

$env:TEMP = $TempPath
$env:TMP = $TempPath

function Find-CommandPath {
    param([string]$Name)
    try {
        $cmdInfo = Get-Command $Name -ErrorAction SilentlyContinue
        if ($cmdInfo -and $cmdInfo.Source) {
            return $cmdInfo.Source
        }
    } catch {}
    return $null
}

function Resolve-CommandPath {
    param(
        [string]$Name,
        [string[]]$Fallbacks = @()
    )
    $found = Find-CommandPath $Name
    if ($found) {
        return $found
    }
    foreach ($candidate in $Fallbacks) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    return $null
}

function Test-HttpsEndpoint {
    param([string]$Url, [int]$TimeoutSec = 6)
    try {
        $resp = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        return @{ ok = $true; status = [int]$resp.StatusCode; error = $null; auth_gated = $false }
    } catch {
        $status = $null
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            $status = [int]$_.Exception.Response.StatusCode.value__
        }
        $authGated = ($status -eq 401 -or $status -eq 403)
        if ($authGated) {
            return @{ ok = $true; status = $status; error = $null; auth_gated = $true }
        }
        return @{ ok = $false; status = $status; error = $_.Exception.Message; auth_gated = $false }
    }
}

function Show-ValueOrMissing {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "NOT FOUND"
    }
    return $Value
}

function Test-PlaceholderSecret {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }
    $normalized = $Value.Trim().ToLowerInvariant()
    return @(
        "<your_key_here>",
        "your_key_here",
        "your-claude-key-here",
        "sk-ant-your-anthropic-key-here"
    ) -contains $normalized
}

function Run-GitDiagnostics {
    param(
        [string]$GitPath,
        [string]$GhPath
    )

    if (-not $GitPath) {
        return
    }

    $repoPath = (Get-Location).Path
    try {
        $inside = & $GitPath -C $repoPath rev-parse --is-inside-work-tree 2>$null
        if ("$inside".Trim() -ne "true") {
            return
        }
    } catch {
        return
    }

    try {
        $branch = (& $GitPath -C $repoPath rev-parse --abbrev-ref HEAD 2>$null | Select-Object -First 1).Trim()
        if (-not [string]::IsNullOrWhiteSpace($branch)) {
            Write-Host "git branch: $branch"
        }
    } catch {}

    try {
        $statusLines = @(& $GitPath -C $repoPath status --porcelain=v1 --untracked-files=no 2>$null)
        $dirtyCount = $statusLines.Count
        Write-Host "git tracked changes: $dirtyCount"
        if ($dirtyCount -ge 50) {
            Write-Host "[WARN] Large tracked-diff count detected. Claude LocalSessionManager may repeatedly prompt for commit/PR actions." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WARN] Unable to collect git status during preflight: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    try {
        $worktreeLines = @(& $GitPath -C $repoPath worktree list 2>$null)
        $prunableCount = @($worktreeLines | Where-Object { $_ -match '\bprunable\b' }).Count
        if ($prunableCount -gt 0) {
            Write-Host "[WARN] git worktree list reports $prunableCount prunable worktree(s). Stale worktrees can cause session and PR context drift." -ForegroundColor Yellow
        }
    } catch {}

    if ($GhPath) {
        try {
            $prJson = & $GhPath pr view --json number,state,mergeStateStatus,headRefName 2>$null
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($prJson)) {
                $pr = $prJson | ConvertFrom-Json
                if ($pr -and $pr.number) {
                    Write-Host "gh current PR: #$($pr.number) [$($pr.state)] merge=$($pr.mergeStateStatus) head=$($pr.headRefName)"
                    if ($pr.mergeStateStatus -eq "DIRTY") {
                        Write-Host "[WARN] Current PR merge state is DIRTY (conflicts or merge blockers). Claude may keep surfacing PR/conflict prompts." -ForegroundColor Yellow
                    }
                }
            }
        } catch {}
    }
}

function Run-ClaudePreflight {
    # Prefer Windows shim/exe over PowerShell shim to avoid execution policy edge cases.
    $claudePath = Resolve-CommandPath "claude.cmd" @(
        (Join-Path $env:APPDATA "npm\claude.cmd"),
        (Join-Path $env:LOCALAPPDATA "AnthropicClaude\claude.exe")
    )
    if (-not $claudePath) {
        $claudePath = Resolve-CommandPath "claude.exe" @(
            (Join-Path $env:LOCALAPPDATA "AnthropicClaude\claude.exe")
        )
    }
    if (-not $claudePath) {
        $claudePath = Resolve-CommandPath "claude" @(
            (Join-Path $env:LOCALAPPDATA "AnthropicClaude\claude.exe")
        )
    }
    $gitPath = Resolve-CommandPath "git" @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe"
    )
    $ghPath = Resolve-CommandPath "gh" @(
        "C:\Program Files\GitHub CLI\gh.exe"
    )
    $uvPath = Resolve-CommandPath "uv" @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts\uv.exe")
    )
    $dockerPath = Resolve-CommandPath "docker" @(
        "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    )

    $claudeSettings = Join-Path $env:USERPROFILE ".claude\settings.json"
    $windowsMcpSettings = Join-Path $env:APPDATA "Claude\Claude Extensions Settings\ant.dir.cursortouch.windows-mcp.json"

    Write-Host "=== Claude Preflight ===" -ForegroundColor Cyan
    Write-Host "TMP/TEMP: $TempPath"
    Write-Host "claude: $(Show-ValueOrMissing $claudePath)"
    Write-Host "git:    $(Show-ValueOrMissing $gitPath)"
    Write-Host "gh:     $(Show-ValueOrMissing $ghPath)"
    Write-Host "uv:     $(Show-ValueOrMissing $uvPath)"
    Write-Host "docker: $(Show-ValueOrMissing $dockerPath)"
    Run-GitDiagnostics -GitPath $gitPath -GhPath $ghPath

    if (Test-PlaceholderSecret $env:ANTHROPIC_API_KEY) {
        Write-Host "[WARN] ANTHROPIC_API_KEY is set to a placeholder value. This forces API-key mode and breaks Claude auth." -ForegroundColor Yellow
        Write-Host "[WARN] Clearing placeholder ANTHROPIC_API_KEY for this session." -ForegroundColor Yellow
        $env:ANTHROPIC_API_KEY = ""
    }

    if (Test-Path $claudeSettings) {
        try {
            $settings = Get-Content -Raw -Path $claudeSettings | ConvertFrom-Json
            $enabled = $settings.enabledPlugins
            if ($enabled) {
                $knownBad = @(
                    "vercel@claude-plugins-official",
                    "typescript-lsp@claude-plugins-official",
                    "semgrep@claude-plugins-official"
                )
                $activeBad = @()
                foreach ($p in $knownBad) {
                    $prop = $enabled.PSObject.Properties[$p]
                    if ($prop -and $prop.Value -eq $true) { $activeBad += $p }
                }
                if ($activeBad.Count -gt 0) {
                    Write-Host "[WARN] Known-bad plugin manifests enabled: $($activeBad -join ', ')" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "[WARN] Failed to parse ${claudeSettings}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    if (Test-Path $windowsMcpSettings) {
        try {
            $w = Get-Content -Raw -Path $windowsMcpSettings | ConvertFrom-Json
            if ($w.isEnabled -eq $true -and -not $uvPath) {
                Write-Host "[WARN] Windows-MCP extension is enabled but 'uv' is missing. This causes repeated 'spawn uv ENOENT' failures." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[WARN] Failed to parse ${windowsMcpSettings}: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }

    $endpoints = @(
        "https://claude.ai/",
        "https://downloads.claude.ai/releases/win32/x64/RELEASES"
    )
    foreach ($url in $endpoints) {
        $probe = Test-HttpsEndpoint -Url $url
        if ($probe.ok) {
            if ($probe.auth_gated -eq $true) {
                Write-Host "[OK]   $url -> $($probe.status) (reachable, auth-gated)"
            } else {
                Write-Host "[OK]   $url -> $($probe.status)"
            }
        } else {
            $statusText = if ($null -eq $probe.status) { "no-status" } else { [string]$probe.status }
            Write-Host "[WARN] $url -> $statusText $($probe.error)" -ForegroundColor Yellow
        }
    }

    if (-not $claudePath) {
        Write-Host "[ERROR] Claude executable not found on PATH and fallback path is missing." -ForegroundColor Red
        return 1
    }

    return 0
}

if (-not $SkipPreflight) {
    $preflightCode = Run-ClaudePreflight
    if ($PreflightOnly) {
        exit $preflightCode
    }
    if ($preflightCode -ne 0) {
        exit $preflightCode
    }
}

if (-not $Cmd -and -not $PreflightOnly) {
    Write-Error "Usage: .\run_claude.ps1 -Cmd '<command to run>' [-TempPath 'C:\Users\\you\\AppData\\Local\\Temp'] [-PreflightOnly] [-SkipPreflight]"
    exit 2
}

if (-not $PreflightOnly) {
    Write-Host "Running command with TMP/TEMP=$TempPath"
    Write-Host "Command: $Cmd"

    try {
        # Execute in the current shell to preserve env adjustments from preflight.
        Invoke-Expression $Cmd
        exit $LASTEXITCODE
    } catch {
        Write-Error "Command failed: $_"
        exit 1
    }
}
