Describe "listener module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/listener.ps1")
    }
    It "parses Steam library roots from a VDF file" {
        $configDir = Join-Path $TestDrive "Steam\config"
        $vdfPath = Join-Path $configDir "libraryfolders.vdf"
        New-Item -ItemType Directory -Force -Path $configDir | Out-Null

        @'
"libraryfolders"
{
    "0"
    {
        "path"      "C:\\Program Files (x86)\\Steam"
    }
    "1"
    {
        "path"      "D:\\SteamLibrary"
    }
}
'@ | Set-Content -LiteralPath $vdfPath -Encoding UTF8

        $roots = @(Get-SteamLibraryRoots -VdfPath $vdfPath)

        ($roots -contains "C:\Program Files (x86)\Steam") | Should -Be $true
        ($roots -contains "D:\SteamLibrary") | Should -Be $true
    }

    It "treats only paths under Steam common roots as game paths" {
        $roots = @(
            "D:\SteamLibrary\steamapps\common",
            "E:\Games\SteamLibrary\steamapps\common"
        )

        (Test-PathUnderRoots -Path "D:\SteamLibrary\steamapps\common\Hades\Hades.exe" -Roots $roots) | Should -Be $true
        (Test-PathUnderRoots -Path "C:\Program Files (x86)\Steam\steam.exe" -Roots $roots) | Should -Be $false
    }

    It "parses Steam appmanifest metadata into a local game catalog entry" {
        $steamAppsDir = Join-Path $TestDrive "SteamLibrary\steamapps"
        $manifestPath = Join-Path $steamAppsDir "appmanifest_1145360.acf"
        New-Item -ItemType Directory -Force -Path $steamAppsDir | Out-Null

        @'
"AppState"
{
    "appid"      "1145360"
    "name"       "Hades"
    "installdir" "Hades"
    "buildid"    "123456"
}
'@ | Set-Content -LiteralPath $manifestPath -Encoding UTF8

        $manifest = Read-SteamAppManifest -Path $manifestPath

        $manifest.AppId | Should -Be "1145360"
        $manifest.Name | Should -Be "Hades"
        $manifest.InstallDir | Should -Be "Hades"
        $manifest.GameRoot | Should -Be (Join-Path $TestDrive "SteamLibrary\steamapps\common\Hades")
    }

    It "resolves a running exe path to Steam game metadata" {
        $games = @(
            [pscustomobject]@{
                AppId        = "1145360"
                Name         = "Hades"
                InstallDir   = "Hades"
                ManifestPath = "D:\SteamLibrary\steamapps\appmanifest_1145360.acf"
                LibraryRoot  = "D:\SteamLibrary"
                GameRoot     = "D:\SteamLibrary\steamapps\common\Hades"
            }
        )

        $game = Resolve-SteamGameMetadata -Path "D:\SteamLibrary\steamapps\common\Hades\Hades.exe" -InstalledGames $games

        $game.Name | Should -Be "Hades"
        $game.AppId | Should -Be "1145360"
    }

    It "matches a per-game listener rule by Steam AppID" {
        $settings = [pscustomobject]@{
            listener = [pscustomobject]@{
                gameProfiles = @(
                    [pscustomobject]@{
                        name        = "Balatro Quiet"
                        appId       = "2379780"
                        onGameStart = "quiet"
                        onGameExit  = "restore"
                    }
                )
            }
        }

        $game = [pscustomobject]@{
            GameName   = "Balatro"
            ProcessName = "Balatro"
            SteamAppId = "2379780"
            Path       = "D:\SteamLibrary\steamapps\common\Balatro\Balatro.exe"
            InstallDir = "Balatro"
        }

        $rule = Resolve-ListenerGameProfile -Settings $settings -GameSnapshot $game -DefaultOnGameStart "gaming" -DefaultOnGameExit "restore"

        $rule.matched | Should -Be $true
        $rule.profile_name | Should -Be "Balatro Quiet"
        $rule.on_game_start | Should -Be "quiet"
        $rule.on_game_exit | Should -Be "restore"
    }
}
