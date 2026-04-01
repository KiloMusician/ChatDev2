<# Test runner for pwsh_helpers - runs process list and pipes to compact-output #>

Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Output "Running Get-ProcessesByCmdline and compacting output..."
.\Get-ProcessesByCmdline.ps1 | ForEach-Object { $_ } | .\compact-output.ps1

Write-Output "Done."
