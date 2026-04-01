# Repository Path Resolver - Usage Guide

## Overview

The `repo_path_resolver` provides centralized, configurable path resolution for
the multi-repository NuSyQ ecosystem. It eliminates hardcoded paths and improves
portability across different development environments.

## Quick Start

### Basic Usage

```python
from src.utils.repo_path_resolver import get_repo_path

# Get repository paths
hub_path = get_repo_path('NUSYQ_HUB_ROOT')
nusyq_path = get_repo_path('NUSYQ_ROOT')
sim_path = get_repo_path('SIMULATEDVERSE_ROOT')

# Use in your code
config_file = hub_path / 'config' / 'secrets.json'
chatdev_path = nusyq_path / 'ChatDev'
temple_path = sim_path / 'src' / 'temple'
```

### String Paths

```python
from src.utils.repo_path_resolver import get_repo_path_str

# Get path as string (useful for subprocess calls)
hub_str = get_repo_path_str('NUSYQ_HUB_ROOT')
subprocess.run(['python', 'script.py'], cwd=hub_str)
```

### Validation

```python
from src.utils.repo_path_resolver import validate_all_paths, print_paths

# Validate all paths exist
validation = validate_all_paths()
if not all(validation.values()):
    print("⚠️ Some repositories not found!")
    print(validation)

# Print diagnostic info
print_paths()
```

## Configuration Priority

The resolver uses this priority order (highest to lowest):

1. **Environment Variables** (highest priority)

   - `NUSYQ_ROOT`
   - `NUSYQ_HUB_ROOT`
   - `SIMULATEDVERSE_ROOT`

2. **nusyq.manifest.yaml** (repository_paths section)

   ```yaml
   repository_paths:
     NUSYQ_ROOT: '%USERPROFILE%/NuSyQ'
     NUSYQ_HUB_ROOT: '%USERPROFILE%/Desktop/Legacy/NuSyQ-Hub'
     SIMULATEDVERSE_ROOT: '%USERPROFILE%/Desktop/SimulatedVerse/SimulatedVerse'
   ```

3. **Hardcoded Defaults** (fallback)
   - `NUSYQ_ROOT`: `C:/Users/<you>/NuSyQ`
   - `NUSYQ_HUB_ROOT`: `C:/Users/<you>/Desktop/Legacy/NuSyQ-Hub`
   - `SIMULATEDVERSE_ROOT`:
     `C:/Users/<you>/Desktop/SimulatedVerse/SimulatedVerse`

## Environment Variable Override

For different deployment environments (CI/CD, other developers, containers):

### PowerShell

```powershell
$env:NUSYQ_ROOT = "D:/Projects/NuSyQ"
$env:NUSYQ_HUB_ROOT = "D:/Projects/NuSyQ-Hub"
$env:SIMULATEDVERSE_ROOT = "D:/Projects/SimulatedVerse"
```

### Bash/Linux

```bash
export NUSYQ_ROOT="/home/user/NuSyQ"
export NUSYQ_HUB_ROOT="/home/user/NuSyQ-Hub"
export SIMULATEDVERSE_ROOT="/home/user/SimulatedVerse"
```

### .env File

```env
NUSYQ_ROOT=D:/Projects/NuSyQ
NUSYQ_HUB_ROOT=D:/Projects/NuSyQ-Hub
SIMULATEDVERSE_ROOT=D:/Projects/SimulatedVerse
```

## Migration from Hardcoded Paths

### Before (hardcoded):

```python
from pathlib import Path

HUB_PATH = Path("C:/Users/<you>/Desktop/Legacy/NuSyQ-Hub")
NUSYQ_ROOT = Path("C:/Users/<you>/NuSyQ")
SIMULATEDVERSE_ROOT = Path("C:/Users/<you>/Desktop/SimulatedVerse/SimulatedVerse")
```

### After (portable):

```python
from src.utils.repo_path_resolver import get_repo_path

HUB_PATH = get_repo_path('NUSYQ_HUB_ROOT')
NUSYQ_ROOT = get_repo_path('NUSYQ_ROOT')
SIMULATEDVERSE_ROOT = get_repo_path('SIMULATEDVERSE_ROOT')
```

## Advanced Usage

### Custom Manifest Path

```python
from pathlib import Path
from src.utils.repo_path_resolver import RepositoryPathResolver

# Use custom manifest location
resolver = RepositoryPathResolver(
    manifest_path=Path('/custom/path/nusyq.manifest.yaml')
)
hub_path = resolver.get_path('NUSYQ_HUB_ROOT')
```

### Get All Paths

```python
from src.utils.repo_path_resolver import get_all_paths

all_repos = get_all_paths()
for repo_name, repo_path in all_repos.items():
    print(f"{repo_name}: {repo_path}")
```

### Validation in Scripts

```python
from src.utils.repo_path_resolver import validate_all_paths
import sys

# Validate before proceeding
validation = validate_all_paths()
missing = [key for key, exists in validation.items() if not exists]

if missing:
    print(f"❌ Missing repositories: {', '.join(missing)}")
    print("Please configure repository paths in nusyq.manifest.yaml")
    sys.exit(1)

# Continue with script...
```

## Diagnostic CLI

Run the path resolver standalone for diagnostics:

```bash
python src/utils/repo_path_resolver.py
```

Output example:

```
🗺️ Repository Path Resolver - Diagnostic Mode
============================================================

📄 Manifest: C:\Users\keath\NuSyQ\nusyq.manifest.yaml

RepositoryPathResolver:
  ✓ NUSYQ_HUB_ROOT: C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
  ✓ NUSYQ_ROOT: C:\Users\keath\NuSyQ
  ✓ SIMULATEDVERSE_ROOT: C:\Users\keath\Desktop\SimulatedVerse\SimulatedVerse

📊 Validation: 3/3 repositories found

🌍 Environment Variable Overrides:
  - NUSYQ_ROOT (not set)
  - NUSYQ_HUB_ROOT (not set)
  - SIMULATEDVERSE_ROOT (not set)

✅ Path resolver diagnostic complete
```

## Testing

```python
# Reset singleton for testing
from src.utils.repo_path_resolver import RepositoryPathResolver

RepositoryPathResolver.reset_instance()

# Create test resolver with custom paths
import os
os.environ['NUSYQ_ROOT'] = '/tmp/test-nusyq'
resolver = RepositoryPathResolver.get_instance()

# Verify
assert str(resolver.get_path('NUSYQ_ROOT')) == '/tmp/test-nusyq'
```

## Benefits

✅ **Portability**: Works across different environments without code changes  
✅ **Centralized**: Single source of truth for repository paths  
✅ **Flexible**: Environment variables override manifest, manifest overrides
defaults  
✅ **Type-Safe**: Returns `pathlib.Path` objects  
✅ **Validated**: Built-in validation to check paths exist  
✅ **Documented**: Clear error messages for missing configurations

## Related Files

- Implementation: `src/utils/repo_path_resolver.py`
- Configuration: `C:/Users/<you>/NuSyQ/nusyq.manifest.yaml` (repository_paths
  section)
- Scripts to migrate: See Phase 1.5 todo (20+ files with hardcoded paths)

## Support

For issues or questions, refer to:

- `AGENTS.md` - Agent navigation and recovery protocol
- `docs/Checklists/PROJECT_STATUS_CHECKLIST.md` - Development progress tracking
