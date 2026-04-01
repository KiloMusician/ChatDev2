Describe "steam-web module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/steam-web.ps1")
    }

    # ── Get-RepoRoot ─────────────────────────────────────────────────────────

    Describe "Get-RepoRoot" {
        It "returns a non-empty path that exists on disk" {
            $root = Get-RepoRoot
            $root | Should -Not -BeNullOrEmpty
            Test-Path -LiteralPath $root | Should -Be $true
        }
    }

    # ── Get-SteamConfig ──────────────────────────────────────────────────────

    Describe "Get-SteamConfig" {
        It "returns webApiKey and steamId from the settings object" {
            $settings = [pscustomobject]@{
                steam = [pscustomobject]@{
                    webApiKey = "TESTKEY"
                    steamId   = "76561198000000001"
                }
            }
            $cfg = Get-SteamConfig -Settings $settings
            $cfg.webApiKey | Should -Be "TESTKEY"
            $cfg.steamId   | Should -Be "76561198000000001"
        }

        It "falls back to KEEPER_STEAM_API_KEY env var when settings key is absent" {
            $env:KEEPER_STEAM_API_KEY = "ENVKEY"
            $env:KEEPER_STEAM_ID     = $null
            try {
                $settings = [pscustomobject]@{ steam = [pscustomobject]@{} }
                $cfg = Get-SteamConfig -Settings $settings
                $cfg.webApiKey | Should -Be "ENVKEY"
            }
            finally {
                Remove-Item Env:KEEPER_STEAM_API_KEY -ErrorAction SilentlyContinue
            }
        }

        It "falls back to KEEPER_STEAM_ID env var when settings steamId is absent" {
            $env:KEEPER_STEAM_ID = "76561198999999999"
            try {
                $settings = [pscustomobject]@{ steam = [pscustomobject]@{} }
                $cfg = Get-SteamConfig -Settings $settings
                $cfg.steamId | Should -Be "76561198999999999"
            }
            finally {
                Remove-Item Env:KEEPER_STEAM_ID -ErrorAction SilentlyContinue
            }
        }

        It "returns null keys when settings has no steam block and env vars are unset" {
            Remove-Item Env:KEEPER_STEAM_API_KEY -ErrorAction SilentlyContinue
            Remove-Item Env:KEEPER_STEAM_ID      -ErrorAction SilentlyContinue
            $settings = [pscustomobject]@{}
            $cfg = Get-SteamConfig -Settings $settings
            [string]$cfg.webApiKey | Should -BeNullOrEmpty
            [string]$cfg.steamId   | Should -BeNullOrEmpty
        }
    }

    # ── Get-SteamApiKey ──────────────────────────────────────────────────────

    Describe "Get-SteamApiKey" {
        It "returns only the webApiKey string" {
            $settings = [pscustomobject]@{
                steam = [pscustomobject]@{
                    webApiKey = "MYKEY"
                    steamId   = "00000"
                }
            }
            Get-SteamApiKey -Settings $settings | Should -Be "MYKEY"
        }
    }

    # ── Get-RepoSettings ─────────────────────────────────────────────────────

    Describe "Get-RepoSettings" {
        It "returns a settings object from real repo config files" {
            # Just verify it returns an object with at least one property
            $settings = Get-RepoSettings
            $settings | Should -Not -BeNullOrEmpty
            $settings.PSObject.Properties.Count | Should -BeGreaterThan 0
        }

        It "machine.local settings override defaults" {
            # Write temporary defaults and machine files to TestDrive
            $fakeRoot = Join-Path $TestDrive "fakerepo"
            $cfgDir   = Join-Path $fakeRoot "config"
            New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null

            @{ color = "blue"; size = 10 } | ConvertTo-Json | Set-Content -Path (Join-Path $cfgDir "defaults.json")
            @{ settings = @{ color = "red" } } | ConvertTo-Json | Set-Content -Path (Join-Path $cfgDir "machine.local.json")

            $result = Get-RepoSettings -RepoRoot $fakeRoot
            $result.color | Should -Be "red"
            $result.size  | Should -Be 10
        }
    }
}
