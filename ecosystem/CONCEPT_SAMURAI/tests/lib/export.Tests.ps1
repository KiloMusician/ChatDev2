Describe "export module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/state.ps1")
        . (Join-Path $repoRoot "lib/health.ps1")
        . (Join-Path $repoRoot "lib/actions.ps1")
        . (Join-Path $repoRoot "lib/export.ps1")
    }

    BeforeEach {
        $script:StateDir     = Join-Path $TestDrive "state"
        $script:SessionsDir  = Join-Path $TestDrive "sessions"
        $script:IncidentsDir = Join-Path $TestDrive "incidents"
        $script:CurrentStatePath = Join-Path $script:StateDir "current.json"
        $script:RollbackPath     = Join-Path $script:StateDir "rollback.json"
        $script:ActionResults    = @()

        foreach ($d in @($script:StateDir, $script:SessionsDir, $script:IncidentsDir)) {
            New-Item -ItemType Directory -Force -Path $d | Out-Null
        }
    }

    # ── Invoke-Prune ─────────────────────────────────────────────────────────

    Describe "Invoke-Prune" {
        It "returns a structured result with the expected fields" {
            $settings = [pscustomobject]@{
                retention = [pscustomobject]@{ maxSessions = 30; incidentDays = 14 }
            }
            $result = Invoke-Prune -Settings $settings
            $result.removed_sessions  | Should -Not -BeNullOrEmpty
            $result.removed_incidents | Should -Not -BeNullOrEmpty
        }

        It "removes session files beyond maxSessions" {
            $settings = [pscustomobject]@{
                retention = [pscustomobject]@{ maxSessions = 2; incidentDays = 14 }
            }
            # Create 5 session files with different timestamps
            1..5 | ForEach-Object {
                $path = Join-Path $script:SessionsDir "session-$_.json"
                "{}" | Set-Content -Path $path
                # Stagger LastWriteTime so sorting is deterministic
                (Get-Item $path).LastWriteTime = (Get-Date).AddMinutes(-$_)
            }

            $result = Invoke-Prune -Settings $settings
            $result.removed_sessions | Should -Be 3
            (Get-ChildItem -LiteralPath $script:SessionsDir -File).Count | Should -Be 2
        }

        It "removes incident files older than incidentDays" {
            $settings = [pscustomobject]@{
                retention = [pscustomobject]@{ maxSessions = 30; incidentDays = 7 }
            }
            $old  = Join-Path $script:IncidentsDir "old.json"
            $new  = Join-Path $script:IncidentsDir "new.json"
            "{}" | Set-Content -Path $old
            "{}" | Set-Content -Path $new
            (Get-Item $old).LastWriteTime = (Get-Date).AddDays(-30)
            (Get-Item $new).LastWriteTime = (Get-Date).AddDays(-1)

            $result = Invoke-Prune -Settings $settings
            $result.removed_incidents | Should -Be 1
            (Get-ChildItem -LiteralPath $script:IncidentsDir -File).Count | Should -Be 1
        }

        It "reports zero removals when nothing exceeds retention" {
            $settings = [pscustomobject]@{
                retention = [pscustomobject]@{ maxSessions = 30; incidentDays = 14 }
            }
            $result = Invoke-Prune -Settings $settings
            $result.removed_sessions  | Should -Be 0
            $result.removed_incidents | Should -Be 0
        }
    }

    # ── Invoke-Export (JSON) ─────────────────────────────────────────────────

    Describe "Invoke-Export JSON" {
        BeforeEach {
            Mock Get-DoctorReport {
                return [pscustomobject]@{
                    risk_level       = "low"
                    findings         = @()
                    top_offenders    = @()
                    steam_games      = @()
                    cpu_percent      = 5
                    power_plan_raw   = "Balanced"
                    game_mode_enabled = $false
                    gpu_mode         = "Hybrid"
                    wsl_running_distros  = @()
                    nahimic_services = @()
                    nahimic_processes = @()
                    sound_devices    = @()
                }
            }
            Mock Get-RecentSessions { return @() }
        }

        It "returns structured result with exported_at bundle_path and format" {
            $settings = [pscustomobject]@{}
            $result = Invoke-Export -Settings $settings
            $result.exported_at | Should -Not -BeNullOrEmpty
            $result.bundle_path | Should -Not -BeNullOrEmpty
            $result.format      | Should -Be "json"
        }

        It "writes the JSON bundle to the incidents directory" {
            $settings = [pscustomobject]@{}
            $result = Invoke-Export -Settings $settings
            Test-Path -LiteralPath $result.bundle_path | Should -Be $true
            $result.bundle_path | Should -Match "\.json$"
        }

        It "bundle file contains valid JSON" {
            $settings = [pscustomobject]@{}
            $result = Invoke-Export -Settings $settings
            $content = Get-Content -LiteralPath $result.bundle_path -Raw
            { $content | ConvertFrom-Json } | Should -Not -Throw
        }
    }

    # ── Invoke-Export HTML ────────────────────────────────────────────────────

    Describe "Invoke-Export HTML" {
        BeforeEach {
            Mock Get-DoctorReport {
                return [pscustomobject]@{
                    risk_level       = "medium"
                    findings         = @("Nahimic detected")
                    top_offenders    = @("msedge")
                    steam_games      = @()
                    cpu_percent      = 45
                    power_plan_raw   = "Balanced"
                    game_mode_enabled = $false
                    gpu_mode         = "Hybrid"
                    wsl_running_distros  = @()
                    nahimic_services = @()
                    nahimic_processes = @()
                    sound_devices    = @()
                }
            }
            Mock Get-RecentSessions { return @() }
        }

        It "returns format html and an html bundle_path" {
            $settings = [pscustomobject]@{}
            $result = Invoke-Export -Settings $settings -AsHtml
            $result.format     | Should -Be "html"
            $result.bundle_path | Should -Match "\.html$"
        }

        It "writes a non-empty HTML file" {
            $settings = [pscustomobject]@{}
            $result = Invoke-Export -Settings $settings -AsHtml
            $content = Get-Content -LiteralPath $result.bundle_path -Raw
            $content | Should -Match "<!DOCTYPE html>"
            $content | Should -Match "keeper\.ps1"
        }
    }
}
