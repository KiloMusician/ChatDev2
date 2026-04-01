# Weekly Adoption Metrics - Task Scheduler Setup Guide

## 🎯 Purpose
Automates weekly tracking of orphan symbol adoption metrics. Runs every Monday at 9:00 AM and saves results to `reports/adoption_YYYYMMDD.json`.

## 📋 Prerequisites
- Windows 10/11 or Windows Server 2016+
- PowerShell 5.1+ (built into Windows)
- Python 3.8+ with project dependencies installed
- NuSyQ-Hub repository at `C:\Users\keath\Desktop\Legacy\NuSyQ-Hub`

## 🚀 Quick Setup (Recommended)

### Option 1: Import XML Task Definition
```powershell
# Open PowerShell as Administrator
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\scripts

# Import the task
schtasks /Create /XML WeeklyAdoptionMetrics.xml /TN "NuSyQ\WeeklyAdoptionMetrics"

# Verify task created
schtasks /Query /TN "NuSyQ\WeeklyAdoptionMetrics"
```

### Option 2: Use Task Scheduler GUI
1. Open **Task Scheduler** (Win + R → `taskschd.msc`)
2. Right-click **Task Scheduler Library** → **Import Task...**
3. Browse to `scripts/WeeklyAdoptionMetrics.xml`
4. Review settings and click **OK**

## 🧪 Testing

### Manual Test Run
```powershell
# Test the PowerShell script directly
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
.\scripts\run_weekly_adoption_metrics.ps1

# Expected output:
# ======================================================================
# 📊 Weekly Adoption Metrics Tracker
# ======================================================================
# Date: 2026-02-17 09:00:00
# Output: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\reports\adoption_20260217.json
# 
# 🔍 Running adoption metrics analysis...
# ✅ Adoption metrics saved successfully
# 📄 File: ...\reports\adoption_20260217.json
# 📦 Size: 2345 bytes
# 
# 📈 Quick Summary:
#   Total Symbols:     28
#   Adoption Rate:     100%
#   CLI Invocations:   10
```

### Test via Task Scheduler
```powershell
# Run task immediately
schtasks /Run /TN "NuSyQ\WeeklyAdoptionMetrics"

# Check last run result (0 = success)
schtasks /Query /TN "NuSyQ\WeeklyAdoptionMetrics" /V /FO LIST | Select-String "Last Result"
```

## 📊 Output Structure

### Reports Directory
```
reports/
├── adoption_20260217.json  ← Latest report
├── adoption_20260210.json  ← Last week
├── adoption_20260203.json  ← 2 weeks ago
└── archive/                ← Old reports (12+ weeks)
    └── adoption_20251201.json
```

### JSON Report Format
```json
{
  "total_symbols": 28,
  "adopted_symbols": 28,
  "adoption_rate": 100.0,
  "cli_invocations": 10,
  "phase_breakdown": {
    "Phase 1": {"symbols": 12, "adopted": 12, "invocations": 1},
    "Phase 2": {"symbols": 4, "adopted": 4, "invocations": 6},
    "Phase 3": {"symbols": 6, "adopted": 6, "invocations": 0},
    "Phase 4": {"symbols": 4, "adopted": 4, "invocations": 0},
    "Phase 5": {"symbols": 2, "adopted": 2, "invocations": 3}
  },
  "receipts_found": [
    "examples_2026-02-17.txt",
    "orchestrator_status_multiple.txt",
    "demo_2026-02-17.txt"
  ],
  "timestamp": "2026-02-17T09:00:42.123456"
}
```

## 🔧 Customization

### Change Schedule
Edit `WeeklyAdoptionMetrics.xml` before importing:
```xml
<!-- Every Monday at 9:00 AM (default) -->
<CalendarTrigger>
  <StartBoundary>2026-02-17T09:00:00</StartBoundary>
  <ScheduleByWeek>
    <DaysOfWeek>
      <Monday />
    </DaysOfWeek>
    <WeeksInterval>1</WeeksInterval>
  </ScheduleByWeek>
</CalendarTrigger>

<!-- Alternative: Every day at 8:00 AM -->
<CalendarTrigger>
  <StartBoundary>2026-02-17T08:00:00</StartBoundary>
  <ScheduleByDay>
    <DaysInterval>1</DaysInterval>
  </ScheduleByDay>
</CalendarTrigger>
```

### Change Report Retention
Edit `run_weekly_adoption_metrics.ps1`:
```powershell
# Keep last 12 weeks (default)
Select-Object -Skip 12

# Keep last 4 weeks (monthly)
Select-Object -Skip 4

# Keep last 52 weeks (yearly)
Select-Object -Skip 52
```

### Add Email Notifications
Add to `run_weekly_adoption_metrics.ps1` after successful run:
```powershell
if ($LASTEXITCODE -eq 0) {
    Send-MailMessage `
        -To "dev-team@example.com" `
        -From "nusyq-bot@example.com" `
        -Subject "Weekly Adoption Metrics: $($metrics.adoption_rate)% ($date)" `
        -Body "Adoption: $($metrics.adopted_symbols)/$($metrics.total_symbols) symbols" `
        -SmtpServer "smtp.example.com" `
        -Attachment $outputFile
}
```

## 📜 Task Logs

### View Task History
```powershell
# Event Viewer logs
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" |
    Where-Object { $_.TaskName -eq "\NuSyQ\WeeklyAdoptionMetrics" } |
    Select-Object -First 10 TimeCreated,Message
```

### View Script Output
Task Scheduler captures stdout/stderr:
1. Open Task Scheduler
2. Find task → Right-click → **Properties**
3. **History** tab (if enabled)

Or redirect output in XML:
```xml
<Arguments>-ExecutionPolicy Bypass -NoProfile -File "...\run_weekly_adoption_metrics.ps1" &gt; "...\logs\adoption_$(Get-Date -Format yyyyMMdd).log" 2&gt;&amp;1</Arguments>
```

## 🛡️ Troubleshooting

### Task Not Running
```powershell
# Check task status
schtasks /Query /TN "NuSyQ\WeeklyAdoptionMetrics" /V /FO LIST

# Common issues:
# 1. Task disabled → Enable in Task Scheduler GUI
# 2. User not logged in → Change to "Run whether user is logged on or not"
# 3. Python not in PATH → Use full path: C:\Python312\python.exe
```

### Python Import Errors
```powershell
# Ensure virtual environment activated (if used)
# Edit run_weekly_adoption_metrics.ps1:
$venvPath = Join-Path $projectRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    . $venvPath
}
python scripts/orphan_adoption_metrics.py --json --save $outputFile
```

### Permission Issues
```powershell
# Run as Administrator if reports/ directory write fails
# Or modify folder permissions:
icacls "C:\Users\keath\Desktop\Legacy\NuSyQ-Hub\reports" /grant Users:F
```

## 🔗 Integration with Dashboard

### Power BI Connection
```powershell
# Export all reports as single CSV for Power BI
$reports = Get-ChildItem reports\adoption_*.json
$reports | ForEach-Object {
    $data = Get-Content $_.FullName | ConvertFrom-Json
    [PSCustomObject]@{
        Date = $_.BaseName -replace 'adoption_',''
        TotalSymbols = $data.total_symbols
        AdoptionRate = $data.adoption_rate
        CLIInvocations = $data.cli_invocations
    }
} | Export-Csv reports\adoption_trends.csv -NoTypeInformation
```

### Excel Pivot Table
Import `adoption_trends.csv` into Excel:
1. **Data** → **Get Data** → **From File** → **From Text/CSV**
2. Select `reports\adoption_trends.csv`
3. Create Pivot Table with Date as rows, metrics as values

## 📚 Related Documentation
- Main summary: `docs/ORPHAN_MODERNIZATION_MASTER_SUMMARY.md`
- Metrics tool: `scripts/orphan_adoption_metrics.py`
- Phase 5 validation: `docs/PHASE_5_DEMO_SYSTEMS_COMPLETE.md`

## 🎯 Success Criteria
- ✅ Task runs every Monday at 9:00 AM
- ✅ JSON file created in `reports/` with current date
- ✅ Old reports archived after 12 weeks
- ✅ No error messages in Event Viewer
- ✅ Adoption rate trends tracked over time
