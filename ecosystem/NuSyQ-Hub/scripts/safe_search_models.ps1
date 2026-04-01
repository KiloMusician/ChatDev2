$pattern = $args[0]
$dirs = $args[1..($args.Length-1)]
if (-not $pattern) { Write-Error "Usage: .\safe_search_models.ps1 <pattern> <dir1> [dir2 ...]"; exit 2 }

if (-not $dirs -or $dirs.Count -eq 0) {
    $cfgPath = Join-Path $PSScriptRoot "..\\config\\model_paths.json"
    if (Test-Path $cfgPath) {
        try {
            $cfg = Get-Content -Path $cfgPath -Raw | ConvertFrom-Json
            if ($cfg.search_dirs) {
                $dirs = @()
                foreach ($d in $cfg.search_dirs) {
                    $dirs += $d.Replace('${USERPROFILE}', $env:USERPROFILE)
                }
            }
        } catch {
            Write-Warning "Failed to parse config/model_paths.json; use explicit dirs."
        }
    }
}

foreach ($d in $dirs) {
    Write-Host "--- Searching: $d for pattern '$pattern' ---"
    if (-not (Test-Path $d)) { Write-Host "MISSING: $d"; continue }
    try {
        Get-ChildItem -Path $d -Directory -Recurse -ErrorAction SilentlyContinue |
            Where-Object Name -match $pattern |
            Select-Object -First 200 | ForEach-Object { Write-Host $_.FullName }
    } catch {
        Write-Host ("Search failed for {0}: {1}" -f $d, $_.Exception.Message)
    }
}
