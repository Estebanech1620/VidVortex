# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['vidvortex_app.py'],
    pathex=[],
    binaries=[],
    datas=[('yt-dlp.conf.example', '.'), ('profiles.json.example', '.'), ('queue.json.example', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VidVortexByEstebanech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\esteb\\OneDrive\\Desktop\\Desktop\\Dev\\MUSIC DOWNLOAD\\VidVortex\\app_logo.ico'],
)
