BeforeAll {
    $script:DefaultsPath = Join-Path $TestDrive "defaults.json"
    $script:StateDir     = "$TestDrive"
    . (Join-Path $PSScriptRoot "..\..\lib\config.ps1")
    . (Join-Path $PSScriptRoot "..\..\lib\listener.ps1")
}

Describe "Read-SteamVdf (VDF parser)" {
    It "extracts library paths from VDF content" {
        $vdf = @'
"libraryfolders"
{
    "0"
    {
        "path"        "C:\\Program Files (x86)\\Steam"
    }
    "1"
    {
        "path"        "D:\\SteamLibrary"
    }
}
'@
        $paths = Read-SteamVdf -Content $vdf
        $paths.Count | Should -Be 2
        $paths | Should -Contain "C:\Program Files (x86)\Steam"
        $paths | Should -Contain "D:\SteamLibrary"
    }
    It "returns empty array for malformed VDF" {
        $paths = Read-SteamVdf -Content "not vdf content"
        $paths | Should -BeNullOrEmpty
    }
}

Describe "Test-IsUnderSteamLibrary" {
    It "returns true for exe under Steam library" {
        $result = Test-IsUnderSteamLibrary -ExePath "C:\SteamLibrary\steamapps\common\Game\game.exe" -LibraryPaths @("C:\SteamLibrary")
        $result | Should -Be $true
    }
    It "returns false for exe outside Steam library" {
        $result = Test-IsUnderSteamLibrary -ExePath "C:\Program Files\SomeApp\app.exe" -LibraryPaths @("C:\SteamLibrary")
        $result | Should -Be $false
    }
    It "is case-insensitive" {
        $result = Test-IsUnderSteamLibrary -ExePath "c:\steamlibrary\steamapps\common\Game\game.exe" -LibraryPaths @("C:\SteamLibrary")
        $result | Should -Be $true
    }
}
