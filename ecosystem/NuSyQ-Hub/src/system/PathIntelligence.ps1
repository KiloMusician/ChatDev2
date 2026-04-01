# KILO-FOOLISH Path Intelligence - PowerShell Interface

param(
    [string]$Search,
    [string]$Resolve,
    [string]$Context,
    [switch]$Optimize,
    [switch]$Aliases,
    [switch]$Report,
    [switch]$Status
)

function Write-PathLog {
    param([string]$Message, [string]$Level = "INFO")

    $colors = @{
        "ERROR" = "Red"; "WARNING" = "Yellow"; "SUCCESS" = "Green"
        "INFO" = "Cyan"; "PATH" = "Magenta"
    }

    Write-Host "[PATH-INTEL] $Message" -ForegroundColor $colors[$Level]
}

function Invoke-PathSearch {
    param([string]$Query)

    Write-PathLog "🔍 Searching for: '$Query'" "PATH"

    try {
        $result = python ".\src\core\PathIntelligence.py" --search $Query 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host $result
        }
        else {
            Write-PathLog "❌ Search failed: $result" "ERROR"
        }
    }
    catch {
        Write-PathLog "❌ Search error: $_" "ERROR"
    }
}

function Invoke-PathResolve {
    param([string]$Path, [string]$Context = $null)

    Write-PathLog "🛣️ Resolving path: '$Path'" "PATH"
    if ($Context) {
        Write-PathLog "📍 Context: '$Context'" "INFO"
    }

    try {
        $args = @("--resolve", $Path)
        if ($Context) {
            $args += @("--context", $Context)
        }

        $result = python ".\src\core\PathIntelligence.py" @args 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host $result
        }
        else {
            Write-PathLog "❌ Resolution failed: $result" "ERROR"
        }
    }
    catch {
        Write-PathLog "❌ Resolution error: $_" "ERROR"
    }
}

function Start-PathOptimization {
    Write-PathLog "🚀 Starting path optimization analysis..." "PATH"

    try {
        $result = python ".\src\core\PathIntelligence.py" --optimize 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host $result
            Write-PathLog "✅ Optimization analysis complete" "SUCCESS"
        }
        else {
            Write-PathLog "❌ Optimization failed: $result" "ERROR"
        }
    }
    catch {
        Write-PathLog "❌ Optimization error: $_" "ERROR"
    }
}

function New-SmartAliases {
    Write-PathLog "🎯 Creating smart path aliases..." "PATH"

    try {
        $result = python ".\src\core\PathIntelligence.py" --aliases 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host $result

            # Create PowerShell functions for aliases
            Write-PathLog "📝 Creating PowerShell alias functions..." "INFO"

            $aliasScript = @"
# KILO-FOOLISH Smart Path Aliases
# Auto-generated on $(Get-Date)

function goto-config { Set-Location ".\src\config" }
function goto-core { Set-Location ".\src\core" }
function goto-data { Set-Location ".\data" }
function goto-docs { Set-Location ".\docs" }
function goto-tests { Set-Location ".\tests" }

function open-secrets { code ".\src\config\SecretsManager.ps1" }
function open-coordinator { code ".\src\core\RepositoryCoordinator.py" }
function open-scanner { code ".\src\core\ArchitectureScanner.py" }
function open-readme { code ".\README.md" }

# Usage examples:
# goto-config    # Navigate to config directory
# open-secrets   # Open secrets manager
"@

            $aliasFile = ".\PathAliases.ps1"
            $aliasScript | Out-File $aliasFile -Encoding UTF8
            Write-PathLog "✅ PowerShell aliases saved to: $aliasFile" "SUCCESS"
            Write-PathLog "💡 Run: . .\PathAliases.ps1 to load aliases" "INFO"
        }
        else {
            Write-PathLog "❌ Alias creation failed: $result" "ERROR"
        }
    }
    catch {
        Write-PathLog "❌ Alias creation error: $_" "ERROR"
    }
}

function Show-PathStatus {
    Write-PathLog "📊 KILO-FOOLISH Path Intelligence Status" "PATH"

    # Check if path intelligence is set up
    if (!(Test-Path ".\src\core\PathIntelligence.py")) {
        Write-PathLog "❌ Path Intelligence not found" "ERROR"
        return
    }

    Write-PathLog "✅ Path Intelligence system ready" "SUCCESS"

    # Check for existing reports
    if (Test-Path ".\PATH_INTELLIGENCE_REPORT.md") {
        $reportAge = (Get-Date) - (Get-Item ".\PATH_INTELLIGENCE_REPORT.md").LastWriteTime
        Write-PathLog "📄 Last report: $($reportAge.Hours) hours ago" "INFO"
    }
    else {
        Write-PathLog "📄 No path intelligence report found" "WARNING"
    }

    # Check for aliases
    if (Test-Path ".\PathAliases.ps1") {
        Write-PathLog "🎯 Smart aliases available in PathAliases.ps1" "SUCCESS"
    }
    else {
        Write-PathLog "🎯 No smart aliases found (run -Aliases to create)" "INFO"
    }

    # Check path intelligence data
    if (Test-Path ".\src\core\path_intelligence.json") {
        try {
            $data = Get-Content ".\src\core\path_intelligence.json" | ConvertFrom-Json
            $aliasCount = $data.path_aliases.PSObject.Properties.Count
            $cacheCount = $data.resolution_cache.PSObject.Properties.Count

            Write-PathLog "🔍 $aliasCount aliases, $cacheCount cached resolutions" "INFO"
        }
        catch {
            Write-PathLog "⚠️ Path intelligence data exists but couldn't be read" "WARNING"
        }
    }
}

function Start-PathReport {
    Write-PathLog "📊 Generating comprehensive path intelligence report..." "PATH"

    try {
        $result = python ".\src\core\PathIntelligence.py" --report 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host $result

            if (Test-Path ".\PATH_INTELLIGENCE_REPORT.md") {
                Write-PathLog "📖 Opening path intelligence report..." "SUCCESS"
                code ".\PATH_INTELLIGENCE_REPORT.md"
            }
        }
        else {
            Write-PathLog "❌ Report generation failed: $result" "ERROR"
        }
    }
    catch {
        Write-PathLog "❌ Report error: $_" "ERROR"
    }
}

# Smart path navigation functions
function Find-KILOPath {
    param([string]$Query)

    if (!$Query) {
        Write-PathLog "🔍 Usage: Find-KILOPath 'search_term'" "INFO"
        return
    }

    Invoke-PathSearch $Query
}

function Resolve-KILOPath {
    param([string]$Path, [string]$From = $null)

    if (!$Path) {
        Write-PathLog "🛣️ Usage: Resolve-KILOPath 'path' [-From 'context']" "INFO"
        return
    }

    Invoke-PathResolve $Path $From
}

# Main execution
Write-Host "`n🛣️ KILO-FOOLISH Path Intelligence System" -ForegroundColor Magenta
Write-Host "=" * 50 -ForegroundColor Magenta

if ($Search) {
    Invoke-PathSearch $Search
}
elseif ($Resolve) {
    Invoke-PathResolve $Resolve $Context
}
elseif ($Optimize) {
    Start-PathOptimization
}
elseif ($Aliases) {
    New-SmartAliases
}
elseif ($Report) {
    Start-PathReport
}
elseif ($Status) {
    Show-PathStatus
}
else {
    Write-PathLog "Available commands:" "INFO"
    Write-PathLog "  -Search 'term'    : Search for paths containing term" "INFO"
    Write-PathLog "  -Resolve 'path'   : Resolve path with suggestions" "INFO"
    Write-PathLog "  -Optimize         : Analyze path structure for optimization" "INFO"
    Write-PathLog "  -Aliases          : Create smart path aliases" "INFO"
    Write-PathLog "  -Report           : Generate comprehensive report" "INFO"
    Write-PathLog "  -Status           : Show system status" "INFO"

    Write-Host "`n🚀 Quick start:" -ForegroundColor Yellow
    Write-Host "  .\src\core\PathIntelligence.ps1 -Status" -ForegroundColor White
    Write-Host "  .\src\core\PathIntelligence.ps1 -Search 'config'" -ForegroundColor White
    Write-Host "  .\src\core\PathIntelligence.ps1 -Report" -ForegroundColor White
}

Write-Host "`n💡 Pro tip: Use Find-KILOPath and Resolve-KILOPath functions for quick navigation!" -ForegroundColor Yellow
