Describe "automation module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/health.ps1")
        . (Join-Path $repoRoot "lib/listener.ps1")
        . (Join-Path $repoRoot "lib/automation.ps1")
    }
    
    It "chooses balanced when the machine is idle and no game is running" {
        Mock Get-ModeRecommendation {
            [pscustomobject]@{
                current_mode         = "coding"
                active_dev_processes = @("Code")
                wsl_active           = $false
                docker_active        = $false
            }
        }
        Mock Get-SteamGameActivity {
            [pscustomobject]@{
                active    = $false
                processes = @()
                roots     = @()
            }
        }
        Mock Get-IdleSeconds { 1800 }

        $settings = [pscustomobject]@{
            automation = [pscustomobject]@{
                idleThresholdSec   = 900
                modeWhenIdle       = "balanced"
                modeWhenActiveDev  = "coding"
                skipWhenGameRunning = $true
            }
        }

        $plan = Get-AutomationPlan -Settings $settings

        $plan.target_mode | Should -Be "balanced"
        $plan.should_apply | Should -Be $true
    }

    It "chooses coding when dev workloads are active and the machine is not idle" {
        Mock Get-ModeRecommendation {
            [pscustomobject]@{
                current_mode         = "balanced"
                active_dev_processes = @("Code", "python")
                wsl_active           = $true
                docker_active        = $true
            }
        }
        Mock Get-SteamGameActivity {
            [pscustomobject]@{
                active    = $false
                processes = @()
                roots     = @()
            }
        }
        Mock Get-IdleSeconds { 30 }

        $settings = [pscustomobject]@{
            automation = [pscustomobject]@{
                idleThresholdSec   = 900
                modeWhenIdle       = "balanced"
                modeWhenActiveDev  = "coding"
                skipWhenGameRunning = $true
            }
        }

        $plan = Get-AutomationPlan -Settings $settings

        $plan.target_mode | Should -Be "coding"
        $plan.should_apply | Should -Be $true
    }

    It "defers automation when a game is running" {
        Mock Get-ModeRecommendation {
            [pscustomobject]@{
                current_mode         = "gaming"
                active_dev_processes = @()
                wsl_active           = $false
                docker_active        = $false
            }
        }
        Mock Get-SteamGameActivity {
            [pscustomobject]@{
                active    = $true
                processes = @([pscustomobject]@{ ProcessName = "Hades" })
                roots     = @("D:\\SteamLibrary\\steamapps\\common")
            }
        }
        Mock Get-IdleSeconds { 60 }

        $settings = [pscustomobject]@{
            automation = [pscustomobject]@{
                idleThresholdSec   = 900
                modeWhenIdle       = "balanced"
                modeWhenActiveDev  = "coding"
                skipWhenGameRunning = $true
            }
        }

        $plan = Get-AutomationPlan -Settings $settings

        $plan.deferred | Should -Be $true
        $plan.should_apply | Should -Be $false
    }
}
