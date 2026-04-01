Describe "brain module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        $script:Root      = $repoRoot
        $script:LibDir    = Join-Path $repoRoot "lib"
        $script:ConfigDir = Join-Path $repoRoot "config"
        $script:StateDir  = Join-Path $TestDrive "state"
        New-Item -ItemType Directory -Force -Path $script:StateDir | Out-Null

        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/state.ps1")
        . (Join-Path $repoRoot "lib/maintenance.ps1")
        . (Join-Path $repoRoot "lib/brain.ps1")

        $script:Settings = Get-Settings
    }

    # ── Get-StatusLabel ──────────────────────────────────────────────────────

    Describe "Get-StatusLabel" {
        It "returns 'critical' at 80" {
            Get-StatusLabel -Score 80 | Should -Be "critical"
        }
        It "returns 'critical' above 80" {
            Get-StatusLabel -Score 95 | Should -Be "critical"
        }
        It "returns 'warning' at 60" {
            Get-StatusLabel -Score 60 | Should -Be "warning"
        }
        It "returns 'warning' at 79" {
            Get-StatusLabel -Score 79 | Should -Be "warning"
        }
        It "returns 'info' at 40" {
            Get-StatusLabel -Score 40 | Should -Be "info"
        }
        It "returns 'info' at 59" {
            Get-StatusLabel -Score 59 | Should -Be "info"
        }
        It "returns 'ok' at 39" {
            Get-StatusLabel -Score 39 | Should -Be "ok"
        }
        It "returns 'ok' at 0" {
            Get-StatusLabel -Score 0 | Should -Be "ok"
        }
    }

    # ── Get-SystemScore ──────────────────────────────────────────────────────

    Describe "Get-SystemScore" {
        It "returns a score object with required fields" {
            $result = Get-SystemScore -Settings $script:Settings
            $result | Should -Not -BeNullOrEmpty
            $result.score   | Should -BeOfType [int]
            $result.status  | Should -BeIn @("ok", "info", "warning", "critical")
            $result.signals | Should -Not -BeNullOrEmpty
            $result.signals.diskPressure         | Should -BeOfType [double]
            $result.signals.cpuPressure          | Should -BeOfType [double]
            $result.signals.ramPressure          | Should -BeOfType [double]
            $result.signals.backgroundContention | Should -BeOfType [double]
        }

        It "score is between 0 and 100" {
            $result = Get-SystemScore -Settings $script:Settings
            $result.score | Should -BeGreaterOrEqual 0
            $result.score | Should -BeLessOrEqual 100
        }

        It "all pressure signals are between 0 and 1" {
            $result = Get-SystemScore -Settings $script:Settings
            $s = $result.signals
            $s.diskPressure         | Should -BeGreaterOrEqual 0
            $s.diskPressure         | Should -BeLessOrEqual 1
            $s.cpuPressure          | Should -BeGreaterOrEqual 0
            $s.cpuPressure          | Should -BeLessOrEqual 1
            $s.ramPressure          | Should -BeGreaterOrEqual 0
            $s.ramPressure          | Should -BeLessOrEqual 1
            $s.backgroundContention | Should -BeGreaterOrEqual 0
            $s.backgroundContention | Should -BeLessOrEqual 1
        }

        It "persists score to state dir" {
            $null = Get-SystemScore -Settings $script:Settings
            $scorePath = Join-Path $script:StateDir "performance_score.json"
            Test-Path -LiteralPath $scorePath | Should -Be $true
        }

        It "issues array contains disk issue when disk pressure is high" {
            Mock Get-DiskPressure { return 0.95 }
            $result = Get-SystemScore -Settings $script:Settings
            ($result.issues | Where-Object { $_ -like "*Disk*" }).Count | Should -BeGreaterThan 0
        }

        It "safe_actions includes docker-prune when disk >= 0.90" {
            Mock Get-DiskPressure { return 0.92 }
            $result = Get-SystemScore -Settings $script:Settings
            $result.safe_actions | Should -Contain "docker-prune"
        }
    }

    # ── Get-AdvisorRecommendation ────────────────────────────────────────────

    Describe "Get-AdvisorRecommendation" {
        It "returns a recommendation object with required fields" {
            $result = Get-AdvisorRecommendation -Settings $script:Settings
            $result.recommended   | Should -Not -BeNullOrEmpty
            $result.why           | Should -Not -BeNullOrEmpty
            $result.confidence    | Should -BeOfType [double]
            $result.confidence    | Should -BeGreaterOrEqual 0
            $result.confidence    | Should -BeLessOrEqual 1
            $result.safe_to_apply | Should -BeOfType [bool]
        }

        It "recommends docker-prune at critical disk pressure" {
            Mock Get-DiskPressure { return 0.95 }
            Mock Get-CpuPressure  { return 0.10 }
            Mock Get-RamPressure  { return 0.30 }
            Mock Get-BackgroundContention { return 0.125 } -ParameterFilter { $true }
            $result = Get-AdvisorRecommendation -Settings $script:Settings
            $result.recommended | Should -Be "docker-prune"
            $result.confidence  | Should -BeGreaterOrEqual 0.90
        }

        It "recommends none when system pressure is low" {
            Mock Get-DiskPressure { return 0.30 }
            Mock Get-CpuPressure  { return 0.05 }
            Mock Get-RamPressure  { return 0.25 }
            Mock Get-BackgroundContention { return 0.0 } -ParameterFilter { $true }
            $result = Get-AdvisorRecommendation -Settings $script:Settings
            $result.recommended | Should -Be "none"
            $result.confidence  | Should -BeGreaterOrEqual 0.85
        }

        It "persists advisor state to state dir" {
            $null = Get-AdvisorRecommendation -Settings $script:Settings
            $advisorPath = Join-Path $script:StateDir "advisor_last.json"
            Test-Path -LiteralPath $advisorPath | Should -Be $true
        }
    }

    # ── Invoke-DemoteDevProcesses ────────────────────────────────────────────

    Describe "Invoke-DemoteDevProcesses" {
        It "returns a result object with action field" {
            $result = Invoke-DemoteDevProcesses -Settings $script:Settings
            $result.action  | Should -Be "demote-dev-processes"
            $result.demoted | Should -Not -BeNullOrEmpty -Because "it should be an array (possibly empty)"
            $result.count   | Should -BeGreaterOrEqual 0
        }
    }

    # ── Invoke-Optimize ──────────────────────────────────────────────────────

    Describe "Invoke-Optimize" {
        It "returns skipped when safe_to_apply is false and -Force not set" {
            Mock Get-AdvisorRecommendation {
                return [pscustomobject]@{
                    recommended   = "clean-temp"
                    why           = "test reason"
                    confidence    = 0.7
                    safe_to_apply = $false
                    score         = 35
                    status        = "ok"
                    issues        = @()
                    signals       = [pscustomobject]@{}
                }
            }
            $result = Invoke-Optimize -Settings $script:Settings
            $result.status | Should -Be "skipped"
        }

        It "returns no-op when recommended action is 'none'" {
            Mock Get-AdvisorRecommendation {
                return [pscustomobject]@{
                    recommended   = "none"
                    why           = "system ok"
                    confidence    = 0.9
                    safe_to_apply = $false
                    score         = 20
                    status        = "ok"
                    issues        = @()
                    signals       = [pscustomobject]@{}
                }
            }
            $result = Invoke-Optimize -Settings $script:Settings
            $result.status | Should -Be "no-op"
        }

        It "applies action when -Force is set regardless of safe_to_apply" {
            Mock Get-AdvisorRecommendation {
                return [pscustomobject]@{
                    recommended   = "demote-dev-processes"
                    why           = "contention high"
                    confidence    = 0.65
                    safe_to_apply = $false
                    score         = 50
                    status        = "info"
                    issues        = @()
                    signals       = [pscustomobject]@{}
                }
            }
            Mock Invoke-DemoteDevProcesses { return [pscustomobject]@{ action = "demote-dev-processes"; demoted = @(); count = 0 } }
            $result = Invoke-Optimize -Settings $script:Settings -Force
            $result.status | Should -Be "applied"
            $result.action | Should -Be "demote-dev-processes"
        }
    }
}
