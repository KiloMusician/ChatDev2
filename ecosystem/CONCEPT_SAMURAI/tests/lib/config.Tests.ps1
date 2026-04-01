Describe "config module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
    }

    BeforeEach {
        $script:ConfigDir = Join-Path $TestDrive "config"
        $script:DefaultsPath = Join-Path $script:ConfigDir "defaults.json"
        $script:ProfilesPath = Join-Path $script:ConfigDir "profiles.json"
        $script:MachinePath = Join-Path $script:ConfigDir "machine.local.json"

        Ensure-Directory -Path $script:ConfigDir

        if (Test-Path -LiteralPath $script:DefaultsPath) {
            Remove-Item -LiteralPath $script:DefaultsPath -Force
        }
        if (Test-Path -LiteralPath $script:ProfilesPath) {
            Remove-Item -LiteralPath $script:ProfilesPath -Force
        }
        if (Test-Path -LiteralPath $script:MachinePath) {
            Remove-Item -LiteralPath $script:MachinePath -Force
        }
    }

    It "deep merges defaults with machine settings overrides" {
        @'
{
  "watch": {
    "sampleIntervalSec": 5,
    "ringBufferSamples": 180
  },
  "retention": {
    "maxSessions": 30
  }
}
'@ | Set-Content -LiteralPath $script:DefaultsPath -Encoding UTF8

        @'
{
  "settings": {
    "watch": {
      "defaultDurationSec": 60
    },
    "retention": {
      "maxSessions": 10
    }
  }
}
'@ | Set-Content -LiteralPath $script:MachinePath -Encoding UTF8

        $settings = Get-Settings

        (Get-ObjectValue -Object (Get-ObjectValue -Object $settings -Name "watch") -Name "sampleIntervalSec") | Should -Be 5
        (Get-ObjectValue -Object (Get-ObjectValue -Object $settings -Name "watch") -Name "ringBufferSamples") | Should -Be 180
        (Get-ObjectValue -Object (Get-ObjectValue -Object $settings -Name "watch") -Name "defaultDurationSec") | Should -Be 60
        (Get-ObjectValue -Object (Get-ObjectValue -Object $settings -Name "retention") -Name "maxSessions") | Should -Be 10
    }

    It "resolves config file paths from ConfigDir when explicit path variables are unset" {
        @'
{
  "watch": {
    "sampleIntervalSec": 15
  }
}
'@ | Set-Content -LiteralPath $script:DefaultsPath -Encoding UTF8

        $script:DefaultsPath = ""
        $script:ProfilesPath = ""
        $script:MachinePath = ""

        $settings = Get-Settings

        (Get-ObjectValue -Object (Get-ObjectValue -Object $settings -Name "watch") -Name "sampleIntervalSec") | Should -Be 15
    }

    It "merges base and machine profile overrides" {
        @'
{
  "gaming": {
    "shutdownWsl": true,
    "setPowerPlan": "high_performance"
  }
}
'@ | Set-Content -LiteralPath $script:ProfilesPath -Encoding UTF8

        @'
{
  "profiles": {
    "gaming": {
      "setPowerPlan": "balanced",
      "setGameMode": false
    }
  }
}
'@ | Set-Content -LiteralPath $script:MachinePath -Encoding UTF8

        $profiles = Get-Profiles
        $gaming = Get-ObjectValue -Object $profiles -Name "gaming"

        (Get-ObjectValue -Object $gaming -Name "shutdownWsl") | Should -Be $true
        (Get-ObjectValue -Object $gaming -Name "setPowerPlan") | Should -Be "balanced"
        (Get-ObjectValue -Object $gaming -Name "setGameMode") | Should -Be $false
    }
}
