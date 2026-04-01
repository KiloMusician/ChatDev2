BeforeAll {
    . (Join-Path $PSScriptRoot "..\..\lib\config.ps1")
    . (Join-Path $PSScriptRoot "..\..\lib\doctor.ps1")
}

Describe "Resolve-DriverCause (Feature E)" {
    It "maps nvlddmkm.sys to NVIDIA description" {
        $result = Resolve-DriverCause -DriverName "nvlddmkm.sys"
        $result | Should -BeLike "*NVIDIA*"
    }
    It "maps ndis.sys to network description" {
        $result = Resolve-DriverCause -DriverName "ndis.sys"
        $result | Should -BeLike "*network*"
    }
    It "returns generic message for unknown driver" {
        $result = Resolve-DriverCause -DriverName "unknown.sys"
        $result | Should -Not -BeNullOrEmpty
    }
}

Describe "Parse-LatencyMonReport (Feature E)" {
    BeforeAll {
        $script:SampleReport = @"
Highest reported ISR routine execution time (µs): 312.40
Driver with highest ISR routine execution time: nvlddmkm.sys
Highest reported DPC routine execution time (µs): 892.10
Driver with highest DPC routine execution time: ndis.sys
"@
    }
    It "extracts top driver from ISR section" {
        $result = Parse-LatencyMonReport -ReportText $script:SampleReport
        $result.topDrivers.Count | Should -BeGreaterOrEqual 1
        $result.topDrivers[0].driver | Should -Be "nvlddmkm.sys"
    }
    It "includes time value" {
        $result = Parse-LatencyMonReport -ReportText $script:SampleReport
        $result.topDrivers[0].maxTimeUs | Should -BeGreaterThan 0
    }
    It "includes mapped cause" {
        $result = Parse-LatencyMonReport -ReportText $script:SampleReport
        $result.topDrivers[0].cause | Should -BeLike "*NVIDIA*"
    }
}

Describe "Get-LatencyMonAutoPath" {
    It "returns null when no LatencyMon files found on TestDrive" {
        $result = Get-LatencyMonAutoPath -SearchPaths @("$TestDrive")
        $result | Should -BeNullOrEmpty
    }
    It "finds newest LatencyMon txt file" {
        "dummy" | Set-Content (Join-Path $TestDrive "LatencyMon_Report.txt")
        $result = Get-LatencyMonAutoPath -SearchPaths @("$TestDrive")
        $result | Should -Not -BeNullOrEmpty
    }
}
