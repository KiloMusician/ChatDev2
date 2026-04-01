# Terminal Depths — PowerShell Quickstart
# ════════════════════════════════════════════════════════════════════════════════
# Universal entry point for Windows PowerShell 5+, PowerShell Core 7+.
# Works in: VS Code terminal, Windows Terminal, ISE, GitHub Actions, CI/CD.
#
# Usage:
#   pwsh bootstrap/td_quickstart.ps1
#   $env:TD_URL="https://my.replit.app"; pwsh bootstrap/td_quickstart.ps1
#   $env:TD_AGENT_NAME="Copilot"; $env:TD_AGENT_TYPE="copilot"; pwsh ...
# ════════════════════════════════════════════════════════════════════════════════
[CmdletBinding()]
param(
    [string]$Command = "",
    [switch]$NoColor
)

$TdUrl = $env:TD_URL ?? "http://localhost:5000"
$TokenFile = $env:TD_TOKEN_FILE ?? (Join-Path $env:USERPROFILE ".td_token")
$AgentName = $env:TD_AGENT_NAME ?? ""
$AgentType = $env:TD_AGENT_TYPE ?? "powershell_agent"

function Write-Td {
    param([string]$Text, [string]$Color = "White")
    if ($NoColor) { Write-Host "  $Text" }
    else { Write-Host "  $Text" -ForegroundColor $Color }
}

function Invoke-TdApi {
    param([string]$Path, [hashtable]$Body = @{}, [string]$Token = "", [string]$Method = "POST")
    $headers = @{ "Content-Type" = "application/json" }
    if ($Token) { $headers["X-Agent-Token"] = $Token }
    $uri = "$TdUrl$Path"
    try {
        if ($Method -eq "GET") {
            return Invoke-RestMethod -Uri $uri -Method GET -Headers $headers -ErrorAction Stop
        }
        $json = $Body | ConvertTo-Json -Compress
        return Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $json -ErrorAction Stop
    } catch {
        return @{ error = $_.Exception.Message }
    }
}

function Render-Output {
    param([array]$Output)
    foreach ($line in $Output) {
        $text = if ($line.s) { $line.s } else { "$line" }
        $color = switch ($line.t) {
            "lore"    { "Magenta" }
            "system"  { "Cyan" }
            "success" { "Green" }
            "error"   { "Red" }
            "warn"    { "Yellow" }
            "xp"      { "Green" }
            "story"   { "Magenta" }
            default   { "Gray" }
        }
        Write-Td $text $color
    }
}

# Banner
Write-Host ""
Write-Td "◈ TERMINAL DEPTHS — PowerShell Quickstart" "Cyan"
Write-Td "Server: $TdUrl" "DarkGray"
Write-Host ""

# Health check
$health = Invoke-TdApi -Path "/api/health" -Method GET
if ($health.error) {
    Write-Td "Server unreachable: $($health.error)" "Red"
    Write-Td "Start: python -m cli.devmentor serve" "DarkGray"
    exit 1
}
Write-Td "Server reachable" "Green"

# Load or register
$token = ""
$agentId = ""
$savedName = ""

if (Test-Path $TokenFile) {
    try {
        $saved = Get-Content $TokenFile | ConvertFrom-Json
        if ($saved.server -eq $TdUrl -and $saved.token) {
            $profile = Invoke-TdApi -Path "/api/agent/profile" -Method GET -Token $saved.token
            if (-not $profile.error) {
                $token = $saved.token
                $agentId = $saved.agent_id
                $savedName = $saved.name
                Write-Td "Loaded identity: $savedName" "Green"
            }
        }
    } catch {}
}

if (-not $token) {
    if (-not $AgentName) {
        $AgentName = Read-Host "  Agent name [$env:USERNAME]"
        if (-not $AgentName) { $AgentName = $env:USERNAME }
    }
    $hostname = $env:COMPUTERNAME.ToLower() -replace '[^a-z0-9]', '-'
    $email = "$($AgentName.ToLower() -replace ' ', '_')@$hostname.terminal-depths"
    
    $result = Invoke-TdApi -Path "/api/agent/register" -Body @{
        name = $AgentName; email = $email; agent_type = $AgentType
    }
    
    if ($result.error) {
        Write-Td "Registration failed: $($result.error)" "Red"
        exit 1
    }
    
    $token = $result.token
    $agentId = $result.agent_id
    @{ token=$token; agent_id=$agentId; name=$AgentName; server=$TdUrl } |
        ConvertTo-Json | Set-Content $TokenFile
    Write-Td "Registered: $AgentName [$AgentType]" "Green"
    Write-Td "Token saved to $TokenFile" "DarkGray"
}

function Run-Command {
    param([string]$Cmd)
    $result = Invoke-TdApi -Path "/api/agent/command" -Body @{ command = $Cmd } -Token $token
    if ($result.error) {
        Write-Td "Error: $($result.error)" "Red"
    } else {
        Render-Output -Output $result.output
    }
}

# Single command mode
if ($Command) {
    Run-Command -Cmd $Command
    return
}

# Interactive REPL
Write-Td "Connected. Type 'exit' to quit." "Green"
Write-Td "Tip: try 'help', 'tutorial', 'quests', 'hive', 'lore'" "DarkGray"
Write-Host ""

while ($true) {
    Write-Host "  ghost@node-7:~`$ " -ForegroundColor Green -NoNewline
    $cmd = Read-Host
    if (-not $cmd) { continue }
    if ($cmd -match '^(exit|quit|q)$') {
        Write-Td "Session ended. Progress saved." "DarkGray"
        break
    }
    Run-Command -Cmd $cmd
    Write-Host ""
}
