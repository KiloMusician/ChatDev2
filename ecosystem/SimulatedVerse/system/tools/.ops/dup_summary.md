# ΞNuSyQ Duplicate Consolidation Report
Generated: 2025-08-27T16:55:17.540325

## Summary Statistics
- **Total Files Analyzed**: 500
- **Duplicate Groups Found**: 0
- **Empty Files**: 6
- **Placeholder Files**: 36
- **Vague-Named Files**: 0

## Duplicate/Near-Duplicate Groups


## Empty/Placeholder Files

| Path | Type | Size | Action |
|------|------|------|--------|
| `.pythonlibs/lib/python3.11/site-packages/numpy/compat/tests/__init__.py` | Empty | 0 | Delete or expand |
| `.pythonlibs/lib/python3.11/site-packages/numpy/_pyinstaller/__init__.py` | Empty | 0 | Delete or expand |
| `.pythonlibs/lib/python3.11/site-packages/numpy/random/tests/data/__init__.py` | Empty | 0 | Delete or expand |
| `.pythonlibs/lib/python3.11/site-packages/numpy/linalg/tests/__init__.py` | Empty | 0 | Delete or expand |
| `.pythonlibs/lib/python3.11/site-packages/numpy/fft/tests/__init__.py` | Empty | 0 | Delete or expand |
| `structures/temple_of_knowledge/floor_05/ledger.json` | Empty | 3 | Delete or expand |
| `temple_boot.py` | Placeholder | 16264 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/_typing/_dtype_like.py` | Placeholder | 5661 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/_compositor.py` | Placeholder | 40308 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/modula2.py` | Placeholder | 53062 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/widgets/__init__.py` | Placeholder | 3006 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/ma/tests/test_old_ma.py` | Placeholder | 32690 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/felix.py` | Placeholder | 9655 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/sql.py` | Placeholder | 41476 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/gleam.py` | Placeholder | 2392 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/core/tests/test_casting_unittests.py` | Placeholder | 34295 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/widgets/_text_area.py` | Placeholder | 84970 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/textedit.py` | Placeholder | 7760 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/core/numeric.py` | Placeholder | 77014 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/templates.py` | Placeholder | 75731 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/demo.py` | Placeholder | 11000 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/python.py` | Placeholder | 53805 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/formatters/latex.py` | Placeholder | 19258 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/graphics.py` | Placeholder | 39145 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/widgets/_input.py` | Placeholder | 27966 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/lib/tests/test_function_base.py` | Placeholder | 157830 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/_animator.py` | Placeholder | 20192 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/core/tests/test_machar.py` | Placeholder | 1067 | Complete implementation |
| `src/nusyq-framework/scp-containment.ts` | Placeholder | 16021 | Complete implementation |
| `scripts/ztp-demo.py` | Placeholder | 2748 | Complete implementation |
| `ui_ascii/widgets/minimap.py` | Placeholder | 9070 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/numpy/array_api/_set_functions.py` | Placeholder | 2948 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/mips.py` | Placeholder | 4656 | Complete implementation |
| `sidecar/bootstrap.py` | Placeholder | 7236 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/itsdangerous/timed.py` | Placeholder | 8083 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/textual/widgets/_welcome.py` | Placeholder | 1519 | Complete implementation |
| `engine/cascade_event.py` | Placeholder | 2188 | Complete implementation |
| `agent/quest_runner.ts` | Placeholder | 7155 | Complete implementation |
| `client/src/components/ui/input.tsx` | Placeholder | 791 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/javascript.py` | Placeholder | 63235 | Complete implementation |
| `.pythonlibs/lib/python3.11/site-packages/pygments/lexers/scripting.py` | Placeholder | 81795 | Complete implementation |
| `quests/qbook.yml` | Placeholder | 6798 | Complete implementation |

## Implementation Plan

1. **Backup Phase**: Copy affected files to `.ops/backups/{timestamp}/`
2. **Rename Phase**: Apply file renames using `git mv`
3. **Merge Phase**: Consolidate duplicate content into primary files
4. **Import Phase**: Update all import statements and path references
5. **Test Phase**: Run lints and tests to verify no breakage
6. **Commit Phase**: Atomic commits with clear messages
