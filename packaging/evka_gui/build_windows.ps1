# build_windows.ps1 — build the EVKA Position GUI into dist\EvkaGUI\ and zip it.
#
# Run from the REPO ROOT on Windows:
#     powershell -ExecutionPolicy Bypass -File packaging\evka_gui\build_windows.ps1
#
# PyInstaller is not a cross-compiler: it bundles a native CPython plus the Qt
# DLLs, so this must run on Windows. Building from Linux is not supported.

param(
    [string]$Python  = "py -3.12",
    [string]$Version = "0.2.1",
    [switch]$Console          # also build the console variant for support
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Repo root = two levels up from this script.
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
Write-Host "Repo root: $Root"

# A clean venv matters: PyInstaller bundles whatever it can find, so a fat dev
# environment silently becomes a fat executable.
$Venv = Join-Path $Root ".venv-build"
if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
Invoke-Expression "$Python -m venv `"$Venv`""

$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --upgrade pip
& $Py -m pip install -e .
& $Py -m pip install pyinstaller

# Pre-flight. PyInstaller does NOT fail when an optional import is missing - it
# logs "missing module ... (optional)" and produces a bundle that launches fine
# and only breaks when the user clicks that feature. ws_client.py deliberately
# degrades on a missing QtWebSockets, so nothing downstream would catch it
# either. Verified on Linux, where the distro splits QtWebSockets into its own
# package: the build silently produced a WebSocket-less app. Fail loudly here.
Write-Host "Pre-flight: checking imports in the build venv..."
# Literal here-string (@'...'@): PowerShell must not interpolate anything here.
& $Py -c @'
import sys
missing = []
for mod in ("PyQt5.QtWebSockets", "PyQt5.QtNetwork", "PyQt5.QtWidgets",
            "pyqtgraph", "numpy", "serial.tools.list_ports",
            "serial.tools.list_ports_windows"):
    try:
        __import__(mod)
    except ImportError as exc:
        missing.append("%s: %s" % (mod, exc))
if missing:
    sys.exit("MISSING IMPORTS:\n  " + "\n  ".join(missing))
print("  all required imports OK")
'@
if ($LASTEXITCODE -ne 0) { throw "Pre-flight import check failed - fix the venv before building" }

if (Test-Path (Join-Path $Root "dist")) { Remove-Item -Recurse -Force (Join-Path $Root "dist") }

& $Py -m PyInstaller --noconfirm --clean packaging\evka_gui\evka_gui.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

if ($Console) {
    $env:EVKA_CONSOLE = "1"
    & $Py -m PyInstaller --noconfirm --clean packaging\evka_gui\evka_gui.spec
    Remove-Item Env:\EVKA_CONSOLE
    if ($LASTEXITCODE -ne 0) { throw "Console build failed" }
}

# Post-build: the bundle must actually start. Replay mode needs no hardware.
Write-Host "Post-flight: launching the frozen app for 8 s..."
& $Py packaging\evka_gui\make_replay_csv.py "$env:TEMP\evka_frames.csv"
$proc = Start-Process -FilePath (Join-Path $Root "dist\EvkaGUI\EvkaGUI.exe") `
    -ArgumentList "--replay", "$env:TEMP\evka_frames.csv" -PassThru
Start-Sleep -Seconds 8
if ($proc.HasExited) {
    throw "App exited within 8 s (code $($proc.ExitCode)). Check %LOCALAPPDATA%\evka_position\crash.log"
}
Stop-Process -Id $proc.Id -Force
Write-Host "  app stayed up - OK"

# The user-facing note ships inside the folder, next to the exe.
Copy-Item packaging\evka_gui\README-WINDOWS.txt (Join-Path $Root "dist\EvkaGUI\")

$Zip = Join-Path $Root "EvkaGUI-win64-v$Version.zip"
if (Test-Path $Zip) { Remove-Item $Zip }
Compress-Archive -Path (Join-Path $Root "dist\EvkaGUI\*") -DestinationPath $Zip

$SizeMb = [math]::Round((Get-Item $Zip).Length / 1MB, 1)
Write-Host ""
Write-Host "Built: $Zip ($SizeMb MB)"
Write-Host "Now smoke-test on a clean Windows machine with no Python installed."
