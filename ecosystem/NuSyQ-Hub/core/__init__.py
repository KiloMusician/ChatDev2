import os
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_src_core = str(_repo_root / "src" / "core")
if os.path.isdir(_src_core):
    __path__.insert(0, _src_core)
