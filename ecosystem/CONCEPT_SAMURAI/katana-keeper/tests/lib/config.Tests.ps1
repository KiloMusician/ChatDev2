BeforeAll {
    $script:LibPath = Join-Path $PSScriptRoot "..\..\lib\config.ps1"
    # Stub $script: path vars that lib functions reference
    $script:DefaultsPath = Join-Path $TestDrive "config\defaults.json"
    $script:ProfilesPath = Join-Path $TestDrive "config\profiles.json"
    $script:MachinePath  = Join-Path $TestDrive "config\machine.local.json"
    New-Item -ItemType Directory -Path (Join-Path $TestDrive "config") -Force | Out-Null
    . $script:LibPath
}

Describe "Read-JsonFile" {
    It "returns Default when file does not exist" {
        Read-JsonFile -Path (Join-Path $TestDrive "missing.json") -Default "fallback" | Should -Be "fallback"
    }
    It "parses valid JSON" {
        '{"key":"val"}' | Set-Content (Join-Path $TestDrive "good.json") -Encoding UTF8
        (Read-JsonFile -Path (Join-Path $TestDrive "good.json")).key | Should -Be "val"
    }
    It "returns Default when file contains invalid JSON" {
        'not json' | Set-Content (Join-Path $TestDrive "bad.json") -Encoding UTF8
        Read-JsonFile -Path (Join-Path $TestDrive "bad.json") -Default 42 | Should -Be 42
    }
}

Describe "Get-ObjectValue" {
    It "returns named property from PSCustomObject" {
        $obj = [pscustomobject]@{ foo = "bar" }
        Get-ObjectValue -Object $obj -Name "foo" -Default "x" | Should -Be "bar"
    }
    It "returns Default when property missing" {
        $obj = [pscustomobject]@{ foo = "bar" }
        Get-ObjectValue -Object $obj -Name "missing" -Default "fallback" | Should -Be "fallback"
    }
    It "returns named key from hashtable" {
        $ht = @{ key = "value" }
        Get-ObjectValue -Object $ht -Name "key" -Default "x" | Should -Be "value"
    }
}

Describe "Merge-Objects" {
    It "overrides base property with override value" {
        $base     = [pscustomobject]@{ a = 1; b = 2 }
        $override = [pscustomobject]@{ b = 99 }
        $result = Merge-Objects -Base $base -Override $override
        $result.b | Should -Be 99
        $result.a | Should -Be 1
    }
    It "adds new properties from override" {
        $base     = [pscustomobject]@{ a = 1 }
        $override = [pscustomobject]@{ c = 3 }
        $result = Merge-Objects -Base $base -Override $override
        $result.c | Should -Be 3
    }
}

Describe "Get-Settings" {
    It "returns defaults when machine.local.json absent" {
        '{"watch":{"sampleIntervalSec":5}}' | Set-Content $script:DefaultsPath -Encoding UTF8
        Remove-Item $script:MachinePath -ErrorAction SilentlyContinue
        $settings = Get-Settings
        $settings.watch.sampleIntervalSec | Should -Be 5
    }
    It "machine.local settings override defaults" {
        '{"watch":{"sampleIntervalSec":5}}' | Set-Content $script:DefaultsPath -Encoding UTF8
        '{"settings":{"watch":{"sampleIntervalSec":10}}}' | Set-Content $script:MachinePath -Encoding UTF8
        $settings = Get-Settings
        $settings.watch.sampleIntervalSec | Should -Be 10
    }
}

Describe "Get-Profiles" {
    It "returns base profiles when no machine override" {
        '{"gaming":{"setGameMode":true}}' | Set-Content $script:ProfilesPath -Encoding UTF8
        Remove-Item $script:MachinePath -ErrorAction SilentlyContinue
        $profiles = Get-Profiles
        $profiles.gaming.setGameMode | Should -Be $true
    }
    It "machine.local profiles override base profiles" {
        '{"gaming":{"setGameMode":true}}' | Set-Content $script:ProfilesPath -Encoding UTF8
        '{"profiles":{"gaming":{"setGameMode":false}}}' | Set-Content $script:MachinePath -Encoding UTF8
        $profiles = Get-Profiles
        $profiles.gaming.setGameMode | Should -Be $false
    }
}
