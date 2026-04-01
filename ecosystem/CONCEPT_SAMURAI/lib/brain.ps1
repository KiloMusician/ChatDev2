# Brain layer - deterministic scoring + rules-based advisor + optional Ollama analysis
# Hot path: Get-SystemScore, Get-AdvisorRecommendation  (no LLM, no network)
# Warm path: Invoke-Analyze  (Ollama, on-demand only, graceful fallback)

# ---- helpers -----------------------------------------------------------------

function Get-RamPressure {
    try {
        $os  = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
        $total = [double]$os.TotalVisibleMemorySize
        $free  = [double]$os.FreePhysicalMemory
        if ($total -le 0) { return 0.5 }
        return [double]([math]::Round(($total - $free) / $total, 3))
    }
    catch { return 0.5 }
}

function Get-CpuPressure {
    try {
        $counter = Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
        return [double]([math]::Round($counter.CounterSamples[0].CookedValue / 100.0, 3))
    }
    catch { return 0.5 }
}

function Get-DiskPressure {
    try {
        $drive = Get-PSDrive C -ErrorAction SilentlyContinue
        if ($null -eq $drive) { return 0.5 }
        $total = $drive.Used + $drive.Free
        if ($total -le 0) { return 0.5 }
        return [double]([math]::Round($drive.Used / $total, 3))
    }
    catch { return 0.5 }
}

function Get-BackgroundContention {
    param([Parameter(Mandatory = $true)]$Settings)

    $brain    = Get-ObjectValue -Object $Settings -Name "brain" -Default $null
    $patterns = @(Get-ObjectValue -Object $brain -Name "devProcessPatterns" -Default @(
        "Code", "node*", "python*", "jupyter*", "ollama*", "Docker*", "com.docker.*", "dockerd*"
    ))

    $running = 0
    $procs = @(Get-Process -ErrorAction SilentlyContinue)
    foreach ($proc in $procs) {
        foreach ($pat in $patterns) {
            if ($proc.ProcessName -like $pat) { $running++; break }
        }
    }

    # Reference ceiling: 8 heavy dev processes = full contention
    $ceiling = [int](Get-ObjectValue -Object $brain -Name "contentionCeiling" -Default 8)
    return [double]([math]::Round([math]::Min($running, $ceiling) / $ceiling, 3))
}

function Get-StatusLabel {
    param([double]$Score)
    if ($Score -ge 80) { return "critical" }
    if ($Score -ge 60) { return "warning" }
    if ($Score -ge 40) { return "info" }
    return "ok"
}

# ---- score -------------------------------------------------------------------

function Get-SystemScore {
    param([Parameter(Mandatory = $true)]$Settings)

    $brain = Get-ObjectValue -Object $Settings -Name "brain" -Default $null

    $wDisk    = [double](Get-ObjectValue -Object $brain -Name "weightDisk"        -Default 0.30)
    $wCpu     = [double](Get-ObjectValue -Object $brain -Name "weightCpu"         -Default 0.25)
    $wRam     = [double](Get-ObjectValue -Object $brain -Name "weightRam"         -Default 0.25)
    $wContend = [double](Get-ObjectValue -Object $brain -Name "weightContention"  -Default 0.20)

    $diskP    = Get-DiskPressure
    $cpuP     = Get-CpuPressure
    $ramP     = Get-RamPressure
    $contendP = Get-BackgroundContention -Settings $Settings

    $raw   = ($diskP * $wDisk) + ($cpuP * $wCpu) + ($ramP * $wRam) + ($contendP * $wContend)
    $score = [int][math]::Round($raw * 100)

    $issues     = @()
    $safeActions = @()

    if ($diskP -ge 0.90) {
        $issues      += "Disk critically full ({0}% used)" -f [int]($diskP * 100)
        $safeActions += "docker-prune"
        $safeActions += "clean-temp"
    }
    elseif ($diskP -ge 0.80) {
        $issues += "Disk pressure high ({0}% used)" -f [int]($diskP * 100)
        $safeActions += "clean-temp"
    }

    if ($cpuP -ge 0.80) {
        $issues      += "CPU pressure high ({0}%)" -f [int]($cpuP * 100)
        $safeActions += "demote-dev-processes"
    }

    if ($ramP -ge 0.85) {
        $issues      += "RAM pressure high ({0}% used)" -f [int]($ramP * 100)
        $safeActions += "demote-dev-processes"
    }

    if ($contendP -ge 0.50) {
        $issues      += "{0} background dev processes competing for resources" -f [int]($contendP * 8)
        $safeActions += "demote-dev-processes"
    }

    $currentMode = Get-CurrentModeName
    if ($currentMode -in @("gaming", "heavy-gaming") -and $contendP -ge 0.25) {
        $issues      += "Dev processes active during gaming mode"
        $safeActions += "demote-dev-processes"
    }

    Save-SystemScore -Score ([pscustomobject]@{
        timestamp = (Get-Date).ToString("o")
        score     = $score
        status    = Get-StatusLabel -Score $score
        signals   = [pscustomobject]@{
            diskPressure          = $diskP
            cpuPressure           = $cpuP
            ramPressure           = $ramP
            backgroundContention  = $contendP
        }
        issues      = @($issues | Select-Object -Unique)
        safe_actions = @($safeActions | Select-Object -Unique)
        mode        = $currentMode
    })
}

# ---- advisor -----------------------------------------------------------------

function Get-AdvisorRecommendation {
    param([Parameter(Mandatory = $true)]$Settings)

    $score = Get-SystemScore -Settings $Settings

    # Priority order: disk > gaming-mode mismatch > cpu/ram > contention
    $action     = $null
    $why        = $null
    $confidence = 0.0

    $disk    = $score.signals.diskPressure
    $cpu     = $score.signals.cpuPressure
    $ram     = $score.signals.ramPressure
    $contend = $score.signals.backgroundContention
    $mode    = $score.mode

    if ($disk -ge 0.90) {
        $action     = "docker-prune"
        $why        = ("Disk is {0}% full. Docker is the most likely large recoverable source." -f [int]($disk * 100))
        $confidence = 0.92
    }
    elseif ($mode -in @("gaming", "heavy-gaming") -and $contend -ge 0.38) {
        $action     = "demote-dev-processes"
        $why        = ("Gaming mode active but {0} dev processes are competing for CPU/RAM." -f [int]($contend * 8))
        $confidence = 0.85
    }
    elseif ($cpu -ge 0.80 -or $ram -ge 0.85) {
        $action     = "demote-dev-processes"
        $why        = ("CPU at {0}%, RAM at {1}%. Lowering dev process priorities reduces contention without stopping tools." -f [int]($cpu * 100), [int]($ram * 100))
        $confidence = 0.78
    }
    elseif ($disk -ge 0.80) {
        $action     = "clean-temp"
        $why        = ("Disk at {0}%. Clearing temp files is a safe first step." -f [int]($disk * 100))
        $confidence = 0.70
    }
    elseif ($contend -ge 0.50) {
        $action     = "demote-dev-processes"
        $why        = "Multiple dev processes active. Demoting priorities improves responsiveness."
        $confidence = 0.65
    }
    else {
        $action     = "none"
        $why        = "System pressure is within acceptable range. No action recommended."
        $confidence = 0.90
    }

    $safeToApply = ($action -ne "none") -and
                  ($score.status -in @("warning", "critical")) -and
                  ($mode -notin @("heavy-gaming"))

    $result = [pscustomobject]@{
        timestamp      = (Get-Date).ToString("o")
        score          = $score.score
        status         = $score.status
        recommended    = $action
        why            = $why
        confidence     = $confidence
        safe_to_apply  = $safeToApply
        issues         = @($score.issues)
        signals        = $score.signals
    }

    $null = Save-AdvisorState -State $result
    return $result
}

# ---- analyze (Ollama - warm path, never blocking) ----------------------------

function Invoke-Analyze {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [int]$TimeoutSeconds = 30
    )

    $brain = Get-ObjectValue -Object $Settings -Name "brain" -Default $null
    if (-not [bool](Get-ObjectValue -Object $brain -Name "enabled" -Default $true)) {
        return [pscustomobject]@{ status = "disabled"; analysis = $null }
    }

    $provider = [string](Get-ObjectValue -Object $brain -Name "provider"     -Default "ollama")
    $model    = [string](Get-ObjectValue -Object $brain -Name "model"        -Default "mistral")
    $endpoint = [string](Get-ObjectValue -Object $brain -Name "ollamaEndpoint" -Default "http://localhost:11434")
    $maxLog   = [int](Get-ObjectValue    -Object $brain -Name "maxLogEntries" -Default 50)

    if ($provider -ne "ollama") {
        return [pscustomobject]@{ status = "unsupported-provider"; provider = $provider; analysis = $null }
    }

    # Test Ollama availability
    try {
        $ping = Invoke-RestMethod -Uri "$endpoint/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    }
    catch {
        return [pscustomobject]@{ status = "ollama-unavailable"; endpoint = $endpoint; analysis = $null }
    }

    # Gather context
    $score   = Get-SystemScore -Settings $Settings
    $logPath = Join-Path $script:Root "state\action_log.jsonl"
    $recentLog = @()
    if (Test-Path -LiteralPath $logPath) {
        $recentLog = @(Get-Content -LiteralPath $logPath -ErrorAction SilentlyContinue |
                       Select-Object -Last $maxLog |
                       ForEach-Object { $_ | ConvertFrom-Json -ErrorAction SilentlyContinue } |
                       Where-Object { $null -ne $_ })
    }

    $contextJson = [pscustomobject]@{
        timestamp    = (Get-Date).ToString("o")
        score        = $score
        recent_log   = @($recentLog)
    } | ConvertTo-Json -Depth 8 -Compress

    $prompt = @"
You are a system performance advisor for a Windows laptop running a gaming + coding workstation.
Analyze this system state and log data. Be concise and practical.

Return JSON only in this exact shape:
{"top_issues":["...","..."],"root_cause":"...","recommended_action":"...","why":"...","confidence":0.0}

System state:
$contextJson
"@

    $body = [pscustomobject]@{
        model  = $model
        prompt = $prompt
        stream = $false
    } | ConvertTo-Json -Depth 3

    try {
        $response = Invoke-RestMethod -Uri "$endpoint/api/generate" `
            -Method Post -Body $body -ContentType "application/json" `
            -TimeoutSec $TimeoutSeconds -ErrorAction Stop

        $raw = [string]$response.response
        # Extract JSON block from response
        if ($raw -match '\{[\s\S]+\}') {
            $parsed = $Matches[0] | ConvertFrom-Json -ErrorAction SilentlyContinue
        }

        return [pscustomobject]@{
            status    = "ok"
            model     = $model
            analysis  = $parsed
            raw       = if ($null -eq $parsed) { $raw } else { $null }
        }
    }
    catch {
        return [pscustomobject]@{
            status  = "error"
            message = $_.Exception.Message
            analysis = $null
        }
    }
}

# ---- optimize (apply advisor recommendation) ---------------------------------

function Invoke-DemoteDevProcesses {
    param([Parameter(Mandatory = $true)]$Settings)

    $brain    = Get-ObjectValue -Object $Settings -Name "brain" -Default $null
    $patterns = @(Get-ObjectValue -Object $brain -Name "devProcessPatterns" -Default @(
        "Code", "node*", "python*", "jupyter*", "ollama*", "Docker*", "com.docker.*", "dockerd*"
    ))

    $demoted = @()
    $skipped = @()
    $procs   = @(Get-Process -ErrorAction SilentlyContinue)

    foreach ($proc in $procs) {
        foreach ($pat in $patterns) {
            if ($proc.ProcessName -like $pat) {
                try {
                    $proc.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::BelowNormal
                    $demoted += $proc.ProcessName
                }
                catch {
                    $skipped += $proc.ProcessName
                }
                break
            }
        }
    }

    return [pscustomobject]@{
        action  = "demote-dev-processes"
        demoted = @($demoted | Select-Object -Unique)
        skipped = @($skipped | Select-Object -Unique)
        count   = $demoted.Count
    }
}

function Invoke-Optimize {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [switch]$Force
    )

    $advice = Get-AdvisorRecommendation -Settings $Settings

    if ($advice.recommended -eq "none") {
        return [pscustomobject]@{
            status  = "no-op"
            reason  = $advice.why
            advice  = $advice
            applied = $null
        }
    }

    if (-not $Force -and -not $advice.safe_to_apply) {
        return [pscustomobject]@{
            status  = "skipped"
            reason  = ("safe_to_apply is false (score={0} {1}); use -Force to override" -f $advice.score, $advice.status)
            advice  = $advice
            applied = $null
        }
    }

    $actionResult = switch ($advice.recommended) {
        "docker-prune"         { Invoke-DockerPrune    -Settings $Settings }
        "clean-temp"           { Invoke-CleanTemp      -Settings $Settings }
        "demote-dev-processes" { Invoke-DemoteDevProcesses -Settings $Settings }
        default {
            return [pscustomobject]@{
                status  = "error"
                reason  = ("Unknown recommended action: {0}" -f $advice.recommended)
                advice  = $advice
                applied = $null
            }
        }
    }

    return [pscustomobject]@{
        status  = "applied"
        action  = $advice.recommended
        why     = $advice.why
        advice  = $advice
        applied = $actionResult
    }
}

# ---- state persistence -------------------------------------------------------

function Save-SystemScore {
    param([Parameter(Mandatory = $true)]$Score)
    $path = Join-Path $script:StateDir "performance_score.json"
    Write-JsonFile -Path $path -Object $Score
    return $Score
}

function Save-AdvisorState {
    param([Parameter(Mandatory = $true)]$State)
    $path = Join-Path $script:StateDir "advisor_last.json"
    Write-JsonFile -Path $path -Object $State
    return $State
}
