# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for QELP (Quick ESXi Log Parser) - ONEFILE BUILD
Single executable file for maximum portability
"""

import os
from pathlib import Path

# Get project root and version info
project_root = Path(SPECPATH)
src_path = project_root / "src" / "qelp"

a = Analysis(
    ['src/qelp/esxi_to_csv.py'],
    pathex=[str(src_path)],
    binaries=[],
    datas=[],
    hiddenimports=['art'],  # Ensure art library for ASCII banners
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'matplotlib', 'numpy', 'scipy', 'pandas'
    ],
    noarchive=False,
    optimize=1,  # Optimize bytecode
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='qelp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols for smaller size
    upx=True,   # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)