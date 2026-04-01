$cfgPath = Join-Path $PSScriptRoot "..\\config\\model_paths.json"
$dirs = @()

if (Test-Path $cfgPath) {
    try {
        $cfg = Get-Content -Path $cfgPath -Raw | ConvertFrom-Json
        if ($cfg.search_dirs) {
            foreach ($d in $cfg.search_dirs) {
                $dirs += $d.Replace('${USERPROFILE}', $env:USERPROFILE)
            }
        }
    } catch {
        Write-Warning "Failed to parse config/model_paths.json; falling back to defaults."
    }
}

if (-not $dirs -or $dirs.Count -eq 0) {
    $dirs = @(
        "$env:USERPROFILE\\.lmstudio\\models",
        "$env:USERPROFILE\\.ollama\\models",
        "$env:USERPROFILE\\Downloads",
        "C:\\models",
        "D:\\models",
        "D:\\gguf",
        "E:\\gguf"
    )
}

foreach ($d in $dirs) {
    Write-Host "--- $d"
    if (Test-Path $d) {
        $found = Get-ChildItem -Path $d -Filter *.gguf -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 5
        if ($found) {
            $found | ForEach-Object { Write-Host $_.FullName }
        } else {
            Write-Host "No .gguf files found under $d"
        }
    } else {
        Write-Host "MISSING"
    }
}
