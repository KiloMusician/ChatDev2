Describe "state module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/state.ps1")
    }
    BeforeEach {
        $script:ConfigDir = Join-Path $TestDrive "config"
        $script:StateDir = Join-Path $TestDrive "state"
        $script:SessionsDir = Join-Path $TestDrive "sessions"
        $script:IncidentsDir = Join-Path $TestDrive "incidents"
        $script:LibDir = Join-Path $TestDrive "lib"
        $script:CurrentStatePath = Join-Path $script:StateDir "current.json"
        $script:RingBufferPath = Join-Path $script:StateDir "ringbuffer.json"
        $script:RollbackPath = Join-Path $script:StateDir "rollback.json"

        Get-ChildItem -LiteralPath $TestDrive -Recurse -File -ErrorAction SilentlyContinue |
            Remove-Item -Force -ErrorAction SilentlyContinue

        Ensure-Directory -Path $script:ConfigDir
        Ensure-Directory -Path $script:StateDir
        Ensure-Directory -Path $script:SessionsDir
        Ensure-Directory -Path $script:IncidentsDir
        Ensure-Directory -Path $script:LibDir
    }

    It "writes current and rollback state to the configured paths" {
        $current = [pscustomobject]@{ mode = "gaming"; status = "ready" }
        $rollback = [pscustomobject]@{ prior_mode = "coding"; prior_power = "Balanced" }

        Save-CurrentState -State $current
        Save-RollbackState -Rollback $rollback

        (Read-JsonFile -Path $script:CurrentStatePath -Default $null).mode | Should -Be "gaming"
        (Read-JsonFile -Path $script:RollbackPath -Default $null).prior_mode | Should -Be "coding"
    }

    It "caps the ring buffer to the configured sample limit" {
        $settings = [pscustomobject]@{
            watch = [pscustomobject]@{
                ringBufferSamples = 2
            }
        }

        Append-RingBuffer -Sample ([pscustomobject]@{ id = 1 }) -Settings $settings
        Append-RingBuffer -Sample ([pscustomobject]@{ id = 2 }) -Settings $settings
        Append-RingBuffer -Sample ([pscustomobject]@{ id = 3 }) -Settings $settings

        $bufferRaw = Read-JsonFile -Path $script:RingBufferPath -Default @()
        $buffer = @()
        foreach ($item in $bufferRaw) {
            $buffer += $item
        }

        $buffer.Count | Should -Be 2
        $buffer[0].id | Should -Be 2
        $buffer[1].id | Should -Be 3
    }

    It "writes a compact session summary file" {
        $startedAt = Get-Date "2026-03-29T10:00:00"
        $endedAt = Get-Date "2026-03-29T10:05:00"
        $before = [pscustomobject]@{ cpu_percent = 10; free_mem_mb = 1000; wsl_active = $true; docker_active = $true }
        $after = [pscustomobject]@{ cpu_percent = 20; free_mem_mb = 900; wsl_active = $false; docker_active = $false; top_offenders = @("Code") }
        $results = @(
            [pscustomobject]@{ changed = $true; skipped = $false; success = $true },
            [pscustomobject]@{ changed = $false; skipped = $true; success = $true }
        )

        $summary = New-SessionSummary -ModeName "gaming" -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $results -Notes @("test")

        $summary.mode | Should -Be "gaming"
        $summary.action_summary.total | Should -Be 2
        $summary.action_summary.changed | Should -Be 1

        $sessionFiles = @(Get-ChildItem -LiteralPath $script:SessionsDir -File)
        $sessionFiles.Count | Should -Be 1
    }
}
