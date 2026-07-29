"""tokens.py — the EVKA operator-UI design tokens, Qt side.

The canonical spec is ``docs/gui_unification/DESIGN_TOKENS.md``; the web dashboard
carries the same values in a CSS ``:root`` block. Keep the three in step — the doc is
the source of truth when they disagree.

New UI uses these names. Existing hard-coded hexes are retrofitted in Phase 3.
"""

from __future__ import annotations

# -- roles ---------------------------------------------------------------------
OK = "#00ff88"           # success, connected, live, go-actions
DANGER = "#ff4444"       # destructive + hardware-affecting
WARN = "#ffd700"         # caution, frozen, reconnecting, RAM-only
ACCENT = "#00ffff"       # headings, live values, the primary read-out
INFO = "#4488ff"         # neutral emphasis
IPT = "#00ff88"          # IPT capture cloud
IPT_TARGET = "#ff8c00"   # solved IPT point P + its sphere
MUTED = "#8899aa"        # secondary labels, hints, units
TEXT = "#eef"            # primary text

# -- surfaces ------------------------------------------------------------------
BG_DEEP = "#0a0a1a"      # inputs, wells
BG_CANVAS = "#0f0f23"    # 3D / plot backgrounds
BG_PANEL = "#1a1a2e"     # panel + window chrome
BORDER = "#2a3550"       # dividers, card edges

# -- axes (physical convention, not themeable) ---------------------------------
AXIS_X = "#ff4444"
AXIS_Y = "#00ff88"
AXIS_Z = "#4488ff"

# -- state -> colour -----------------------------------------------------------
STATE_LIVE = OK
STATE_BUSY = WARN        # frozen, reconnecting, marginal
STATE_DOWN = DANGER      # disconnected, invalid frame, rejected fit
STATE_IDLE = MUTED

# -- scales --------------------------------------------------------------------
TYPE_SCALE = (10, 12, 14, 16, 20, 28)
SPACE_SCALE = (4, 8, 12, 16, 24)
