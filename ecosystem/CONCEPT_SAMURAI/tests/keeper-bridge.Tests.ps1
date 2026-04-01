Describe "keeper bridge" {
    BeforeAll {
        $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
        $bridgePath = Join-Path $repoRoot "tools\keeper-bridge.ps1"
    }

    It "returns a machine-readable snapshot payload" {
        $raw = & $bridgePath snapshot | Out-String
        $payload = $raw | ConvertFrom-Json

        $payload.ok | Should -Be $true
        $payload.command | Should -Be "snapshot"
        $payload.data.surface | Should -Be "bridge"
        $payload.data.health | Should -Not -BeNullOrEmpty
        $payload.data.doctor | Should -Not -BeNullOrEmpty
    }

    It "returns machine-readable Steam metadata" {
        $raw = & $bridgePath games | Out-String
        $payload = $raw | ConvertFrom-Json

        $payload.ok | Should -Be $true
        $payload.command | Should -Be "games"
        $payload.data | Should -Not -BeNullOrEmpty
        $payload.data.active | Should -BeOfType [bool]
    }
}
