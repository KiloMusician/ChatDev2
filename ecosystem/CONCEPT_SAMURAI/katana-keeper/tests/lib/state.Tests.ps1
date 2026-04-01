BeforeAll {
    $script:DefaultsPath     = Join-Path $TestDrive "config\defaults.json"
    $script:CurrentStatePath = Join-Path $TestDrive "state\current.json"
    $script:RingBufferPath   = Join-Path $TestDrive "state\ringbuffer.json"
    $script:RollbackPath     = Join-Path $TestDrive "state\rollback.json"
    New-Item -ItemType Directory -Path (Join-Path $TestDrive "config") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $TestDrive "state")  -Force | Out-Null
    . (Join-Path $PSScriptRoot "..\..\lib\config.ps1")
    . (Join-Path $PSScriptRoot "..\..\lib\state.ps1")
}

Describe "Save-CurrentState / Read back" {
    It "writes and reads back mode" {
        Save-CurrentState -State ([pscustomobject]@{ mode = "gaming"; status = "ready" })
        $read = Get-Content $script:CurrentStatePath -Raw | ConvertFrom-Json
        $read.mode | Should -Be "gaming"
    }
}

Describe "Save-RollbackState / Read back" {
    It "persists rollback data" {
        Save-RollbackState -Rollback ([pscustomobject]@{ priorMode = "coding"; stoppedServices = @("WSearch") })
        $read = Get-Content $script:RollbackPath -Raw | ConvertFrom-Json
        $read.priorMode | Should -Be "coding"
    }
}

Describe "Add-RingBufferSample" {
    BeforeEach {
        Remove-Item $script:RingBufferPath -ErrorAction SilentlyContinue
        '{"watch":{"ringBufferSamples":3}}' | Set-Content $script:DefaultsPath -Encoding UTF8
    }
    It "appends samples" {
        $settings = [pscustomobject]@{ watch = [pscustomobject]@{ ringBufferSamples = 3 } }
        Add-RingBufferSample -Sample @{ ts = 1 } -Settings $settings
        Add-RingBufferSample -Sample @{ ts = 2 } -Settings $settings
        $buf = Get-Content $script:RingBufferPath -Raw | ConvertFrom-Json
        $buf.Count | Should -Be 2
    }
    It "trims oldest when over capacity" {
        $settings = [pscustomobject]@{ watch = [pscustomobject]@{ ringBufferSamples = 2 } }
        Add-RingBufferSample -Sample @{ ts = 1 } -Settings $settings
        Add-RingBufferSample -Sample @{ ts = 2 } -Settings $settings
        Add-RingBufferSample -Sample @{ ts = 3 } -Settings $settings
        $buf = Get-Content $script:RingBufferPath -Raw | ConvertFrom-Json
        $buf.Count  | Should -Be 2
        $buf[0].ts  | Should -Be 2
        $buf[-1].ts | Should -Be 3
    }
}

Describe "Get-CurrentModeName" {
    It "returns idle when no current.json" {
        Remove-Item $script:CurrentStatePath -ErrorAction SilentlyContinue
        Get-CurrentModeName | Should -Be "idle"
    }
    It "returns mode from current.json" {
        '{"mode":"gaming"}' | Set-Content $script:CurrentStatePath -Encoding UTF8
        Get-CurrentModeName | Should -Be "gaming"
    }
}
