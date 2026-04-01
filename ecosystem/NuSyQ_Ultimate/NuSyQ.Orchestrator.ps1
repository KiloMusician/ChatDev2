<#
.SYNOPSIS
    NuSyQ AI Ecosystem Orchestrator

.DESCRIPTION
    Automated, declarative setup and maintenance system for the NuSyQ AI development environment.
    Reads nusyq.manifest.yaml and orchestrates:
    - Package installations (winget, pip, VS Code extensions, Ollama models)
    - Environment variable configuration
    - Directory structure creation
    - Health checks and validation
    - Automated reporting and state persistence

.PARAMETER Force
    Force reinstall of all packages even if already present

.PARAMETER SkipHealthChecks
    Skip health check validation (faster, but less safe)

.PARAMETER DryRun
    Show what would be done without making changes

.EXAMPLE
    .\NuSyQ.Orchestrator.ps1
    # Standard execution with full setup

.EXAMPLE
    .\NuSyQ.Orchestrator.ps1 -DryRun
    # Preview changes without executing

.NOTES
    Requires:
    - PowerShell 7+
    - Administrator privileges
    - Internet connection (for package downloads)

    Author: NuSyQ Development Team
    Version: 2.0.0
    Last Updated: 2025-10-05
#>

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$SkipHealthChecks,
    [switch]$DryRun
)

# If running under Windows PowerShell (<7), attempt to re-invoke using PowerShell Core (pwsh)
if ($PSVersionTable.PSVersion.Major -lt 7) {
  $pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue)
  if ($pwsh) {
    Write-Host "Detected PowerShell $($PSVersionTable.PSVersion.ToString()); re-invoking with pwsh..." -ForegroundColor Yellow
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $MyInvocation.MyCommand.Path @PSBoundParameters
    exit $LASTEXITCODE
  } else {
    Write-Warning "PowerShell Core (pwsh) not found. This script requires PowerShell 7+. Continuing may fail." 
  }
}

# === Dynamic Configuration Loading ===
# Load environment configuration for flexible paths
$envConfigPath = Join-Path $PSScriptRoot "config\environment.json"
$flexibleConfig = $null

if (Test-Path $envConfigPath) {
    try {
        $flexibleConfig = Get-Content $envConfigPath -Raw | ConvertFrom-Json
        Write-Host "✅ Loaded flexible environment configuration" -ForegroundColor Green
    } catch {
        Write-Warning "Could not load environment configuration: $_"
    }
}

# Get flexible Python path
function Get-FlexiblePythonPath {
    # Try venv first (most reliable)
    $venvPaths = @(
        "$PSScriptRoot\.venv\Scripts\python.exe",
        "$PSScriptRoot\venv\Scripts\python.exe"
    )

    foreach ($path in $venvPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    # Fall back to system Python from config
    if ($flexibleConfig -and $flexibleConfig.PYTHON_PATH) {
        return $flexibleConfig.PYTHON_PATH
    }

    # Final fallback
    return "python"
}

# Get GitHub user (for authentication)
$GitHubUser = if ($flexibleConfig -and $flexibleConfig.GITHUB_USER) {
    $flexibleConfig.GITHUB_USER
} else {
    "KiloMusician"
}

# === Error Handling Configuration ===
$ErrorActionPreference = 'Stop'  # Halt on any error
$ProgressPreference = 'SilentlyContinue'  # Suppress progress bars for performance

# === Path Resolution ===
# Resolve script directory and manifest location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestYaml = Join-Path $ScriptDir 'nusyq.manifest.yaml'

# Validate manifest exists
if (-not (Test-Path $ManifestYaml)) {
    throw "❌ Manifest not found at: $ManifestYaml`nPlease ensure nusyq.manifest.yaml exists in the script directory."
}

# === Dependency Checks ===
Write-Host "`n🔍 Checking dependencies..." -ForegroundColor Cyan

# Check Python
$pythonPath = Get-FlexiblePythonPath
try {
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "❌ Python not found at: $pythonPath"
    Write-Host "Please install Python 3.8+ and ensure it's in PATH" -ForegroundColor Yellow
    exit 1
}

# Check Ollama (if not skipped)
if (-not $SkipHealthChecks) {
    try {
        $ollamaVersion = & ollama --version 2>&1
        Write-Host "✅ Ollama: $ollamaVersion" -ForegroundColor Green
    } catch {
        Write-Warning "⚠️  Ollama not found. Some features may not work."
        Write-Host "Install from: https://ollama.ai/download" -ForegroundColor Yellow
    }
}

# Check GitHub CLI
try {
    $ghVersion = & gh --version 2>&1 | Select-Object -First 1
    Write-Host "✅ GitHub CLI: $ghVersion" -ForegroundColor Green
} catch {
    Write-Warning "⚠️  GitHub CLI not found. Issue creation will fallback to logging."
    Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
}

# === PowerShell.Yaml Module Setup ===
# Ensure YAML parsing capability is available
Write-Host "`n🔧 Checking PowerShell.Yaml module..." -ForegroundColor Cyan

try {
    # Check if module is already installed
  if (-not (Get-Module -ListAvailable -Name PowerShell.Yaml)) {
    if ($DryRun) {
      Write-Host "   [DryRun] PowerShell.Yaml not available, skipping install" -ForegroundColor Yellow
    } else {
      Write-Host "   Installing PowerShell.Yaml module..." -ForegroundColor Yellow
      Install-Module PowerShell.Yaml -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
      Write-Host "   ✅ PowerShell.Yaml installed successfully" -ForegroundColor Green
    }
  }

  # Import the module if available; in DryRun we avoid throwing on import failure
  try {
    if (-not $DryRun) { Import-Module PowerShell.Yaml -ErrorAction Stop; Write-Host "   ✅ PowerShell.Yaml module loaded" -ForegroundColor Green }
    else { Write-Host "   [DryRun] Skipping PowerShell.Yaml import" -ForegroundColor Cyan }
    } catch {
    if ($DryRun) { Write-Warning "   [DryRun] PowerShell.Yaml import failed, continuing due to DryRun" }
    else { throw "Failed to install/import PowerShell.Yaml module: $($_.Exception.Message)`nManual installation: Install-Module PowerShell.Yaml -Scope CurrentUser -Force" }
  }

} catch {
    throw @"
❌ Failed to install/import PowerShell.Yaml module:
   $($_.Exception.Message)

   Manual installation:
   Install-Module PowerShell.Yaml -Scope CurrentUser -Force
"@
}

# --- Load manifest with validation (with fallback YAML parsing)
function Load-YamlAsObject([string]$path){
  # Prefer native ConvertFrom-Yaml if available
  if (Get-Command -Name ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
    return (Get-Content $path -Raw) | ConvertFrom-Yaml
  }

  # Fallback: try to use Python to parse YAML and emit JSON
  $python = Get-FlexiblePythonPath
  try {
  # Write a small Python parser to a temp file using an array of lines to avoid
  # here-string parsing issues in PowerShell across different environments.
  $pyLines = @(
    'import sys, json',
    'try:',
    '  import yaml',
    "except Exception as e:",
    "  # Avoid Python f-strings which can confuse some PowerShell parsers when",
    "  # the here-string is processed; use percent-format instead.",
    "  sys.stderr.write('PY_YAML_MISSING: {0}\\n'.format(str(e)))",
    "  raise",
    "p = sys.argv[1]",
    "with open(p, 'r', encoding='utf-8') as f:",
    "  data = yaml.safe_load(f)",
    "# Use default=str to allow dates and other non-JSON-serializable objects to be",
    "# converted to strings for safe transport back to PowerShell.",
    "print(json.dumps(data, default=str, ensure_ascii=False))"
  )

    $tmp = Join-Path $env:TEMP "nusyq_parse_yaml.py"
    Set-Content -Path $tmp -Value $pyLines -Encoding UTF8 -Force

    $outFile = Join-Path $env:TEMP "nusyq_parse_yaml_out.json"
    $errFile = Join-Path $env:TEMP "nusyq_parse_yaml_err.txt"

    # Ensure previous temp files are removed
    Remove-Item -Path $outFile,$errFile -ErrorAction SilentlyContinue

    # Start Python and capture stdout/stderr separately to avoid mixing
    $psiArgs = @($tmp, $path)
    try {
      Start-Process -FilePath $python -ArgumentList $psiArgs -NoNewWindow -RedirectStandardOutput $outFile -RedirectStandardError $errFile -Wait -ErrorAction Stop | Out-Null
    } catch {
      Remove-Item $tmp -ErrorAction SilentlyContinue
      throw "Failed to execute Python parser ($python): $($_.Exception.Message)"
    }

    $stderr = ''
    $stdout = ''
    if (Test-Path $errFile) { $stderr = Get-Content -Path $errFile -Raw -ErrorAction SilentlyContinue }
    if (Test-Path $outFile) { $stdout = Get-Content -Path $outFile -Raw -ErrorAction SilentlyContinue }

    Remove-Item $tmp -ErrorAction SilentlyContinue
    Remove-Item $outFile,$errFile -ErrorAction SilentlyContinue

    if ($stderr -and $stderr -match 'PY_YAML_MISSING') {
      # If PyYAML is missing, print a colored suggestion and then throw.
      function Write-SuggestionLocal {
          param([string]$Title,[string]$File,[int]$Line,[string]$Message)
          try { Write-Host "`n$Title" -ForegroundColor Magenta } catch {}
          try { Write-Host ("{0}:{1}" -f $File, $Line) -ForegroundColor Magenta } catch {}
          try { Write-Host $Message -ForegroundColor Magenta } catch {}
    try { Write-Host (('To open: code -g "{0}:{1}"' -f $File, $Line)) -ForegroundColor Cyan } catch {}
        }

        $suggestMsg = "PyYAML is not installed in the Python environment ($python)."
        # Avoid printing an ampersand which can be parsed specially; show the explicit python command instead.
        $suggestCmd = "Install in the active environment: $python -m pip install pyyaml"
        Write-SuggestionLocal -Title "SUGGESTION:" -File $ManifestYaml -Line 1 -Message ("{0}`n{1}" -f $suggestMsg, $suggestCmd)

        throw ("PyYAML not installed in Python environment ({0}). Install with: {1}`nPython stderr: {2}" -f $python, "$python -m pip install pyyaml", $stderr)
    }

    if (-not $stdout) {
      throw "Python parser produced no JSON output. Stderr: $stderr"
    }

    try {
      return $stdout | ConvertFrom-Json
    } catch {
      throw "Conversion from JSON failed with error: $($_.Exception.Message). Python stdout starts with: $([string]$stdout).Substring(0, [Math]::Min(200, $stdout.Length))"
    }
  } catch {
    throw "No YAML parser available: ConvertFrom-Yaml cmdlet not found and Python-based YAML parse failed: $($_.Exception.Message)"
  }
}

try {
  $manifest = Load-YamlAsObject $ManifestYaml

  # Validate manifest structure
  $requiredSections = @('meta', 'folders')
  foreach($section in $requiredSections) {
    if(-not $manifest.PSObject.Properties.Name.Contains($section)) {
      $msg = "Missing required section '$section' in manifest"
      throw $msg
    }
  }

  # Validate meta section
  if(-not $manifest.meta.name) {
    throw "Missing required field 'meta.name' in manifest"
  }

  Write-Host "✅ Manifest validation passed: $($manifest.meta.name)" -ForegroundColor Green

} catch {
  throw "Manifest validation failed: $($_.Exception.Message)"
}

# --- Expand env vars in manifest strings
function Expand-PathString([string]$s){
  if([string]::IsNullOrWhiteSpace($s)){ return $s }
  return [Environment]::ExpandEnvironmentVariables($s)
}

# --- Paths
$root     = Expand-PathString $manifest.meta.root_dir
$logs     = Expand-PathString $manifest.meta.logs_dir
$reports  = Expand-PathString $manifest.meta.reports_dir
$stateDir = Expand-PathString $manifest.meta.state_dir
$timestamp = (Get-Date).ToString('yyyy-MM-dd_HH-mm-ss')

# --- Create dirs
New-Item -ItemType Directory -Force -Path $root,$logs,$reports,$stateDir | Out-Null
$logFile   = Join-Path $logs "orchestrator_$timestamp.log"
$stateFile = Join-Path $stateDir 'nusyq_state.json'
Start-Transcript -Path $logFile -Append | Out-Null

function Stage([string]$name){ Write-Host "`n=== $name ===" -ForegroundColor Cyan }

# --- Elevation check
if (-not $DryRun) {
  if(-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")){
    throw "Please run as Administrator (PowerShell 7+)."
  }
} else {
  Write-Host "[DryRun] Skipping Administrator elevation check" -ForegroundColor Yellow
}

# --- PATH refresh for current session
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')

# --- Ensure Ollama is on PATH (User)
$ollamaInstallDir = Join-Path $env:LOCALAPPDATA "Programs\Ollama"
if(Test-Path (Join-Path $ollamaInstallDir "ollama.exe")){
  $userPath = [Environment]::GetEnvironmentVariable('Path','User')
  if($userPath -notlike "*$ollamaInstallDir*"){
    [Environment]::SetEnvironmentVariable(
      'Path',
      ($userPath + ";" + $ollamaInstallDir),
      'User'
    )
    Write-Host "Added Ollama to User PATH: $ollamaInstallDir" -ForegroundColor Green
  } else {
    Write-Host "Ollama already in User PATH: $ollamaInstallDir" -ForegroundColor Cyan
  }
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
} else {
  Write-Warning "Ollama install not found at $ollamaInstallDir"
}

# --- Apply environment variables from manifest
Stage "Environment Variables"
if($manifest.env){
  # Support both hashtable and PSCustomObject shapes
  foreach($prop in $manifest.env.PSObject.Properties){
    $key = $prop.Name
    $val = Expand-PathString $prop.Value
    [Environment]::SetEnvironmentVariable($key, $val, 'User')
    Write-Host "Set (User) $key = $val"
  }
  # refresh current session too
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
}

# --- Create folders
Stage "Create Folders"
foreach($f in $manifest.folders){
  $p = Expand-PathString $f
  New-Item -ItemType Directory -Force -Path $p | Out-Null
  Write-Host "Ensured: $p"
}

# --- Winget helper (audited)
function Install-Winget {
  param([Parameter(Mandatory)][string]$Id,[switch]$Exact)
  $exactFlag = $Exact.IsPresent ? '-e' : ''
  $auditFile = Join-Path $reports ("audit_" + ($Id -replace '\.','_') + "_$timestamp.txt")
  try {
    winget source update | Out-Null
    Write-Host "`n-- AUDIT winget show $Id --" -ForegroundColor Yellow
    winget show --id $Id $exactFlag | Tee-Object -FilePath $auditFile | Out-Null
    winget install --id $Id $exactFlag --accept-package-agreements --accept-source-agreements --silent
    Write-Host "✅ Successfully installed $Id" -ForegroundColor Green
  } catch {
    Write-Warning "Failed to install $Id via winget: $($_.Exception.Message)"
  }
}

# --- Pip helper
function Pip-Install([string]$pkg){
  try {
    $pythonPath = Get-FlexiblePythonPath
    Write-Host "`n-- pip install $pkg --" -ForegroundColor Yellow
    & $pythonPath -m pip install --upgrade pip | Out-Null
    & $pythonPath -m pip install $pkg
    Write-Host "✅ Successfully installed $pkg" -ForegroundColor Green
  } catch {
    Write-Warning "Failed to install $pkg via pip: $($_.Exception.Message)"
  }
}

# --- VS Code extensions
function Install-CodeExt([string]$ext){
  try {
    code --install-extension $ext | Out-Null
    Write-Host "✅ Successfully installed VS Code extension: $ext" -ForegroundColor Green
  } catch {
  # Use ${NAME} to delimit variables and avoid PowerShell parsing issues with ':'
    Write-Warning "Failed to install VS Code extension ${ext}: $($_.Exception.Message)"
  }
}

# --- Ollama model pulls
function Get-InstalledOllamaModels{
  try {
    $out = & ollama list 2>$null
  } catch {
    $out = ''
  }
  $models = @()
  if ($out) {
    foreach ($line in $out -split "`n") {
      $trim = $line.Trim()
      if ([string]::IsNullOrWhiteSpace($trim)) { continue }
      # First token typically contains model[:tag]
      $first = ($trim -split '\s+')[0]
      $name = ($first -split ':')[0]
      if ($name) { $models += $name }
    }
    $models = $models | Select-Object -Unique
  }
  return $models
}

function Ensure-OllamaModel([string]$model, [array]$installedModels){
  # Normalize base name (strip tag)
  $base = ($model -split ':')[0]
  try {
    if ($installedModels -and ($installedModels -contains $base)) {
      Write-Host "Skipping pull; Ollama model already installed: $model" -ForegroundColor Cyan
      return
    }

    Write-Host "Attempting to pull Ollama model: $model" -ForegroundColor Yellow
    & ollama pull $model
    Write-Host "✅ Successfully pulled Ollama model: $model" -ForegroundColor Green
  } catch {
    Write-Warning "Ollama pull failed for ${model}: $($_.Exception.Message)"
  }
}

# ============================
# Stage: Winget packages
# ============================
if($manifest.winget_packages){
  Stage "Winget Packages"
  foreach($pkg in $manifest.winget_packages){
    $id = $pkg.id
    $exact = $false
    if($pkg.PSObject.Properties.Name -contains 'exact'){ $exact = [bool]$pkg.exact }
    Install-Winget -Id $id -Exact:($exact)
  }
}

# ============================
# Stage: Pip packages
# ============================
if($manifest.pip_packages){
  Stage "Pip Packages"
  foreach($p in $manifest.pip_packages){
    Pip-Install $p
  }
}

# ============================
# Stage: VS Code extensions
# ============================
if($manifest.vscode_extensions){
  Stage "VS Code Extensions"
  foreach($e in $manifest.vscode_extensions){
    Install-CodeExt $e
  }
}

# ============================
# Stage: Ollama models
# ============================
if($manifest.ollama_models){
  Stage "Ollama Models"
  # Read installed models once and refresh after pulls
  $installedModels = Get-InstalledOllamaModels

  foreach($m in $manifest.ollama_models){
    # Prefer phi3.5 if present instead of phi4 to match local installation
    $base = ($m -split ':')[0]
    if ($base -match '^phi4' -and ($installedModels -contains 'phi3.5')) {
      Write-Host "Detected local phi3.5 installation; preferring phi3.5 over phi4" -ForegroundColor Yellow
      $candidate = 'phi3.5'
      Ensure-OllamaModel $candidate $installedModels
      # refresh installed list after potential change
      $installedModels = Get-InstalledOllamaModels
      continue
    }

    # If base model already installed, skip pull; otherwise pull
    if ($installedModels -contains $base) {
      Write-Host "Skipping pull; Ollama model already installed: $m" -ForegroundColor Cyan
    } else {
      Ensure-OllamaModel $m $installedModels
      $installedModels = Get-InstalledOllamaModels
    }
  }
}

# ============================
# Stage: Post-install commands
# ============================
if($manifest.post_install){
  Stage "Post-install"
  foreach($cmd in $manifest.post_install){
    Write-Host "Run: $cmd"
    iex $cmd
  }
}

# ============================
# Stage: Reports
# ============================
if($manifest.reports){
  Stage "Reports"
  foreach($r in $manifest.reports){
    switch ($r.type){
      'winget_export'     { winget export --output (Join-Path $reports "winget_packages_$timestamp.json") }
      'vscode_extensions' { code --list-extensions --show-versions > (Join-Path $reports "vscode_extensions_$timestamp.txt") }
      'ollama_models'     { try { ollama list > (Join-Path $reports "ollama_models_$timestamp.txt") } catch { Write-Warning "ollama list failed." } }
      'system_baseline'   { Get-ComputerInfo | Out-File (Join-Path $reports "SystemBaseline_$timestamp.txt") }
      default             { Write-Warning "Unknown report type: $($r.type)" }
    }
  }
}

# ============================
# Stage: Configuration Backup
# ============================
Stage "Configuration Backup"
$backupDir = Join-Path $stateDir "config_backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$configFiles = @(
  $ManifestYaml,
  (Join-Path $root "knowledge-base.yaml"),
  (Join-Path $root "AI_Hub/ai-ecosystem.yaml"),
  (Join-Path $root "config/tasks.yaml")
)

foreach($configFile in $configFiles) {
  if(Test-Path $configFile) {
    $fileName = [System.IO.Path]::GetFileName($configFile)
    $backupPath = Join-Path $backupDir "${fileName}_$timestamp.bak"
    Copy-Item $configFile $backupPath -Force
    Write-Host "✅ Backed up: $fileName" -ForegroundColor Green
  }
}

# ============================
# Stage: Health checks
# ============================
$health = @()
if($manifest.health_checks){
  Stage "Health Checks"
  foreach($hc in $manifest.health_checks){
    $cmd = $hc.cmd
    $expect = $hc.expect
    $out = ''
    $ok = $false
    try {
      $out = (iex $cmd | Out-String)
      if($null -ne $expect -and $out -match [Regex]::Escape($expect)){ $ok = $true }
      elseif(-not $expect){ $ok = $true }
    } catch {
      $out = $_.Exception.Message
      $ok = $false
    }
    $health += [pscustomobject]@{ command = $cmd; expect = $expect; ok = $ok; output = $out.Trim() }
    $status = $ok ? 'OK' : 'FAIL'
    Write-Host ("[{0}] {1}" -f $status, $cmd) -ForegroundColor ($ok ? 'Green' : 'Red')
  }
}

# ============================
# Stage: Persist state
# ============================
Stage "Persist State"
$state = [pscustomobject]@{
  timestamp = $timestamp
  manifest_version = $manifest.meta.version
  env = $manifest.env
  installed = [pscustomobject]@{
    winget_packages   = $manifest.winget_packages
    pip_packages      = $manifest.pip_packages
    vscode_extensions = $manifest.vscode_extensions
    ollama_models     = $manifest.ollama_models
  }
  health = $health
}
$state | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8 $stateFile
Write-Host "State saved: $stateFile" -ForegroundColor Green

Stop-Transcript | Out-Null
Write-Host "`nDone. Logs: $logFile" -ForegroundColor Green
Write-Host "Reports: $reports" -ForegroundColor Green
