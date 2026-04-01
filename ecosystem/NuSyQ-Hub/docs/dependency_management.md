# Dependency Management

To update and lock dependencies for this project, use the provided script:

```bash
./scripts/update_dependencies.sh
```

The script uses [`pip-compile`](https://github.com/jazzband/pip-tools) to refresh pinned versions in `requirements.txt` and generates `requirements-dev.txt` for optional development dependencies defined in `pyproject.toml`.
