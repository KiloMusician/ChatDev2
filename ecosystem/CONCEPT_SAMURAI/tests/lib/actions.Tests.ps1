Describe "actions module" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\\..')).Path
        . (Join-Path $repoRoot "lib/config.ps1")
        . (Join-Path $repoRoot "lib/actions.ps1")
    }

    It "uses the default Docker process patterns when no override exists" {
        Remove-Variable -Name Settings -Scope Script -ErrorAction SilentlyContinue

        $patterns = @(Get-DockerProcessPatterns)

        ($patterns -contains "Docker*") | Should -Be $true
        ($patterns -contains "com.docker.*") | Should -Be $true
        ($patterns -contains "dockerd*") | Should -Be $true
    }

    It "uses configured Docker process patterns when provided" {
        $script:Settings = [pscustomobject]@{
            processPatterns = [pscustomobject]@{
                docker = @("Docker*", "custom-docker*")
            }
        }

        $patterns = @(Get-DockerProcessPatterns)

        $patterns.Count | Should -Be 2
        ($patterns -contains "custom-docker*") | Should -Be $true
    }
}
