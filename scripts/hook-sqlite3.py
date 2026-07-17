# PyInstaller hook for sqlite3
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

hiddenimports = collect_submodules('sqlite3')
binaries = collect_dynamic_libs('sqlite3')

# On Windows, also collect the sqlite3.dll
import os, glob
python_dir = os.path.dirname(os.path.dirname(__import__('sqlite3').__file__))
dlls_dir = os.path.join(python_dir, 'DLLs')
if os.path.exists(dlls_dir):
    for f in glob.glob(os.path.join(dlls_dir, 'sqlite3.*')):
        binaries.append((f, '.'))
    for f in glob.glob(os.path.join(dlls_dir, '_sqlite3.*')):
        binaries.append((f, '.'))
