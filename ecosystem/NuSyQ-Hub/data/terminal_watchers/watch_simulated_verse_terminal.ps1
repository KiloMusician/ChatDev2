# Terminal Watcher for simulated_verse
# Auto-generated for SimulatedVerse consciousness engine monitoring

$logFile = "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\data\terminal_logs\simulatedverse.log"
$terminalName = "simulated_verse"

Write-Host "=== $terminalName Terminal - Live Output ===" -ForegroundColor Cyan
Write-Host "Watching: $logFile" -ForegroundColor Gray
Write-Host ""

# Ensure log file exists
if (!(Test-Path $logFile)) {
    New-Item -ItemType File -Path $logFile -Force | Out-Null
    Write-Host "Created log file: $logFile" -ForegroundColor Yellow
}

# Tail the log file and format output
Get-Content $logFile -Wait -Tail 20 | ForEach-Object {
    $line = $_
    if ($null -eq $line) {
        return
    }

    $trimmed = $line.Trim()
    if ($trimmed.Length -eq 0) {
        return
    }

    $entry = $null
    if ($trimmed.StartsWith("{") -and $trimmed.EndsWith("}")) {
        try {
            $entry = $trimmed | ConvertFrom-Json -ErrorAction Stop
        } catch {
            $entry = $null
        }
    }

    if ($null -ne $entry) {
        $timestamp = $entry.timestamp
        $level = $entry.level
        $message = $entry.message
        if ($null -ne $message) {
            $message = "$message"
            $message = ($message -replace '[^\x00-\x7F]', '?')
        }

        # Color based on level
        $color = switch ($level) {
            "ERROR" { "Red" }
            "WARNING" { "Yellow" }
            "INFO" { "White" }
            "DEBUG" { "Gray" }
            default { "White" }
        }

        Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "[$level] " -NoNewline -ForegroundColor $color
        Write-Host $message -ForegroundColor $color
    } else {
        # If not JSON, just print the line
        $safeLine = ($line -replace '[^\x00-\x7F]', '?')
        Write-Host $safeLine -ForegroundColor White
    }
}
