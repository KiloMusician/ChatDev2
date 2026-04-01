# Non-interactive Git audit for NuSyQ-Hub
# Writes audit artifacts into .git\tmp_audit\
# Run with PowerShell (pwsh) from repo root:
# pwsh -NoProfile -File .\scripts\git_audit_noninteractive.ps1

param()

Set-Location -LiteralPath (Split-Path -LiteralPath $MyInvocation.MyCommand.Path -Parent)\..\

$targetDir = '.git\tmp_audit'
if (-Not (Test-Path $targetDir)) { New-Item -ItemType Directory -Force -Path $targetDir | Out-Null }

# Avoid interactive pagers
$env:GIT_PAGER = ''

# Fetch remotes
git fetch --all --prune --no-tags > "$targetDir\fetch.log" 2>&1

# Branch
git rev-parse --abbrev-ref HEAD > "$targetDir\branch.txt" 2>&1

# Status
git status --porcelain > "$targetDir\status.txt" 2>&1

# Recent commits (500)
git --no-pager log -n 500 --pretty=format:'%h %ad %an %s' --date=iso --name-status > "$targetDir\recent_commits.txt" 2>&1

# Deletions in last 60 days
git --no-pager log --diff-filter=D --summary --since='60 days' > "$targetDir\deletions_60d.txt" 2>&1

# Fetch origin/master
git fetch origin master:refs/remotes/origin/master --no-tags --prune > "$targetDir\fetch_master.log" 2>&1

# Diff vs origin/master
git --no-pager diff --name-status origin/master...HEAD > "$targetDir\diff_origin_master.txt" 2>&1

# Duplicate filenames (by name)
Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Group-Object -Property Name | Where-Object {$_.Count -gt 1} | ForEach-Object { $_.Name | Out-File -Append -FilePath "$targetDir\dups_by_name.txt"; $_.Group | ForEach-Object { $_.FullName | Out-File -Append -FilePath "$targetDir\dups_by_name.txt" }; Out-File -Append -FilePath "$targetDir\dups_by_name.txt" -InputObject '---' }

# Duplicate by content (SHA1 hash)
Get-ChildItem -Recurse -File | Where-Object {!$_.FullName.Contains('\.git\')} | ForEach-Object { @{Path=$_.FullName; Hash=(Get-FileHash $_.FullName -Algorithm SHA1).Hash } } | Group-Object -Property Hash | Where-Object {$_.Count -gt 1} | ForEach-Object { $_.Group | ForEach-Object { $_.Path | Out-File -Append -FilePath "$targetDir\dups_by_content.txt" }; Out-File -Append -FilePath "$targetDir\dups_by_content.txt" -InputObject '---' }

# Search for KILO legacy refs
try {
    Select-String -Path .\**\* -Pattern 'KILO-FOOLISH|KILO_FOOLISH|KILO-FOOL|KILO' -SimpleMatch -CaseSensitive:$false > "$targetDir\kilo_refs.txt" -ErrorAction SilentlyContinue
} catch {
    "" | Out-File -FilePath "$targetDir\kilo_refs.txt"
}

Write-Host "NU_SYG_AUDIT_DONE -- outputs: $targetDir"
