# Terminal Depths Universal Command for PowerShell
# Installation: Add this directory to $PROFILE

function td {
    <#
    .SYNOPSIS
    Launch Terminal Depths from anywhere
    
    .DESCRIPTION
    Universal launcher for Terminal Depths game/engine
    Works in: PowerShell, VS Code, Docker, CMD, Git Bash
    
    .PARAMETER Mode
    Launch mode: cli (default), web, repl, agent, daemon
    
    .PARAMETER Surface
    Output surface: terminal (default), web, vscode, godot, touchdesigner
    
    .PARAMETER Port
    Port for web/daemon modes (default 7777)
    
    .PARAMETER NoColor
    Disable ANSI colors
    
    .EXAMPLE
    td
    # Launch CLI mode
    
    .EXAMPLE
    td -Mode web -Port 7777
    # Launch web interface
    
    .EXAMPLE
    td -Mode agent -Agent Ada
    # Launch with agent delegation
    #>
    
    param(
        [ValidateSet("cli", "web", "repl", "agent", "daemon")]
        [string]$Mode = "cli",
        
        [ValidateSet("terminal", "web", "vscode", "godot", "touchdesigner")]
        [string]$Surface = "terminal",
        
        [int]$Port = 7777,
        
        [string]$Agent,
        
        [string[]]$Tags,
        
        [switch]$NoColor
    )
    
    # Find NuSyQ root
    $nusyqRoot = if (Test-Path "$PSScriptRoot/../scripts/terminal_depths_launcher.py") {
        Resolve-Path "$PSScriptRoot/../"
    } elseif (Test-Path "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\scripts\terminal_depths_launcher.py") {
        "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub"
    } else {
        Write-Error "Terminal Depths launcher not found. Check NUSYQ_ROOT."
        return
    }
    
    # Build arguments
    $args = @(
        "-m", "scripts.terminal_depths_launcher",
        "--mode", $Mode,
        "--surface", $Surface,
        "--port", $Port
    )
    
    if ($Agent) {
        $args += @("--agent", $Agent)
    }
    
    if ($Tags) {
        $args += @("--tags") + $Tags
    }
    
    if ($NoColor) {
        $args += "--no-color"
    }
    
    # Run launcher
    Push-Location $nusyqRoot
    try {
        & python @args
    } finally {
        Pop-Location
    }
}

# Create aliases for convenience
Set-Alias -Name terminal-depths -Value td -Scope Global -Option AllScope
Set-Alias -Name cyberterminal -Value td -Scope Global -Option AllScope

# Export to make available in all sessions
Export-ModuleMember -Function td -Alias terminal-depths, cyberterminal
