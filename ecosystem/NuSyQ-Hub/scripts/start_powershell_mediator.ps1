param(
  [string]$NodeExe = 'node',
  [string]$MediatorScript = (Join-Path (Get-Location) 'scripts\powershell_mediator.js'),
  [string]$LogDir = (Join-Path (Get-Location) '.vscode\mediator'),
  [string]$PwshExe = 'C:\\Program Files\\PowerShell\\7\\pwsh.exe'
)

if (-not (Test-Path $MediatorScript)) {
  Write-Error "Mediator script not found: $MediatorScript"
  exit 1
}
try { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null } catch {}

$argsList = @($MediatorScript, '--pwsh', $PwshExe, '--logDir', $LogDir)
Write-Output "Starting PSES mediator via: $NodeExe $($argsList -join ' ')"
$proc = Start-Process -FilePath $NodeExe -ArgumentList $argsList -WindowStyle Hidden -PassThru
if ($proc -and $proc.Id) {
  $pidFile = Join-Path $LogDir 'launcher.pid'
  try { Set-Content -Path $pidFile -Value $proc.Id -Encoding UTF8 -Force } catch {}
  Write-Output "Mediator launched (PID $($proc.Id)), launcher.pid written to $pidFile"
} else {
  Write-Output 'Mediator launched (no pid available)'
}
