# keeper-mcp.ps1 — Bridge-backed MCP stdio server exposing keeper commands as tools
# JSON-RPC 2.0 over stdin/stdout (MCP protocol)

[Console]::InputEncoding  = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$KeeperRoot   = if ($env:KEEPER_ROOT) { $env:KEEPER_ROOT } else { (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$KeeperBridge = Join-Path $KeeperRoot "tools\keeper-bridge.ps1"
$AgentManifestPath = Join-Path $KeeperRoot "agent_manifest.json"

function Send-Response {
    param([hashtable]$Response)
    $json = $Response | ConvertTo-Json -Depth 12 -Compress
    [Console]::WriteLine($json)
}

function Send-Error {
    param([object]$Id, [int]$Code, [string]$Message)
    Send-Response @{
        jsonrpc = "2.0"
        id      = $Id
        error   = @{ code = $Code; message = $Message }
    }
}

function Send-ToolResult {
    param([object]$Id, [string]$Text)
    Send-Response @{
        jsonrpc = "2.0"
        id      = $Id
        result  = @{ content = @(@{ type = "text"; text = $Text }) }
    }
}

function Get-HostPowerShellExecutable {
    foreach ($candidate in @("pwsh.exe", "pwsh", "powershell.exe")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
    }

    throw "No PowerShell executable was found for keeper-mcp.ps1."
}

function Get-BoolArgument {
    param($Arguments, [string]$Name, [bool]$Default = $false)

    if ($null -eq $Arguments -or -not $Arguments.ContainsKey($Name)) {
        return $Default
    }

    return [bool]$Arguments[$Name]
}

function Get-StringArgument {
    param($Arguments, [string]$Name, [string]$Default = "")

    if ($null -eq $Arguments -or -not $Arguments.ContainsKey($Name)) {
        return $Default
    }

    return [string]$Arguments[$Name]
}

function Invoke-KeeperBridgeCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$ExtraArgs = @()
    )

    if (-not (Test-Path -LiteralPath $KeeperBridge)) {
        throw "Keeper bridge was not found: $KeeperBridge"
    }

    $powerShell = Get-HostPowerShellExecutable
    $allArgs = @(
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $KeeperBridge,
        $Command
    ) + $ExtraArgs

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $powerShell
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true

    foreach ($argument in $allArgs) {
        [void]$startInfo.ArgumentList.Add($argument)
    }

    $process = [System.Diagnostics.Process]::Start($startInfo)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    $text = (@($stdout, $stderr) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) -join "`n"
    $text = $text.Trim()

    if ($process.ExitCode -ne 0) {
        if ([string]::IsNullOrWhiteSpace($text)) {
            throw "Keeper bridge command '$Command' failed with exit code $($process.ExitCode)."
        }
        throw $text
    }

    return $text
}

function Get-AgentBootstrapPayload {
    $manifest = $null
    if (Test-Path -LiteralPath $AgentManifestPath) {
        $manifest = Get-Content -LiteralPath $AgentManifestPath -Raw -ErrorAction SilentlyContinue
    }

    $payload = [pscustomobject]@{
        keeper_root          = $KeeperRoot
        bridge_path          = $KeeperBridge
        manifest_path        = $AgentManifestPath
        preferred_bootstrap  = @(
            "Call keeper_snapshot first.",
            "Use keeper_score / keeper_advisor / keeper_games / keeper_think before broader flows.",
            "Use keeper_analyze only when deterministic outputs are insufficient."
        )
        manifest             = if ([string]::IsNullOrWhiteSpace($manifest)) { $null } else { $manifest | ConvertFrom-Json }
    }

    return ($payload | ConvertTo-Json -Depth 12)
}

$tools = @(
    @{
        name        = "keeper_bootstrap"
        description = "Return the Keeper agent manifest and low-token startup guidance. Call this before broader orchestration if you need repo-local agent context."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_snapshot"
        description = "Get the full structured Keeper runtime snapshot. Preferred first call for current state, recent sessions, listener state, and brain state."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_status"
        description = "Get the current health snapshot only."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_games"
        description = "Get Steam/game metadata only."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_score"
        description = "Get weighted system pressure score (0-100) with disk/CPU/RAM/contention signals."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_advisor"
        description = "Get the deterministic advisor recommendation for the current pressure state."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_think"
        description = "Get the maintenance audit: disk, Docker, WSL, temp, downloads, npm cache, and suggested actions."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_doctor"
        description = "Get structured diagnostics. Set audio_triage=true to include focused audio/Nahimic/driver triage."
        inputSchema = @{
            type       = "object"
            properties = @{
                audio_triage            = @{ type = "boolean"; description = "Include focused audio triage output." }
                latencymon_report_path  = @{ type = "string"; description = "Optional explicit LatencyMon report path." }
            }
            required   = @()
        }
    },
    @{
        name        = "keeper_recommend"
        description = "Get the deterministic mode recommendation without applying it."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_recommend_apply"
        description = "Apply the current deterministic mode recommendation."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_auto"
        description = "Get the safe automation plan for coding vs balanced."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_auto_apply"
        description = "Apply the safe automation plan now."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_mode"
        description = "Apply or restore a Keeper mode profile."
        inputSchema = @{
            type       = "object"
            properties = @{
                mode = @{
                    type        = "string"
                    enum        = @("gaming", "coding", "balanced", "diagnose", "audio-safe", "quiet", "rimworld-mod", "heavy-gaming", "restore")
                    description = "Mode profile to apply."
                }
                kill_code = @{
                    type        = "boolean"
                    description = "When true, enables Keeper's KillCode behavior for this run."
                }
            }
            required   = @("mode")
        }
    },
    @{
        name        = "keeper_export"
        description = "Write an incident export bundle. Set html=true for HTML output and audio_triage=true for focused audio triage."
        inputSchema = @{
            type       = "object"
            properties = @{
                html                   = @{ type = "boolean"; description = "Write HTML output." }
                audio_triage           = @{ type = "boolean"; description = "Include focused audio triage." }
                latencymon_report_path = @{ type = "string"; description = "Optional explicit LatencyMon report path." }
            }
            required   = @()
        }
    },
    @{
        name        = "keeper_maintain"
        description = "Run the maintenance pass now."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    },
    @{
        name        = "keeper_optimize"
        description = "Apply the advisor recommendation. Set force=true to override safe_to_apply gating."
        inputSchema = @{
            type       = "object"
            properties = @{
                force = @{ type = "boolean"; description = "Override safe_to_apply gating." }
            }
            required   = @()
        }
    },
    @{
        name        = "keeper_analyze"
        description = "Run Ollama-assisted deep analysis. Use after snapshot/score/advisor/doctor, not before."
        inputSchema = @{ type = "object"; properties = @{}; required = @() }
    }
)

while ($true) {
    $line = [Console]::ReadLine()
    if ($null -eq $line) { break }

    $line = $line.Trim()
    if ($line -eq "") { continue }

    try {
        $request = $line | ConvertFrom-Json -AsHashtable -ErrorAction Stop
    }
    catch {
        Send-Error -Id $null -Code -32700 -Message "Parse error"
        continue
    }

    $id     = $request["id"]
    $method = $request["method"]
    $params = $request["params"]

    switch ($method) {
        "initialize" {
            Send-Response @{
                jsonrpc = "2.0"
                id      = $id
                result  = @{
                    protocolVersion = "2024-11-05"
                    capabilities    = @{ tools = @{ listChanged = $false } }
                    serverInfo      = @{ name = "katana-keeper"; version = "1.1.0" }
                }
            }
        }
        "notifications/initialized" {
            continue
        }
        "tools/list" {
            Send-Response @{
                jsonrpc = "2.0"
                id      = $id
                result  = @{ tools = $tools }
            }
        }
        "tools/call" {
            try {
                $toolName = [string]$params["name"]
                $toolArgs = $params["arguments"]
                $output = $null

                switch ($toolName) {
                    "keeper_bootstrap" {
                        $output = Get-AgentBootstrapPayload
                    }
                    "keeper_snapshot" {
                        $output = Invoke-KeeperBridgeCommand -Command "snapshot"
                    }
                    "keeper_status" {
                        $output = Invoke-KeeperBridgeCommand -Command "status"
                    }
                    "keeper_games" {
                        $output = Invoke-KeeperBridgeCommand -Command "games"
                    }
                    "keeper_score" {
                        $output = Invoke-KeeperBridgeCommand -Command "score"
                    }
                    "keeper_advisor" {
                        $output = Invoke-KeeperBridgeCommand -Command "advisor"
                    }
                    "keeper_think" {
                        $output = Invoke-KeeperBridgeCommand -Command "think"
                    }
                    "keeper_doctor" {
                        $extraArgs = @()
                        if (Get-BoolArgument -Arguments $toolArgs -Name "audio_triage") {
                            $extraArgs += "-AudioTriage"
                        }

                        $latencyMonReportPath = Get-StringArgument -Arguments $toolArgs -Name "latencymon_report_path"
                        if (-not [string]::IsNullOrWhiteSpace($latencyMonReportPath)) {
                            $extraArgs += @("-LatencyMonReportPath", $latencyMonReportPath)
                        }

                        $output = Invoke-KeeperBridgeCommand -Command "doctor" -ExtraArgs $extraArgs
                    }
                    "keeper_recommend" {
                        $output = Invoke-KeeperBridgeCommand -Command "recommend"
                    }
                    "keeper_recommend_apply" {
                        $output = Invoke-KeeperBridgeCommand -Command "recommend" -ExtraArgs @("-Apply")
                    }
                    "keeper_auto" {
                        $output = Invoke-KeeperBridgeCommand -Command "auto"
                    }
                    "keeper_auto_apply" {
                        $output = Invoke-KeeperBridgeCommand -Command "auto" -ExtraArgs @("-Apply")
                    }
                    "keeper_mode" {
                        $mode = Get-StringArgument -Arguments $toolArgs -Name "mode"
                        if ([string]::IsNullOrWhiteSpace($mode)) {
                            throw "keeper_mode requires a non-empty 'mode' argument."
                        }

                        $extraArgs = @($mode)
                        if (Get-BoolArgument -Arguments $toolArgs -Name "kill_code") {
                            $extraArgs += "-KillCode"
                        }

                        $output = Invoke-KeeperBridgeCommand -Command "mode" -ExtraArgs $extraArgs
                    }
                    "keeper_export" {
                        $extraArgs = @()
                        if (Get-BoolArgument -Arguments $toolArgs -Name "html") {
                            $extraArgs += "-Html"
                        }
                        if (Get-BoolArgument -Arguments $toolArgs -Name "audio_triage") {
                            $extraArgs += "-AudioTriage"
                        }

                        $latencyMonReportPath = Get-StringArgument -Arguments $toolArgs -Name "latencymon_report_path"
                        if (-not [string]::IsNullOrWhiteSpace($latencyMonReportPath)) {
                            $extraArgs += @("-LatencyMonReportPath", $latencyMonReportPath)
                        }

                        $output = Invoke-KeeperBridgeCommand -Command "export" -ExtraArgs $extraArgs
                    }
                    "keeper_maintain" {
                        $output = Invoke-KeeperBridgeCommand -Command "maintain"
                    }
                    "keeper_optimize" {
                        $extraArgs = @()
                        if (Get-BoolArgument -Arguments $toolArgs -Name "force") {
                            $extraArgs += "-Force"
                        }

                        $output = Invoke-KeeperBridgeCommand -Command "optimize" -ExtraArgs $extraArgs
                    }
                    "keeper_analyze" {
                        $output = Invoke-KeeperBridgeCommand -Command "analyze"
                    }
                    default {
                        throw "Unknown tool: $toolName"
                    }
                }

                Send-ToolResult -Id $id -Text $output
            }
            catch {
                Send-Error -Id $id -Code -32000 -Message $_.Exception.Message
            }
        }
        default {
            Send-Error -Id $id -Code -32601 -Message "Method not found: $method"
        }
    }
}
