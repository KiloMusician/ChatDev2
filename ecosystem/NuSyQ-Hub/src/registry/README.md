# NuSyQ Model Registry

This folder contains a tiny Model Registry API and helpers.

Run the registry API (development):

```powershell
# from repo root
python -m src.registry.run_api
```

Start as a background service (Windows PowerShell helper):

```powershell
# from repo root
.\scripts\run_registry_service.ps1
```

POST examples (dry-run / apply):

```powershell
# dry-run (will not persist)
Invoke-RestMethod -Method POST -Uri 'http://127.0.0.1:8700/register' -Body (@{path='/models/gpt-oss-20b.gguf'; name='gpt-oss-20b'; provider='lmstudio'; format='gguf'; size_bytes=123456; apply=$false} | ConvertTo-Json) -ContentType 'application/json'

# apply (persist)
Invoke-RestMethod -Method POST -Uri 'http://127.0.0.1:8700/register' -Body (@{path='/models/gpt-oss-20b.gguf'; name='gpt-oss-20b'; provider='lmstudio'; format='gguf'; size_bytes=123456; apply=$true} | ConvertTo-Json) -ContentType 'application/json'
```

Rollback helper:

```powershell
python scripts/rollback_registration.py --path 'C:\path\to\model' --yes
```
