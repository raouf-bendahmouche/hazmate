# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for License Management System

import sys
from PyInstaller.utils.hooks import get_module_file_attribute

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('db/schema.sql', 'db'),
        ('ui', 'ui'),
        ('notifications', 'notifications'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
    ],
    hookspath=[],
    hooksconfig={
        'PyQt5': {'qt_plugins': ['platforms', 'imageformats', 'styles']},
    },
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LicenseManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
