#!/usr/bin/env pwsh
<#
Runs `code --list-extensions --show-versions` (if available) and writes JSON report.
If VS Code CLI (`code`) is not on PATH, the script writes a best-effort message.
#>
Set-StrictMode -Version Latest

$out = @{}
try {
  # Prefer simple invocation and capture output to avoid Start-Process redirect issues
  $codeCmd = 'code'
  $text = & $codeCmd --list-extensions --show-versions 2>$null
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($text)) {
    throw 'code CLI not available or returned no output'
  }
  $exts = @()
  foreach ($line in $text -split "`n") {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line.Trim() -split '@'
    if ($parts.Length -ge 2) {
      $exts += [PSCustomObject]@{ id = $parts[0]; version = $parts[1] }
    } else {
      $exts += [PSCustomObject]@{ id = $line.Trim(); version = '' }
    }
  }
  $out.extensions = $exts
} catch {
  $out.error = "Failed to run 'code' CLI: $($_.Exception.Message)"
}

$reportPath = Join-Path $PSScriptRoot 'extensions_report.json'
($out | ConvertTo-Json -Depth 4) | Set-Content -Path $reportPath -Encoding UTF8
Write-Output "Wrote extensions report to $reportPath"
