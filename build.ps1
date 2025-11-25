# build.ps1
param(
  [string]$Name = "w0rmw00d"
)

# Create & activate venv
python -m venv .venv
# dot-source the activation script for PowerShell
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
} else {
    Write-Error "Activation script not found. Ensure Python created the venv."
    exit 1
}

python -m pip install --upgrade pip
pip install pygame pyinstaller

# Build using the spec (one-dir, debug)
pyinstaller --noconfirm --clean --onedir --console --debug=all w0rmw00d.spec

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Build complete: dist\$Name\$Name.exe"   