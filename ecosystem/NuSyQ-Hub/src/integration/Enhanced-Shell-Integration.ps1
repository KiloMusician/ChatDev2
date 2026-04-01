# Enhanced PowerShell Profile for Improved Shell Integration

# Idempotent load guard: if this file is dot-sourced multiple times, avoid
# re-defining functions and causing duplicate prompt wrappers which can
# lead to recursive prompt invocation and stack overflows.
# Allow users to opt-out of loading this integration by setting the
# NUSYQ_DISABLE_PWSH environment variable to '1' in their terminal or
# VS Code terminal settings. This helps debugging when the integrated
# terminal behaves badly.
if ($env:NUSYQ_DISABLE_PWSH -eq '1') {
    Write-Host "Enhanced Shell Integration disabled via NUSYQ_DISABLE_PWSH=1" -ForegroundColor Yellow
    return
}

if ($global:_ENH_SHELL_INTEGRATION_LOADED) { return }
$global:_ENH_SHELL_INTEGRATION_LOADED = $true
# Location: $PROFILE or specific profile location

# ==========================================
# 🚀 ENHANCED SHELL INTEGRATION SETTINGS
# ==========================================

# PSReadLine Configuration for Better Command Detection
Set-PSReadLineOption -PredictionSource HistoryAndPlugin -PredictionViewStyle ListView
Set-PSReadLineOption -EditMode Windows -BellStyle None
Set-PSReadLineOption -HistorySearchCursorMovesToEnd
Set-PSReadLineOption -MaximumHistoryCount 4000

# Try to load compressed-output helpers (optional)
try { . "$PSScriptRoot\pwsh_output_helpers.ps1" } catch {}

# Enhanced Prompt with Command Feedback
function prompt {
    # Guard against recursive re-entry which can happen if prompt calls cause
    # other scriptblocks to be evaluated which in turn call the prompt again.
    if ($global:_ENH_SHELL_PROMPT_GUARD) { return ' ' }
    $global:_ENH_SHELL_PROMPT_GUARD = $true
    try {
        $currentPath = (Get-Location).Path.Replace($HOME, "~")
        $gitBranch = ""

        # Get Git branch if in a repo (silently fail on error)
        try {
            $gitBranch = (git branch --show-current 2>$null)
            if ($gitBranch) { $gitBranch = " ($gitBranch)" }
        } catch { $gitBranch = "" }

        # Use Write-Host for colored output but return a stable string prompt.
        Write-Host "PS " -NoNewline -ForegroundColor Blue
        Write-Host $currentPath -NoNewline -ForegroundColor Green
        if ($gitBranch) { Write-Host $gitBranch -NoNewline -ForegroundColor Yellow }
        Write-Host "> " -NoNewline -ForegroundColor White
        # Return a minimal prompt string; avoids PowerShell attempting to
        # re-evaluate scriptblocks that could re-enter the prompt function.
        return ' '
    }
    finally {
        $global:_ENH_SHELL_PROMPT_GUARD = $false
    }
}

# ==========================================
# 🔧 ENHANCED COMMAND FUNCTIONS
# ==========================================

function Invoke-WithProgress {
    param(
        [string]$Command,
        [string]$Description = "Executing command"
    )

    Write-Host "🚀 $Description..." -ForegroundColor Cyan
    Write-Host "📝 Command: $Command" -ForegroundColor DarkGray

    $startTime = Get-Date
    try {
        $result = Invoke-Expression $Command
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds

        Write-Host "✅ Completed in $($duration.ToString('F2'))s" -ForegroundColor Green
        return $result
    }
    catch {
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds

    # Use compressed error printing to avoid massive repeated stacks
    try { . "$PSScriptRoot\pwsh_output_helpers.ps1" } catch {}
    $err = $_.Exception.ToString()
    Write-CompressedError -ErrorText ("Failed after $($duration.ToString('F2'))s`n`n" + $err) -Prefix "Failed"
    throw
    }
}

function Start-EnhancedContextBrowser {
    param(
        [int]$Port = 8501,
        [switch]$OpenBrowser = $true
    )

    $scriptPath = "src/interface/Enhanced-Interactive-Context-Browser.py"

    if (-not (Test-Path $scriptPath)) {
        Write-Host "❌ Enhanced Context Browser not found at: $scriptPath" -ForegroundColor Red
        return
    }

    Write-Host "🔍 Enhanced Context Browser Launcher" -ForegroundColor Magenta
    Write-Host "=" * 50 -ForegroundColor DarkGray

    # Check Python availability
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "🐍 Python: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Python not available" -ForegroundColor Red
        return
    }

    # Check Streamlit availability
    try {
        $streamlitVersion = python -c "import streamlit; print(streamlit.__version__)" 2>&1
        Write-Host "⚡ Streamlit: $streamlitVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Streamlit not available" -ForegroundColor Red
        return
    }

    # Launch the application
    $command = "streamlit run `"$scriptPath`" --server.port $Port"
    if (-not $OpenBrowser) {
        $command += " --server.headless true"
    }

    Write-Host "🚀 Starting Enhanced Context Browser on port $Port..." -ForegroundColor Cyan
    Write-Host "🌐 URL: http://localhost:$Port" -ForegroundColor Blue
    Write-Host "📝 Command: $command" -ForegroundColor DarkGray
    Write-Host "=" * 50 -ForegroundColor DarkGray

    Invoke-Expression $command
}

function Test-ContextBrowser {
    Write-Host "🧪 Testing Enhanced Context Browser Components..." -ForegroundColor Yellow

    # Prefer the venv python if present, otherwise fallback to system python
    $venvPython = Join-Path -Path (Get-Location) -ChildPath ".venv\Scripts\python.exe"
    $pythonCmd = $null
    if (Test-Path $venvPython) { $pythonCmd = $venvPython } else {
        $p = Get-Command python -ErrorAction SilentlyContinue
        if ($p) { $pythonCmd = $p.Path }
    }

    if (-not $pythonCmd) { Write-Host "Warning: python not found on PATH and .venv not present" -ForegroundColor Yellow }

    $tests = @(
        @{ Name = "Python Import"; Command = "python -c `"print('✅ Python working')`"" },
        @{ Name = "Streamlit Import"; Command = "python -c `"import streamlit; print('✅ Streamlit available')`"" },
        @{ Name = "File Existence"; Command = "Test-Path 'src/interface/Enhanced-Interactive-Context-Browser.py'" },
        @{ Name = "Syntax Check"; Command = "python -m py_compile 'src/interface/Enhanced-Interactive-Context-Browser.py'" }
    )

    foreach ($test in $tests) {
        Write-Host "  🔍 $($test.Name)..." -NoNewline
        try {
            $exit = 1
            $result = $null
            switch ($test.Name) {
                'Python Import' {
                    if (-not $pythonCmd) { throw "python not found" }
                    $result = & $pythonCmd -c "print('✅ Python working')" 2>&1
                    $exit = $LASTEXITCODE
                }
                'Streamlit Import' {
                    if (-not $pythonCmd) { throw "python not found" }
                    $result = & $pythonCmd -c "import streamlit; print('✅ Streamlit available')" 2>&1
                    $exit = $LASTEXITCODE
                }
                'File Existence' {
                    $ok = Test-Path 'src/interface/Enhanced-Interactive-Context-Browser.py'
                    if ($ok) { $exit = 0; $result = $true } else { $exit = 1; $result = $false }
                }
                'Syntax Check' {
                    if (-not $pythonCmd) { throw "python not found" }
                    $result = & $pythonCmd -m py_compile 'src/interface/Enhanced-Interactive-Context-Browser.py' 2>&1
                    $exit = $LASTEXITCODE
                }
                default {
                    # Fallback: attempt to run the command string safely
                    $cmd = $test.Command
                    $result = Invoke-Expression $cmd 2>&1
                    $exit = $LASTEXITCODE
                }
            }

            if (($exit -eq 0) -or ($result -eq $true)) {
                Write-Host " ✅" -ForegroundColor Green
            } else {
                Write-Host " ❌" -ForegroundColor Red
                $body = "ExitCode=$exit`nOutput:`n$result"
                if (Get-Command Write-CompressedError -ErrorAction SilentlyContinue) {
                    Write-CompressedError -ErrorText $body -Prefix "Test Failed"
                } else {
                    Write-Host "    ExitCode: $exit" -ForegroundColor DarkRed
                    foreach ($ln in ($result -split "`n")) { Write-Host "    $ln" -ForegroundColor DarkRed }
                }
            }
        }
        catch {
            Write-Host " ❌" -ForegroundColor Red
            try { . "$PSScriptRoot\pwsh_output_helpers.ps1" } catch {}
            Write-CompressedError -ErrorText $_.Exception.ToString() -Prefix "Exception"
        }
    }
}

# ==========================================
# 🎯 ALIASES AND SHORTCUTS
# ==========================================

Set-Alias -Name "context" -Value Start-EnhancedContextBrowser
Set-Alias -Name "testcontext" -Value Test-ContextBrowser
Set-Alias -Name "run" -Value Invoke-WithProgress

# ==========================================
# 🚀 STARTUP MESSAGE
# ==========================================

Write-Host ""
Write-Host "🛡️ Enhanced Shell Integration Loaded!" -ForegroundColor Green
Write-Host "📚 Available commands:" -ForegroundColor Cyan
Write-Host "  • context [port] - Start Enhanced Context Browser" -ForegroundColor White
Write-Host "  • testcontext    - Test Context Browser components" -ForegroundColor White
Write-Host "  • run <command>  - Execute command with progress feedback" -ForegroundColor White
Write-Host ""
