param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "release") { Remove-Item "release" -Recurse -Force }
New-Item -ItemType Directory -Path "release" | Out-Null

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Procesos AM" --icon "app_procesos/assets/logo.ico" --add-data "app_procesos/assets;app_procesos/assets" --add-data "MANUAL_EQUIPO.html;." --additional-hooks-dir "pyinstaller_hooks" "main.py"

if (-not (Test-Path "dist/Procesos AM.exe")) {
    throw "PyInstaller no generó dist/Procesos AM.exe"
}

& "$env:ProgramFiles(x86)\NSIS\makensis.exe" "/DAPP_VERSION=$Version" "build\installer.nsi"

$manifest = [ordered]@{
    version = $Version
    fecha = (Get-Date -Format "yyyy-MM-dd")
    instalador = "INSTALADOR_PROCESOS_AM_V2.exe"
    mensaje = "PlayOps Suite $Version: corrección del monitoreo para clientes migrados a AWS."
}
$manifest | ConvertTo-Json | Set-Content "release/version.json" -Encoding utf8

if (-not (Test-Path "release/INSTALADOR_PROCESOS_AM_V2.exe")) {
    throw "NSIS no generó el instalador"
}

Get-FileHash "release/INSTALADOR_PROCESOS_AM_V2.exe" -Algorithm SHA256 | Select-Object Algorithm, Hash | Format-List | Out-File "release/SHA256.txt" -Encoding utf8
