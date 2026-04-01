Register local LLM models with LM Studio

This small utility helps register already-downloaded GGUF models with LM Studio
by creating directory junctions (Windows) or symlinks (POSIX) into LM Studio's
models folder.

Usage (dry-run):

```powershell
python scripts/register_local_models.py --search-dirs "C:\\models" "D:\\gguf" --lmstudio-dir "C:\\Users\\keath\\.lmstudio\\models"
```

To actually create links, add `--apply`:

```powershell
python scripts/register_local_models.py --search-dirs "C:\\models" "D:\\gguf" --lmstudio-dir "C:\\Users\\keath\\.lmstudio\\models" --apply --http-ping "http://localhost:1234/v1/models"
```

Notes:

- The script will attempt a native symlink first and fall back to creating a
  junction using PowerShell on Windows.
- Do NOT copy large model files; junctions/symlinks avoid duplication.
- If LM Studio is running with Just-In-Time model loading, the new models should
  appear in the GET /v1/models response; otherwise restart LM Studio.
- If you omit `--search-dirs`, the script will read `config/model_paths.json`
  and expand `${USERPROFILE}` automatically.
- Prefer `scripts/discover_and_sync_models.py` for full discovery + API query + sync.

PowerShell / wrapper note:

- When running PowerShell one-liners via automation or remote wrappers (VS Code
  tasks, run*in_terminal helpers), the
  `$*`automatic variable can be mangled by shell quoting and may disappear leading to errors like`The
  term '.Name' is not recognized`.
- To avoid this, prefer the safe `Where-Object Name -match '<pattern>'` form or
  run scripts (ps1 files) instead of embedding `$_` in ad-hoc quoted commands.
- You can also use the provided `scripts\safe_search_models.ps1` which uses safe
  `Where-Object` syntax and limits output.
