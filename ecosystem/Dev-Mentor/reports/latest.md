# DevMentor Ops Report

Generated: `2026-03-21T17:44:37.387850`

## Summary

- **doctor**: ✅ Environment healthy. All core systems operational.
- **check**: ❌ Checked 121 Python, 5315 JSON, 433 Markdown files. Found 3 errors. 2 warnings.
- **prune**: ✅ Found 9 potential bloat issues.

**Total**: 12 failures, 5 warnings

## Failures

- [check] .vscode\extensions.json: Expecting value: line 3 column 5 (char 29)
- [check] .vscode\settings.json: Expecting property name enclosed in double quotes: line 13 column 3 (char 396)
- [check] state\codex_probe\app_server_schema.json: Expecting value: line 1 column 1 (char 0)
- [prune] state\serena_memory.db: Large file: 22.0MB
- [prune] .mypy_cache\3.12\numpy\__init__.data.json: Large file: 6.2MB
- [prune] .mypy_cache\3.12\builtins.data.json: Large file: 1.9MB
- [prune] app\game_engine\__pycache__\commands.cpython-311.pyc: Large file: 1.7MB
- [prune] app\game_engine\commands.py: Large file: 1.4MB
- [prune] : Duplicate content in 4 files
- [prune] : Empty directory
- [prune] : Empty directory
- [prune] : Empty directory

## Suggestions

1. Run: python scripts/devmentor_bootstrap.py start
2. Consider compressing or moving large files
3. Review and consolidate duplicate files

## Next Actions

1. Fix any failures listed above
2. Review and address warnings
3. Run `ops check` after fixes to verify
4. Run `ops export` to create portable backup
