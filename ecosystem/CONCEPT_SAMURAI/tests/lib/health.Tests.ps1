Describe "health module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/health.ps1")
        . (Join-Path $repoRoot "lib/actions.ps1")
        . (Join-Path $repoRoot "lib/listener.ps1")
    }
    It "auto-discovers the newest LatencyMon report from the provided search paths" {
        $oldPath = Join-Path $TestDrive "LatencyMon-old.txt"
        $newPath = Join-Path $TestDrive "LatencyMon-new.txt"

        "old" | Set-Content -LiteralPath $oldPath -Encoding UTF8
        Start-Sleep -Milliseconds 50
        "new" | Set-Content -LiteralPath $newPath -Encoding UTF8

        (Get-LatencyMonAutoPath -SearchPaths @($TestDrive)) | Should -Be $newPath
    }

    It "returns an empty LatencyMon summary when no path is provided" {
        $emptyDir = Join-Path $TestDrive "empty"
        New-Item -ItemType Directory -Force -Path $emptyDir | Out-Null
        $summary = Get-LatencyMonSummary -SearchPaths @($emptyDir)

        $summary.provided | Should -Be $false
        $summary.exists | Should -Be $false
        $summary.matched_drivers.Count | Should -Be 0
    }

    It "flags a missing LatencyMon report path" {
        $missingPath = Join-Path $TestDrive "missing-latencymon.txt"

        $summary = Get-LatencyMonSummary -Path $missingPath

        $summary.provided | Should -Be $true
        $summary.exists | Should -Be $false
        $summary.report_path | Should -Be $missingPath
        $summary.notes.Count | Should -Be 1
    }

    It "extracts the top driver from a LatencyMon report" {
        $reportPath = Join-Path $TestDrive "LatencyMon.txt"
        @'
Highest reported ISR routine execution time (us): 842.10
Driver with highest ISR routine execution time: nvlddmkm.sys - NVIDIA Windows Kernel Mode Driver
Highest reported DPC routine execution time (us): 532.50
ndis.sys - Network Driver Interface Specification (NDIS)
'@ | Set-Content -LiteralPath $reportPath -Encoding UTF8

        $summary = Get-LatencyMonSummary -Path $reportPath

        $summary.provided | Should -Be $true
        $summary.exists | Should -Be $true
        $summary.top_driver | Should -Be "nvlddmkm.sys"
        ($summary.matched_drivers -contains "nvlddmkm.sys") | Should -Be $true
        ($summary.matched_drivers -contains "ndis.sys") | Should -Be $true
        $summary.matched_lines.Count | Should -BeGreaterThan 0
    }

    It "resolves MSI GPU mode values into friendly labels" {
        (Resolve-MsiGpuModeValue -Value 1).mode | Should -Be "MSHybrid"
        (Resolve-MsiGpuModeValue -Value 0).mode | Should -Be "Discrete Only"
        (Resolve-MsiGpuModeValue -Value $null).mode | Should -Be "Unknown"
    }

    It "recommends coding mode when dev workloads are active" {
        Mock Get-HealthState {
            [pscustomobject]@{
                mode          = "idle"
                wsl_active    = $true
                docker_active = $true
                cpu_percent   = 30
            }
        }
        Mock Get-ProcessSnapshotsByPatterns {
            @([pscustomobject]@{ ProcessName = "Code" })
        }
        Mock Get-ActiveSteamGames {
            [pscustomobject]@{
                active    = $false
                processes = @()
            }
        }

        $settings = [pscustomobject]@{
            recommendation = [pscustomobject]@{
                preferBalancedWhenMixed = $true
                devProcessPatterns      = @("Code")
            }
            listener = [pscustomobject]@{
                steamVdfPath = $null
            }
        }

        $recommendation = Get-ModeRecommendation -Settings $settings

        $recommendation.recommended_mode | Should -Be "coding"
    }

    It "recommends balanced mode for mixed gaming and dev workloads" {
        Mock Get-HealthState {
            [pscustomobject]@{
                mode          = "idle"
                wsl_active    = $false
                docker_active = $false
                cpu_percent   = 30
            }
        }
        Mock Get-ProcessSnapshotsByPatterns {
            @([pscustomobject]@{ ProcessName = "Code" })
        }
        Mock Get-ActiveSteamGames {
            [pscustomobject]@{
                active    = $true
                processes = @(
                    [pscustomobject]@{
                        ProcessName = "Hades"
                        GameName    = "Hades"
                        SteamAppId  = "1145360"
                    }
                )
            }
        }

        $settings = [pscustomobject]@{
            recommendation = [pscustomobject]@{
                preferBalancedWhenMixed = $true
                devProcessPatterns      = @("Code")
            }
            listener = [pscustomobject]@{
                steamVdfPath = $null
            }
        }

        $recommendation = Get-ModeRecommendation -Settings $settings

        $recommendation.recommended_mode | Should -Be "balanced"
        $recommendation.active_games.Count | Should -Be 1
        $recommendation.active_games[0].GameName | Should -Be "Hades"
    }
}
