# PCB Hand Soldering, Testing & Debug Guide
## ESP32 Encoder Board with Buck Converter

---

## 1. Hand Soldering Tips — Through-Hole Components on Pertinax

### Best Practices
- **Tin your iron tip** frequently with fresh solder (60/40 or lead-free compatible with your board)
- **Heat both the pad and component lead** simultaneously for 2–3 seconds before applying solder
- **Use a damp natural sponge** (not brass wire cleaner—it removes too much tin) to clean your tip
- **Minimum solder joint = shiny, cone-shaped fillet** from pad to lead; avoid dull/grainy appearance
- **Work in a ventilated area** and use solder with rosin core (flux is essential)
- **Temperature:** 350–375°C iron tip for lead-free solder; 320–350°C for 60/40

### Ferro Beads & Decoupling Caps
- **Heat ferrite bead both sides** (0603 or axial) before applying solder—they dissipate heat
- **100nF ceramic caps on encoder signal lines** should be soldered quickly (these are small); use a narrow iron tip
- **Capacitors on power rails** (C1 220μF, C2 100nF at 5V_RAIL junction) are most critical—extra flux helps

### Voltage Dividers (Most Common Weak Point)
- **Two resistors per divider** create multiple joints—solder each resistor lead separately
- **Don't rush:** Apply flux to each pad, heat 2–3 seconds, then add solder
- **Common error:** Insufficient heat → cold joint (dull, grainy, unreliable)
- **Test immediately after soldering:** Probe GPIO with multimeter; should measure 0V or 3.3V when encoder powered

---

## 2. Common Mistakes in 12V ESP32 Encoder Boards

### Power & Protection
| Mistake | Consequence | Fix |
|---------|-------------|-----|
| **DC jack polarity reversed** | Reverse voltage through ESP32, magic smoke | Double-check jack pin labeling (red=+, black/stripe=−); use multimeter before connecting power |
| **Missing reverse polarity MOSFET (Q1)** | No protection; any polarity error kills board | Verify Q1 (AO3401A) is soldered between J4 and 5V_RAIL; test with reversed polarity before powering ESP32 |
| **5V_RAIL cap not soldered flush** | Intermittent crashes, brownouts on load spikes | Ensure C1 (220μF) and C2 (100nF) are soldered solid; probe them with multimeter at 5V after power-on |
| **Ground star point floating** | Noise, encoder counts erratic, Wi-Fi dropout | Verify all GND traces converge at ONE point near C1; use multimeter continuity on all GND leads |
| **Battery modules (TP4056/MT3608) swapped or backwards** | Short circuit, module damage, 5V loss | Verify polarity markings on module silk-screen before soldering; test with standalone module first if unsure |

### Signal Conditioning (Most Critical)
| Mistake | Consequence | Fix |
|---------|-------------|-----|
| **Missing voltage divider on encoder signals** | 5V directly to ESP32 GPIO → internal ESD diode damage, counts miss/misread | Verify all 7 dividers (R1/R2, R3/R4, R5/R6, R7/R8, R9/R10, R11/R12, R13/R14) are present and soldered; measure GPIO voltage: should be ≤3.3V when encoder HIGH |
| **Wrong resistor values in dividers** | GPIO sees 4V+ or only 1V → register as 1 but miss 0s (or vice versa) | Verify values with multimeter or visual inspection; 10k/20k is standard (other combos possible but measure GPIO voltage carefully) |
| **Ferrite beads forgotten** | EMI coupling into signal lines; encoder counts become chaotic with Wi-Fi enabled | Confirm FB1, FB2, FB3 are present on encoder power leads; single bead after screw terminal, before divider network |
| **Signal trace too long or unshielded** | Capacitive coupling from 5V_RAIL or adjacent traces; jitter in quadrature | Route signal traces short & direct from divider junction to ESP32 GPIO; keep traces on top layer if possible; avoid parallel runs |
| **TVS diodes missing or wrong polarity** | No ESD protection; board dies after first cable touch-up | Verify 7x TVS diodes (1.5KE3.3CA) are soldered at each divider output-to-GPIO junction; check cathode band faces GPIO side |

### Encoder Connectors
| Mistake | Consequence | Fix |
|---------|-------------|-----|
| **Screw terminals loose** | Intermittent contact, random encoder dropouts mid-test | Tighten all 3 connectors. v4 order is J1=Wire, J2=Phi, J3=Theta; pull connector off, re-seat, re-tighten. |
| **Encoder wires reversed in connector** | Counts go backwards; worse, A/B swapped creates invalid quadrature | Verify PCB-derived v4 order: Wire A→J1.1, GND→J1.2, B→J1.3, +5V→J1.4; Phi +5V→J2.1, A→J2.2, GND→J2.3, B→J2.4; Theta A→J3.1, GND→J3.2, B→J3.3, +5V→J3.4. Physically reverify before power. |
| **Common ground not connected at board edge** | Encoder floating GND; quadrature counts unreliable | Ensure encoder GND wire connects to J1/J2/J3 GND pin; measure continuity from encoder GND to board GND star point |

### ESP32 Mount & Headers
| Mistake | Consequence | Fix |
|---------|-------------|-----|
| **ESP32 header pins soldered wrong order** | GPIO numbering incorrect; all encoders fail or intermix | Verify header orientation: v4 uses GPIO 7/8 for Wire, 4/5 for Phi, 9/10 for Theta; test with `pio device monitor` and check boot messages |
| **VIN/GND swapped on ESP32** | No power to ESP32 or backwards polarity | Probe VIN pad with multimeter: should be 5V ±0.2V; GND should be 0V; if backwards, LED1 won't light |
| **USB cable too short or damaged** | Serial upload fails; cannot debug | Use proper USB micro-B cable; test with known-good cable first; if upload times out, hold BOOT → RESET → release BOOT, retry |

---

## 3. Testing Procedure for New PCB — Buck Converter + Encoder Interface

### Phase 0: Visual Inspection (Before Power-On)
```
□ Check all 7 voltage divider resistors are present (measure each with ohm-meter if soldered to board)
□ Verify C1 (220μF), C2 (100nF) at 5V_RAIL junction
□ Confirm Q1 (SI2301) + D1 (SS34) reverse polarity protection on DC jack path
□ Check all 3 connectors (J1, J2, J3) are soldered and tightened
□ Verify no solder bridges between adjacent traces (especially on dividers)
□ Confirm ESP32 headers are soldered straight and pins numbered correctly
□ Test point pins (TP1-TP5) should be soldered flush
□ Look for cold joints: dull/grainy solder—these fail randomly
```

### Phase 1: Power Section Test (No encoders, no ESP32 installed yet)

#### 1a. DC Jack Power Path
```bash
# Minimum required hardware:
# - C1 (220μF) and C2 (100nF) soldered at 5V_RAIL
# - D1 and Q1 soldered
# - All GND points wired to central star point
# - Reverse polarity MOSFET Q1 + gate resistor R19

# Apply 5V DC to J4 (red=+, black=−)
# Measure TP1 (should read 5V_RAIL)
# Measure TP5 (should read 0V = GND)
# Measure TP1 − TP5 = should be ~4.8–5.1V

Expected: LED1 lights up (green power LED)
```

#### 1b. Reverse Polarity Test (Critical for 12V boards)
```bash
# DO NOT install ESP32 yet
# Reverse the DC cable polarity (red ↔ black)
# Apply power

Expected: LED1 should NOT light; measure TP1 = 0V (protection working)
Reverse it back, power on → LED1 lights again

If LED1 lights on reversed polarity: Q1 or R19 not soldered or connected
```

#### 1c. Battery Module Test (if TP4056 + MT3608 installed)
```bash
# Connect LiPo battery to J5 (watch polarity!)
# Measure TP4 (LiPo +): should read ~3.7V (if battery is charged)
# Measure TP3 (MT3608 output, before D2): should read ~5.1V

# Optional: Verify auto-charge circuit
#   Connect USB to TP4056 module; measure TP3 again after 5 seconds
#   Should still be ~5V; D3 (1N5817) diode allows external 5V to back-charge

Expected: Both 5V_RAIL and battery paths work independently
```

### Phase 2: ESP32 Mount & Boot Test

#### 2a. Insert ESP32 into Headers
```bash
□ Power off board completely
□ Insert Wemos D1 R32 into female headers with USB port facing right/accessible
□ Ensure all pins are fully seated (no gaps between module and header)
□ Verify no bent pins or socket damage
```

#### 2b. First Power-On with Serial Monitor
```bash
# Set up serial monitor before power
pio device monitor -e wemos_d1_r32 --baud 115200

# Then power on the board
# Expected output within 2 seconds:
#   [0.000] ESP32-S3 (or WROOM-32)
#   [0.123] Starting SphericalSensor
#   [1.500] Zeroing encoders...
#   [2.000] Ready, awaiting commands

Measure TP2 (3.3V rail from ESP32): should read ~3.2–3.3V
```

#### 2c. Command Test (No encoders yet)
```bash
# Type into serial monitor: PING

Expected: 
  PONG

# Type: STATUS

Expected:
  THETA=0 PHI=0 WIRE=0 (all counts zero, 3.3V present)
```

### Phase 3: Individual Encoder Tests

#### 3a. Draw-Wire Encoder (DWEM2)
```bash
# v4: connect only draw-wire to J1; leave J2 and J3 unconnected
# Apply external 5V to encoder (see wiring in setup_test_guide.md)
# Upload v4 main firmware:
#   pio run -e esp32s3_v4 --target upload
#   pio device monitor -e esp32s3_v4

# Expected: DATA/SENSOR radius changes while pulling wire.

If COUNT = 0 always:
  □ Check GPIO 7/8 are receiving 0V/3.3V when encoder powered
  □ Verify external 5V supply is actually powering encoder
  □ Test voltage dividers with multimeter: 5V → ~3.3V at GPIO
```

#### 3b. Theta Rotary Encoder (E40S6)
```bash
# v4: connect only theta to J3; leave J1 and J2 unconnected
# Apply external 5V to encoder
# Upload v4 main firmware:
#   pio run -e esp32s3_v4 --target upload
#   pio device monitor -e esp32s3_v4

# Expected: DATA/SENSOR theta changes while rotating theta.

If THETA_counts = 0:
  □ Verify GPIO 9/10 toggling with multimeter (should see 0V/3.3V alternating)
  □ Check ferrite FB1 is not broken
  □ Confirm R1/R2 divider resistors are soldered
```

#### 3c. Phi Rotary Encoder (E40S6)
```bash
# Connect only phi to J2; leave J1 and J3 unconnected
# Apply external 5V to encoder
# Upload v4 main firmware:
#   pio run -e esp32s3_v4 --target upload
#   pio device monitor -e esp32s3_v4

# Expected: DATA/SENSOR phi changes while rotating phi.
```

### Phase 4: Full Integration Test

#### 4a. Connect All Three Encoders
```bash
# Wire all 3 encoders to their connectors (J1, J2, J3)
# Upload main firmware:
#   pio run -e wemos_d1_r32 --target upload

# Expected at boot:
#   [2.0s] Zeroing encoders...
#   [3.0s] DATA,0.0,0.0,0.0,0.0,0.0,0.0,1.0  (x=0, y=0, z=0 at home)

# Move robot axes:
#   - Pull draw-wire: z increases (mm)
#   - Rotate theta: x/y change, spherical angle theta changes
#   - Rotate phi: z component changes, spherical angle phi changes
```

#### 4b. Test ZERO Command
```bash
# Send: ZERO

Expected:
  [*] ZERO received
  [*] Spherical zero point set
  [*] Ready for motion

# Subsequent DATA frames should start from all zeros again
```

---

## 4. Debug Checklist for First Power-On

### If Board Does NOT Boot

**Symptom:** No serial output, LED1 not lit

| Check | Command / Method | Expected | Action if Failed |
|-------|------------------|----------|------------------|
| **5V_RAIL present** | Multimeter: TP1 to TP5 | ~5V | Check Q1 reverse polarity MOSFET; verify D1 is not reversed; test DC jack with reversed polarity (should block—see Phase 1b) |
| **3.3V rail present** | Multimeter: TP2 to TP5 | ~3.3V | ESP32 not receiving power from VIN; check VIN solder joint and trace from 5V_RAIL |
| **ESP32 USB detected** | `lsusb` on PC | "ESP32" or "USB UART" device | ESP32 not seated in headers; remove and re-insert with proper alignment; check USB cable |
| **ESP32 reset pin** | Multimeter between RST and GND | Voltage should toggle on press | Reset button not soldered or broken; tap button lightly to feel click |
| **Reverse polarity damage** | Visual inspection | No burnt components near Q1, D1 | If detected, MOSFET or diode failed during incorrect polarity insertion; replace Q1 and D1 |

### If Serial Monitor Shows Garbage

**Symptom:** Serial output is random characters, not recognizable text

| Check | Fix |
|-------|-----|
| **Baud rate wrong** | Ensure monitor is 115200 baud: `pio device monitor -e wemos_d1_r32 --baud 115200` |
| **USB cable issue** | Try a different USB micro-B cable; known-good cable only |
| **ESP32 COM port wrong** | List ports: `ls /dev/ttyUSB* /dev/ttyACM*`; confirm correct port in upload |

### If Encoder Counts Stay Zero

**Symptom:** `COUNT=0` always, even when moving encoder

| GPIO | Encoder | Debug | Expected |
|------|---------|-------|----------|
| **7** (Wire A) | Draw-wire A line | Multimeter to GPIO 7 while pulling wire | Toggle 0V ↔ 3.3V |
| **8** (Wire B) | Draw-wire B line | Multimeter to GPIO 8 while pulling wire | Toggle 0V ↔ 3.3V (opposite phase to GPIO 7) |
| **9** (Theta A) | Rotary A | GPIO 9 during rotation | Smooth quadrature pattern (1, 0 alternating) |
| **10** (Theta B) | Rotary B | GPIO 10 during rotation | 90° out of phase with GPIO 9 |
| **4** (Phi A) | Rotary A | GPIO 4 during rotation | Smooth quadrature pattern |
| **5** (Phi B) | Rotary B | GPIO 5 during rotation | 90° out of phase with GPIO 4 |

**If GPIO not toggling:**
1. Check encoder is powered (measure encoder +5V)
2. Verify common GND between encoder and ESP32 board
3. Probe *before* divider (at encoder cable): should see 5V swings
4. Probe *after* divider (at GPIO): should see 3.3V swings
5. If input is 5V but GPIO stuck at 3.3V or 0V: **divider resistor open or wrong value**

### If Encoder Counts Go Backwards

**Symptom:** Pulling wire decreases COUNT; rotating theta CW decreases counts

| Encoder | Fix |
|---------|-----|
| Draw-wire (J1) | Swap A ↔ B wires on J1 terminal block |
| Theta (J3) | Swap A ↔ B wires on J3 terminal block |
| Phi (J2) | Swap A ↔ B wires on J2 terminal block |

### If Counts Jump Randomly

**Symptom:** COUNT increases/decreases by random amounts, not smooth transitions

| Cause | Check | Fix |
|-------|-------|-----|
| **Common GND missing** | Multimeter continuity from encoder GND pin to board TP5 | Solder encoder GND wire to J connector GND pad; verify continuity to main GND bus |
| **Loose screw terminal** | Wiggle each J1/J2/J3 connector | Tighten with small screwdriver; pull connector off and re-seat firmly |
| **Cold solder joint in divider** | Probe GPIO with meter while moving encoder; watch for sudden voltage dips | Re-heat and re-solder suspect divider resistor joints (dull/grainy appearance) |
| **Ferrite bead broken** | Visual inspection of FB1/FB2/FB3 | If cracked, replace ferrite bead |
| **Wi-Fi interference** | Disable Wi-Fi in firmware (`ENABLE_WIFI = 0`) | If counts stabilize, add shielding or move board away from router |

### If One Encoder Works but Others Don't

| Scenario | Likely Cause | Fix |
|----------|--------------|-----|
| **Theta works, Phi doesn't** | Wrong GPIO or divider not soldered | Verify GPIO 4/5 are receiving correct voltage (multimeter); check the J2 divider parts. |
| **Wire works, both rotary encoders fail** | GPIOs 4/5/9/10 not connected or miswired | Re-check ESP32 header pins match silk-screen; use `STATUS`/serial output to confirm axis changes. |
| **Only one channel of rotary works** | One quadrature line missing | Verify both A and B wires are connected to J connector; measure both GPIO outputs |

### If Board Powers Off When Encoders Connected

**Symptom:** Supply current spikes; board resets

| Cause | Fix |
|-------|-----|
| **Encoder drawing too much current** | External 5V supply undersized (use ≥500mA); verify LED1 is dim but on |
| **Short circuit in divider or connector** | Visual inspection for solder bridges between signal and GND pins; use multimeter continuity check between adjacent J connector pins |
| **External 5V supply poor quality** | Replace with known-good bench supply; verify 5V output is clean (oscilloscope if available) |

### If Battery Module Doesn't Charge

**Symptom:** Multimeter shows 0V on TP3 (MT3608 output) or TP4 (battery) always

| Check | Expected | Action |
|-------|----------|--------|
| **TP4056 module powered** | Multimeter TP1 (5V_RAIL) = 5V | If 0V, fix 5V_RAIL first (Phase 1a) |
| **Battery connected** | Multimeter TP4 (battery +) = 3.7–4.2V | Confirm JST-PH connector J5 is soldered and battery is inserted |
| **MT3608 module output** | Multimeter TP3 should read ~5V when LiPo connected | If 0V: MT3608 module may be defective; test in isolation on bench power |
| **Auto-charge diode D3** | Multimeter: apply 5V to J4, measure TP3 | Should read ~5V; if not, D3 may be reversed or failed |

---

## 5. Final Validation Checklist

```
□ All 3 encoders report correct counts in both directions
□ ZERO command resets all counters reliably
□ Serial output stable at 115200 baud, no dropouts
□ No voltage spikes or oscillation on 5V_RAIL (scope)
□ All test points (TP1-TP5) accessible and labeled
□ Board operates with battery power (if TP4056/MT3608 present)
□ Reverse polarity protection tested (reversed DC jack → no damage)
□ Wi-Fi connection stable (if ENABLE_WIFI=1)
□ Temperature measurement stable on thermistor (if present)
□ No audible buzzing or clicking from regulators
□ LED1 (power) and LED2 (battery low, if present) work correctly
```

---

## References

- **Individual Hardware Test Plan:** `docs/hardware_design/assembly/individual_hardware_test_plan.md`
- **Setup & Test Guide:** `docs/integration/setup_test_guide.md`
- **PCB Layout Guide:** `docs/hardware_design/5v/pcb_layout_guide.md`
- **Reverse Polarity Protection:** `docs/hardware_design/assembly/REVERSE_POLARITY_PROTECTION.md`
- **Bill of Materials:** `docs/hardware_design/5v/bill_of_materials.md`

---

*Last Updated: 2026-04-05*
*Firmware Version: SphericalSensor v2.0+*
*Target Hardware: ESP32 Wemos D1 R32 on pertinax board*
