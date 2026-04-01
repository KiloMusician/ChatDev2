# Ollama Terminal - Local LLM Monitor
# Shows: Running models + API status + recent generations + model list
# Use -AutoStart to automatically attempt `ollama serve` when offline.

param(
    [switch]$Watch,
    [int]$IntervalSeconds = 7,
    [switch]$NoClear,
    [switch]$AutoStart   # Automatically start Ollama if offline
)

function Resolve-PythonCmd {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @("py", "-3") }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @("python") }
    return @()
}

$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $RepoRoot
$logFile = Join-Path $RepoRoot "data\terminal_logs\ollama.log"
$ollamaApi = "http://localhost:11434"
$runMode = if ($Watch) { "WATCH" } else { "ONE-SHOT" }

do {
    if (-not $NoClear) { Clear-Host }
    Write-Host "=== OLLAMA (Local LLM Platform) ===" -ForegroundColor Cyan
    Write-Host "Run Mode: $runMode" -ForegroundColor DarkGray
    Write-Host ""

    Write-Host "--- API Status -----------------------------------------------" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "$ollamaApi/api/tags" -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $models = ($response.Content | ConvertFrom-Json).models
        Write-Host "  Ollama API: ONLINE " -NoNewline -ForegroundColor Green
        Write-Host "$ollamaApi" -ForegroundColor Cyan
        Write-Host "  Models Available: $($models.Count)" -ForegroundColor White
    } catch {
        Write-Host "  Ollama API: OFFLINE" -ForegroundColor Red

        if ($AutoStart) {
            $pythonCmd = @(Resolve-PythonCmd)
            $managedStartOk = $false
            if (@($pythonCmd).Count -gt 0 -and (Test-Path (Join-Path $RepoRoot "scripts\start_nusyq.py"))) {
                Write-Host "  AutoStart: invoking NuSyQ Ollama manager..." -ForegroundColor Yellow
                $pythonExe = $pythonCmd[0]
                $pythonArgs = @()
                if (@($pythonCmd).Count -gt 1) {
                    $pythonArgs = $pythonCmd[1..(@($pythonCmd).Count - 1)]
                }
                & $pythonExe @pythonArgs "scripts\start_nusyq.py" "ollama" "ensure" | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Start-Sleep -Seconds 2
                    try {
                        $retry = Invoke-WebRequest -Uri "$ollamaApi/api/tags" `
                            -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
                        $models = ($retry.Content | ConvertFrom-Json).models
                        Write-Host "  AutoStart: Ollama manager recovered the API " -NoNewline -ForegroundColor Green
                        Write-Host "$ollamaApi" -ForegroundColor Cyan
                        $managedStartOk = $true
                    } catch { <# continue to raw fallback #> }
                }
            }

            if ($managedStartOk) {
                # Manager path succeeded; skip raw binary launch.
            } else {
            # Locate ollama.exe — prefer PATH, fall back to standard install dir.
            $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
            $ollamaExe = $null
            if ($ollamaCommand) {
                $ollamaExe = $ollamaCommand.Source
            }
            if (-not $ollamaExe) {
                $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.EXE"
            }

            if (Test-Path $ollamaExe) {
                Write-Host "  AutoStart: launching ollama serve..." -ForegroundColor Yellow
                Start-Process -FilePath $ollamaExe -ArgumentList "serve" `
                    -WindowStyle Hidden -PassThru | Out-Null

                # Give the server up to 10 seconds to become ready.
                $ready = $false
                for ($i = 0; $i -lt 10; $i++) {
                    Start-Sleep -Seconds 1
                    try {
                        $retry = Invoke-WebRequest -Uri "$ollamaApi/api/tags" `
                            -Method GET -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
                        $models = ($retry.Content | ConvertFrom-Json).models
                        Write-Host "  AutoStart: Ollama is now ONLINE " -NoNewline -ForegroundColor Green
                        Write-Host "$ollamaApi" -ForegroundColor Cyan
                        $ready = $true
                        break
                    } catch { <# still starting #> }
                }

                if (-not $ready) {
                    Write-Host "  AutoStart: timed out waiting for Ollama." -ForegroundColor DarkYellow
                    Write-Host "  Run manually: " -NoNewline -ForegroundColor Yellow
                    Write-Host "ollama serve" -ForegroundColor Cyan
                    $models = @()
                }
            } else {
                Write-Host "  AutoStart: ollama.exe not found at '$ollamaExe'" -ForegroundColor DarkYellow
                Write-Host "  Install from: " -NoNewline -ForegroundColor Yellow
                Write-Host "https://ollama.com/download" -ForegroundColor Cyan
                $models = @()
            }
            }
        } else {
            Write-Host "  Start with: " -NoNewline -ForegroundColor Yellow
            Write-Host "ollama serve" -ForegroundColor Cyan
            Write-Host "  (use -AutoStart to do this automatically)" -ForegroundColor DarkGray
            $models = @()
        }
    }
    Write-Host ""

    if ($models.Count -gt 0) {
        Write-Host "--- Installed Models ----------------------------------------" -ForegroundColor Yellow
        $models | Select-Object -First 8 | ForEach-Object {
            $size = [math]::Round($_.size / 1GB, 1)
            Write-Host "  - $($_.name)" -NoNewline -ForegroundColor White
            Write-Host " ($size GB)" -ForegroundColor DarkGray
        }
        if ($models.Count -gt 8) {
            Write-Host "  ... and $($models.Count - 8) more" -ForegroundColor DarkGray
        }
        Write-Host ""
    }

    Write-Host "--- Recent Activity ------------------------------------------" -ForegroundColor Yellow
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "  $_" -ForegroundColor White
        }
    } else {
        Write-Host "  (no activity logged yet)" -ForegroundColor DarkGray
    }
    Write-Host ""

    Write-Host "--- Quick Reference ------------------------------------------" -ForegroundColor Yellow
    Write-Host "  ollama list              " -NoNewline -ForegroundColor Gray
    Write-Host "# List installed models" -ForegroundColor DarkGray
    Write-Host "  ollama run qwen2.5-coder " -NoNewline -ForegroundColor Gray
    Write-Host "# Start interactive session" -ForegroundColor DarkGray
    Write-Host "  ollama pull <model>      " -NoNewline -ForegroundColor Gray
    Write-Host "# Download new model" -ForegroundColor DarkGray

    if ($Watch) {
        Write-Host ""
        Write-Host "Refreshing in $IntervalSeconds`s... (Ctrl+C to stop)" -ForegroundColor DarkGray
        Start-Sleep -Seconds $IntervalSeconds
    } else {
        Write-Host ""
        Write-Host "One-shot complete. Re-run with -Watch for continuous refresh." -ForegroundColor DarkGray
    }
} while ($Watch)
