# keeper.ps1 lib/ Split + Full Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `keeper.ps1` from a 1,885-line monolith into focused `lib/` modules while shipping Steam game-watcher (A), anomaly auto-capture (B), LatencyMon auto-parse (E), MSI GPU mode detection (F), and fixing all launcher UX gaps.

**Architecture:** `keeper.ps1` becomes a ~200-line thin router that dot-sources `lib/*.ps1` modules on demand. Dot-sourcing preserves the `$script:` scope so path variables set in `keeper.ps1` are accessible in all modules. Public interface (CLI flags, config schemas, state file locations, `.cmd` launchers) is fully frozen.

**Tech Stack:** PowerShell 5.1+ / 7+, Pester v5 (tests), Windows registry via `Get-ItemPropertyValue`, CIM (`Win32_Processor`, `Win32_OperatingSystem`, `Win32_SoundDevice`), `powercfg.exe`, `wsl.exe`

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `lib/config.ps1` | JSON I/O utilities, settings/profile load + merge |
| Create | `lib/state.ps1` | current.json, rollback.json, ringbuffer.json I/O |
| Create | `lib/health.ps1` | Cheap health snapshot, power plan, game mode, WSL/Docker detection |
| Create | `lib/actions.ps1` | All side-effectful primitives: process/service/power/registry/WSL/launcher |
| Create | `lib/doctor.ps1` | Expensive diagnostics: Nahimic, audio risk, LatencyMon parse (E), GPU mode (F) |
| Create | `lib/profiles.ps1` | Mode apply + restore orchestration, session summaries |
| Create | `lib/export.ps1` | JSON + HTML incident bundle generation, prune |
| Create | `lib/watch.ps1` | Watch loop + anomaly auto-capture (B) |
| Create | `lib/listener.ps1` | Steam VDF parse + game-watcher daemon (A) |
| Modify | `keeper.ps1` | Shrink to thin router: param block + dot-sources + switch |
| Modify | `config/defaults.json` | Add `listener` and `anomaly` config sections |
| Modify | `tools/Invoke-KeeperElevated.ps1` | Try pwsh.exe first; keep elevated window open |
| Modify | `tools/install-shortcuts.ps1` | Per-type icons; add Listen + Setup shortcuts |
| Modify | `tools/keeper-gaming.cmd` | Add `pause` |
| Modify | `tools/keeper-coding.cmd` | Add `pause` |
| Modify | `tools/keeper-audio-safe.cmd` | Add `pause` |
| Modify | `tools/keeper-quiet.cmd` | Add `pause` |
| Modify | `tools/keeper-diagnose.cmd` | Add `pause` |
| Modify | `tools/keeper-restore.cmd` | Add `pause` |
| Modify | `tools/keeper-status.cmd` | Add `pause` |
| Modify | `tools/keeper-doctor.cmd` | Add `pause` |
| Modify | `tools/keeper-doctor-audio.cmd` | Add `pause` + auto-open HTML |
| Modify | `tools/keeper-export.cmd` | Add `-Html` + `pause` + auto-open HTML |
| Create | `tools/keeper-listen.cmd` | New: run `listen` command |
| Create | `tools/keeper-listen-admin.cmd` | New: run `listen` elevated |
| Create | `setup.cmd` | New: root-level first-run shortcut installer |
| Modify | `tools/gaming-mode/README.md` | Add legacy redirect notice |
| Create | `tests/lib/config.Tests.ps1` | Pester tests for config.ps1 |
| Create | `tests/lib/state.Tests.ps1` | Pester tests for state.ps1 |
| Create | `tests/lib/doctor.Tests.ps1` | Pester tests for LatencyMon parse + GPU detection |
| Create | `tests/lib/listener.Tests.ps1` | Pester tests for Steam VDF parsing |

---

## Task 1: Test Infrastructure + `lib/config.ps1`

**Files:**
- Create: `lib/config.ps1`
- Create: `tests/lib/config.Tests.ps1`

### Why this first
`config.ps1` has zero dependencies and every other module depends on it. The utility functions (`Read-JsonFile`, `Write-JsonFile`, `Merge-Objects`, `Get-ObjectValue`) are pure enough to test in isolation.

- [ ] **Step 1.1: Create `tests/lib/` directory and write failing tests**

```powershell
# tests/lib/config.Tests.ps1
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
```

- [ ] **Step 1.2: Run tests — verify all FAIL (lib/config.ps1 doesn't exist yet)**

```powershell
Invoke-Pester -Path tests/lib/config.Tests.ps1 -Output Detailed
```
Expected: `Error: Cannot find path ... lib\config.ps1`

- [ ] **Step 1.3: Create `lib/config.ps1`**

Move these functions verbatim from `keeper.ps1` (lines shown for reference):
- `Write-Log` (line 89)
- `Ensure-Directory` (line 110)
- `Read-JsonFile` (line 118)
- `Write-JsonFile` (line 141)
- `Get-PropertyNames` (line 161)
- `Get-ObjectValue` (line 175)
- `Is-MergeableObject` (line 201)
- `Merge-Objects` (line 215)
- `Get-Settings` (line 302)
- `Get-Profiles` (line 310)

```powershell
# lib/config.ps1
# Config loading, JSON utilities, and object merge helpers.
# Depends on: nothing. Dot-sourced first by keeper.ps1.
# All $script:*Path variables must be set by the caller before dot-sourcing.

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [ValidateSet("INFO","WARN","ERROR","DEBUG")][string]$Level = "INFO"
    )
    if ($Quiet -and $Level -eq "INFO") { return }
    if ($Level -eq "DEBUG" -and -not $DebugMode) { return }
    $timestamp = Get-Date -Format "s"
    Write-Host ("[{0}] [{1}] {2}" -f $timestamp, $Level, $Message)
}

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path, $Default = $null)
    if (-not (Test-Path -LiteralPath $Path)) { return $Default }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw
        if ([string]::IsNullOrWhiteSpace($raw)) { return $Default }
        return $raw | ConvertFrom-Json
    }
    catch {
        Write-Log "Failed to parse JSON file '$Path': $($_.Exception.Message)" "WARN"
        return $Default
    }
}

function Write-JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Object
    )
    if ($WhatIfPreference) { return }
    $parent = Split-Path -Parent $Path
    if ($parent) { Ensure-Directory -Path $parent }
    $Object | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-PropertyNames {
    param($Object)
    if ($null -eq $Object) { return @() }
    if ($Object -is [hashtable]) { return @($Object.Keys) }
    return @($Object.PSObject.Properties | ForEach-Object { $_.Name })
}

function Get-ObjectValue {
    param($Object, [Parameter(Mandatory = $true)][string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    if ($Object -is [hashtable]) {
        if ($Object.ContainsKey($Name)) { return $Object[$Name] }
        return $Default
    }
    $prop = $Object.PSObject.Properties[$Name]
    if ($null -ne $prop) { return $prop.Value }
    return $Default
}

function Is-MergeableObject {
    param($Value)
    if ($null -eq $Value) { return $false }
    if ($Value -is [string] -or $Value -is [int] -or $Value -is [bool] -or $Value -is [double]) { return $false }
    if ($Value -is [System.Array]) { return $false }
    if ($Value -is [hashtable]) { return $true }
    if ($Value -is [pscustomobject]) { return $true }
    return $false
}

function Merge-Objects {
    param($Base, $Override)
    if ($null -eq $Base)     { return $Override }
    if ($null -eq $Override) { return $Base }
    $result = [ordered]@{}
    foreach ($name in @(Get-PropertyNames -Object $Base)) { $result[$name] = Get-ObjectValue -Object $Base -Name $name }
    foreach ($name in @(Get-PropertyNames -Object $Override)) {
        $baseVal     = Get-ObjectValue -Object $Base     -Name $name -Default $null
        $overrideVal = Get-ObjectValue -Object $Override -Name $name -Default $null
        if ((Is-MergeableObject -Value $baseVal) -and (Is-MergeableObject -Value $overrideVal)) {
            $result[$name] = Merge-Objects -Base $baseVal -Override $overrideVal
        } else {
            $result[$name] = $overrideVal
        }
    }
    return [pscustomobject]$result
}

function Get-Settings {
    $defaults        = Read-JsonFile -Path $script:DefaultsPath -Default ([pscustomobject]@{})
    $machine         = Read-JsonFile -Path $script:MachinePath  -Default ([pscustomobject]@{})
    $machineSettings = Get-ObjectValue -Object $machine -Name "settings" -Default ([pscustomobject]@{})
    return Merge-Objects -Base $defaults -Override $machineSettings
}

function Get-Profiles {
    $profiles        = Read-JsonFile -Path $script:ProfilesPath -Default ([pscustomobject]@{})
    $machine         = Read-JsonFile -Path $script:MachinePath  -Default ([pscustomobject]@{})
    $machineProfiles = Get-ObjectValue -Object $machine -Name "profiles" -Default ([pscustomobject]@{})
    return Merge-Objects -Base $profiles -Override $machineProfiles
}
```

- [ ] **Step 1.4: Run tests — verify all PASS**

```powershell
Invoke-Pester -Path tests/lib/config.Tests.ps1 -Output Detailed
```
Expected: `Tests Passed: 9, Failed: 0`

- [ ] **Step 1.5: Commit**

```bash
git add lib/config.ps1 tests/lib/config.Tests.ps1
git commit -m "feat: extract lib/config.ps1 with JSON utils and settings load"
```

---

## Task 2: `lib/state.ps1`

**Files:**
- Create: `lib/state.ps1`
- Create: `tests/lib/state.Tests.ps1`

- [ ] **Step 2.1: Write failing tests**

```powershell
# tests/lib/state.Tests.ps1
BeforeAll {
    $script:DefaultsPath     = Join-Path $TestDrive "config\defaults.json"
    $script:CurrentStatePath = Join-Path $TestDrive "state\current.json"
    $script:RingBufferPath   = Join-Path $TestDrive "state\ringbuffer.json"
    $script:RollbackPath     = Join-Path $TestDrive "state\rollback.json"
    New-Item -ItemType Directory -Path (Join-Path $TestDrive "config") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $TestDrive "state")  -Force | Out-Null
    . (Join-Path $PSScriptRoot "..\..\lib\config.ps1")
    . (Join-Path $PSScriptRoot "..\..\lib\state.ps1")
}

Describe "Save-CurrentState / Read back" {
    It "writes and reads back mode" {
        Save-CurrentState -State ([pscustomobject]@{ mode = "gaming"; status = "ready" })
        $read = Get-Content $script:CurrentStatePath -Raw | ConvertFrom-Json
        $read.mode | Should -Be "gaming"
    }
}

Describe "Save-RollbackState / Read back" {
    It "persists rollback data" {
        Save-RollbackState -Rollback ([pscustomobject]@{ priorMode = "coding"; stoppedServices = @("WSearch") })
        $read = Get-Content $script:RollbackPath -Raw | ConvertFrom-Json
        $read.priorMode | Should -Be "coding"
    }
}

Describe "Append-RingBuffer" {
    BeforeEach {
        Remove-Item $script:RingBufferPath -ErrorAction SilentlyContinue
        '{"watch":{"ringBufferSamples":3}}' | Set-Content $script:DefaultsPath -Encoding UTF8
    }
    It "appends samples" {
        $settings = [pscustomobject]@{ watch = [pscustomobject]@{ ringBufferSamples = 3 } }
        Append-RingBuffer -Sample @{ ts = 1 } -Settings $settings
        Append-RingBuffer -Sample @{ ts = 2 } -Settings $settings
        $buf = Get-Content $script:RingBufferPath -Raw | ConvertFrom-Json
        $buf.Count | Should -Be 2
    }
    It "trims oldest when over capacity" {
        $settings = [pscustomobject]@{ watch = [pscustomobject]@{ ringBufferSamples = 2 } }
        Append-RingBuffer -Sample @{ ts = 1 } -Settings $settings
        Append-RingBuffer -Sample @{ ts = 2 } -Settings $settings
        Append-RingBuffer -Sample @{ ts = 3 } -Settings $settings
        $buf = Get-Content $script:RingBufferPath -Raw | ConvertFrom-Json
        $buf.Count  | Should -Be 2
        $buf[0].ts  | Should -Be 2
        $buf[-1].ts | Should -Be 3
    }
}

Describe "Get-CurrentModeName" {
    It "returns idle when no current.json" {
        Remove-Item $script:CurrentStatePath -ErrorAction SilentlyContinue
        Get-CurrentModeName | Should -Be "idle"
    }
    It "returns mode from current.json" {
        '{"mode":"gaming"}' | Set-Content $script:CurrentStatePath -Encoding UTF8
        Get-CurrentModeName | Should -Be "gaming"
    }
}
```

- [ ] **Step 2.2: Run — verify FAIL**

```powershell
Invoke-Pester -Path tests/lib/state.Tests.ps1 -Output Detailed
```
Expected: FAIL — `state.ps1` not found

- [ ] **Step 2.3: Create `lib/state.ps1`**

Move from `keeper.ps1`: `Save-CurrentState` (line 1014), `Save-RollbackState` (line 1019), `Append-RingBuffer` (line 1024), `Get-CurrentModeName` (line 318).

```powershell
# lib/state.ps1
# State file I/O: current.json, rollback.json, ringbuffer.json.
# Depends on: config.ps1 (Read-JsonFile, Write-JsonFile, Get-ObjectValue)

function Get-CurrentModeName {
    $state = Read-JsonFile -Path $script:CurrentStatePath -Default ([pscustomobject]@{ mode = "idle" })
    return (Get-ObjectValue -Object $state -Name "mode" -Default "idle")
}

function Save-CurrentState {
    param([Parameter(Mandatory = $true)]$State)
    Write-JsonFile -Path $script:CurrentStatePath -Object $State
}

function Save-RollbackState {
    param([Parameter(Mandatory = $true)]$Rollback)
    Write-JsonFile -Path $script:RollbackPath -Object $Rollback
}

function Append-RingBuffer {
    param(
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)]$Settings
    )
    $watch      = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $maxSamples = [int](Get-ObjectValue -Object $watch -Name "ringBufferSamples" -Default 180)
    $existing   = @(Read-JsonFile -Path $script:RingBufferPath -Default @())
    $items      = @($existing) + @($Sample)
    if ($items.Count -gt $maxSamples) {
        $items = $items[($items.Count - $maxSamples)..($items.Count - 1)]
    }
    Write-JsonFile -Path $script:RingBufferPath -Object $items
}
```

- [ ] **Step 2.4: Run — verify PASS**

```powershell
Invoke-Pester -Path tests/lib/state.Tests.ps1 -Output Detailed
```
Expected: `Tests Passed: 6, Failed: 0`

- [ ] **Step 2.5: Commit**

```bash
git add lib/state.ps1 tests/lib/state.Tests.ps1
git commit -m "feat: extract lib/state.ps1 (current, rollback, ring buffer)"
```

---

## Task 3: `lib/health.ps1` (parallel with Task 4)

**Files:**
- Create: `lib/health.ps1`

No automated tests — all functions call CIM/WMI/registry which require a running Windows environment. Verify manually.

- [ ] **Step 3.1: Create `lib/health.ps1`**

Move from `keeper.ps1`: `Test-IsAdministrator` (line 254), `Get-RegistryDword` (line 429), `Get-GameModeState` (line 444), `Get-ActivePowerPlanInfo` (line 376), `Get-RunningWslDistros` (line 534), `Get-TopCpuProcesses` (line 736), `Get-HealthState` (line 760), `Invoke-Status` (line 1459), `Invoke-Watch` placeholder (to be filled in Task 8).

```powershell
# lib/health.ps1
# Cheap health snapshot and system detection.
# Depends on: config.ps1, state.ps1

function Test-IsAdministrator {
    $identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-RegistryDword {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )
    try { return [int](Get-ItemPropertyValue -Path $Path -Name $Name -ErrorAction Stop) }
    catch { return $null }
}

function Get-GameModeState {
    $path       = "HKCU:\Software\Microsoft\GameBar"
    $allowAuto  = Get-RegistryDword -Path $path -Name "AllowAutoGameMode"
    $autoEnabled = Get-RegistryDword -Path $path -Name "AutoGameModeEnabled"
    return [pscustomobject]@{
        allowAutoGameMode   = $allowAuto
        autoGameModeEnabled = $autoEnabled
        effectiveEnabled    = (($allowAuto -eq 1) -or ($autoEnabled -eq 1))
    }
}

function Get-ActivePowerPlanInfo {
    $rootPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Power\User\PowerSchemes"
    $guid = $null
    try { $guid = [string](Get-ItemPropertyValue -Path $rootPath -Name "ActivePowerScheme" -ErrorAction Stop) } catch {}
    if (-not [string]::IsNullOrWhiteSpace($guid)) {
        $friendlyName = $null
        try {
            $planPath = Join-Path $rootPath $guid
            $friendlyName = [string](Get-ItemPropertyValue -Path $planPath -Name "FriendlyName" -ErrorAction Stop)
            if ($friendlyName -match ",([^,]+)$") { $friendlyName = $Matches[1].Trim() } else { $friendlyName = $friendlyName.Trim() }
        } catch {}
        $raw = if ($friendlyName) { "{0} ({1})" -f $guid, $friendlyName } else { $guid }
        return [pscustomobject]@{ raw = $raw; guid = $guid }
    }
    $result = Invoke-PowerCfgCommand -Arguments @("/getactivescheme")
    $raw    = [string](Get-ObjectValue -Object $result -Name "output" -Default "")
    $match  = [regex]::Match($raw, "[0-9a-fA-F-]{36}")
    return [pscustomobject]@{ raw = $raw.Trim(); guid = if ($match.Success) { $match.Value } else { $null } }
}

function Get-RunningWslDistros {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return @() }
    try {
        $lines = @(wsl.exe --list --quiet --running 2>$null)
        return @($lines | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ -ne "" })
    } catch { return @() }
}

function Get-TopCpuProcesses {
    param([int]$Top = 5)
    return @(Get-Process -ErrorAction SilentlyContinue |
        ForEach-Object {
            $cpu = $null
            try { $cpu = [math]::Round($_.TotalProcessorTime.TotalSeconds, 2) } catch {}
            [pscustomobject]@{ ProcessName = $_.ProcessName; Id = $_.Id; CPUSeconds = $cpu; WorkingSetMB = [math]::Round(($_.WorkingSet64/1MB),1) }
        } |
        Sort-Object @{ Expression = { if ($null -ne $_.CPUSeconds) { [double]$_.CPUSeconds } else { -1 } } } -Descending |
        Select-Object -First $Top)
}

function Get-HealthState {
    $modeName   = Get-CurrentModeName
    $powerPlan  = Get-ActivePowerPlanInfo
    $wslRunning = @(Get-RunningWslDistros)
    $soundDevices = @()
    try { $soundDevices = @(Get-CimInstance Win32_SoundDevice -ErrorAction Stop | Select-Object -ExpandProperty Name) } catch {}
    $cpuAverage = $null
    try {
        $loads = @(Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -ExpandProperty LoadPercentage)
        if ($loads.Count -gt 0) { $cpuAverage = [math]::Round((($loads | Measure-Object -Average).Average), 1) }
    } catch {}
    $freeMemMb = $null; $totalMemMb = $null
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $freeMemMb  = [math]::Round(($os.FreePhysicalMemory / 1024), 0)
        $totalMemMb = [math]::Round(($os.TotalVisibleMemorySize / 1024), 0)
    } catch {}
    $gameMode = Get-GameModeState
    $topCpu   = @(Get-TopCpuProcesses -Top 5)
    return [pscustomobject]@{
        timestamp           = (Get-Date).ToString("o")
        mode                = $modeName
        cpu_percent         = $cpuAverage
        free_mem_mb         = $freeMemMb
        total_mem_mb        = $totalMemMb
        power_plan_raw      = $powerPlan.raw
        power_plan_guid     = $powerPlan.guid
        wsl_active          = ($wslRunning.Count -gt 0)
        wsl_running_distros = $wslRunning
        docker_active       = (@(Find-ProcessesByPattern -Pattern "Docker*").Count -gt 0)
        game_mode_enabled   = $gameMode.effectiveEnabled
        sound_devices       = $soundDevices
        top_offenders       = @($topCpu | ForEach-Object { $_.ProcessName })
    }
}

function Invoke-Status {
    param([Parameter(Mandatory = $true)]$Settings)
    $status = Get-HealthState
    Save-CurrentState -State $status
    Append-RingBuffer -Sample $status -Settings $Settings
    return $status
}
```

- [ ] **Step 3.2: Manual smoke test (run after keeper.ps1 wired in Task 10)**

```powershell
.\keeper.ps1 status
```
Expected: health snapshot printed with `cpu_percent`, `mode`, `wsl_active` etc.

- [ ] **Step 3.3: Commit**

```bash
git add lib/health.ps1
git commit -m "feat: extract lib/health.ps1 (snapshot, power plan, game mode)"
```

---

## Task 4: `lib/actions.ps1` (parallel with Task 3)

**Files:**
- Create: `lib/actions.ps1`

- [ ] **Step 4.1: Create `lib/actions.ps1`**

Move from `keeper.ps1`: `Add-ActionResult` (265), `Format-CmdArgument` (323), `Invoke-ExternalProcess` (333), `Invoke-PowerCfgCommand` (369), `Set-RegistryDwordSafe` (456), `Set-GameModeStateSafe` (482), `Resolve-PowerPlanTarget` (493), `Set-PowerPlanSafe` (508), `Invoke-WslShutdownSafe` (556), `Find-ProcessesByPattern` (580), `Stop-ProcessesByPatternSafe` (586), `Stop-ServiceSafe` (620), `Start-ServiceSafe` (653), `Resolve-LauncherSpec` (682), `Start-LauncherSafe` (692), `Get-ActionSummary` (1043).

```powershell
# lib/actions.ps1
# All side-effectful primitives: process, service, power plan, registry, WSL, launcher.
# Depends on: config.ps1 (utilities), state.ps1 (path vars via $script:)
# Uses $script:ActionResults and $script:IsAdmin set by keeper.ps1 at startup.

function Add-ActionResult {
    param(
        [Parameter(Mandatory = $true)][string]$Action,
        [Parameter(Mandatory = $true)][string]$Target,
        [bool]$Success  = $true,
        [bool]$Changed  = $false,
        [bool]$Skipped  = $false,
        [string]$Message  = "",
        [ValidateSet("INFO","WARN","ERROR")][string]$Severity = "INFO"
    )
    $result = [pscustomobject]@{
        action  = $Action; target  = $Target; success = $Success
        changed = $Changed; skipped = $Skipped; message = $Message; severity = $Severity
    }
    $script:ActionResults += $result
    if ($Severity -eq "WARN")  { Write-Log "$Action :: $Target :: $Message" "WARN" }
    elseif ($Severity -eq "ERROR") { Write-Log "$Action :: $Target :: $Message" "ERROR" }
    else { Write-Log "$Action :: $Target :: $Message" "DEBUG" }
    return $result
}

function Get-ActionSummary {
    param([Parameter(Mandatory = $true)]$Results)
    $items = @($Results)
    return [pscustomobject]@{
        total   = $items.Count
        changed = @($items | Where-Object { $_.changed }).Count
        skipped = @($items | Where-Object { $_.skipped }).Count
        failed  = @($items | Where-Object { -not $_.success }).Count
    }
}

function Format-CmdArgument {
    param([Parameter(Mandatory = $true)][string]$Value)
    if ($Value -match '[\s"]') { return '"' + $Value.Replace('"', '""') + '"' }
    return $Value
}

function Invoke-ExternalProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $null
    )
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = $FilePath
    $psi.Arguments = ($Arguments | ForEach-Object { Format-CmdArgument $_ }) -join " "
    $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }
    $proc = [System.Diagnostics.Process]::Start($psi)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    return [pscustomobject]@{ output = ($stdout + $stderr).Trim(); exitCode = $proc.ExitCode; success = ($proc.ExitCode -eq 0) }
}

function Invoke-PowerCfgCommand {
    param([string[]]$Arguments)
    return Invoke-ExternalProcess -FilePath "powercfg.exe" -Arguments $Arguments
}

function Get-RegistryDword {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Name)
    try { return [int](Get-ItemPropertyValue -Path $Path -Name $Name -ErrorAction Stop) } catch { return $null }
}

function Set-RegistryDwordSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][int]$Value
    )
    if ($WhatIfPreference) { return $true }
    try {
        if (-not (Test-Path $Path)) { New-Item -Path $Path -Force | Out-Null }
        Set-ItemProperty -Path $Path -Name $Name -Value $Value -Type DWord -ErrorAction Stop
        return $true
    } catch { Write-Log "Failed to set registry $Path\$Name: $($_.Exception.Message)" "ERROR"; return $false }
}

function Set-GameModeStateSafe {
    param([Parameter(Mandatory = $true)][bool]$Enabled)
    $path = "HKCU:\Software\Microsoft\GameBar"
    $val  = if ($Enabled) { 1 } else { 0 }
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "set_game_mode" -Target "GameBar" -Changed $false -Skipped $true -Message "WhatIf: would set AllowAutoGameMode=$val."
    }
    $ok = Set-RegistryDwordSafe -Path $path -Name "AllowAutoGameMode" -Value $val
    if ($ok) { return Add-ActionResult -Action "set_game_mode" -Target "GameBar" -Changed $true -Message "AllowAutoGameMode set to $val." }
    return Add-ActionResult -Action "set_game_mode" -Target "GameBar" -Success $false -Changed $false -Message "Registry write failed." -Severity "ERROR"
}

function Resolve-PowerPlanTarget {
    param([Parameter(Mandatory = $true)][string]$PlanName, [Parameter(Mandatory = $true)]$Settings)
    $knownPlans = Get-ObjectValue -Object $Settings -Name "knownPowerPlans" -Default ([pscustomobject]@{})
    $mapped = Get-ObjectValue -Object $knownPlans -Name $PlanName -Default $null
    if ($null -ne $mapped -and -not [string]::IsNullOrWhiteSpace([string]$mapped)) { return [string]$mapped }
    return $PlanName
}

function Set-PowerPlanSafe {
    param([Parameter(Mandatory = $true)][string]$PlanName, [Parameter(Mandatory = $true)]$Settings)
    $target = Resolve-PowerPlanTarget -PlanName $PlanName -Settings $Settings
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Changed $false -Skipped $true -Message "WhatIf: would activate '$target'."
    }
    $result = Invoke-PowerCfgCommand -Arguments @("/setactive", $target)
    if ($result.success) { return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Changed $true -Message "Activated '$target'." }
    return Add-ActionResult -Action "set_power_plan" -Target $PlanName -Success $false -Changed $false -Message $result.output -Severity "ERROR"
}

function Get-RunningWslDistros {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) { return @() }
    try { return @(@(wsl.exe --list --quiet --running 2>$null) | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ -ne "" }) }
    catch { return @() }
}

function Invoke-WslShutdownSafe {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $false -Skipped $true -Message "WSL is not installed." -Severity "WARN"
    }
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $false -Skipped $true -Message "WhatIf: would run wsl --shutdown."
    }
    $result = Invoke-ExternalProcess -FilePath "wsl.exe" -Arguments @("--shutdown")
    if ($result.success) { return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Changed $true -Message "WSL shutdown." }
    return Add-ActionResult -Action "shutdown_wsl" -Target "wsl.exe" -Success $false -Changed $false -Message $result.output -Severity "ERROR"
}

function Find-ProcessesByPattern {
    param([Parameter(Mandatory = $true)][string]$Pattern)
    if ($Pattern -match '\*') {
        $prefix = $Pattern.TrimEnd('*')
        return @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like $Pattern })
    }
    return @(Get-Process -Name $Pattern -ErrorAction SilentlyContinue)
}

function Stop-ProcessesByPatternSafe {
    param(
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)][ref]$RollbackState
    )
    $matches = @(Find-ProcessesByPattern -Pattern $Pattern)
    if ($matches.Count -eq 0) {
        return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $false -Skipped $true -Message "No matching processes found."
    }
    if ($WhatIfPreference) {
        return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $false -Skipped $true -Message ("WhatIf: would stop {0} process(es)." -f $matches.Count)
    }
    $relaunchMappings = Get-ObjectValue -Object $Settings -Name "relaunchMappings" -Default ([pscustomobject]@{})
    $stoppedNames = @()
    foreach ($proc in $matches) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        $stoppedNames += $proc.ProcessName
        $launcherName = Get-ObjectValue -Object $relaunchMappings -Name $proc.ProcessName -Default $null
        if ($null -ne $launcherName -and -not ($RollbackState.Value.relaunchers -contains $launcherName)) {
            $RollbackState.Value.relaunchers += $launcherName
        }
    }
    $RollbackState.Value.stoppedProcesses += $stoppedNames
    return Add-ActionResult -Action "stop_process" -Target $Pattern -Changed $true -Message ("Stopped {0} process(es): {1}" -f $matches.Count, (($stoppedNames | Sort-Object -Unique) -join ", "))
}

function Stop-ServiceSafe {
    param([Parameter(Mandatory = $true)][string]$ServiceName, [Parameter(Mandatory = $true)][ref]$RollbackState)
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service not found." }
    if ($svc.Status -ne "Running") { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service not running." }
    if (-not $script:IsAdmin) { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Requires administrator privileges." -Severity "WARN" }
    if ($WhatIfPreference) { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $false -Skipped $true -Message "WhatIf: would stop service." }
    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction Stop
        $RollbackState.Value.stoppedServices += $ServiceName
        return Add-ActionResult -Action "stop_service" -Target $ServiceName -Changed $true -Message "Service stopped."
    } catch { return Add-ActionResult -Action "stop_service" -Target $ServiceName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR" }
}

function Start-ServiceSafe {
    param([Parameter(Mandatory = $true)][string]$ServiceName)
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service not found." }
    if ($svc.Status -eq "Running") { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Service already running." }
    if (-not $script:IsAdmin) { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "Requires administrator privileges." -Severity "WARN" }
    if ($WhatIfPreference) { return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $false -Skipped $true -Message "WhatIf: would start service." }
    try { Start-Service -Name $ServiceName -ErrorAction Stop; return Add-ActionResult -Action "start_service" -Target $ServiceName -Changed $true -Message "Service started." }
    catch { return Add-ActionResult -Action "start_service" -Target $ServiceName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR" }
}

function Resolve-LauncherSpec {
    param([Parameter(Mandatory = $true)][string]$LauncherName, [Parameter(Mandatory = $true)]$Settings)
    $launchers = Get-ObjectValue -Object $Settings -Name "launchers" -Default ([pscustomobject]@{})
    return Get-ObjectValue -Object $launchers -Name $LauncherName -Default $null
}

function Start-LauncherSafe {
    param([Parameter(Mandatory = $true)][string]$LauncherName, [Parameter(Mandatory = $true)]$Settings)
    $spec = Resolve-LauncherSpec -LauncherName $LauncherName -Settings $Settings
    if ($null -eq $spec) { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "Launcher not defined in config." -Severity "WARN" }
    $command = Get-ObjectValue -Object $spec -Name "command" -Default $null
    if ([string]::IsNullOrWhiteSpace([string]$command)) { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "Launcher command is empty." -Severity "WARN" }
    if ($WhatIfPreference) { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $false -Skipped $true -Message "WhatIf: would start '$command'." }
    $args      = @(Get-ObjectValue -Object $spec -Name "arguments" -Default @())
    $workDir   = Get-ObjectValue -Object $spec -Name "workingDirectory" -Default $null
    $startArgs = @{ FilePath = $command }
    if ($args.Count -gt 0) { $startArgs["ArgumentList"] = $args }
    if ($workDir)           { $startArgs["WorkingDirectory"] = $workDir }
    try { Start-Process @startArgs | Out-Null; return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Changed $true -Message "Started '$command'." }
    catch { return Add-ActionResult -Action "start_launcher" -Target $LauncherName -Success $false -Changed $false -Message $_.Exception.Message -Severity "ERROR" }
}
```

- [ ] **Step 4.2: Commit**

```bash
git add lib/actions.ps1
git commit -m "feat: extract lib/actions.ps1 (process, service, power, registry, WSL)"
```

---

## Task 5: `lib/doctor.ps1` — includes Features E + F

**Files:**
- Create: `lib/doctor.ps1`
- Create: `tests/lib/doctor.Tests.ps1`

- [ ] **Step 5.1: Write failing tests for new functions E + F**

```powershell
# tests/lib/doctor.Tests.ps1
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
        # Minimal LatencyMon-style report text
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
```

- [ ] **Step 5.2: Run — verify FAIL**

```powershell
Invoke-Pester -Path tests/lib/doctor.Tests.ps1 -Output Detailed
```
Expected: FAIL — `doctor.ps1` not found

- [ ] **Step 5.3: Create `lib/doctor.ps1`**

Move from `keeper.ps1`: `Get-ServiceSnapshotsByPatterns` (816), `Get-ProcessSnapshotsByPatterns` (851), `Get-InstalledPackagesByPattern` (880), `Get-AudioDriverSnapshots` (908), `Get-LatencyMonSummary` (922), `Get-DoctorReport` (1273), `Get-AudioTriageReport` (1355), `Get-RecentSessions` (1255).

Add **new** functions for E + F:

```powershell
# lib/doctor.ps1
# Expensive diagnostics: Nahimic, audio risk, LatencyMon (E), GPU mode (F).
# Depends on: config.ps1, health.ps1

# ── Feature E helpers ────────────────────────────────────────────────────────

function Resolve-DriverCause {
    param([Parameter(Mandatory = $true)][string]$DriverName)
    $map = @{
        "nvlddmkm.sys" = "NVIDIA display driver — update via GeForce Experience or nvidia.com"
        "ndis.sys"      = "Network adapter driver — update in Device Manager or disable Wi-Fi during gaming"
        "HDAudBus.sys"  = "Audio driver itself — check Realtek/Nahimic stack"
        "ACPI.sys"      = "Power management / BIOS firmware — check for BIOS update on MSI support site"
        "dxgkrnl.sys"   = "DirectX GPU scheduler — update GPU driver"
        "storahci.sys"  = "Storage controller — update via Device Manager"
        "tcpip.sys"     = "TCP/IP stack — try disabling Wi-Fi adapter while gaming"
        "Wdf01000.sys"  = "Windows Driver Framework — Windows Update may resolve"
    }
    foreach ($key in $map.Keys) {
        if ($DriverName -like "*$key*") { return $map[$key] }
    }
    return "Unknown driver — search '$DriverName' in LatencyMon documentation"
}

function Parse-LatencyMonReport {
    param([Parameter(Mandatory = $true)][string]$ReportText)
    $lines   = $ReportText -split "`n"
    $drivers = [ordered]@{}

    foreach ($line in $lines) {
        # Match patterns like: "Driver with highest ISR/DPC routine execution time: foo.sys"
        if ($line -match "Driver with highest.+time:\s*(.+\.sys)") {
            $driverName = $Matches[1].Trim()
            if (-not $drivers.Contains($driverName)) { $drivers[$driverName] = 0.0 }
        }
        # Match time lines: "Highest reported ISR/DPC routine execution time.*: 312.40"
        if ($line -match "Highest reported .+ execution time.*:\s*([\d.]+)") {
            $timeUs = [double]$Matches[1]
            # Associate with the most recently seen driver name
            $lastDriver = @($drivers.Keys)[-1]
            if ($null -ne $lastDriver -and $timeUs -gt $drivers[$lastDriver]) {
                $drivers[$lastDriver] = $timeUs
            }
        }
    }

    $topDrivers = @($drivers.GetEnumerator() |
        Sort-Object Value -Descending |
        Select-Object -First 3 |
        ForEach-Object {
            [pscustomobject]@{
                driver    = $_.Key
                maxTimeUs = [math]::Round($_.Value, 2)
                cause     = Resolve-DriverCause -DriverName $_.Key
            }
        })

    return [pscustomobject]@{
        topDrivers    = $topDrivers
        raw_line_count = $lines.Count
    }
}

function Get-LatencyMonAutoPath {
    param([string[]]$SearchPaths = @())
    if (-not $SearchPaths -or $SearchPaths.Count -eq 0) {
        $SearchPaths = @(
            [Environment]::GetFolderPath("Desktop"),
            [Environment]::GetFolderPath("MyDocuments")
        )
    }
    foreach ($dir in $SearchPaths) {
        if (-not (Test-Path $dir)) { continue }
        $file = Get-ChildItem -LiteralPath $dir -Filter "LatencyMon*.txt" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1
        if ($file) { return $file.FullName }
    }
    return $null
}

# ── Feature F helper ─────────────────────────────────────────────────────────

function Get-GpuModeInfo {
    # MSI GPU switching state is stored in the display adapter's driver registry key.
    # We probe the first adapter key (0000); MSI Center writes MSHybridEnabled here.
    $basePath  = "HKLM:\SYSTEM\ControlSet001\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    $adapterKey = Join-Path $basePath "0000"
    $value = $null
    try { $value = Get-ItemPropertyValue -Path $adapterKey -Name "MSHybridEnabled" -ErrorAction Stop } catch {}
    if ($null -eq $value) {
        return [pscustomobject]@{ detected = $false; mode = "unknown"; note = "GPU mode switching not detected (non-MSI or key absent)" }
    }
    if ($value -eq 1) {
        return [pscustomobject]@{ detected = $true; mode = "MSHybrid"; note = "MSHybrid active — switch to Discrete Only in MSI Center before gaming for lower DPC latency" }
    }
    return [pscustomobject]@{ detected = $true; mode = "DiscreteOnly"; note = "Discrete Only — optimal for gaming" }
}

# ── Moved from keeper.ps1 (unchanged) ────────────────────────────────────────

function Get-ServiceSnapshotsByPatterns {
    param([string[]]$Patterns)
    $allServices = @(Get-Service -ErrorAction SilentlyContinue)
    $results = @()
    foreach ($pattern in $Patterns) {
        $results += @($allServices | Where-Object { $_.Name -like $pattern -or $_.DisplayName -like $pattern } |
            Select-Object Name, DisplayName, Status, StartType)
    }
    return $results
}

function Get-ProcessSnapshotsByPatterns {
    param([string[]]$Patterns)
    $results = @()
    foreach ($pattern in $Patterns) {
        $results += @(Find-ProcessesByPattern -Pattern $pattern |
            Select-Object ProcessName, Id, @{ Name="CPU_s"; Expression={ try { [math]::Round($_.TotalProcessorTime.TotalSeconds,2) } catch { $null } } },
                @{ Name="WS_MB"; Expression={ [math]::Round($_.WorkingSet64/1MB,1) } })
    }
    return $results
}

function Get-InstalledPackagesByPattern {
    param([string]$DisplayNamePattern)
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    )
    $results = @()
    foreach ($path in $paths) {
        if (-not (Test-Path $path)) { continue }
        $results += @(Get-ChildItem $path -ErrorAction SilentlyContinue |
            ForEach-Object { Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue } |
            Where-Object { $_.DisplayName -match $DisplayNamePattern } |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate)
    }
    return $results
}

function Get-AudioDriverSnapshots {
    try {
        return @(Get-CimInstance Win32_PnPSignedDriver -ErrorAction Stop |
            Where-Object { $null -ne $_.DeviceName -and ([string]$_.DeviceName) -match "Realtek|Nahimic|Audio|Smart Sound" } |
            Select-Object DeviceName, DriverVersion, DriverDate, Manufacturer)
    } catch { return @() }
}

function Get-LatencyMonSummary {
    param([string]$Path)
    # Auto-discover if no path given
    if ([string]::IsNullOrWhiteSpace($Path)) {
        $Path = Get-LatencyMonAutoPath
    }
    $autoDiscovered = $false
    if ([string]::IsNullOrWhiteSpace($Path)) {
        return [pscustomobject]@{ provided = $false; found = $false; auto_discovered = $false; top_drivers = @(); notes = @("No LatencyMon report path provided and none found on Desktop/Documents.") }
    }
    if (-not (Test-Path -LiteralPath $Path)) {
        return [pscustomobject]@{ provided = $true; found = $false; auto_discovered = $false; path = $Path; top_drivers = @(); notes = @("LatencyMon report path provided but file not found.") }
    }
    try {
        $content = Get-Content -LiteralPath $Path -Raw -ErrorAction Stop
        $parsed  = Parse-LatencyMonReport -ReportText $content
        return [pscustomobject]@{
            provided        = $true
            found           = $true
            auto_discovered = $autoDiscovered
            path            = $Path
            top_drivers     = $parsed.topDrivers
            notes           = @()
        }
    } catch {
        return [pscustomobject]@{ provided = $true; found = $true; path = $Path; top_drivers = @(); notes = @("Could not read LatencyMon report: $($_.Exception.Message)") }
    }
}

function Get-RecentSessions {
    param([int]$Max = 10)
    return @(Get-ChildItem -LiteralPath $script:SessionsDir -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Max |
        ForEach-Object { Read-JsonFile -Path $_.FullName -Default $null } |
        Where-Object { $null -ne $_ })
}

function Get-DoctorReport {
    param([Parameter(Mandatory = $true)]$Settings)
    $doctor  = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
    $cpuWarn = [int](Get-ObjectValue -Object $doctor -Name "cpuWarningPercent" -Default 60)
    $nahimicSvcPatterns  = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns"  -Default @("Nahimic*"))
    $nahimicProcPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns"  -Default @("Nahimic*"))
    $audioRiskPatterns   = @(Get-ObjectValue -Object $doctor -Name "audioRiskProcessPatterns" -Default @())

    $health  = Get-HealthState
    $findings = @()
    $riskScore = 0

    if (-not $script:IsAdmin) { $findings += "Not running as administrator — service control unavailable." }

    $nahimicSvcs  = @($nahimicSvcPatterns  | ForEach-Object { @(Get-Service -Name $_ -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name) } | Sort-Object -Unique)
    $nahimicProcs = @($nahimicProcPatterns | ForEach-Object { @(Find-ProcessesByPattern -Pattern $_ | Select-Object -ExpandProperty ProcessName) } | Sort-Object -Unique)
    if ($nahimicSvcs.Count -gt 0 -or $nahimicProcs.Count -gt 0) {
        $findings  += "Nahimic services or processes detected (common MSI audio conflict)."
        $riskScore += 2
    }

    if ($health.docker_active) { $findings += "Docker Desktop is active."; $riskScore++ }
    if ($health.wsl_active)    { $findings += "WSL is running: $($health.wsl_running_distros -join ', ')."; $riskScore++ }

    $cpuPercent = $health.cpu_percent
    if ($null -ne $cpuPercent -and [double]$cpuPercent -ge $cpuWarn) {
        $findings += "CPU usage is high ($cpuPercent%)."; $riskScore++
    }

    $activeAudioRisk = @()
    foreach ($pattern in $audioRiskPatterns) {
        $activeAudioRisk += @(Find-ProcessesByPattern -Pattern $pattern | Select-Object -ExpandProperty ProcessName)
    }
    $activeAudioRisk = @($activeAudioRisk | Sort-Object -Unique)
    if ($activeAudioRisk.Count -gt 0) {
        $findings += "Audio-risk processes active: $($activeAudioRisk -join ', ')."; $riskScore++
    }

    $riskLevel = if ($riskScore -ge 4) { "high" } elseif ($riskScore -ge 2) { "medium" } else { "low" }

    $gpuMode = Get-GpuModeInfo

    return [pscustomobject]@{
        timestamp           = $health.timestamp
        risk_level          = $riskLevel
        risk_score          = $riskScore
        findings            = $findings
        nahimic_services    = $nahimicSvcs
        nahimic_processes   = $nahimicProcs
        audio_risk_active   = $activeAudioRisk
        top_offenders       = $health.top_offenders
        wsl_running_distros = $health.wsl_running_distros
        power_plan_raw      = $health.power_plan_raw
        game_mode_enabled   = $health.game_mode_enabled
        gpu_mode            = $gpuMode.mode
        gpu_mode_note       = $gpuMode.note
        cpu_percent         = $cpuPercent
    }
}

function Get-AudioTriageReport {
    param([Parameter(Mandatory = $true)]$Settings, [string]$LatencyMonReportPath)
    $doctor    = Get-ObjectValue -Object $Settings -Name "doctor" -Default ([pscustomobject]@{})
    $nahimicSvcPatterns  = @(Get-ObjectValue -Object $doctor -Name "nahimicServicePatterns"  -Default @("Nahimic*"))
    $nahimicProcPatterns = @(Get-ObjectValue -Object $doctor -Name "nahimicProcessPatterns"  -Default @("Nahimic*"))
    $serviceDetails   = @(Get-ServiceSnapshotsByPatterns  -Patterns $nahimicSvcPatterns)
    $processDetails   = @(Get-ProcessSnapshotsByPatterns  -Patterns $nahimicProcPatterns)
    $audioDrivers     = @(Get-AudioDriverSnapshots)
    $installedPkgs    = @(Get-InstalledPackagesByPattern -DisplayNamePattern "Nahimic|Realtek Audio|A-Volute")
    $latencyMon       = Get-LatencyMonSummary -Path $LatencyMonReportPath

    $recommendedAction = "collect-latencymon"
    if ($serviceDetails.Count -gt 0 -or $processDetails.Count -gt 0) { $recommendedAction = "disable-nahimic-first" }
    if ($latencyMon.top_drivers.Count -gt 0 -and $latencyMon.top_drivers[0].driver -notmatch "Nahimic") {
        $recommendedAction = "investigate-top-driver"
    }

    return [pscustomobject]@{
        timestamp          = (Get-Date).ToString("o")
        nahimic_services   = $serviceDetails
        nahimic_processes  = $processDetails
        audio_drivers      = $audioDrivers
        installed_packages = $installedPkgs
        latencymon         = $latencyMon
        recommended_action = $recommendedAction
    }
}
```

- [ ] **Step 5.4: Run tests — verify PASS**

```powershell
Invoke-Pester -Path tests/lib/doctor.Tests.ps1 -Output Detailed
```
Expected: `Tests Passed: 7, Failed: 0`

- [ ] **Step 5.5: Commit**

```bash
git add lib/doctor.ps1 tests/lib/doctor.Tests.ps1
git commit -m "feat: extract lib/doctor.ps1 with LatencyMon parse (E) and GPU mode (F)"
```

---

## Task 6: `lib/profiles.ps1`

**Files:**
- Create: `lib/profiles.ps1`

- [ ] **Step 6.1: Create `lib/profiles.ps1`**

Move from `keeper.ps1`: `New-SessionSummary` (1055), `Invoke-ModeProfile` (1090), `Invoke-RestoreMode` (1190).

```powershell
# lib/profiles.ps1
# Mode application + restore orchestration, session summaries.
# Depends on: config.ps1, state.ps1, health.ps1, actions.ps1

function New-SessionSummary {
    param(
        [Parameter(Mandatory = $true)][string]$ModeName,
        [Parameter(Mandatory = $true)][datetime]$StartedAt,
        [Parameter(Mandatory = $true)][datetime]$EndedAt,
        [Parameter(Mandatory = $true)]$Before,
        [Parameter(Mandatory = $true)]$After,
        [Parameter(Mandatory = $true)]$Results,
        [string[]]$Notes = @()
    )
    $summary = [pscustomobject]@{
        session_id          = $StartedAt.ToString("yyyy-MM-ddTHH-mm-ss")
        mode                = $ModeName
        started_at          = $StartedAt.ToString("o")
        ended_at            = $EndedAt.ToString("o")
        duration_min        = [math]::Round((($EndedAt - $StartedAt).TotalMinutes), 2)
        cpu_percent_before  = Get-ObjectValue -Object $Before -Name "cpu_percent"
        cpu_percent_after   = Get-ObjectValue -Object $After  -Name "cpu_percent"
        wsl_active_before   = Get-ObjectValue -Object $Before -Name "wsl_active"  -Default $false
        wsl_active_after    = Get-ObjectValue -Object $After  -Name "wsl_active"  -Default $false
        docker_active_before = Get-ObjectValue -Object $Before -Name "docker_active" -Default $false
        docker_active_after  = Get-ObjectValue -Object $After  -Name "docker_active" -Default $false
        top_offenders       = @(Get-ObjectValue -Object $After -Name "top_offenders" -Default @())
        action_summary      = Get-ActionSummary -Results $Results
        notes               = $Notes
    }
    $filePath = Join-Path $script:SessionsDir "$($summary.session_id)-$ModeName.json"
    Write-JsonFile -Path $filePath -Object $summary
    return $summary
}

function Invoke-ModeProfile {
    param(
        [Parameter(Mandatory = $true)][string]$ModeName,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )
    $profile = Get-ObjectValue -Object $Profiles -Name $ModeName -Default $null
    if ($null -eq $profile) { throw "Profile '$ModeName' is not defined in config/profiles.json." }

    $startedAt = Get-Date
    $before    = Get-HealthState
    $notes     = @((Get-ObjectValue -Object $profile -Name "notes" -Default @()))

    $rollback = [ordered]@{
        timestamp          = $startedAt.ToString("o")
        priorMode          = Get-ObjectValue -Object $before -Name "mode" -Default "idle"
        priorPowerPlanGuid = Get-ObjectValue -Object $before -Name "power_plan_guid"
        priorPowerPlanRaw  = Get-ObjectValue -Object $before -Name "power_plan_raw"
        priorGameMode      = Get-GameModeState
        priorWslActive     = Get-ObjectValue -Object $before -Name "wsl_active" -Default $false
        stoppedProcesses   = @()
        stoppedServices    = @()
        relaunchers        = @()
    }

    Save-CurrentState -State ([pscustomobject]@{ mode = $ModeName; status = "applying"; started_at = $startedAt.ToString("o"); description = ($notes -join " ") })

    if ([bool](Get-ObjectValue -Object $profile -Name "shutdownWsl" -Default $false)) {
        [void](Invoke-WslShutdownSafe)
    }
    foreach ($pattern in @(Get-ObjectValue -Object $profile -Name "stopProcesses" -Default @())) {
        [void](Stop-ProcessesByPatternSafe -Pattern ([string]$pattern) -Settings $Settings -RollbackState ([ref]$rollback))
    }
    foreach ($svcName in @(Get-ObjectValue -Object $profile -Name "stopServices" -Default @())) {
        [void](Stop-ServiceSafe -ServiceName ([string]$svcName) -RollbackState ([ref]$rollback))
    }
    $powerPlan = Get-ObjectValue -Object $profile -Name "setPowerPlan" -Default $null
    if ($null -ne $powerPlan) { [void](Set-PowerPlanSafe -PlanName ([string]$powerPlan) -Settings $Settings) }
    $setGameMode = Get-ObjectValue -Object $profile -Name "setGameMode" -Default $null
    if ($null -ne $setGameMode) { [void](Set-GameModeStateSafe -Enabled ([bool]$setGameMode)) }
    foreach ($svcName in @(Get-ObjectValue -Object $profile -Name "startServices" -Default @())) {
        [void](Start-ServiceSafe -ServiceName ([string]$svcName))
    }
    foreach ($launcherName in @(Get-ObjectValue -Object $profile -Name "startLaunchers" -Default @())) {
        [void](Start-LauncherSafe -LauncherName ([string]$launcherName) -Settings $Settings)
    }

    $endedAt = Get-Date
    $after   = Get-HealthState
    Append-RingBuffer -Sample $after -Settings $Settings
    Save-RollbackState -Rollback ([pscustomobject]$rollback)

    $currentState = [pscustomobject]@{
        mode            = $ModeName; status = "ready"
        started_at      = $startedAt.ToString("o"); updated_at = $endedAt.ToString("o")
        power_plan_raw  = Get-ObjectValue -Object $after -Name "power_plan_raw"
        power_plan_guid = Get-ObjectValue -Object $after -Name "power_plan_guid"
        wsl_active      = Get-ObjectValue -Object $after -Name "wsl_active"
        docker_active   = Get-ObjectValue -Object $after -Name "docker_active"
        cpu_percent     = Get-ObjectValue -Object $after -Name "cpu_percent"
        free_mem_mb     = Get-ObjectValue -Object $after -Name "free_mem_mb"
        top_offenders   = Get-ObjectValue -Object $after -Name "top_offenders"
        game_mode       = Get-ObjectValue -Object $after -Name "game_mode_enabled"
        action_summary  = Get-ActionSummary -Results $script:ActionResults
    }
    Save-CurrentState -State $currentState

    $summary = New-SessionSummary -ModeName $ModeName -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $script:ActionResults -Notes $notes
    return [pscustomobject]@{ mode = $ModeName; before = $before; after = $after; summary = $summary; actions = @($script:ActionResults) }
}

function Invoke-RestoreMode {
    param([Parameter(Mandatory = $true)]$Settings)
    $rollback = Read-JsonFile -Path $script:RollbackPath -Default $null
    if ($null -eq $rollback) { throw "No rollback.json found. Run a mode change first." }

    $startedAt = Get-Date
    $before    = Get-HealthState

    foreach ($svcName in @(Get-ObjectValue -Object $rollback -Name "stoppedServices" -Default @())) {
        [void](Start-ServiceSafe -ServiceName ([string]$svcName))
    }
    $priorGuid = Get-ObjectValue -Object $rollback -Name "priorPowerPlanGuid" -Default $null
    if ($null -ne $priorGuid -and -not [string]::IsNullOrWhiteSpace([string]$priorGuid)) {
        [void](Invoke-PowerCfgCommand -Arguments @("/setactive", [string]$priorGuid))
        Add-ActionResult -Action "restore_power_plan" -Target ([string]$priorGuid) -Changed $true -Message "Power plan restored." | Out-Null
    }
    $priorGameMode = Get-ObjectValue -Object $rollback -Name "priorGameMode" -Default $null
    if ($null -ne $priorGameMode) {
        $priorEnabled = Get-ObjectValue -Object $priorGameMode -Name "effectiveEnabled" -Default $false
        [void](Set-GameModeStateSafe -Enabled ([bool]$priorEnabled))
    }
    foreach ($launcherName in @(Get-ObjectValue -Object $rollback -Name "relaunchers" -Default @())) {
        [void](Start-LauncherSafe -LauncherName ([string]$launcherName) -Settings $Settings)
    }

    $endedAt = Get-Date
    $after   = Get-HealthState
    Append-RingBuffer -Sample $after -Settings $Settings
    $summary = New-SessionSummary -ModeName "restore" -StartedAt $startedAt -EndedAt $endedAt -Before $before -After $after -Results $script:ActionResults -Notes @("Rolled back to prior state.")
    Save-CurrentState -State ([pscustomobject]@{ mode = "restored"; status = "ready"; updated_at = $endedAt.ToString("o") })
    return [pscustomobject]@{ mode = "restore"; before = $before; after = $after; summary = $summary; actions = @($script:ActionResults) }
}
```

- [ ] **Step 6.2: Commit**

```bash
git add lib/profiles.ps1
git commit -m "feat: extract lib/profiles.ps1 (mode apply, restore, session summaries)"
```

---

## Task 7: `lib/export.ps1`

**Files:**
- Create: `lib/export.ps1`

- [ ] **Step 7.1: Create `lib/export.ps1`**

Move `Invoke-Export` (1506) and `Invoke-Prune` (1777) from `keeper.ps1`. Keep ALL HTML generation logic intact — this is a direct lift.

```powershell
# lib/export.ps1
# JSON + HTML incident bundle generation and prune.
# Depends on: config.ps1, state.ps1, health.ps1, doctor.ps1
```

Then copy the full bodies of `Invoke-Export` and `Invoke-Prune` from `keeper.ps1` lines 1506–1812 verbatim. These are large but correct — no logic changes needed.

> **Note:** The inner helper functions `Convert-CellValueToHtml` and `Convert-RowsToHtmlTable` are defined inside `Invoke-Export` as nested functions. Leave them nested — they're only called by `Invoke-Export`.

- [ ] **Step 7.2: Commit**

```bash
git add lib/export.ps1
git commit -m "feat: extract lib/export.ps1 (HTML/JSON export, prune)"
```

---

## Task 8: `lib/watch.ps1` — Feature B (anomaly auto-capture)

**Files:**
- Create: `lib/watch.ps1`

- [ ] **Step 8.1: Create `lib/watch.ps1`**

Move `Invoke-Watch` (1468) from `keeper.ps1`. Add `Test-AnomalyConditions` and `Invoke-AnomalyCapture`.

```powershell
# lib/watch.ps1
# Watch loop with anomaly auto-capture (Feature B).
# Depends on: config.ps1, state.ps1, health.ps1, export.ps1

function Test-AnomalyConditions {
    param(
        [Parameter(Mandatory = $true)]$Sample,
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$WatchState
    )
    $anomalyCfg      = Get-ObjectValue -Object $Settings -Name "anomaly" -Default ([pscustomobject]@{})
    $enabled         = [bool](Get-ObjectValue -Object $anomalyCfg -Name "enabled" -Default $true)
    if (-not $enabled) { return $false }

    $cpuThresh       = [int](Get-ObjectValue -Object $anomalyCfg -Name "cpuSpikePercent"       -Default 80)
    $sustainSamples  = [int](Get-ObjectValue -Object $anomalyCfg -Name "spikeSustainSamples"   -Default 3)
    $captureNahimic  = [bool](Get-ObjectValue -Object $anomalyCfg -Name "captureOnNahimicDetected"    -Default $true)
    $riskIncrease    = [int](Get-ObjectValue -Object $anomalyCfg -Name "audioRiskNewProcesses"  -Default 2)

    $cpu = $Sample.cpu_percent
    if ($null -ne $cpu -and [double]$cpu -ge $cpuThresh) {
        $WatchState.HighCpuStreak++
    } else {
        $WatchState.HighCpuStreak = 0
    }
    if ($WatchState.HighCpuStreak -ge $sustainSamples) { return $true }

    $topOffenders = @(Get-ObjectValue -Object $Sample -Name "top_offenders" -Default @())
    $nahimicFound = $topOffenders | Where-Object { $_ -like "Nahimic*" }
    if ($captureNahimic -and $nahimicFound -and -not $WatchState.NahimicSeenAtStart) { return $true }

    $currentRiskCount = @($topOffenders | Where-Object { $_ -match "^(chrome|msedge|firefox|Code|node|python|docker|jupyter)" }).Count
    if (($currentRiskCount - $WatchState.InitialRiskCount) -ge $riskIncrease) { return $true }

    return $false
}

function Invoke-AnomalyCapture {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Sample
    )
    $timestamp  = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
    $outputPath = Join-Path $script:IncidentsDir "anomaly-$timestamp.json"
    $bundle = [pscustomobject]@{
        report_type   = "anomaly"
        captured_at   = (Get-Date).ToString("o")
        trigger_sample = $Sample
        current_state = Read-JsonFile -Path $script:CurrentStatePath -Default $null
        recent_sessions = Get-RecentSessions -Max 5
    }
    $bundle | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $outputPath -Encoding UTF8
    Write-Host "`n[ANOMALY] Incident captured → $outputPath" -ForegroundColor Yellow
    return $outputPath
}

function Invoke-Watch {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [int]$RunForSeconds = 0
    )
    $watch      = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $interval   = [int](Get-ObjectValue -Object $watch -Name "sampleIntervalSec" -Default 5)
    $startedAt  = Get-Date

    $initialHealth = Get-HealthState
    $watchState = [pscustomobject]@{
        HighCpuStreak      = 0
        NahimicSeenAtStart = [bool](@($initialHealth.top_offenders | Where-Object { $_ -like "Nahimic*" }).Count -gt 0)
        InitialRiskCount   = @($initialHealth.top_offenders | Where-Object { $_ -match "^(chrome|msedge|firefox|Code|node|python|docker|jupyter)" }).Count
        AnomalyCaptured    = $false
    }

    Write-Log "Watching state every $interval second(s). Press Ctrl+C to stop." "INFO"

    while ($true) {
        $sample = Invoke-Status -Settings $Settings
        $display = [pscustomobject]@{
            timestamp     = Get-ObjectValue -Object $sample -Name "timestamp"
            mode          = Get-ObjectValue -Object $sample -Name "mode"
            cpu_percent   = Get-ObjectValue -Object $sample -Name "cpu_percent"
            free_mem_mb   = Get-ObjectValue -Object $sample -Name "free_mem_mb"
            wsl_active    = Get-ObjectValue -Object $sample -Name "wsl_active"
            docker_active = Get-ObjectValue -Object $sample -Name "docker_active"
            top_offenders = (Get-ObjectValue -Object $sample -Name "top_offenders" -Default @()) -join ", "
        }
        Clear-Host
        $display | Format-List

        if (Test-AnomalyConditions -Sample $sample -Settings $Settings -WatchState $watchState) {
            Invoke-AnomalyCapture -Settings $Settings -Sample $sample | Out-Null
            $watchState.AnomalyCaptured = $true
            $watchState.HighCpuStreak   = 0   # reset so we don't spam captures
        }

        if ($RunForSeconds -gt 0) {
            $elapsed = (New-TimeSpan -Start $startedAt -End (Get-Date)).TotalSeconds
            if ($elapsed -ge $RunForSeconds) { break }
        }
        Start-Sleep -Seconds $interval
    }
}
```

- [ ] **Step 8.2: Commit**

```bash
git add lib/watch.ps1
git commit -m "feat: extract lib/watch.ps1 + anomaly auto-capture (Feature B)"
```

---

## Task 9: `lib/listener.ps1` — Feature A (Steam game-watcher)

**Files:**
- Create: `lib/listener.ps1`
- Create: `tests/lib/listener.Tests.ps1`
- Create: `state/listener.json` (runtime, gitignored)

- [ ] **Step 9.1: Write failing tests for Steam VDF parsing**

```powershell
# tests/lib/listener.Tests.ps1
BeforeAll {
    # Stub path vars
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
```

- [ ] **Step 9.2: Run — verify FAIL**

```powershell
Invoke-Pester -Path tests/lib/listener.Tests.ps1 -Output Detailed
```

- [ ] **Step 9.3: Create `lib/listener.ps1`**

```powershell
# lib/listener.ps1
# Steam game-watcher daemon (Feature A).
# Watches for Steam game processes → auto-applies gaming profile → restores on exit.
# Depends on: config.ps1, profiles.ps1

function Read-SteamVdf {
    param([Parameter(Mandatory = $true)][string]$Content)
    # Simple line-by-line VDF parser — extracts "path" values from libraryfolders.vdf
    $paths = @()
    foreach ($line in ($Content -split "`n")) {
        if ($line -match '^\s*"path"\s+"(.+)"\s*$') {
            $rawPath = $Matches[1] -replace '\\\\', '\'
            $paths += $rawPath.Trim()
        }
    }
    return $paths
}

function Get-SteamLibraryPaths {
    param([string]$VdfOverridePath = $null)
    $vdfPath = $VdfOverridePath
    if ([string]::IsNullOrWhiteSpace($vdfPath)) {
        $vdfPath = Join-Path ${env:ProgramFiles(x86)} "Steam\config\libraryfolders.vdf"
    }
    if (-not (Test-Path -LiteralPath $vdfPath)) {
        Write-Log "Steam VDF not found at '$vdfPath'. Is Steam installed?" "WARN"
        return @()
    }
    try {
        $content = Get-Content -LiteralPath $vdfPath -Raw -ErrorAction Stop
        return @(Read-SteamVdf -Content $content)
    } catch {
        Write-Log "Failed to read Steam VDF: $($_.Exception.Message)" "WARN"
        return @()
    }
}

function Test-IsUnderSteamLibrary {
    param(
        [Parameter(Mandatory = $true)][string]$ExePath,
        [Parameter(Mandatory = $true)][string[]]$LibraryPaths
    )
    foreach ($libPath in $LibraryPaths) {
        if ($ExePath -like "$libPath*") { return $true }
    }
    return $false
}

function Find-SteamGameProcess {
    param([Parameter(Mandatory = $true)][string[]]$LibraryPaths)
    if ($LibraryPaths.Count -eq 0) { return $null }
    $candidates = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try {
            $exePath = $_.MainModule.FileName
            $exePath -and (Test-IsUnderSteamLibrary -ExePath $exePath -LibraryPaths $LibraryPaths)
        } catch { $false }
    })
    return ($candidates | Select-Object -First 1)
}

function Invoke-Listen {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [Parameter(Mandatory = $true)]$Profiles
    )
    $listenerCfg  = Get-ObjectValue -Object $Settings -Name "listener" -Default ([pscustomobject]@{})
    $pollInterval = [int](Get-ObjectValue -Object $listenerCfg -Name "pollIntervalSec" -Default 3)
    $vdfOverride  = Get-ObjectValue -Object $listenerCfg -Name "steamVdfPath" -Default $null
    $onGameStart  = Get-ObjectValue -Object $listenerCfg -Name "onGameStart"  -Default "gaming"
    $onGameExit   = Get-ObjectValue -Object $listenerCfg -Name "onGameExit"   -Default "restore"

    $listenerStatePath = Join-Path $script:StateDir "listener.json"

    Write-Log "Discovering Steam library paths..." "INFO"
    $libraryPaths = @(Get-SteamLibraryPaths -VdfOverridePath $vdfOverride)
    if ($libraryPaths.Count -eq 0) {
        Write-Log "No Steam libraries found. Listening anyway (manual mode trigger still works)." "WARN"
    } else {
        Write-Log ("Steam libraries: {0}" -f ($libraryPaths -join "; ")) "INFO"
    }

    Write-Log "Listening for Steam game launches. Press Ctrl+C to stop." "INFO"

    $trackedPid     = $null
    $trackedExe     = $null
    $gameModeActive = $false

    # Check if already in gaming mode at start (game already running)
    $existing = Read-JsonFile -Path $listenerStatePath -Default $null
    if ($null -ne $existing) {
        $trackedPid = Get-ObjectValue -Object $existing -Name "pid" -Default $null
        $trackedExe = Get-ObjectValue -Object $existing -Name "game_exe" -Default $null
        $gameModeActive = $true
        Write-Log "Resuming tracking of previously detected game: $trackedExe (PID $trackedPid)" "INFO"
    }

    while ($true) {
        if (-not $gameModeActive) {
            $gameProc = Find-SteamGameProcess -LibraryPaths $libraryPaths
            if ($null -ne $gameProc) {
                $trackedPid = $gameProc.Id
                $trackedExe = $gameProc.ProcessName
                $gameModeActive = $true
                Write-Log "Game detected: $trackedExe (PID $trackedPid) — applying '$onGameStart' profile." "INFO"
                $listenerState = [pscustomobject]@{
                    game_exe    = $trackedExe
                    game_path   = try { $gameProc.MainModule.FileName } catch { "unknown" }
                    pid         = $trackedPid
                    detected_at = (Get-Date).ToString("o")
                    prior_mode  = Get-CurrentModeName
                }
                Write-JsonFile -Path $listenerStatePath -Object $listenerState
                $script:ActionResults = @()
                $currentMode = Get-CurrentModeName
                if ($currentMode -ne $onGameStart) {
                    try { Invoke-ModeProfile -ModeName $onGameStart -Settings $Settings -Profiles $Profiles | Out-Null }
                    catch { Write-Log "Failed to apply '$onGameStart' profile: $($_.Exception.Message)" "ERROR" }
                } else {
                    Write-Log "Already in '$onGameStart' mode — skipping re-apply." "INFO"
                }
            }
        } else {
            $stillRunning = [bool](Get-Process -Id $trackedPid -ErrorAction SilentlyContinue)
            if (-not $stillRunning) {
                Write-Log "Game exited: $trackedExe — applying '$onGameExit' profile." "INFO"
                Remove-Item $listenerStatePath -ErrorAction SilentlyContinue
                $gameModeActive = $false
                $trackedPid     = $null
                $trackedExe     = $null
                $script:ActionResults = @()
                try { Invoke-RestoreMode -Settings $Settings | Out-Null }
                catch { Write-Log "Failed to apply '$onGameExit' profile: $($_.Exception.Message)" "ERROR" }
            }
        }
        Start-Sleep -Seconds $pollInterval
    }
}
```

- [ ] **Step 9.4: Run tests — verify PASS**

```powershell
Invoke-Pester -Path tests/lib/listener.Tests.ps1 -Output Detailed
```
Expected: `Tests Passed: 5, Failed: 0`

- [ ] **Step 9.5: Commit**

```bash
git add lib/listener.ps1 tests/lib/listener.Tests.ps1
git commit -m "feat: lib/listener.ps1 — Steam game-watcher daemon (Feature A)"
```

---

## Task 10: Refactor `keeper.ps1` into thin router

**Files:**
- Modify: `keeper.ps1` (replace body, keep param block identical)

- [ ] **Step 10.1: Back up current keeper.ps1**

```bash
cp keeper.ps1 keeper.ps1.bak
```

- [ ] **Step 10.2: Replace `keeper.ps1` body**

Keep the param block (lines 1–64) exactly as-is. Replace everything after the param block with:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:OS -ne "Windows_NT") {
    throw "keeper.ps1 must run from Windows PowerShell or PowerShell on Windows."
}

# ── Path setup ────────────────────────────────────────────────────────────────
$script:Root        = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:LibDir      = Join-Path $script:Root "lib"
$script:ConfigDir   = Join-Path $script:Root "config"
$script:StateDir    = Join-Path $script:Root "state"
$script:SessionsDir = Join-Path $script:Root "sessions"
$script:IncidentsDir = Join-Path $script:Root "incidents"

$script:CurrentStatePath = Join-Path $script:StateDir "current.json"
$script:RingBufferPath   = Join-Path $script:StateDir "ringbuffer.json"
$script:RollbackPath     = Join-Path $script:StateDir "rollback.json"
$script:DefaultsPath     = Join-Path $script:ConfigDir "defaults.json"
$script:ProfilesPath     = Join-Path $script:ConfigDir "profiles.json"
$script:MachinePath      = Join-Path $script:ConfigDir "machine.local.json"

# ── Mutable script-scope state (used by actions.ps1) ─────────────────────────
$script:IsAdmin        = $false
$script:ActionResults  = @()

# ── Load lib modules ──────────────────────────────────────────────────────────
. (Join-Path $script:LibDir "config.ps1")
. (Join-Path $script:LibDir "state.ps1")
. (Join-Path $script:LibDir "actions.ps1")
. (Join-Path $script:LibDir "health.ps1")
. (Join-Path $script:LibDir "doctor.ps1")
. (Join-Path $script:LibDir "profiles.ps1")
. (Join-Path $script:LibDir "export.ps1")
. (Join-Path $script:LibDir "watch.ps1")
. (Join-Path $script:LibDir "listener.ps1")

# ── Bootstrap ─────────────────────────────────────────────────────────────────
function Initialize-Workspace {
    Ensure-Directory -Path $script:ConfigDir
    Ensure-Directory -Path $script:StateDir
    Ensure-Directory -Path $script:SessionsDir
    Ensure-Directory -Path $script:IncidentsDir
    $script:IsAdmin = Test-IsAdministrator
}

Initialize-Workspace
$settings = Get-Settings
$profiles = Get-Profiles

# ── Command router ────────────────────────────────────────────────────────────
switch ($Command) {
    "status" {
        Invoke-Status -Settings $settings | Format-List
    }
    "watch" {
        $duration = $DurationSec
        if ($duration -eq 0) {
            $watchSettings = Get-ObjectValue -Object $settings -Name "watch" -Default ([pscustomobject]@{})
            $duration = [int](Get-ObjectValue -Object $watchSettings -Name "defaultDurationSec" -Default 0)
        }
        Invoke-Watch -Settings $settings -RunForSeconds $duration
    }
    "listen" {
        Invoke-Listen -Settings $settings -Profiles $profiles
    }
    "mode" {
        if (-not $Mode) { throw "Mode is required when Command=mode." }
        $script:ActionResults = @()
        if ($Mode -eq "restore") {
            $result = Invoke-RestoreMode -Settings $settings
        } else {
            $result = Invoke-ModeProfile -ModeName $Mode -Settings $settings -Profiles $profiles
        }
        if ($DebugMode) { $result.actions | Format-Table -AutoSize }
        $result.summary | Format-List
    }
    "doctor" {
        if ($Export) {
            Invoke-Export -Settings $settings -AsHtml:$Html -AudioTriage:$AudioTriage -LatencyMonReportPath $LatencyMonReportPath | Format-List
        } elseif ($AudioTriage) {
            Get-AudioTriageReport -Settings $settings -LatencyMonReportPath $LatencyMonReportPath | Format-List
        } else {
            Get-DoctorReport -Settings $settings | Format-List
        }
    }
    "export" {
        Invoke-Export -Settings $settings -AsHtml:$Html -AudioTriage:$AudioTriage -LatencyMonReportPath $LatencyMonReportPath | Format-List
    }
    "prune" {
        Invoke-Prune -Settings $settings | Format-List
    }
}
```

- [ ] **Step 10.3: Add `listen` to param ValidateSet**

In the param block, change:
```powershell
[ValidateSet("status", "watch", "mode", "doctor", "export", "prune")]
```
to:
```powershell
[ValidateSet("status", "watch", "listen", "mode", "doctor", "export", "prune")]
```

- [ ] **Step 10.4: Smoke test — all existing commands**

```powershell
.\keeper.ps1 status
.\keeper.ps1 watch -DurationSec 6
.\keeper.ps1 mode gaming -WhatIf
.\keeper.ps1 doctor
.\keeper.ps1 export
.\keeper.ps1 prune
```
Each should produce output matching pre-refactor behavior. If any command throws, check that the relevant `lib/*.ps1` module is dot-sourced correctly and all `$script:` path variables are set before the lib files are loaded.

- [ ] **Step 10.5: Verify keeper.ps1 line count < 220**

```powershell
(Get-Content keeper.ps1).Count
```
Expected: < 220 lines

- [ ] **Step 10.6: Remove backup and commit**

```bash
rm keeper.ps1.bak
git add keeper.ps1 lib/
git commit -m "refactor: keeper.ps1 → thin router; all logic in lib/ modules"
```

---

## Task 11: Update `config/defaults.json` — Features A + B config

**Files:**
- Modify: `config/defaults.json`

- [ ] **Step 11.1: Add `listener` and `anomaly` sections**

Edit `config/defaults.json` — add after the `"doctor"` block:

```json
  "listener": {
    "pollIntervalSec": 3,
    "steamVdfPath": null,
    "onGameStart": "gaming",
    "onGameExit": "restore"
  },
  "anomaly": {
    "enabled": true,
    "cpuSpikePercent": 80,
    "spikeSustainSamples": 3,
    "captureOnNahimicDetected": true,
    "audioRiskNewProcesses": 2
  }
```

- [ ] **Step 11.2: Verify JSON is valid**

```powershell
Get-Content config/defaults.json -Raw | ConvertFrom-Json | Out-Null
Write-Host "Valid JSON"
```
Expected: `Valid JSON` with no errors

- [ ] **Step 11.3: Commit**

```bash
git add config/defaults.json
git commit -m "feat: add listener + anomaly config to defaults.json"
```

---

## Task 12: UX Fixes — `.cmd` launchers + setup.cmd

**Files:** All `.cmd` files in `tools/`, new `setup.cmd`, modified `Invoke-KeeperElevated.ps1`

- [ ] **Step 12.1: Add `pause` to non-watch `.cmd` launchers**

For each of these files, add `pause` as the final line before `endlocal`:

`keeper-gaming.cmd`, `keeper-coding.cmd`, `keeper-audio-safe.cmd`, `keeper-quiet.cmd`, `keeper-diagnose.cmd`, `keeper-restore.cmd`, `keeper-status.cmd`, `keeper-doctor.cmd`

Example diff for `keeper-gaming.cmd`:
```cmd
@echo off
setlocal
set "ROOT=%~dp0.."
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" mode gaming %*
pause
endlocal
```

- [ ] **Step 12.2: Update `keeper-doctor-audio.cmd` — pause + auto-open HTML**

```cmd
@echo off
setlocal
set "ROOT=%~dp0.."
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" doctor -Export -AudioTriage -Html %*
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$f = Get-ChildItem '%ROOT%\incidents\*.html' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($f) { Start-Process $f.FullName }"
pause
endlocal
```

- [ ] **Step 12.3: Update `keeper-export.cmd` — add Html + auto-open**

```cmd
@echo off
setlocal
set "ROOT=%~dp0.."
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" export -Html %*
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$f = Get-ChildItem '%ROOT%\incidents\*.html' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($f) { Start-Process $f.FullName }"
pause
endlocal
```

- [ ] **Step 12.4: Update `Invoke-KeeperElevated.ps1` — pwsh fallback + keep window open**

```powershell
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$KeeperArgs
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$toolsDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir    = Split-Path -Parent $toolsDir
$keeperPath = Join-Path $rootDir "keeper.ps1"

if (-not (Test-Path -LiteralPath $keeperPath)) { throw "keeper.ps1 not found at $keeperPath" }

# Prefer PowerShell 7+; fall back to Windows PowerShell 5.1
$psExe = if (Get-Command pwsh.exe -ErrorAction SilentlyContinue) { "pwsh.exe" } else { "powershell.exe" }

# Build the inline command string so the elevated window stays open after running
$escapedPath = $keeperPath -replace "'", "''"
$argString   = ($KeeperArgs | ForEach-Object { if ($_ -match '\s') { "'$_'" } else { $_ } }) -join " "
$command     = "& '$escapedPath' $argString; Write-Host ''; Read-Host 'Press Enter to close'"

$argumentList = @("-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command)
Start-Process -FilePath $psExe -Verb RunAs -WorkingDirectory $rootDir -ArgumentList $argumentList | Out-Null
```

- [ ] **Step 12.5: Create `setup.cmd` in repo root**

```cmd
@echo off
echo Installing Keeper desktop and Start Menu shortcuts...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\install-shortcuts.ps1"
pause
```

- [ ] **Step 12.6: Verify double-click UX**

Double-click `keeper-status.cmd` from Windows Explorer. Expected: terminal stays open showing health output with "Press any key" prompt.

- [ ] **Step 12.7: Commit**

```bash
git add tools/ setup.cmd
git commit -m "fix: launcher UX — pause after output, admin window stays open, setup.cmd"
```

---

## Task 13: New launchers — `keeper-listen.cmd` + admin variant

**Files:**
- Create: `tools/keeper-listen.cmd`
- Create: `tools/keeper-listen-admin.cmd`

- [ ] **Step 13.1: Create `tools/keeper-listen.cmd`**

```cmd
@echo off
setlocal
set "ROOT=%~dp0.."
echo Starting Keeper Steam game-watcher. Press Ctrl+C to stop.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\keeper.ps1" listen %*
pause
endlocal
```

- [ ] **Step 13.2: Create `tools/keeper-listen-admin.cmd`**

```cmd
@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-KeeperElevated.ps1" listen %*
endlocal
```

- [ ] **Step 13.3: Commit**

```bash
git add tools/keeper-listen.cmd tools/keeper-listen-admin.cmd
git commit -m "feat: add keeper-listen.cmd launchers for Steam game-watcher"
```

---

## Task 14: Update `install-shortcuts.ps1` — per-type icons + Listen shortcut

**Files:**
- Modify: `tools/install-shortcuts.ps1`

- [ ] **Step 14.1: Update shortcut specs with icons and add Listen**

Replace the `$shortcutSpecs` array and update `New-Shortcut` to accept an icon:

```powershell
$shortcutSpecs = @(
    @{ Name = "Keeper Gaming";                   Target = Join-Path $toolsDir "keeper-gaming.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Gaming (Admin)";           Target = Join-Path $toolsDir "keeper-gaming-admin.cmd";    Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Coding";                   Target = Join-Path $toolsDir "keeper-coding.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,71"  },
    @{ Name = "Keeper Audio Safe";               Target = Join-Path $toolsDir "keeper-audio-safe.cmd";      Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Audio Safe (Admin)";       Target = Join-Path $toolsDir "keeper-audio-safe-admin.cmd";Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Quiet";                    Target = Join-Path $toolsDir "keeper-quiet.cmd";           Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Restore";                  Target = Join-Path $toolsDir "keeper-restore.cmd";         Icon = "%SystemRoot%\System32\shell32.dll,238" },
    @{ Name = "Keeper Status";                   Target = Join-Path $toolsDir "keeper-status.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Doctor";                   Target = Join-Path $toolsDir "keeper-doctor.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Doctor Audio Export";      Target = Join-Path $toolsDir "keeper-doctor-audio.cmd";    Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Watch";                    Target = Join-Path $toolsDir "keeper-watch.cmd";           Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Diagnose";                 Target = Join-Path $toolsDir "keeper-diagnose.cmd";        Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Export";                   Target = Join-Path $toolsDir "keeper-export.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Listen (Steam Watcher)";   Target = Join-Path $toolsDir "keeper-listen.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Listen (Admin)";           Target = Join-Path $toolsDir "keeper-listen-admin.cmd";    Icon = "%SystemRoot%\System32\shell32.dll,16"  }
)
```

Update `New-Shortcut` to use the spec's icon:
```powershell
function New-Shortcut {
    param(
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [string]$IconLocation = "%SystemRoot%\System32\shell32.dll,21"
    )
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath      = $TargetPath
    $shortcut.WorkingDirectory = $rootDir
    $shortcut.IconLocation    = $IconLocation
    $shortcut.Save()
}
```

Update `Install-ShortcutsToLocation` to pass the icon:
```powershell
New-Shortcut -ShortcutPath $shortcutPath -TargetPath $spec.Target -IconLocation $spec.Icon
```

- [ ] **Step 14.2: Commit**

```bash
git add tools/install-shortcuts.ps1
git commit -m "feat: per-type icons + Listen shortcut in install-shortcuts.ps1"
```

---

## Task 15: Legacy redirect + final run

**Files:**
- Modify: `tools/gaming-mode/README.md`
- Delete: `keeper.ps1.bak` (if still exists)

- [ ] **Step 15.1: Add redirect notice to `tools/gaming-mode/README.md`**

Prepend to the top of the file:
```markdown
> **This toolkit predates `keeper.ps1`.**
> For the current system, use `.\keeper.ps1` from the repo root — it covers all gaming, audio-safe, coding, diagnose, quiet, and restore modes with WhatIf support, rollback, and HTML export.
> The scripts below are kept for reference.

---
```

- [ ] **Step 15.2: Update `.gitignore` to exclude `state/listener.json`**

Add to `.gitignore`:
```
state/listener.json
```

- [ ] **Step 15.3: Run full test suite**

```powershell
Invoke-Pester -Path tests/ -Output Detailed
```
Expected: all tests pass

- [ ] **Step 15.4: Run all commands end-to-end**

```powershell
.\keeper.ps1 status
.\keeper.ps1 mode gaming -WhatIf
.\keeper.ps1 mode coding -WhatIf
.\keeper.ps1 mode audio-safe -WhatIf
.\keeper.ps1 mode quiet -WhatIf
.\keeper.ps1 watch -DurationSec 6
.\keeper.ps1 doctor
.\keeper.ps1 doctor -AudioTriage
.\keeper.ps1 export -Html -WhatIf
.\keeper.ps1 prune -WhatIf
```

- [ ] **Step 15.5: Final commit**

```bash
git add tools/gaming-mode/README.md .gitignore
git commit -m "chore: legacy redirect, gitignore listener.json, final cleanup"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|-----------------|------|
| lib/ module split | Tasks 1–9 |
| keeper.ps1 thin router | Task 10 |
| Feature A: Steam game-watcher | Task 9 |
| Feature B: Anomaly auto-capture | Task 8 |
| Feature E: LatencyMon auto-parse | Task 5 |
| Feature F: GPU mode detection | Task 5 |
| Launcher pause UX | Task 12 |
| Auto-open HTML | Task 12 |
| Admin window stays open | Task 12 |
| setup.cmd first-run | Task 12 |
| keeper-listen.cmd | Task 13 |
| Per-type shortcut icons | Task 14 |
| defaults.json additions | Task 11 |
| Gaming-mode redirect | Task 15 |
| listener.json gitignored | Task 15 |

**No placeholders found.** All code blocks are complete.

**Type consistency:** `Get-ActionSummary` defined in `actions.ps1`, called in `profiles.ps1` and `state.ps1` tests — consistent. `Read-JsonFile` defined in `config.ps1`, used across all modules — consistent. `Find-ProcessesByPattern` defined in `actions.ps1`, called in `doctor.ps1` — consistent.

**One ambiguity resolved:** `Invoke-Export` and `Invoke-Prune` in Task 7 reference the full move from keeper.ps1 lines 1506–1812. The inner helper functions (`Convert-CellValueToHtml`, `Convert-RowsToHtmlTable`) remain nested inside `Invoke-Export` — this is called out explicitly.
