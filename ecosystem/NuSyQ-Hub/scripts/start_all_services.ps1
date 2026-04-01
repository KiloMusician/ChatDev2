# NuSyQ Multi-Repository Service Startup Automation
# Starts Ollama, SimulatedVerse, and validates NuSyQ-Hub integration
# Run: .\scripts\start_all_services.ps1

param(
    [switch]$SkipOllama,
    [switch]$SkipSimulatedVerse,
    [switch]$SkipPreflight,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
Write-Host "NuSyQ Multi-Repository Service Startup" -ForegroundColor Cyan

$hubRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

function Resolve-PythonCmd {
    if ($env:PYTHON_EXE -and (Test-Path $env:PYTHON_EXE)) {
        return @($env:PYTHON_EXE)
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return @("python3")
    }
    $candidates = @(
        (Join-Path $env:USERPROFILE "AppData\\Local\\Programs\\Python\\Python312\\python.exe"),
        (Join-Path $env:USERPROFILE "AppData\\Local\\Programs\\Python\\Python311\\python.exe"),
        (Join-Path $env:USERPROFILE "AppData\\Local\\Programs\\Python\\Python310\\python.exe"),
        "C:\\Python312\\python.exe",
        "C:\\Python311\\python.exe",
        "C:\\Python310\\python.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return @($candidate)
        }
    }
    return @()
}

function Invoke-Python {
    param([string[]]$Args)
    $py = Resolve-PythonCmd
    if ($py.Count -eq 0) {
        throw "Python not found on PATH."
    }
    & $py @Args
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try {
        return Get-Content -Path $Path -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Resolve-SimulatedVersePath {
    $candidates = @()
    if ($env:SIMULATEDVERSE_PATH) { $candidates += $env:SIMULATEDVERSE_PATH }

    $serviceConfig = Read-JsonFile (Join-Path $hubRoot "config/service_config.json")
    if ($serviceConfig -and $serviceConfig.paths -and $serviceConfig.paths.simulatedverse) {
        $candidates += $serviceConfig.paths.simulatedverse
    }

    $workspaceMapping = Join-Path $hubRoot "config/workspace_mapping.yaml"
    if (Test-Path $workspaceMapping) {
        try {
            $yamlLines = Get-Content -Path $workspaceMapping
            $simLine = $yamlLines | Where-Object { $_ -match 'SimulatedVerse' } | Select-Object -First 1
            if ($simLine) {
                $idx = [Array]::IndexOf($yamlLines, $simLine)
                for ($back = 1; $back -le 3; $back++) {
                    if ($idx - $back -lt 0) { break }
                    $prev = $yamlLines[$idx - $back].Trim()
                    if ($prev.StartsWith('path:')) {
                        $candidates += $prev.Split(':', 2)[1].Trim()
                        break
                    }
                }
            }
        } catch {
            # best-effort; ignore YAML parse issues
        }
    }

    $candidates += @(
        (Join-Path $env:USERPROFILE "Desktop\SimulatedVerse\SimulatedVerse"),
        (Join-Path $env:USERPROFILE "Desktop\SimulatedVerse"),
        (Join-Path (Split-Path $hubRoot -Parent) "SimulatedVerse\SimulatedVerse")
    )

    foreach ($candidate in $candidates) {
        if (-not $candidate) { continue }
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Resolve-SimulatedVersePort {
    if ($env:SIMULATEDVERSE_PORT) { return $env:SIMULATEDVERSE_PORT }
    $serviceConfig = Read-JsonFile (Join-Path $hubRoot "config/service_config.json")
    if ($serviceConfig -and $serviceConfig.services -and $serviceConfig.services.simverse_dev -and $serviceConfig.services.simverse_dev.port) {
        return [string]$serviceConfig.services.simverse_dev.port
    }
    return "5002"
}

function Find-AvailablePort {
    param([int]$StartPort)
    for ($port = $StartPort; $port -lt ($StartPort + 10); $port++) {
        $inUse = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if (-not $inUse) { return $port }
    }
    return $StartPort
}

$preflightScript = Join-Path $PSScriptRoot "check_env.py"
if (-not $SkipPreflight -and (Test-Path $preflightScript)) {
    Write-Host "`nRunning preflight (env + paths)..." -ForegroundColor Yellow
    try {
        Invoke-Python @($preflightScript) | Out-String | Write-Host
    } catch {
        Write-Warning "Python not available for preflight (py/python not on PATH)."
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Preflight reported missing config; continuing startup."
    }
}

$simverseHost = $env:SIMULATEDVERSE_HOST
if (-not $simverseHost) {
    $simverseHost = "http://127.0.0.1"
}
$simversePort = Resolve-SimulatedVersePort
$simversePortInt = [int]$simversePort
$simversePort = [string](Find-AvailablePort -StartPort $simversePortInt)
$env:SIMULATEDVERSE_PORT = $simversePort
$simverseBase = "$simverseHost`:$simversePort"

# Configure Ollama environment
if (-not $SkipOllama) {
    Write-Host "`nConfiguring Ollama..." -ForegroundColor Yellow

    # Set OLLAMA_MODELS to user home directory (not D: drive)
    $ollamaPath = Join-Path $env:USERPROFILE ".ollama\models"
    if ($env:OLLAMA_MODELS -ne $ollamaPath) {
        Write-Host "   Setting OLLAMA_MODELS: $ollamaPath" -ForegroundColor Gray
        $env:OLLAMA_MODELS = $ollamaPath

        # Set permanently for user
        try {
            [System.Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $ollamaPath, 'User')
            Write-Host "   Environment variable set permanently" -ForegroundColor Green
        } catch {
            Write-Warning "   Could not set permanent environment variable (requires restart)"
        }
    }

    # Check if Ollama is already running
    $ollamaRunning = $false
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -Method GET -TimeoutSec 2 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $ollamaRunning = $true
            Write-Host "   Ollama already running on port 11434" -ForegroundColor Green
        }
    } catch {
        Write-Host "   Ollama not running, starting service..." -ForegroundColor Gray
    }

    # Start Ollama if not running
    if (-not $ollamaRunning) {
        Write-Host "   Starting Ollama service..." -ForegroundColor Gray
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -PassThru | Out-Null
        Start-Sleep -Seconds 3

        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:11434/api/tags" -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "   Ollama started successfully" -ForegroundColor Green

                # List available models
                if ($Verbose) {
                    Write-Host "   Available models:" -ForegroundColor Gray
                    & ollama list
                }
            }
        } catch {
            Write-Warning "   Ollama may not have started correctly"
        }
    }
}

# Start SimulatedVerse
if (-not $SkipSimulatedVerse) {
    Write-Host "`nStarting SimulatedVerse Consciousness Engine..." -ForegroundColor Yellow

    $simversePath = Resolve-SimulatedVersePath
    if ($simversePath) {
        $env:SIMULATEDVERSE_PATH = $simversePath
        # Check if ChatDev dependencies are installed
        Write-Host "   Checking ChatDev dependencies..." -ForegroundColor Gray
        Push-Location "$simversePath\ChatDev"

        try {
            $pipList = Invoke-Python @("-m", "pip", "list") 2>&1 | Out-String
        } catch {
            $pipList = ""
            Write-Warning "Python/pip not available; skipping ChatDev dependency check."
        }
        $needsInstall = @()

        if ($pipList -notmatch "easydict") { $needsInstall += "easydict" }
        if ($pipList -notmatch "faiss") { $needsInstall += "faiss-cpu" }
        if ($pipList -notmatch "beautifulsoup4") { $needsInstall += "beautifulsoup4" }
        if ($pipList -notmatch "tenacity") { $needsInstall += "tenacity" }

        if ($needsInstall.Count -gt 0) {
            Write-Host "   Installing missing dependencies: $($needsInstall -join ', ')" -ForegroundColor Gray
            try {
                Invoke-Python @("-m", "pip", "install") $needsInstall "--quiet" | Out-Null
                Write-Host "   Dependencies installed" -ForegroundColor Green
            } catch {
                Write-Warning "   Failed to install ChatDev dependencies (python/pip not on PATH)."
            }
        } else {
            Write-Host "   All dependencies present" -ForegroundColor Green
        }

        Pop-Location

        $useMinimal = -not $env:DATABASE_URL
        $npmScript = if ($useMinimal) { "dev:minimal" } else { "dev" }
        $healthPath = if ($useMinimal) { "/api/health" } else { "/healthz" }

        if ($useMinimal) {
            Write-Host "   DATABASE_URL missing; using agent-only mode (dev:minimal)" -ForegroundColor Yellow
        }

        # Start SimulatedVerse dev server
        Write-Host "   Launching consciousness engine on port $simversePort..." -ForegroundColor Gray
        Push-Location $simversePath

        # Start npm dev server using cmd to inherit PATH (log to NuSyQ-Hub/logs)
        $logsDir = Join-Path $hubRoot "logs"
        if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }
        $logFile = Join-Path $logsDir "simverse.dev.log"
        $npmDir = $null
        try {
            $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
            if ($npmCmd) { $npmDir = Split-Path -Parent $npmCmd.Source }
        } catch {
            $npmDir = $null
        }
        if (-not $npmDir -and (Test-Path "C:\\Program Files\\nodejs\\npm.cmd")) {
            $npmDir = "C:\\Program Files\\nodejs"
        }
        $env:PORT = $simversePort
        $env:SIMULATEDVERSE_PORT = $simversePort
        $logFileErr = Join-Path $logsDir "simverse.dev.err.log"

        if ($useMinimal) {
            $env:NODE_ENV = "development"
            $nodeExe = $null
            if (Test-Path "C:\\Program Files\\nodejs\\node.exe") {
                $nodeExe = "C:\\Program Files\\nodejs\\node.exe"
            } else {
                try {
                    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
                    if ($nodeCmd) { $nodeExe = $nodeCmd.Source }
                } catch {
                    $nodeExe = "node"
                }
            }
            $tsxCli = Join-Path $simversePath "node_modules\\tsx\\dist\\cli.cjs"
            Start-Process -FilePath $nodeExe -ArgumentList $tsxCli, "server/minimal-agent-server.ts" -WorkingDirectory $simversePath -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $logFileErr -PassThru | Out-Null
        } else {
            $npmExe = if ($npmDir) { Join-Path $npmDir "npm.cmd" } else { "npm" }
            Start-Process -FilePath $npmExe -ArgumentList "run", $npmScript -WorkingDirectory $simversePath -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $logFileErr -PassThru | Out-Null
        }

        Write-Host "   Waiting for SimulatedVerse to initialize..." -ForegroundColor Gray
        Start-Sleep -Seconds 10

        try {
            $response = Invoke-WebRequest -Uri "$simverseBase$healthPath" -Method GET -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "   SimulatedVerse running on port $simversePort" -ForegroundColor Green
            }
        } catch {
            Write-Warning "   SimulatedVerse may still be initializing (check logs)"
        }

        Pop-Location
    } else {
        Write-Warning "   SimulatedVerse path not found. Set SIMULATEDVERSE_PATH to the repo root (e.g., C:\Users\you\Desktop\SimulatedVerse\SimulatedVerse)."
    }
}

# Validate NuSyQ-Hub integration
Write-Host "`nRunning integration health check..." -ForegroundColor Yellow
$healthCheckPath = Join-Path $PSScriptRoot "integration_health_check.py"

if (Test-Path $healthCheckPath) {
    try {
        $healthResult = Invoke-Python @($healthCheckPath) 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
    } catch {
        $healthResult = $null
        Write-Warning "Python not available for integration health check."
    }

    if ($healthResult) {
        Write-Host "`nService Status:" -ForegroundColor Cyan

        if ($healthResult.ollama_status.ok) {
            Write-Host "   Ollama: ONLINE ($($healthResult.ollama_base))" -ForegroundColor Green
        } else {
            Write-Host "   Ollama: OFFLINE" -ForegroundColor Red
        }

        if ($healthResult.simulatedverse_status.ok) {
            Write-Host "   SimulatedVerse: ONLINE ($($healthResult.simulatedverse_base))" -ForegroundColor Green
        } else {
            Write-Host "   SimulatedVerse: OFFLINE" -ForegroundColor Red
        }

        if ($healthResult.chatdev_exists) {
            Write-Host "   ChatDev: CONFIGURED ($($healthResult.FS_CHATDEV_PATH.path))" -ForegroundColor Green
        }

        if ($healthResult.openai_key_sets) {
            Write-Host "   OpenAI API: CONFIGURED" -ForegroundColor Green
        }
    }
} else {
    Write-Warning "Health check script not found, skipping validation"
}

Write-Host "`nService startup complete!" -ForegroundColor Green
Write-Host "   Ollama: http://127.0.0.1:11434" -ForegroundColor Gray
Write-Host "   SimulatedVerse: $simverseBase" -ForegroundColor Gray
Write-Host "`nTo monitor services: Get-Process ollama,node" -ForegroundColor Cyan
