<#
.SYNOPSIS
  Collapse consecutive identical lines from input and annotate repetition counts.

.DESCRIPTION
  Reads from pipeline or a file and writes lines; when consecutive lines are identical,
  emits the line once and appends " (repeated: N)" if N > 1.
#>

param(
    [string]$Path
)

function Emit($line, $count) {
    if ($count -gt 1) {
        Write-Output "${line}  (repeated: $count)"
    } else {
        Write-Output $line
    }
}

$prev = $null
$count = 0

if ($Path) {
    $iter = Get-Content -Path $Path -ErrorAction Stop
} else {
    $iter = [Console]::In.ReadToEnd().Split([Environment]::NewLine)
}

foreach ($ln in $iter) {
    if ($ln -eq $prev) {
        $count++
    } else {
        if ($prev -ne $null) { Emit $prev $count }
        $prev = $ln
        $count = 1
    }
}

if ($prev -ne $null) { Emit $prev $count }
<#
. compact-output.ps1
.
Purpose: Read stdin and collapse consecutive identical lines. When the same line
appears N>1 times in a row, print it once and append a marker `(repeated: N times)`
on a separate line. This prevents spammy, repeated error messages from flooding
terminals and logs.

Usage:
  Get-ProcessesByCmdline.ps1 | pwsh -NoProfile -File .\scripts\pwsh_helpers\compact-output.ps1
#>

$prev = $null
$count = 0

# Read all input and split into lines (safe for piped large output)
$raw = [Console]::In.ReadToEnd()
if ($raw -eq $null -or $raw.Length -eq 0) { exit 0 }

$lines = $raw -split "`n"

foreach ($line in $lines) {
    # Trim trailing CR and avoid treating empty final line as duplicate
    $l = $line.TrimEnd("`r")
    if ($l -eq $prev) {
        $count++
    } else {
        if ($prev -ne $null) {
            if ($count -gt 1) {
                Write-Output $prev
                Write-Output "(repeated: $count times)"
            } else {
                Write-Output $prev
            }
        }
        $prev = $l
        $count = 1
    }
}

# Flush last group
if ($prev -ne $null) {
    if ($count -gt 1) {
        Write-Output $prev
        Write-Output "(repeated: $count times)"
    } else {
        Write-Output $prev
    }
}
