# Stepwise non-interactive audit
# Creates .tmp_audit in repo root and writes discrete artifacts to it.
Set-StrictMode -Version Latest
$repo = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $repo
$out = Join-Path $repo '.tmp_audit'
if (-Not (Test-Path $out)) { New-Item -ItemType Directory -Path $out | Out-Null }
Write-Output "AUDIT_FOLDER=$out"
# 1) fetch
git fetch --all --prune > (Join-Path $out 'fetch.log') 2>&1
Write-Output "FETCHED"
# 2) branch
git rev-parse --abbrev-ref HEAD > (Join-Path $out 'branch.txt')
Write-Output "BRANCH_WRITTEN"
# 3) status
git status --porcelain > (Join-Path $out 'status.txt')
Write-Output "STATUS_WRITTEN"
# 4) recent commits
git --no-pager log -n 500 --pretty=format:'%h %ad %an %s' --date=iso --name-status > (Join-Path $out 'recent_commits.txt')
Write-Output "RECENT_COMMITS_WRITTEN"
# 5) deletions last 60 days
git --no-pager log --diff-filter=D --summary --since='60 days' > (Join-Path $out 'deletions_60d.txt')
Write-Output "DELETIONS_WRITTEN"
# 6) fetch master remote
git fetch origin master:refs/remotes/origin/master --no-tags --prune > (Join-Path $out 'fetch_master.log') 2>&1
Write-Output "FETCH_MASTER_DONE"
# 7) diff against origin/master
git --no-pager diff --name-status origin/master...HEAD > (Join-Path $out 'diff_origin_master.txt')
Write-Output "DIFF_WRITTEN"
# 8) dups by name
Get-ChildItem -Recurse -File | Group-Object -Property Name | Where-Object {$_.Count -gt 1} | ForEach-Object { $_.Name | Out-File -Append -FilePath (Join-Path $out 'dups_by_name.txt'); $_.Group | ForEach-Object { $_.FullName | Out-File -Append -FilePath (Join-Path $out 'dups_by_name.txt') }; Out-File -Append -FilePath (Join-Path $out 'dups_by_name.txt') -InputObject '---' }
Write-Output "DUPS_BY_NAME_WRITTEN"
# 9) dups by content (SHA1)
Get-ChildItem -Recurse -File | Where-Object {!$_.FullName.Contains('\.git\')} | ForEach-Object { @{Path=$_.FullName; Hash=(Get-FileHash $_.FullName -Algorithm SHA1).Hash } } | Group-Object -Property Hash | Where-Object {$_.Count -gt 1} | ForEach-Object { $_.Group | ForEach-Object { $_.Path | Out-File -Append -FilePath (Join-Path $out 'dups_by_content.txt') }; Out-File -Append -FilePath (Join-Path $out 'dups_by_content.txt') -InputObject '---' }
Write-Output "DUPS_BY_CONTENT_WRITTEN"
# 10) kilo refs
Try {
    Select-String -Path .\**\* -Pattern 'KILO-FOOLISH|KILO_FOOLISH|KILO-FOOL|KILO' -SimpleMatch -CaseSensitive:$false > (Join-Path $out 'kilo_refs.txt') -ErrorAction SilentlyContinue
    Write-Output "KILO_REFS_WRITTEN"
} Catch {
    Write-Output "KILO_REFS_FAILED"
}
Write-Output "AUDIT_DONE"
