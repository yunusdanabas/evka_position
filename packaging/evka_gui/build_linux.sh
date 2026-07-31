#!/usr/bin/env bash
# build_linux.sh — validate the PyInstaller spec without a Windows machine.
#
#     ./packaging/evka_gui/build_linux.sh
#
# This produces a LINUX binary, which is not the shippable artifact. Its purpose
# is to exercise the spec, the import graph and the frozen-path code cheaply:
# those are where a first freeze actually fails, and they are platform-agnostic.
# It found the pyqtgraph/PyOpenGL startup crash that the Windows build would
# otherwise have hit (see the OpenGL note in evka_gui.spec).
#
# What it CANNOT tell you: Qt-on-Windows DLLs, COM ports, SmartScreen, or
# whether PyQt5.QtWebSockets is present in your Windows venv.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

OUT="${EVKA_BUILD_DIR:-/tmp/evka-speccheck}"
VENV="$OUT/venv"

if [[ ! -x "$VENV/bin/python" ]]; then
    echo "== creating build venv at $VENV"
    # --system-site-packages reuses the distro PyQt5/numpy instead of downloading
    # ~100 MB of wheels. It also makes the venv "dirty" on purpose, which is how
    # the PyOpenGL contamination was reproduced.
    python3 -m venv --system-site-packages "$VENV"
    "$VENV/bin/pip" install -q pyinstaller
fi

echo "== building"
"$VENV/bin/python" -m PyInstaller --noconfirm --clean \
    --distpath "$OUT/dist" --workpath "$OUT/build" \
    packaging/evka_gui/evka_gui.spec

echo "== smoke test: launch the frozen app in replay mode"
python3 packaging/evka_gui/make_replay_csv.py "$OUT/frames.csv"

# The app runs until killed, so "still alive at the timeout" is the pass
# condition: timeout(1) exits 124 when it had to terminate the process.
set +e
QT_QPA_PLATFORM=offscreen timeout 8 "$OUT/dist/EvkaGUI/EvkaGUI" --replay "$OUT/frames.csv"
rc=$?
set -e

if [[ $rc -eq 124 ]]; then
    echo "PASS — app stayed up (spec and import graph are sound)"
    echo "Bundle: $(du -sh "$OUT/dist/EvkaGUI" | cut -f1) at $OUT/dist/EvkaGUI"
else
    echo "FAIL — app exited early with code $rc"
    echo "Missing-module report: $OUT/build/evka_gui/warn-evka_gui.txt"
    exit 1
fi
