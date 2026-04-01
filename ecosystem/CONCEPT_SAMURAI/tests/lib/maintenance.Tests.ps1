Describe "maintenance module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        $script:Root      = $repoRoot
        $script:LibDir    = Join-Path $repoRoot "lib"
        $script:ConfigDir = Join-Path $repoRoot "config"
        $script:StateDir  = Join-Path $TestDrive "state"
        New-Item -ItemType Directory -Force -Path $script:StateDir | Out-Null

        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/actions.ps1")
        . (Join-Path $repoRoot "lib/state.ps1")
        . (Join-Path $repoRoot "lib/maintenance.ps1")

        $script:Settings = Get-Settings
    }

    BeforeEach {
        $script:ActionResults = @()
    }

    # ── Get-FolderSizeGB ─────────────────────────────────────────────────────

    Describe "Get-FolderSizeGB" {
        It "returns 0 for an empty directory" {
            $emptyDir = Join-Path $TestDrive "empty_folder"
            New-Item -ItemType Directory -Force -Path $emptyDir | Out-Null
            Get-FolderSizeGB -Path $emptyDir | Should -Be 0
        }

        It "returns 0 for a non-existent path" {
            Get-FolderSizeGB -Path (Join-Path $TestDrive "no_such_dir") | Should -Be 0
        }

        It "calculates correct size for known content" {
            $dir = Join-Path $TestDrive "sized_folder"
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            # Write 1 MB of data
            [System.IO.File]::WriteAllBytes((Join-Path $dir "file.bin"), ([byte[]]::new(1MB)))
            $size = Get-FolderSizeGB -Path $dir
            $size | Should -BeGreaterThan 0
            $size | Should -BeLessThan 0.01  # 1 MB < 0.01 GB
        }
    }

    # ── Test-MaintenanceSafe ─────────────────────────────────────────────────

    Describe "Test-MaintenanceSafe" {
        It "returns safe when in coding mode with low CPU" {
            Mock Get-CurrentModeName { return "coding" }
            Mock Get-Counter {
                return [pscustomobject]@{
                    CounterSamples = @([pscustomobject]@{ CookedValue = 5.0 })
                }
            }
            $result = Test-MaintenanceSafe -Settings $script:Settings
            $result.safe | Should -Be $true
            $result.reasons.Count | Should -Be 0
        }

        It "blocks when mode is in denyModes" {
            Mock Get-CurrentModeName { return "gaming" }
            $result = Test-MaintenanceSafe -Settings $script:Settings
            $result.safe | Should -Be $false
            ($result.reasons | Where-Object { $_ -like "*gaming*" }).Count | Should -BeGreaterThan 0
        }

        It "blocks when mode is heavy-gaming" {
            Mock Get-CurrentModeName { return "heavy-gaming" }
            $result = Test-MaintenanceSafe -Settings $script:Settings
            $result.safe | Should -Be $false
        }

        It "blocks when CPU is above threshold" {
            Mock Get-CurrentModeName { return "balanced" }
            Mock Get-Counter {
                return [pscustomobject]@{
                    CounterSamples = @([pscustomobject]@{ CookedValue = 85.0 })
                }
            }
            $result = Test-MaintenanceSafe -Settings $script:Settings
            $result.safe | Should -Be $false
            ($result.reasons | Where-Object { $_ -like "*CPU*" }).Count | Should -BeGreaterThan 0
        }
    }

    # ── Get-MaintenancePlan ──────────────────────────────────────────────────

    Describe "Get-MaintenancePlan" {
        It "returns a plan with disk and issues fields" {
            $plan = Get-MaintenancePlan -Settings $script:Settings
            $plan | Should -Not -BeNullOrEmpty
            $plan.disk   | Should -Not -BeNullOrEmpty
            $plan.issues | Should -Not -BeNullOrEmpty
        }

        It "disk report includes used_gb free_gb total_gb" {
            $plan = Get-MaintenancePlan -Settings $script:Settings
            $plan.disk.used_gb  | Should -BeGreaterOrEqual 0
            $plan.disk.free_gb  | Should -BeGreaterOrEqual 0
            $plan.disk.total_gb | Should -BeGreaterThan 0
            $plan.disk.pct_used | Should -BeGreaterOrEqual 0
            $plan.disk.pct_used | Should -BeLessOrEqual 100
        }

        It "issues is an array" {
            $plan = Get-MaintenancePlan -Settings $script:Settings
            @($plan.issues) | Should -BeOfType [object]
        }
    }

    # ── Invoke-MaintenancePass ───────────────────────────────────────────────

    Describe "Invoke-MaintenancePass" {
        It "skips when in gaming mode" {
            Mock Get-CurrentModeName { return "gaming" }
            $result = Invoke-MaintenancePass -Settings $script:Settings
            $result.status | Should -Be "skipped"
            $result.safe_to_maintain | Should -Be $false
        }

        It "returns a structured result object" {
            Mock Get-CurrentModeName { return "coding" }
            Mock Get-Counter {
                return [pscustomobject]@{
                    CounterSamples = @([pscustomobject]@{ CookedValue = 2.0 })
                }
            }
            $result = Invoke-MaintenancePass -Settings $script:Settings
            $result.status           | Should -Not -BeNullOrEmpty
            $result.safe_to_maintain | Should -BeOfType [bool]
            $result.summary          | Should -Not -BeNullOrEmpty
            $result.disk             | Should -Not -BeNullOrEmpty
        }

        It "result status is one of the valid values" {
            Mock Get-CurrentModeName { return "coding" }
            Mock Get-Counter {
                return [pscustomobject]@{
                    CounterSamples = @([pscustomobject]@{ CookedValue = 2.0 })
                }
            }
            $result = Invoke-MaintenancePass -Settings $script:Settings
            $result.status | Should -BeIn @("skipped", "ok", "partial", "no-op")
        }
    }
}
