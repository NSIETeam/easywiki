# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for OrgMind v2.1 — single-file executable"""
import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH).parent  # scripts/ -> OrgMind root

a = Analysis(
    [str(ROOT / 'orgmind' / 'main_sqlite.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'frontend' / 'dist'), 'frontend/dist'),
        (str(ROOT / 'frontend' / 'dist' / 'assets'), 'frontend/dist/assets'),
        (str(ROOT / 'orgmind'), 'orgmind'),
        (str(ROOT / 'README.md'), '.'),
    ],
    hiddenimports=[
        'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        'fastapi', 'fastapi.middleware', 'fastapi.middleware.cors',
        'starlette', 'starlette.middleware',
        'sentence_transformers', 'sentence_transformers.models',
        'jieba', 'jieba.finalseg', 'jieba.posseg',
        'bcrypt', 'numpy', 'numpy.core', 'numpy.linalg',
        'openai', 'tenacity', 'pyjwt',
        'pydantic', 'pydantic.deprecated',
        'transformers', 'torch',
        'huggingface_hub',
        'tqdm', 'PIL', 'PIL.Image',
        'scipy', 'scipy.sparse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'pandas', 'IPython',
        'jupyter', 'notebook', 'sqlalchemy', 'redis',
        'celery', 'kafka', 'pytest', 'setuptools',
    ],
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
    name='OrgMind',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'frontend' / 'dist' / 'icon.svg') if (ROOT / 'frontend' / 'dist' / 'icon.svg').exists() else None,
)
