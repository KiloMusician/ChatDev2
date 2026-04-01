Describe "watch module anomaly rules" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/watch.ps1")
    }
    It "captures a sustained CPU spike once the threshold is reached" {
        $settings = [pscustomobject]@{
            anomaly = [pscustomobject]@{
                enabled                 = $true
                cpuSpikePercent         = 80
                spikeSustainSamples     = 3
                captureOnNahimicDetected = $true
                audioRiskNewProcesses   = 2
            }
        }

        $state = [pscustomobject]@{
            initialized        = $true
            cpuSpikeSamples    = 2
            nahimicSeen        = $false
            lastAudioRiskCount = 0
            capturedSignatures = @()
        }

        $result = Test-AnomalyConditions -Settings $settings -Sample ([pscustomobject]@{ cpu_percent = 85 }) -State $state -NahimicDetectedOverride $false -AudioRiskProcessCountOverride 0

        $result.should_capture | Should -Be $true
        $result.reasons.Count | Should -Be 1
        ($result.reasons[0] -match 'CPU stayed above') | Should -Be $true
        ($result.state.capturedSignatures -contains 'cpu') | Should -Be $true
    }

    It "captures a newly detected Nahimic presence only once" {
        $settings = [pscustomobject]@{
            anomaly = [pscustomobject]@{
                enabled                 = $true
                cpuSpikePercent         = 80
                spikeSustainSamples     = 3
                captureOnNahimicDetected = $true
                audioRiskNewProcesses   = 2
            }
        }

        $state = [pscustomobject]@{
            initialized        = $true
            cpuSpikeSamples    = 0
            nahimicSeen        = $false
            lastAudioRiskCount = 0
            capturedSignatures = @()
        }

        $first = Test-AnomalyConditions -Settings $settings -Sample ([pscustomobject]@{ cpu_percent = 10 }) -State $state -NahimicDetectedOverride $true -AudioRiskProcessCountOverride 0
        $second = Test-AnomalyConditions -Settings $settings -Sample ([pscustomobject]@{ cpu_percent = 10 }) -State $first.state -NahimicDetectedOverride $true -AudioRiskProcessCountOverride 0

        $first.should_capture | Should -Be $true
        $second.should_capture | Should -Be $false
    }

    It "uses the first sample as a baseline for Nahimic and audio-risk counts" {
        $settings = [pscustomobject]@{
            anomaly = [pscustomobject]@{
                enabled                 = $true
                cpuSpikePercent         = 80
                spikeSustainSamples     = 3
                captureOnNahimicDetected = $true
                audioRiskNewProcesses   = 2
            }
        }

        $state = [pscustomobject]@{
            initialized        = $false
            cpuSpikeSamples    = 0
            nahimicSeen        = $false
            lastAudioRiskCount = 0
            capturedSignatures = @()
        }

        $result = Test-AnomalyConditions -Settings $settings -Sample ([pscustomobject]@{ cpu_percent = 10 }) -State $state -NahimicDetectedOverride $true -AudioRiskProcessCountOverride 5

        $result.should_capture | Should -Be $false
        $result.state.initialized | Should -Be $true
        $result.state.nahimicSeen | Should -Be $true
        $result.state.lastAudioRiskCount | Should -Be 5
    }
}
