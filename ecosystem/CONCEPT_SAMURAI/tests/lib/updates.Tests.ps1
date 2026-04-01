Describe "updates module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/actions.ps1")
        . (Join-Path $repoRoot "lib/updates.ps1")
    }
    It "parses winget upgrade table output into package objects" {
        $sample = @'
Name                        Id                          Version                     Available                   Source
-----------------------------------------------------------------------------------------------------------------------
Git                         Git.Git                     2.51.0                      2.53.0.2                    winget
Node.js                     OpenJS.NodeJS.22            22.20.0                     22.22.2                     winget
Windows Subsystem for Linux Microsoft.WSL               2.6.1.0                     2.6.3                       winget
3 upgrades available.
'@

        $items = @(ConvertFrom-WingetUpgradeOutput -Text $sample)

        $items.Count | Should -Be 3
        $items[0].Id | Should -Be "Git.Git"
        $items[2].Name | Should -Be "Windows Subsystem for Linux"
    }

    It "parses winget output even when progress lines appear before the table" {
        $sample = @"
`r   - `r
Name                        Id                          Version                     Available                   Source
-----------------------------------------------------------------------------------------------------------------------
Git                         Git.Git                     2.51.0                      2.53.0.2                    winget
1 upgrades available.
"@

        $items = @(ConvertFrom-WingetUpgradeOutput -Text $sample)

        $items.Count | Should -Be 1
        $items[0].Id | Should -Be "Git.Git"
    }

    It "blocks denied packages unless explicitly allowed" {
        $packages = @(
            [pscustomobject]@{ Name = "Git"; Id = "Git.Git"; Version = "1"; Available = "2"; Source = "winget" },
            [pscustomobject]@{ Name = "Docker Desktop"; Id = "Docker.DockerDesktop"; Version = "1"; Available = "2"; Source = "winget" },
            [pscustomobject]@{ Name = "Visual Studio Code"; Id = "Microsoft.VisualStudioCode"; Version = "1"; Available = "2"; Source = "winget" }
        )

        $settings = [pscustomobject]@{
            updates = [pscustomobject]@{
                allowPackageIds   = @("Docker.DockerDesktop")
                allowNamePatterns = @()
                denyPackageIds    = @("Docker.DockerDesktop", "Microsoft.VisualStudioCode")
                denyNamePatterns  = @("*Visual Studio Code*")
            }
        }

        $guarded = Get-GuardedUpdateSets -Packages $packages -Settings $settings

        (@($guarded.allowed).Count) | Should -Be 2
        (@($guarded.blocked).Count) | Should -Be 1
        (@($guarded.allowed | Select-Object -ExpandProperty Id) -contains "Docker.DockerDesktop") | Should -Be $true
        (@($guarded.blocked | Select-Object -ExpandProperty Id) -contains "Microsoft.VisualStudioCode") | Should -Be $true
    }
}
