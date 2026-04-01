<#
.SYNOPSIS
  Create a symbolic link inside the NuSyQ-Hub workspace pointing to the SimulatedVerse folder on the Desktop.

USAGE
  Run in an elevated PowerShell prompt or with Developer Mode enabled:
    .\scripts\create_simulatedverse_symlink.ps1 -Target 'C:\Users\keath\Desktop\SimulatedVerse' -LinkPath '.\\SimulatedVerse'
#>

param(
    [string]$Target = 'C:\Users\keath\Desktop\SimulatedVerse',
    [string]$LinkPath = '.\SimulatedVerse'
)

Write-Output "Creating symlink: $LinkPath -> $Target"
if (-Not (Test-Path $Target)) {
    Write-Error "Target does not exist: $Target"
    exit 2
}

try {
    if (Test-Path $LinkPath) {
        Write-Output "Link path already exists: $LinkPath"
        exit 0
    }
    New-Item -ItemType SymbolicLink -Path $LinkPath -Target $Target -Force
    Write-Output "Created symbolic link."
} catch {
    Write-Error "Failed to create symbolic link: $_"
    Write-Output "If this fails, enable Developer Mode or run PowerShell as Administrator."
    exit 1
}
