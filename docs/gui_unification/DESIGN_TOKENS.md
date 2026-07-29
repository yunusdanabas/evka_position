# EVKA Operator UI — Design Tokens & Action Vocabulary

The two operator UIs — the PyQt5 desktop (`tools/evka_gui/`) and the firmware web
dashboard (`firmware/src/WebDashboard.cpp`) — are used roughly equally, often by the
same person in the same session. They must read as one product.

Qt cannot render HTML components, so **nothing below is shared code**. What is shared
is the spec: the colour roles, the type/spacing scale, and one canonical name per
action. Each UI implements them natively.

> Source of truth for this doc is the doc itself. When a UI disagrees with it, the UI
> is wrong. New UI must be built against it; existing UI is retrofitted in Phase 3.

---

## 1. Colour roles

The web already had a coherent HUD palette. The desktop was a hybrid — Flat-UI colours
(`#27ae60`, `#c0392b`, `#f39c12`, `#2980b9`) fighting HUD colours (`#00ff88`, `#ff4444`)
inside the same window. **The HUD palette wins**: it is what the field operator sees on
the phone, and it is the one that was internally consistent.

| Role | Hex | Use | Replaces on desktop |
|---|---|---|---|
| `ok` | `#00ff88` | Success, connected, live, go-actions (ARM, CONNECT, APPLY) | `#27ae60` |
| `danger` | `#ff4444` | Destructive + hardware-affecting (ZERO (HW), CLEAR, DISCONNECT, DELETE) | `#c0392b` |
| `warn` | `#ffd700` | Caution, marginal fit, frozen, reconnecting, RAM-only state | `#f39c12`, `#e67e22` |
| `accent` | `#00ffff` | Headings, live values, focus, the primary read-out | `#00bcd4` |
| `info` | `#4488ff` | Neutral emphasis, Z axis, links | `#2980b9` |
| `ipt` | `#00ff88` | IPT capture cloud (same green as `ok`) | — |
| `ipt-target` | `#ff8c00` | The solved IPT point P + its sphere | `#ff6600` |
| `muted` | `#8899aa` | Secondary labels, hints, units | `#7f8c8d`, `#aaaaaa` |
| `text` | `#eef` | Primary text | `#e0e0e0` |
| `bg-deep` | `#0a0a1a` | Inputs, wells, recessed surfaces | — |
| `bg-canvas` | `#0f0f23` | 3D / plot backgrounds | — |
| `bg-panel` | `#1a1a2e` | Panel + window chrome | — |
| `border` | `#2a3550` | Dividers, card edges | — |

Axis colours are **not** themeable — they are a physical convention and already agree:
X `#ff4444`, Y `#00ff88`, Z `#4488ff`.

## 2. Type & spacing

- **Monospace everywhere for numbers.** A position that shifts width as it counts is
  unreadable. Both UIs already do this; keep it.
- Type scale: `10 / 12 / 14 / 16 / 20 / 28 px`. 16 px is the floor for any web
  `<input>` — below that, iOS Safari zooms the page on focus.
- Spacing scale: `4 / 8 / 12 / 16 / 24 px`.
- **Touch targets ≥ 44 px** on the web (the dashboard is used on a phone). The desktop
  may go smaller; it has a mouse.

## 3. Action vocabulary — one name per action

Same action, same name, both UIs. The table fixes three real defects:

1. The desktop shipped **raw protocol tokens as button labels** (`SAVE_POINT`,
   `DEL_POINT`). The wire format is not operator-facing language.
2. The web called the same concept **two different things** — `SAVE ORIGIN` in the
   session panel, `SET ORIGIN` in the endpoint calibration tab.
3. A bare **`CLEAR`** appeared in the web's CONTROL block meaning "clear the trail",
   colliding with `CLEAR` elsewhere meaning "clear the table".

| Action | Canonical label | Role | Was (web) | Was (desktop) |
|---|---|---|---|---|
| Re-zero all encoders (firmware `ZERO`) | `ZERO (HW)` | danger | `ZERO (HW)` | `Hardware ZERO` |
| Zero the client-side display offsets | `ZERO (SW)` | warn | `ZERO (SW)` | `Software Zero (All)` |
| Drop those offsets | `CLEAR SW ZERO` | muted | `CLEAR` (ambiguous) | `Clear SW Zero` |
| Store a point on the device | `SAVE POINT` | ok | `SAVE POINT` | `SAVE_POINT` ✗ |
| Remove the last stored point | `DEL LAST POINT` | danger | `DEL LAST POINT` | `DEL_POINT` ✗ |
| Mark the session origin | `SET ORIGIN` | ok | `SAVE ORIGIN` / `SET ORIGIN` ✗ | `Set Origin` |
| Forget the session origin | `CLEAR ORIGIN` | muted | — | `Clear Origin` |
| Empty the 3D trail | `CLEAR TRAIL` | muted | `CLEAR` (ambiguous) ✗ | `Clear Trail` |
| Reset per-axis extremes | `RESET MIN/MAX` | muted | `RESET MIN/MAX` | `Reset Min/Max` |
| Capture a manual point | `CAPTURE SNAPSHOT` | ok | `CAPTURE` | `Capture Snapshot` |
| Pause the position stream | `FREEZE` | warn | `FREEZE` | `Freeze` |
| Flash the status LED | `BLINK LED` | info | `BLINK LED` | `Blink LED` |
| Apply calibration to RAM | `APPLY (RAM)` | warn | `APPLY (RAM)` | `APPLY (RAM)` |
| Apply + persist to flash | `APPLY + SAVE (NVS)` | ok | `APPLY + SAVE (NVS)` | `APPLY + SAVE (NVS)` |
| Begin an IPT sweep | `ARM` | ok | *(new)* | `ARM` |
| End the sweep | `STOP` | warn | *(new)* | `STOP` |
| Fit the hidden point | `SOLVE` | accent | *(new)* | `SOLVE` |
| Start writing the stream to file | `RECORD` | danger | *(new)* | *(new)* |

**Casing rule.** Action buttons — commands aimed at the machine — are `ALL CAPS` in
both UIs. Window chrome, menus and toolbar entries keep each platform's idiom: Title
Case with an ellipsis on the desktop (`Calibration…`), all-caps in the web's HUD header.
Unifying the *chrome* would make the desktop feel like a kiosk; unifying the *actions*
is what lets an operator move between the two without re-learning.

## 4. State colour semantics

Both UIs signal connection and data state constantly. Same state, same colour:

| State | Colour |
|---|---|
| Connected / live | `ok` |
| Frozen, reconnecting, RAM-only calibration, marginal fit | `warn` |
| Disconnected, invalid frame, rejected fit | `danger` |
| Idle / never connected | `muted` |

An invalid frame (`is_valid == 0`) turns the X/Y/Z read-outs `danger` in both UIs
already. Keep that — it is the single most important state on the screen.
