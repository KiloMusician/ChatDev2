[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$KeeperArgs
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$toolsDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir    = Split-Path -Parent $toolsDir
$keeperPath = Join-Path $rootDir "keeper.ps1"

if (-not (Test-Path -LiteralPath $keeperPath)) { throw "keeper.ps1 not found at $keeperPath" }

# Prefer PowerShell 7+; fall back to Windows PowerShell 5.1
$psExe = if (Get-Command pwsh.exe -ErrorAction SilentlyContinue) { "pwsh.exe" } else { "powershell.exe" }

# Build inline command so the elevated window stays open after running
$escapedPath = $keeperPath -replace "'", "''"
$argString   = ($KeeperArgs | ForEach-Object { if ($_ -match '\s') { "'$_'" } else { $_ } }) -join " "
$command     = "& '$escapedPath' $argString; Write-Host ''; Read-Host 'Press Enter to close'"

$argumentList = @("-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command)
Start-Process -FilePath $psExe -Verb RunAs -WorkingDirectory $rootDir -ArgumentList $argumentList | Out-Null
