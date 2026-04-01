<#
Package and install local VS Code extensions present in the workspace.
This script finds extension package folders (those containing package.json with 'engines.vscode')
and packages them using npx vsce package (requires Node.js and npm). It will then install the
packaged vsix using the `code` CLI.
#>

param (
    [string]$WorkspaceRoot = "$(Get-Location)"
)

Write-Host "Scanning for local VS Code extension directories under $WorkspaceRoot..." -ForegroundColor Cyan

$candidateDirs = Get-ChildItem -Path $WorkspaceRoot -Recurse -Force -Directory -ErrorAction SilentlyContinue | Where-Object {
    test-path (Join-Path -Path $_.FullName -ChildPath "package.json")
}

foreach ($d in $candidateDirs) {
    $pkgJsonPath = Join-Path -Path $d.FullName -ChildPath "package.json"
    $pkg = Get-Content $pkgJsonPath -Raw | ConvertFrom-Json
    if ($pkg.engines -and $pkg.engines.vscode) {
        # It's a VS Code extension project
        Write-Host "Found local extension: $($pkg.name) at $($d.FullName)" -ForegroundColor Green
        Push-Location $d.FullName
        try {
            if (Get-Command -Name npm -ErrorAction SilentlyContinue) {
                Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
                & npm install --no-audit --no-fund | Out-Null
            }
            Write-Host "Packaging extension with npx vsce..." -ForegroundColor Yellow
            $r = & npx -y vsce package 2>&1
            if ($LASTEXITCODE -eq 0) {
                # Find vsix (most recent)
                $vsix = Get-ChildItem -Path $d.FullName -Filter "*.vsix" -Recurse | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                if ($vsix) {
                    Write-Host "Installing vsix: $($vsix.FullName)" -ForegroundColor Yellow
                    & code --install-extension $vsix.FullName --force
                }
            } else {
                Write-Warning "Failed to package extension: $r"
            }
        } catch {
            Write-Warning "Packaging/install failed: $_"
        } finally {
            Pop-Location
        }
    }
}

Write-Host "Done. If packaging fails, open the extension in VS Code and press F5 or install a vsix manually." -ForegroundColor Green
