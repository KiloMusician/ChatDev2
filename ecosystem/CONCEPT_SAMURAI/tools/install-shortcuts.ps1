<#
.SYNOPSIS
Install desktop and Start Menu shortcuts for keeper command wrappers.

.DESCRIPTION
Creates Windows `.lnk` shortcuts that point at the `.cmd` launchers in `tools/`.
This keeps `keeper.ps1` as the single source of truth while making the repo easy
to launch from Explorer or the Start Menu.

.EXAMPLE
.\tools\install-shortcuts.ps1

.EXAMPLE
.\tools\install-shortcuts.ps1 -NoDesktop -StartMenuOnly
#>
[CmdletBinding()]
param(
    [switch]$NoDesktop,
    [switch]$StartMenuOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$toolsDir     = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir      = Split-Path -Parent $toolsDir
$desktopDir   = [Environment]::GetFolderPath("Desktop")
$startMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\CONCEPT"

$shortcutSpecs = @(
    @{ Name = "Keeper UI";                     Target = Join-Path $toolsDir "keeper-ui.cmd";                Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Web Dashboard";          Target = Join-Path $toolsDir "keeper-web.cmd";               Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Gaming";                 Target = Join-Path $toolsDir "keeper-gaming.cmd";            Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Gaming (Admin)";         Target = Join-Path $toolsDir "keeper-gaming-admin.cmd";      Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Coding";                 Target = Join-Path $toolsDir "keeper-coding.cmd";            Icon = "%SystemRoot%\System32\shell32.dll,71"  },
    @{ Name = "Keeper Balanced";               Target = Join-Path $toolsDir "keeper-balanced.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Auto";                   Target = Join-Path $toolsDir "keeper-auto.cmd";              Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Auto Apply (Admin)";     Target = Join-Path $toolsDir "keeper-auto-admin.cmd";        Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Schedule";               Target = Join-Path $toolsDir "keeper-schedule.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Schedule (Admin)";       Target = Join-Path $toolsDir "keeper-schedule-admin.cmd";    Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Audio Safe";             Target = Join-Path $toolsDir "keeper-audio-safe.cmd";        Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Audio Safe (Admin)";     Target = Join-Path $toolsDir "keeper-audio-safe-admin.cmd";  Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Quiet";                  Target = Join-Path $toolsDir "keeper-quiet.cmd";             Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Restore";                Target = Join-Path $toolsDir "keeper-restore.cmd";           Icon = "%SystemRoot%\System32\shell32.dll,238" },
    @{ Name = "Keeper Status";                 Target = Join-Path $toolsDir "keeper-status.cmd";            Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Doctor";                 Target = Join-Path $toolsDir "keeper-doctor.cmd";            Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Recommend";              Target = Join-Path $toolsDir "keeper-recommend.cmd";         Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Updates";                Target = Join-Path $toolsDir "keeper-updates.cmd";           Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Updates (Admin)";        Target = Join-Path $toolsDir "keeper-updates-admin.cmd";     Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Updates Apply (Admin)";  Target = Join-Path $toolsDir "keeper-updates-apply-admin.cmd"; Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Doctor Audio Export";    Target = Join-Path $toolsDir "keeper-doctor-audio.cmd";      Icon = "%SystemRoot%\System32\shell32.dll,168" },
    @{ Name = "Keeper Watch";                  Target = Join-Path $toolsDir "keeper-watch.cmd";             Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Diagnose";               Target = Join-Path $toolsDir "keeper-diagnose.cmd";          Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Export";                 Target = Join-Path $toolsDir "keeper-export.cmd";            Icon = "%SystemRoot%\System32\shell32.dll,21"  },
    @{ Name = "Keeper Listen (Steam Watcher)"; Target = Join-Path $toolsDir "keeper-listen.cmd";            Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Listen (Admin)";         Target = Join-Path $toolsDir "keeper-listen-admin.cmd";      Icon = "%SystemRoot%\System32\shell32.dll,16"  },
    @{ Name = "Keeper Setup";                  Target = Join-Path $rootDir  "setup.cmd";                    Icon = "%SystemRoot%\System32\shell32.dll,21"  }
)

function Ensure-Directory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function New-Shortcut {
    param(
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [Parameter(Mandatory = $true)][string]$TargetPath,
        [string]$IconLocation = "%SystemRoot%\System32\shell32.dll,21"
    )
    $shell    = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath       = $TargetPath
    $shortcut.WorkingDirectory = $rootDir
    $shortcut.IconLocation     = $IconLocation
    $shortcut.Save()
}

function Install-ShortcutsToLocation {
    param([Parameter(Mandatory = $true)][string]$Destination)
    Ensure-Directory -Path $Destination
    foreach ($spec in $shortcutSpecs) {
        if (-not (Test-Path -LiteralPath $spec.Target)) {
            Write-Warning "Skipping missing launcher: $($spec.Target)"
            continue
        }
        $shortcutPath = Join-Path $Destination ($spec.Name + ".lnk")
        New-Shortcut -ShortcutPath $shortcutPath -TargetPath $spec.Target -IconLocation $spec.Icon
        Write-Host ("Created shortcut: {0}" -f $shortcutPath)
    }
}

if (-not $NoDesktop -and -not $StartMenuOnly) {
    Install-ShortcutsToLocation -Destination $desktopDir
}

Install-ShortcutsToLocation -Destination $startMenuDir

Write-Host "Shortcut installation complete."
