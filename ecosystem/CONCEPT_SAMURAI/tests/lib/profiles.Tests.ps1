Describe "profiles module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/actions.ps1")
        . (Join-Path $repoRoot "lib/state.ps1")
        . (Join-Path $repoRoot "lib/health.ps1")
        . (Join-Path $repoRoot "lib/profiles.ps1")
    }

    BeforeEach {
        $script:ActionResults = @()
        $script:callOrder = [System.Collections.Generic.List[string]]::new()

        Mock Get-HealthState {
            [pscustomobject]@{
                mode            = "idle"
                power_plan_guid = "SCHEME_BALANCED"
                power_plan_raw  = "Balanced"
                wsl_active      = $true
                docker_active   = $true
                cpu_percent     = 10
                free_mem_mb     = 1000
                top_offenders   = @("Code")
                game_mode_enabled = $false
            }
        }

        Mock Get-GameModeState {
            [pscustomobject]@{
                allowAutoGameMode  = 0
                autoGameModeEnabled = 0
                effectiveEnabled   = $false
            }
        }

        Mock Save-CurrentState {}
        Mock Append-RingBuffer {}
        Mock Save-RollbackState {}
        Mock Get-ActionSummary { [pscustomobject]@{ total = 0; changed = 0; skipped = 0; failed = 0 } }
        Mock New-SessionSummary { [pscustomobject]@{ session_id = "test" } }

        Mock Stop-ProcessesByPatternSafe {
            param($Pattern, $Settings, [ref]$RollbackState)
            [void]$script:callOrder.Add("stop:$Pattern")
            Add-ActionResult -Action "stop_process" -Target ([string]$Pattern) -Changed $true -Message "ok"
        }

        Mock Invoke-WslShutdownSafe {
            [void]$script:callOrder.Add("wsl")
            Add-ActionResult -Action "shutdown_wsl" -Target "WSL" -Changed $true -Message "ok"
        }

        Mock Stop-ServiceSafe {
            param($ServiceName, [ref]$RollbackState)
            [void]$script:callOrder.Add("service:$ServiceName")
            Add-ActionResult -Action "stop_service" -Target ([string]$ServiceName) -Changed $true -Message "ok"
        }

        Mock Set-PowerPlanSafe {
            param($PlanName, $Settings)
            [void]$script:callOrder.Add("power:$PlanName")
            Add-ActionResult -Action "set_power_plan" -Target ([string]$PlanName) -Changed $true -Message "ok"
        }

        Mock Set-GameModeStateSafe {
            param([bool]$Enabled)
            [void]$script:callOrder.Add("game:$Enabled")
            Add-ActionResult -Action "set_game_mode" -Target ([string]$Enabled) -Changed $true -Message "ok"
        }

        Mock Start-ServiceSafe {}
        Mock Start-LauncherSafe {}
    }

    It "stops Docker-backed processes before shutting down WSL" {
        $profiles = [pscustomobject]@{
            gaming = [pscustomobject]@{
                shutdownWsl   = $true
                stopProcesses = @("Code", "Docker*", "com.docker.*")
                stopServices  = @("WSearch")
                setPowerPlan  = "high_performance"
                setGameMode   = $true
                startServices = @()
                startLaunchers = @()
                notes         = @("test")
            }
        }

        $null = Invoke-ModeProfile -ModeName "gaming" -Settings ([pscustomobject]@{}) -Profiles $profiles

        $script:callOrder.IndexOf("stop:Docker*") | Should -BeLessThan $script:callOrder.IndexOf("wsl")
        $script:callOrder.IndexOf("stop:com.docker.*") | Should -BeLessThan $script:callOrder.IndexOf("wsl")
        $script:callOrder.IndexOf("wsl") | Should -BeLessThan $script:callOrder.IndexOf("service:WSearch")
    }
}
