# lib/export.ps1
# JSON + HTML incident bundle generation and prune.
# Depends on: config.ps1, state.ps1, health.ps1, doctor.ps1

function Invoke-Export {
    param(
        [Parameter(Mandatory = $true)]$Settings,
        [switch]$AsHtml,
        [switch]$AudioTriage,
        [string]$LatencyMonReportPath
    )

    Ensure-Directory -Path $script:IncidentsDir

    $timestamp  = Get-Date -Format "yyyy-MM-ddTHH-mm-ss"
    $baseName   = "keeper-export-$timestamp"
    $jsonPath   = Join-Path $script:IncidentsDir "$baseName.json"
    $htmlPath   = Join-Path $script:IncidentsDir "$baseName.html"

    # ── Collect data ──────────────────────────────────────────────────────────
    $health        = Get-HealthState
    $recentSessions = @(Get-ChildItem -LiteralPath $script:SessionsDir -File -ErrorAction SilentlyContinue |
                        Sort-Object LastWriteTime -Descending | Select-Object -First 10 |
                        ForEach-Object { Read-JsonFile -Path $_.FullName -Default $null } |
                        Where-Object { $null -ne $_ })
    $ringBuffer    = @(Read-JsonFile -Path $script:RingBufferPath -Default @())
    $currentState  = Read-JsonFile -Path $script:CurrentStatePath -Default $null
    $rollbackState = Read-JsonFile -Path $script:RollbackPath -Default $null

    $doctorReport = $null
    try { $doctorReport = Get-DoctorReport -Settings $Settings } catch {}

    $audioReport = $null
    if ($AudioTriage) {
        try { $audioReport = Get-AudioTriageReport -Settings $Settings -LatencyMonReportPath $LatencyMonReportPath } catch {}
    }

    $bundle = [pscustomobject]@{
        exported_at     = (Get-Date).ToString("o")
        health          = $health
        current_state   = $currentState
        rollback_state  = $rollbackState
        recent_sessions = $recentSessions
        ring_buffer     = $ringBuffer
        doctor_report   = $doctorReport
        audio_triage    = $audioReport
    }

    # ── Write JSON ────────────────────────────────────────────────────────────
    $bundle | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    $result = [pscustomobject]@{
        json_path = $jsonPath
        html_path = $null
        exported_at = $bundle.exported_at
    }

    # ── Write HTML ────────────────────────────────────────────────────────────
    if ($AsHtml) {
        function Convert-CellValueToHtml {
            param($Value)
            if ($null -eq $Value) { return '<span style="color:#888">null</span>' }
            $str = [string]$Value
            if ($str.Length -gt 120) { $str = $str.Substring(0, 120) + "…" }
            return [System.Web.HttpUtility]::HtmlEncode($str)
        }

        function Convert-RowsToHtmlTable {
            param([object[]]$Rows, [string]$Caption = "")
            if (-not $Rows -or $Rows.Count -eq 0) { return "<p><em>No data.</em></p>" }
            $first = $Rows[0]
            $cols  = if ($first -is [hashtable]) { @($first.Keys) } else { @($first.PSObject.Properties.Name) }
            $sb    = [System.Text.StringBuilder]::new()
            if ($Caption) { [void]$sb.Append("<h3>$([System.Web.HttpUtility]::HtmlEncode($Caption))</h3>") }
            [void]$sb.Append('<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;font-size:12px;width:100%">')
            [void]$sb.Append('<thead><tr style="background:#333;color:#fff">')
            foreach ($col in $cols) { [void]$sb.Append("<th>$([System.Web.HttpUtility]::HtmlEncode($col))</th>") }
            [void]$sb.Append('</tr></thead><tbody>')
            $rowIdx = 0
            foreach ($row in $Rows) {
                $bg = if ($rowIdx % 2 -eq 0) { '#f9f9f9' } else { '#fff' }
                [void]$sb.Append("<tr style=`"background:$bg`">")
                foreach ($col in $cols) {
                    $val = if ($row -is [hashtable]) { $row[$col] } else { $row.PSObject.Properties[$col]?.Value }
                    [void]$sb.Append("<td>$(Convert-CellValueToHtml $val)</td>")
                }
                [void]$sb.Append('</tr>')
                $rowIdx++
            }
            [void]$sb.Append('</tbody></table>')
            return $sb.ToString()
        }

        $sb = [System.Text.StringBuilder]::new()
        [void]$sb.Append(@"
<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>Katana Keeper Export — $($bundle.exported_at)</title>
<style>
  body { font-family: Consolas, monospace; background:#1a1a1a; color:#ddd; margin:20px; }
  h1 { color:#f90; } h2 { color:#0af; border-bottom:1px solid #333; padding-bottom:4px; }
  h3 { color:#8cf; margin-top:12px; } table { margin-bottom:16px; }
  th { text-align:left; } td,th { padding:4px 8px; }
  .badge-low    { background:#2a7a2a; color:#fff; padding:2px 8px; border-radius:3px; }
  .badge-medium { background:#7a6a00; color:#fff; padding:2px 8px; border-radius:3px; }
  .badge-high   { background:#7a1a1a; color:#fff; padding:2px 8px; border-radius:3px; }
  pre { background:#111; padding:12px; overflow-x:auto; font-size:12px; }
  .section { margin-bottom:28px; }
</style></head><body>
<h1>&#x1F5E1;&#xFE0F; Katana Keeper — System Export</h1>
<p>Generated: <strong>$($bundle.exported_at)</strong></p>
"@)

        # Health snapshot
        [void]$sb.Append('<div class="section"><h2>Health Snapshot</h2>')
        if ($bundle.health) {
            $healthRows = @($bundle.health.PSObject.Properties | ForEach-Object { [pscustomobject]@{ Property = $_.Name; Value = $_.Value } })
            [void]$sb.Append((Convert-RowsToHtmlTable -Rows $healthRows))
        }
        [void]$sb.Append('</div>')

        # Doctor report
        if ($bundle.doctor_report) {
            $dr = $bundle.doctor_report
            $badgeClass = "badge-$($dr.risk_level)"
            [void]$sb.Append("<div class=`"section`"><h2>Doctor Report</h2>")
            [void]$sb.Append("<p>Risk: <span class=`"$badgeClass`">$($dr.risk_level.ToUpper())</span> (score $($dr.risk_score))</p>")
            if ($dr.findings.Count -gt 0) {
                [void]$sb.Append("<h3>Findings</h3><ul>")
                foreach ($f in $dr.findings) { [void]$sb.Append("<li>$([System.Web.HttpUtility]::HtmlEncode($f))</li>") }
                [void]$sb.Append("</ul>")
            }
            [void]$sb.Append("<p>GPU Mode: <strong>$([System.Web.HttpUtility]::HtmlEncode($dr.gpu_mode))</strong> — $([System.Web.HttpUtility]::HtmlEncode($dr.gpu_mode_note))</p>")
            [void]$sb.Append('</div>')
        }

        # Audio triage
        if ($bundle.audio_triage) {
            [void]$sb.Append('<div class="section"><h2>Audio Triage</h2>')
            $at = $bundle.audio_triage
            [void]$sb.Append("<p>Recommended action: <strong>$([System.Web.HttpUtility]::HtmlEncode($at.recommended_action))</strong></p>")
            if ($at.latencymon -and $at.latencymon.top_drivers.Count -gt 0) {
                [void]$sb.Append((Convert-RowsToHtmlTable -Rows $at.latencymon.top_drivers -Caption "Top LatencyMon Drivers"))
            }
            if ($at.nahimic_services.Count -gt 0) {
                [void]$sb.Append((Convert-RowsToHtmlTable -Rows $at.nahimic_services -Caption "Nahimic Services"))
            }
            [void]$sb.Append('</div>')
        }

        # Recent sessions
        if ($bundle.recent_sessions.Count -gt 0) {
            [void]$sb.Append('<div class="section"><h2>Recent Sessions</h2>')
            [void]$sb.Append((Convert-RowsToHtmlTable -Rows $bundle.recent_sessions))
            [void]$sb.Append('</div>')
        }

        # Ring buffer summary (last 10)
        if ($bundle.ring_buffer.Count -gt 0) {
            [void]$sb.Append('<div class="section"><h2>Ring Buffer (last 10 samples)</h2>')
            $last10 = @($bundle.ring_buffer)[-10..-1]
            [void]$sb.Append((Convert-RowsToHtmlTable -Rows $last10))
            [void]$sb.Append('</div>')
        }

        [void]$sb.Append('</body></html>')

        $sb.ToString() | Set-Content -LiteralPath $htmlPath -Encoding UTF8
        $result.html_path = $htmlPath

        # Auto-open HTML in default browser
        try { Start-Process $htmlPath } catch {}
    }

    Write-Log "Export saved → $jsonPath" "INFO"
    if ($AsHtml) { Write-Log "HTML report → $htmlPath" "INFO" }
    return $result
}

function Invoke-Prune {
    param([Parameter(Mandatory = $true)]$Settings)
    $watch  = Get-ObjectValue -Object $Settings -Name "watch" -Default ([pscustomobject]@{})
    $keep   = [int](Get-ObjectValue -Object $Settings -Name "sessionRetention" -Default 30)
    $retain = [int](Get-ObjectValue -Object $Settings -Name "incidentRetentionDays" -Default 14)
    Get-ChildItem $script:SessionsDir  -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -Skip $keep |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem $script:IncidentsDir -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$retain) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Log "Prune complete (kept last $keep sessions, $retain day incident retention)." "INFO"
    return [pscustomobject]@{ pruned_at = (Get-Date).ToString("o"); sessions_kept = $keep; incident_retention_days = $retain }
}
