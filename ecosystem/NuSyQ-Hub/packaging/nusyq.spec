# PyInstaller spec for NuSyQ Control Center
block_cipher = None

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root = Path('.').resolve()
entry = root / "scripts" / "nusyq_launcher.py"

hidden = collect_submodules("src") + collect_submodules("scripts")

a = Analysis(
    [str(entry)],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "docs"), "docs"),
        (str(root / "state"), "state"),
    ],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="nusyq",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="nusyq",
)
