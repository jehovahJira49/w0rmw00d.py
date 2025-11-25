# PyInstaller spec to include background.png and keep console; edit paths if needed.
# Run: pyinstaller w0rmw00d.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

script = "seed.py"
base_path = str(Path(".").resolve())

# include app assets + pygame data files
datas = [(str(Path("background.png")), ".")]
datas += collect_data_files("pygame")  # collect pygame data/assets

# include pygame submodules as hidden imports to avoid missing imports at runtime
hidden_imports = collect_submodules("pygame")

a = Analysis(
    [script],
    pathex=[base_path],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="w0rmw00d",
    debug=True,            # keep debug info in bootloader
    strip=False,
    upx=False,
    console=True,          # show console for debugging
)