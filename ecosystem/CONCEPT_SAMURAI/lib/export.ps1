function Invoke-Export {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [switch]$AsHtml,
        [switch]$AudioTriage,
        [string]$LatencyMonReportPath
    )

    $timestamp = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
    $doctorReport = Get-DoctorReport -Settings $Settings
    $audioTriageReport = $null
    if ($AudioTriage) {
        $audioTriageReport = Get-AudioTriageReport -Settings $Settings -LatencyMonReportPath $LatencyMonReportPath
    }

    $bundle = [pscustomobject]@{
        report_type     = if ($AudioTriage) { "audio-triage" } else { "general" }
        exported_at     = (Get-Date).ToString("o")
        current_state   = Read-JsonFile -Path $script:CurrentStatePath -Default $null
        rollback_state  = Read-JsonFile -Path $script:RollbackPath -Default $null
        recent_sessions = Get-RecentSessions -Max 10
        doctor_report   = $doctorReport
        audio_triage    = $audioTriageReport
    }

    if ($AsHtml) {
        $filePrefix = if ($AudioTriage) { "audio-triage" } else { "export" }
        $htmlPath = Join-Path $script:IncidentsDir ("{0}-{1}.html" -f $filePrefix, $timestamp)

        $doctor = $bundle.doctor_report
        $riskColor = switch ($doctor.risk_level) {
            "high"   { "#f85149" }
            "medium" { "#f0883e" }
            default  { "#3fb950" }
        }

        $findingsHtml = if ($doctor.findings -and $doctor.findings.Count -gt 0) {
            ($doctor.findings | ForEach-Object { "<li>$_</li>" }) -join "`n"
        } else {
            "<li>No issues found.</li>"
        }

        $offendersHtml = if ($doctor.top_offenders -and $doctor.top_offenders.Count -gt 0) {
            ($doctor.top_offenders | ForEach-Object { "<code>$_</code>" }) -join " &nbsp;"
        } else {
            "<em>none</em>"
        }

        $steamGamesHtml = if ($doctor.steam_games -and $doctor.steam_games.Count -gt 0) {
            ($doctor.steam_games | ForEach-Object {
                $name = [System.Net.WebUtility]::HtmlEncode([string](Get-ObjectValue -Object $_ -Name "GameName" -Default "Unknown"))
                $appId = [string](Get-ObjectValue -Object $_ -Name "SteamAppId" -Default "")
                if ([string]::IsNullOrWhiteSpace([string]$appId)) {
                    "<li>$name</li>"
                }
                else {
                    "<li>$name <code>AppID $([System.Net.WebUtility]::HtmlEncode($appId))</code></li>"
                }
            }) -join "`n"
        }
        else {
            "<li><em>No active Steam games detected.</em></li>"
        }

        $sessionsHtml = ""
        foreach ($s in @($bundle.recent_sessions)) {
            if ($null -ne $s) {
                $sessionsHtml += "<tr><td>$($s.session_id)</td><td>$($s.mode)</td><td>$($s.duration_min) min</td><td>$($s.cpu_percent_before)%</td><td>$($s.cpu_percent_after)%</td></tr>`n"
            }
        }
        if (-not $sessionsHtml) { $sessionsHtml = "<tr><td colspan='5'><em>No sessions recorded yet.</em></td></tr>" }

        $currentMode = if ($bundle.current_state) { $bundle.current_state.mode } else { "idle" }
        $powerPlan = $doctor.power_plan_raw
        $gameMode = if ($doctor.game_mode_enabled) { "On" } else { "Off" }
        $gpuMode = if ($doctor.gpu_mode) { $doctor.gpu_mode } else { "Unknown" }
        $wslDistros = if ($doctor.wsl_running_distros -and $doctor.wsl_running_distros.Count -gt 0) {
            $doctor.wsl_running_distros -join ", "
        } else { "none" }
        $nahimicFlag = if ($doctor.nahimic_services.Count -gt 0 -or $doctor.nahimic_processes.Count -gt 0) {
            "<span style='color:#f0883e'>&#9888; Detected</span>"
        } else { "<span style='color:#3fb950'>&#10003; Not detected</span>" }

        $audioTriageSection = ""
        if ($AudioTriage -and $null -ne $bundle.audio_triage) {
            $triage = $bundle.audio_triage

            function Convert-CellValueToHtml {
                param($Value)

                if ($null -eq $Value) {
                    return ""
                }

                if ($Value -is [DateTime]) {
                    return [System.Net.WebUtility]::HtmlEncode($Value.ToString("o"))
                }

                if ($Value -is [array]) {
                    return [System.Net.WebUtility]::HtmlEncode(($Value -join ", "))
                }

                return [System.Net.WebUtility]::HtmlEncode([string]$Value)
            }

            function Convert-RowsToHtmlTable {
                param(
                    [AllowEmptyCollection()][array]$Rows = @(),
                    [Parameter(Mandatory = $true)][string[]]$Columns
                )

                if ($Rows.Count -eq 0) {
                    return "<tr><td colspan='$($Columns.Count)'><em>None</em></td></tr>"
                }

                $htmlRows = @()
                foreach ($row in $Rows) {
                    $cells = foreach ($column in $Columns) {
                        "<td>$(Convert-CellValueToHtml -Value (Get-ObjectValue -Object $row -Name $column -Default $null))</td>"
                    }
                    $htmlRows += "<tr>$($cells -join '')</tr>"
                }

                return ($htmlRows -join "`n")
            }

            $triageFindingsHtml = if ($triage.next_steps.Count -gt 0) {
                ($triage.next_steps | ForEach-Object { "<li>$([System.Net.WebUtility]::HtmlEncode($_))</li>" }) -join "`n"
            } else {
                "<li>No audio-specific recommendations captured.</li>"
            }

            $triageReasonsHtml = if ($triage.recommendation_reasons.Count -gt 0) {
                ($triage.recommendation_reasons | ForEach-Object { "<li>$([System.Net.WebUtility]::HtmlEncode($_))</li>" }) -join "`n"
            } else {
                "<li>No special audio-risk reasons detected.</li>"
            }

            $latencyMonPath = if ($triage.latencymon_summary.report_path) {
                [System.Net.WebUtility]::HtmlEncode([string]$triage.latencymon_summary.report_path)
            } else { "<em>not provided</em>" }

            $latencyMonDriver = if ($triage.latencymon_summary.top_driver) {
                [System.Net.WebUtility]::HtmlEncode([string]$triage.latencymon_summary.top_driver)
            } else { "<em>not identified</em>" }

            $latencyMonSource = if ($triage.latencymon_summary.auto_discovered) {
                "<p><em>Auto-discovered newest LatencyMon report.</em></p>"
            } else {
                ""
            }

            $latencyMonLines = if ($triage.latencymon_summary.matched_lines.Count -gt 0) {
                "<pre>" + [System.Net.WebUtility]::HtmlEncode(($triage.latencymon_summary.matched_lines -join [Environment]::NewLine)) + "</pre>"
            } else {
                "<p><em>No LatencyMon lines captured yet.</em></p>"
            }

            $audioTriageSection = @"
  <h2>Audio Triage Recommendation</h2>
  <div class="card" style="margin-bottom:1rem">
    <label>Recommended Action</label>
    <span class="val">$([System.Net.WebUtility]::HtmlEncode([string]$triage.recommended_action))</span>
    <p style="margin-top:.8rem;font-size:.85rem;color:#8b949e">Uninstall Nahimic now: $(if ($triage.recommend_uninstall_now) { 'Yes' } else { 'No' })</p>
  </div>

  <h2>Why</h2>
  <ul>
    $triageReasonsHtml
  </ul>

  <h2>Next Steps</h2>
  <ul>
    $triageFindingsHtml
  </ul>

  <h2>Nahimic Services</h2>
  <table>
    <tr><th>Name</th><th>Status</th><th>Start Type</th><th>Image Path</th></tr>
    $(Convert-RowsToHtmlTable -Rows @($triage.nahimic_service_details) -Columns @("Name","Status","StartType","ImagePath"))
  </table>

  <h2>Nahimic Processes</h2>
  <table>
    <tr><th>Process</th><th>PID</th><th>CPU Seconds</th><th>Working Set MB</th></tr>
    $(Convert-RowsToHtmlTable -Rows @($triage.nahimic_process_details) -Columns @("ProcessName","Id","CPUSeconds","WorkingSetMB"))
  </table>

  <h2>Audio Drivers</h2>
  <table>
    <tr><th>Device</th><th>Version</th><th>Date</th><th>Manufacturer</th></tr>
    $(Convert-RowsToHtmlTable -Rows @($triage.audio_driver_inventory) -Columns @("DeviceName","DriverVersion","DriverDate","Manufacturer"))
  </table>

  <h2>Installed Audio Packages</h2>
  <table>
    <tr><th>Package</th><th>Version</th><th>Publisher</th><th>Install Date</th></tr>
    $(Convert-RowsToHtmlTable -Rows @($triage.installed_audio_packages) -Columns @("DisplayName","DisplayVersion","Publisher","InstallDate"))
  </table>

  <h2>LatencyMon Summary</h2>
  <div class="grid">
    <div class="card"><label>Report Path</label><span class="val">$latencyMonPath</span></div>
    <div class="card"><label>Top Driver</label><span class="val">$latencyMonDriver</span></div>
  </div>
  $latencyMonSource
  $latencyMonLines
"@
        }

        $html = @"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>keeper.ps1 Export — $timestamp</title>
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e1e4e8;padding:2rem;font-size:14px}
    .container{max-width:860px;margin:0 auto}
    h1{font-size:1.6rem;color:#58a6ff;font-family:Consolas,monospace;margin-bottom:.3rem}
    .sub{color:#8b949e;margin-bottom:2rem;font-size:.85rem}
    h2{font-size:1rem;font-weight:600;color:#c9d1d9;margin:1.5rem 0 .8rem;border-bottom:1px solid #30363d;padding-bottom:.4rem}
    .grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
    .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem}
    .card label{font-size:.75rem;color:#8b949e;display:block;margin-bottom:.2rem}
    .card .val{font-family:Consolas,monospace;font-size:.9rem;color:#e6edf3}
    .risk-badge{display:inline-block;padding:.25rem .75rem;border-radius:999px;font-weight:600;font-size:.8rem;color:#fff;background:$riskColor;margin-bottom:1rem}
    ul{list-style:none;padding:0}
    ul li{padding:.3rem 0;border-bottom:1px solid #21262d;font-size:.85rem}
    ul li:last-child{border-bottom:none}
    table{width:100%;border-collapse:collapse;font-size:.83rem}
    th{text-align:left;color:#8b949e;font-weight:500;padding:.4rem .6rem;border-bottom:1px solid #30363d}
    td{padding:.4rem .6rem;border-bottom:1px solid #21262d;font-family:Consolas,monospace}
    code{background:#21262d;padding:.1rem .35rem;border-radius:3px;font-family:Consolas,monospace}
    .footer{margin-top:2rem;color:#6e7681;font-size:.75rem;text-align:center}
  </style>
</head>
<body>
<div class="container">
  <h1>keeper.ps1 — System Report</h1>
  <p class="sub">Generated: $($bundle.exported_at)</p>

  <h2>Current State</h2>
  <div class="grid">
    <div class="card"><label>Active Mode</label><span class="val">$currentMode</span></div>
    <div class="card"><label>Power Plan</label><span class="val">$powerPlan</span></div>
    <div class="card"><label>Game Mode</label><span class="val">$gameMode</span></div>
    <div class="card"><label>GPU Mode</label><span class="val">$gpuMode</span></div>
    <div class="card"><label>WSL Running</label><span class="val">$wslDistros</span></div>
    <div class="card"><label>CPU %</label><span class="val">$($doctor.cpu_percent)%</span></div>
    <div class="card"><label>Nahimic</label><span class="val">$nahimicFlag</span></div>
  </div>

  <h2>Doctor Report — Risk Level</h2>
  <div class="risk-badge">$($doctor.risk_level.ToUpper())</div>
  <ul>
    $findingsHtml
  </ul>

  <h2>Top CPU Offenders</h2>
  <p>$offendersHtml</p>

  <h2>Active Steam Games</h2>
  <ul>
    $steamGamesHtml
  </ul>

  <h2>Recent Sessions (last 10)</h2>
  <table>
    <tr><th>Session ID</th><th>Mode</th><th>Duration</th><th>CPU Before</th><th>CPU After</th></tr>
    $sessionsHtml
  </table>

  $audioTriageSection

  <p class="footer">keeper.ps1 — lightweight Windows mode orchestrator</p>
</div>
</body>
</html>
"@
        $html | Set-Content -Path $htmlPath -Encoding UTF8
        return [pscustomobject]@{
            exported_at = $bundle.exported_at
            bundle_path = $htmlPath
            format      = "html"
        }
    }
    else {
        $filePrefix = if ($AudioTriage) { "audio-triage" } else { "export" }
        $bundlePath = Join-Path $script:IncidentsDir ("{0}-{1}.json" -f $filePrefix, $timestamp)
        Write-JsonFile -Path $bundlePath -Object $bundle
        return [pscustomobject]@{
            exported_at = $bundle.exported_at
            bundle_path = $bundlePath
            format      = "json"
        }
    }
}

function Invoke-Prune {
    param([Parameter(Mandatory = $true)]$Settings)

    $retention = Get-ObjectValue -Object $Settings -Name "retention" -Default ([pscustomobject]@{})
    $maxSessions = [int](Get-ObjectValue -Object $retention -Name "maxSessions" -Default 30)
    $incidentDays = [int](Get-ObjectValue -Object $retention -Name "incidentDays" -Default 14)

    $removedSessions = 0
    $removedIncidents = 0

    $sessionFiles = @(Get-ChildItem -LiteralPath $script:SessionsDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
    if ($sessionFiles.Count -gt $maxSessions) {
        $toRemove = @($sessionFiles | Select-Object -Skip $maxSessions)
        $removedSessions = $toRemove.Count

        if (-not $WhatIfPreference) {
            $toRemove | Remove-Item -Force -ErrorAction SilentlyContinue
        }
    }

    $incidentCutoff = (Get-Date).AddDays(-$incidentDays)
    $incidentFiles = @(Get-ChildItem -LiteralPath $script:IncidentsDir -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $incidentCutoff })
    $removedIncidents = $incidentFiles.Count

    if (-not $WhatIfPreference -and $incidentFiles.Count -gt 0) {
        $incidentFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    }

    return [pscustomobject]@{
        removed_sessions  = $removedSessions
        removed_incidents = $removedIncidents
        what_if           = [bool]$WhatIfPreference
    }
}
