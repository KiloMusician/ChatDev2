<#
Installs workspace recommended VS Code extensions for all repositories under workspace roots.
This script uses the `code` CLI (VS Code) so ensure `code` is on your PATH (VSCode: 'Shell Command: Install 'code' command in PATH').
This should be run in a local developer machine (not recommended for CI jobs unless headless 'code' is available).
#>

param (
    [string]$WorkspaceRoot = "$(Get-Location)",
    [switch]$InstallOptional = $false
)

function Install-ExtensionsFromFile {
    param(
        [string]$file
    )
    if (Test-Path $file) {
        $raw = Get-Content $file -Raw
        # Remove single-line comments (// comments) to support JSONC content reliably
        $rawClean = $raw -replace "//.*", ""
        $json = $rawClean | ConvertFrom-Json
        if ($null -ne $json.recommendations) {
            foreach ($ext in $json.recommendations) {
                Write-Host "Installing extension: $ext" -ForegroundColor Green
                try {
                    & code --install-extension $ext --force
                } catch {
                    Write-Warning ([string]::Format("Failed to install {0}: {1}", $ext, $_.Exception.Message))
                }
            }
        }
        if ($InstallOptional) {
            # Install all properties that appear to be optional/extra recommendation arrays
            foreach ($prop in $json.PSObject.Properties) {
                $propName = $prop.Name
                if ($propName -match "Optional|optional|terminalRecommendations|ollama") {
                    $arr = $prop.Value
                    if ($arr -and $arr.GetType().Name -eq 'Object[]') {
                        foreach ($ext in $arr) {
                            if ($ext -and -not [string]::IsNullOrWhiteSpace($ext)) {
                                Write-Host "Installing optional extension [$propName]: $ext" -ForegroundColor DarkCyan
                                try {
                                    & code --install-extension $ext --force
                                } catch {
                                    Write-Warning ([string]::Format("Failed to install optional {0} from ${propName}: {1}", $ext, $_.Exception.Message))
                                }
                            }
                        }
                    }
                }
            }
        }
        # Support for local extension directories defined as localRecommendations or localExtensions in extensions.json (non-standard)
        if ($null -ne $json.localRecommendations -or $null -ne $json.localExtensions) {
            $localList = @()
            if ($null -ne $json.localRecommendations) { $localList += $json.localRecommendations }
            if ($null -ne $json.localExtensions) { $localList += $json.localExtensions }
            foreach ($localExtPath in $localList) {
                # Resolve path relative to the extensions.json parent
                $parentDir = Split-Path -Parent $file
                $absPath = Join-Path -Path $parentDir -ChildPath $localExtPath
                if (-not (Test-Path $absPath)) {
                    Write-Warning "Local extension not found: $absPath"
                    continue
                }
                # Try to package the extension with vsce (npx vsce package) or install directly if a .vsix already exists
                $vsixCandidates = Get-ChildItem -Path $absPath -Filter "*.vsix" -Recurse -ErrorAction SilentlyContinue
                if ($vsixCandidates.Count -gt 0) {
                    foreach ($vsix in $vsixCandidates) {
                        Write-Host "Installing local extension (vsix): $($vsix.FullName)" -ForegroundColor Yellow
                        try {
                            & code --install-extension $vsix.FullName --force
                        } catch {
                            Write-Warning ([string]::Format("Failed to install local vsix {0}: {1}", $vsix.FullName, $_.Exception.Message))
                        }
                    }
                } else {
                    # If no vsix, attempt to package with npx vsce if Node.js/npm is available
                    $packSuccess = $false
                    try {
                        Write-Host "Packaging local extension at: $absPath" -ForegroundColor Cyan
                        Push-Location $absPath
                        if (Get-Command -Name vsce -ErrorAction SilentlyContinue) {
                            $r = & vsce package --allow-missing-repository 2>&1
                        } elseif (Get-Command -Name npm -ErrorAction SilentlyContinue) {
                            # Try via npx @vscode/vsce; if not installed, npx will try to fetch it
                            & npm install --no-audit --no-fund | Out-Null
                            $r = & npx -y @vscode/vsce package --allow-missing-repository 2>&1
                        } else {
                            Write-Warning "npm not found. Cannot package local extension. Install vsce and use the packaged vsix or open the extension for development mode in VS Code."
                            $r = ""
                        }
                        $lastCode = $LASTEXITCODE
                        Pop-Location
                        if ($lastCode -eq 0) {
                            # Find the created vsix
                            $vsix = Get-ChildItem -Path $absPath -Filter "*.vsix" -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                            if ($vsix) {
                                Write-Host "Installing packaged local extension: $($vsix.FullName)" -ForegroundColor Yellow
                                & code --install-extension $vsix.FullName --force
                                $packSuccess = $true
                            }
                        } else {
                            Write-Warning "vsce packaging failed. Output: $r"
                        }
                    } catch {
                        Write-Warning "Failed to package/install local extension: $_"
                    }
                    if (-not $packSuccess) {
                        Write-Host "Tip: To install this local extension manually, open it in VS Code and press F5 (Run Extension) or package it with npx vsce package and run: code --install-extension <path>.vsix" -ForegroundColor Gray
                    }
                }
            }
        }
    }
}

Write-Host "Scanning for .vscode/extensions.json files under $WorkspaceRoot..."
$files = Get-ChildItem -Path $WorkspaceRoot -Recurse -Filter extensions.json -ErrorAction SilentlyContinue
foreach ($f in $files) {
    Write-Host "Found: $($f.FullName)" -ForegroundColor Cyan
    Install-ExtensionsFromFile -file $f.FullName
}

Write-Host "Done. If you need to install additional OS-level tooling (like Ruff in the venv), run the setup script or install packages manually." -ForegroundColor Green
