$cfgPath = Join-Path $PSScriptRoot "..\config\model_paths.json"
$cfg = Get-Content -Path $cfgPath -Raw | ConvertFrom-Json
$dirs = @()
foreach ($d in $cfg.search_dirs) { $dirs += $d.Replace('${USERPROFILE}', $env:USERPROFILE) }
$lmDir = $cfg.lmstudio_models_dir.Replace('${USERPROFILE}', $env:USERPROFILE)
$python = 'C:\\Users\\keath\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
& $python (Join-Path $PSScriptRoot "sync_ollama_to_lmstudio.py") --ollama-base http://localhost:11434 --lmstudio-dir $lmDir --search-dirs $dirs
