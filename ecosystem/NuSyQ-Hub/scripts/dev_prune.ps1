<#
Safer prune helper: only prunes the named volumes used by the dev compose stack.
#>
param(
  [switch]$Force
)

$volumes = @('nusyq_pgdata','nusyq_redisdata')

foreach ($v in $volumes) {
  $exists = docker volume ls -q --filter name=$v
  if ($exists) {
    if ($Force) {
      Write-Host "Removing volume $v"
      docker volume rm $v
    } else {
      Write-Host "Volume $v exists. Run `./scripts/dev_prune.ps1 -Force` to remove it."
    }
  } else {
    Write-Host "Volume $v not present; skipping."
  }
}
