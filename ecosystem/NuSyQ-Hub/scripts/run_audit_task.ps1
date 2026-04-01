<#
Robust non-interactive audit script for NuSyQ-Hub
- Loads GitHub token from config\secrets.json into $env:GITHUB_TOKEN for this process (if present)
- Writes machine-readable audit artifacts into .tmp_audit/
- Avoids inline quoting and pipeline races by collecting hashes in-memory
#>

## Ensure we run from the repository root (parent of the scripts folder)
if ($PSScriptRoot) {
    Set-Location -LiteralPath (Split-Path -Path $PSScriptRoot -Parent)
} else {
    # fallback to workspace path if $PSScriptRoot is not available
    Set-Location -LiteralPath 'C:\Users\malik\Desktop\NuSyQ-Hub'
}

try {
    $cfgPath = Join-Path -Path (Join-Path -Path (Get-Location) -ChildPath 'config') -ChildPath 'secrets.json'
    if (Test-Path $cfgPath) {
        $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
        if ($cfg.github -and $cfg.github.token) {
            $env:GITHUB_TOKEN = $cfg.github.token
        }
    }
} catch {
    Write-Host "WARN: could not read config/secrets.json: $($_.Exception.Message)"
}

# Prepare audit folder
New-Item -ItemType Directory -Force -Path .tmp_audit | Out-Null

# Core git artifacts
git rev-parse --abbrev-ref HEAD > .tmp_audit\branch.txt 2>&1
git status --porcelain > .tmp_audit\status.txt 2>&1
git --no-pager log -n 500 --pretty=format:'%h %ad %an %s' --date=iso --name-status > .tmp_audit\recent_commits.txt 2>&1
git --no-pager log --diff-filter=D --summary --since='60 days' > .tmp_audit\deletions_60d.txt 2>&1

# Fetch origin/master ref explicitly and capture output
git fetch origin master:refs/remotes/origin/master --no-tags --prune > .tmp_audit\fetch_master.log 2>&1
git --no-pager diff --name-status origin/master...HEAD > .tmp_audit\diff_origin_master.txt 2>&1

# Duplicate detection: by filename (exclude .git and .tmp_audit)
Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike '*\\.git\\*' -and $_.FullName -notlike '*\\.tmp_audit\\*' } |
    Group-Object -Property Name |
    Where-Object { $_.Count -gt 1 } |
    ForEach-Object {
        $_.Name
        $_.Group | ForEach-Object { $_.FullName }
        '---'
    } | Out-File -FilePath .tmp_audit\dups_by_name.txt -Encoding utf8

# Duplicate detection: by content (safe in-memory hash collection)
$files = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notlike '*\\.git\\*' -and $_.FullName -notlike '*\\.tmp_audit\\*' }

$hashList = New-Object System.Collections.Generic.List[object]
foreach ($f in $files) {
    try {
        $h = Get-FileHash -LiteralPath $f.FullName -Algorithm SHA1 -ErrorAction Stop
        $hashList.Add([pscustomobject]@{ Path = $f.FullName; Hash = $h.Hash }) | Out-Null
    } catch {
        $hashList.Add([pscustomobject]@{ Path = $f.FullName; Hash = "ERROR: $($_.Exception.Message)" }) | Out-Null
    }
}

$hashList | Group-Object -Property Hash |
    Where-Object { $_.Count -gt 1 } |
    ForEach-Object {
        $_.Group | ForEach-Object { $_.Path }
        '---'
    } | Out-File -FilePath .tmp_audit\dups_by_content.txt -Encoding utf8

# KILO references (use Select-String safely)
Select-String -Path .\**\* -Pattern 'KILO-FOOLISH|KILO_FOOLISH|KILO-FOOL|KILO' -SimpleMatch -CaseSensitive:$false > .tmp_audit\kilo_refs.txt -ErrorAction SilentlyContinue

# Probe: was token visible to the process
if ($env:GITHUB_TOKEN) { 'PRESENT' | Out-File -FilePath .tmp_audit\agent_probe.txt -Encoding utf8 } else { 'MISSING' | Out-File -FilePath .tmp_audit\agent_probe.txt -Encoding utf8 }

Write-Host 'RUN_AUDIT_SCRIPT_DONE'
