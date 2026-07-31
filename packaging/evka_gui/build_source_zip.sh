#!/usr/bin/env bash
# Build the portable GUI zip: Python source that runs on any OS with Python 3.10+.
#
# This is the companion to build_windows.ps1. That one produces an 84 MB bundle with
# a frozen interpreter and can only be built on Windows; this one is ~200 KB, builds
# anywhere, and is the only option for Linux and macOS operators.
#
# git archive is doing the real work: it emits exactly the tracked files at HEAD, so
# __pycache__, .venv, local recordings and anything else gitignored cannot leak into
# a release artifact. Do not replace it with `zip -r` or `cp`.
#
#   ./packaging/evka_gui/build_source_zip.sh [version]
#
# Writes EvkaGUI-src-v<version>.zip to the repo root and verifies it by running the
# GUI out of a clean extraction.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# Default to the package version so this cannot silently drift from pyproject.toml.
VERSION="${1:-$(python3 - <<'PY'
import re, pathlib
print(re.search(r'^version = "([^"]+)"',
                pathlib.Path("pyproject.toml").read_text(), re.M).group(1))
PY
)}"
NAME="EvkaGUI-src-v${VERSION}"
ZIP="$ROOT/${NAME}.zip"

# Every package tools/evka_gui imports, directly or transitively. Verified with:
#   grep -rhoE '^from tools\.[a-z_.]+' tools/*/*.py
PATHS=(
  tools/__init__.py
  tools/evka_gui
  tools/position_checker
  tools/ipt
  tools/calibration
  tools/remote_tester
  requirements.txt
  pyproject.toml
  README.md
)

# git archive --add-file places the file at the archive root under its basename, so
# the temp file has to actually be named RUN.txt (--add-file-with-path needs git 2.44+).
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
RUNTXT="$STAGE/RUN.txt"
cat > "$RUNTXT" <<EOF
EVKA Position GUI ${VERSION} — portable source build
=====================================================

Runs on Windows, Linux and macOS. Requires Python 3.10 or newer.
If you want a Windows build with no Python at all, use EvkaGUI-win64-v${VERSION}.zip
from the same release instead.

1. Install the dependencies (once):

     python -m venv .venv
     # Windows:      .venv\\Scripts\\activate
     # Linux/macOS:  source .venv/bin/activate
     pip install -r requirements.txt

2. Run the GUI from THIS folder (the one containing "tools"):

     python -m tools.evka_gui

   Connect to the device with one of:

     python -m tools.evka_gui --tcp 192.168.1.50
     python -m tools.evka_gui --ws  192.168.1.50
     python -m tools.evka_gui --serial COM3          (Windows)
     python -m tools.evka_gui --serial /dev/ttyUSB0  (Linux)

   Replay a recorded session with no hardware:

     python -m tools.evka_gui --replay my_session.csv

Session exports (saved points and snapshots) include the individual encoder
readings as wire_mm, theta_deg and phi_deg. A blank cell means no reading was
available for that row, which is not the same as a reading of 0.0.

On Linux, PyQt5 may need system Qt libraries: apt install python3-pyqt5
EOF

echo "== building ${NAME}.zip from tracked files at HEAD"
rm -f "$ZIP"
git archive --format=zip --prefix="${NAME}/" --add-file="$RUNTXT" \
  -o "$ZIP" HEAD -- "${PATHS[@]}"

# Verify by running it, not by trusting it: a zip that imports cleanly but whose
# entry point is broken is worse than no zip.
echo "== smoke test: launch the GUI from a clean extraction"
TMP="$(mktemp -d)"
trap 'rm -rf "$STAGE" "$TMP"' EXIT
python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$ZIP" "$TMP"
python3 - "$TMP/$NAME" <<'PY'
import subprocess, sys, time, os
root = sys.argv[1]
env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=root)
p = subprocess.Popen([sys.executable, "-m", "tools.evka_gui"], cwd=root, env=env,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(6)
if p.poll() is not None:
    print("FAIL — GUI exited early:\n" + p.communicate()[0])
    sys.exit(1)
p.terminate()
try:
    p.wait(timeout=10)
except subprocess.TimeoutExpired:
    p.kill()
print("PASS — GUI started and stayed up from the extracted zip")
PY

echo
echo "Built: $ZIP ($(du -h "$ZIP" | cut -f1))"
