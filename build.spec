# -*- mode: python ; coding: utf-8 -*-
import os

# Get absolute paths
workspace = os.getcwd()
src_path = os.path.join(workspace, 'src')
assets_path = os.path.join(workspace, 'assets')
config_path = os.path.join(workspace, 'config')

block_cipher = None

a = Analysis(
    [os.path.join(src_path, 'main.py')],
    pathex=[workspace],
    binaries=[],
    datas=[
        (os.path.join(src_path, 'ui'), 'src/ui'),
        (os.path.join(src_path, 'core'), 'src/core'),
        (os.path.join(src_path, 'utils'), 'src/utils'),
        (assets_path, 'assets'),
        (config_path, 'config')
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pandas',
        'numpy'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='trading_bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True temporarily for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(assets_path, 'icon.ico')
) 