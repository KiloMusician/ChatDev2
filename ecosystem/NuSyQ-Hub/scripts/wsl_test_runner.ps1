Param(
    [string]$Distro = "",
    [string]$Workdir = "",
    [string]$Command = "python -m pytest tests -q"
)

$ErrorActionPreference = "Stop"

function Get-WslPath {
    param([string]$Path)
    if (-not $Path) { $Path = (Get-Location).Path }
    # Convert C:\foo\bar -> /mnt/c/foo/bar
    $converted = $Path -replace '^([A-Za-z]):\\','/mnt/$1/' -replace '\\','/'
    return $converted
}

try {
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        Write-Error "wsl.exe not found. Install WSL or run this on a WSL-enabled host.";
        exit 1
    }

    $targetDir = if ($Workdir) { $Workdir } else { (Get-Location).Path }
    $wslDir = Get-WslPath -Path $targetDir

    $distroArg = if ($Distro) { "-d `"$Distro`"" } else { "" }
    $execCmd = "cd `"$wslDir`" && $Command"

    Write-Host "[WSL Test Runner] Using directory: $wslDir"
    if ($Distro) { Write-Host "[WSL Test Runner] Distro: $Distro" }
    Write-Host "[WSL Test Runner] Command: $Command"

    $fullArgs = "${distroArg} -- bash -lc `"$execCmd`""
    & wsl.exe $distroArg -- bash -lc "$execCmd"
    exit $LASTEXITCODE
} catch {
    Write-Error "WSL test runner failed: $_"
    exit 1
}
