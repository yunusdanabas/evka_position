# Version B — Built-In Fixed Laser Module Shortlist

**Parent doc:** [`README.md`](README.md) — Version B use case (permanently mounted module on the phi head, no operator handling, automation-first).

**Fixed requirement (2026-07-01, revised):** range ≤ 40 m, laser device accuracy ≤ 10 mm (target sub-cm) across that full range, device's own datasheet spec. No tiers.

**2026-07-01 addendum:** extended research pass (assisted by a Copilot CLI research agent) swept 13 industrial automation sensor manufacturers to find phase-shift alternatives to Dimetix. Found 5 qualifying candidates (§3) and — just as usefully — a documented list of 11 manufacturers/product lines that turned out to be the wrong technology (§3.2), so they don't get re-researched later.

---

## 1. The Previous Primary Pick (TF02-i-RS485) No Longer Qualifies

This is the headline change from the prior research pass. TF02-i-RS485 and every other Benewake ToF module in that shortlist (TF03, TFmini-S/Plus) measure distance via **pulsed time-of-flight** — direct round-trip pulse timing — which tops out at ±5 cm at short range and ±1% of reading at long range (±400 mm at 40 m). That's 5–40× over the ≤10 mm budget. This isn't a marginal miss; it's a different measurement technique that was never going to hit this spec. See `version_a_handheld_devices.md` §1 for the phase-shift vs. pulsed-ToF physics explanation.

**These modules are kept below only as explicitly excluded reference entries** — they were the right answer under the old tiered framework's Tier 2/3, but not under the current fixed spec.

## 2. Primary Recommendation: Dimetix Industrial Phase-Shift Sensors

| Specification | Value |
|---|---|
| Technology | Phase-shift (AMCW) — same principle as the handheld candidates in Version A, packaged as an industrial fixed-mount sensor |
| Range | **Confirmed SKUs (2026-07-08)** — the exact 40 m-class D-Series parts are the **DAE-10-050** (P/N 500633) and **DBN-50-050** (P/N 500635), both 50 m max on natural surfaces (25% margin over the 40 m requirement). Resolves the long-standing "which current SKU?" open risk. |
| Accuracy | **DAE-10-050: ±1 mm @2σ** (10× margin under the ≤10 mm budget); **DBN-50-050: ±5 mm @2σ** (still passes ≤10 mm, at roughly half the price — the budget Dimetix entry) |
| Sample rate | 20 Hz normal (DAE up to ~50–100 Hz fast mode) |
| Interface | RS232 (single device) or RS422/RS485 (multi-drop), plus USB; DAE-10-050 also offers 4–20 mA analog |
| Protocol | **Public** Dimetix D-Series ASCII command set, `<cr><lf>`-terminated (in the technical reference manual — **the only fully-documented byte-level protocol in this study**, and the lowest integration risk; **not** Modbus RTU, unlike the now-excluded TF02-i) |
| **Price (confirmed, Dimetix's own shop)** | **DBN-50-050: CHF 1,076 / ~$1,332**; **DAE-10-050: CHF 2,298–2,699 / ~$2,700–2,844 / ~126,394 TRY**. Accessories: reflective target plate CHF 72, EtherNet/IP interface module CHF 620. |
| Turkey / LCSC / AliExpress | Swiss OEM — ordered via `shop.dimetix.com` or an EU distributor (Laser-View Technologies, Eurolase); TR dealers **Megasensor** and **Ulusat** carry the D-Series |

**Pros:** by far the most accuracy margin (±1 mm vs. a ±10 mm requirement) and range margin (rated well past 40 m) of any Version B candidate; industrial housing, IP-rated variants exist; mature, documented protocol.
**Cons:** an order of magnitude more expensive than the excluded ToF modules or the Version A OEM modules; no fast domestic sourcing; RS422 (not RS-485/Modbus) needs a different transceiver family than the MAX485 already discussed for the old TF02-i plan — see §4.

## 3. Extended Shortlist — 2026-07-01 Research Addendum

All confirmed phase-shift/AMCW (or a documented phase-shift+runtime hybrid) via manufacturer datasheets, not just product-family naming — several of these vendors also sell short-range triangulation and long-range pulsed-ToF sensors under confusingly similar model numbers, so the "confirmed tech" column matters as much as the numbers.

| Brand/Model | Confirmed Tech | Range | Accuracy (flat) | Interface | Price | Availability |
|---|---|---|---|---|---|---|
| **Micro-Epsilon optoNCDT ILR2250 / ILR3800** ⭐ | Phase-shift (phase comparison) | up to 100 m (no reflector) / 150 m (reflector) | ILR2250: ±1 mm linearity; ILR3800: <±1 mm linearity, <300 µm repeatability; ILR2250 up to **333 Hz** | RS422/USB native; PROFINET/EtherNet-IP/IO-Link via IF2030/IF2035 adapter | **ILR2250: ~$1,800 / ~84,294 TRY (ESTIMATE, 2026-07-08)**; ILR3800 quote-only | Direct from Micro-Epsilon (Germany); TR dealers İmaj Teknik, Simtekno. The confirmed phase-comparison pick — **use these, not the ILR11xx line** |
| **Micro-Epsilon optoNCDT ILR1171/1181/1191** ⚠ | **Pulsed ToF (correction, 2026-07-08)** — survey-2 confirms the older ILR1171/1191 branch is *pulse runtime*, not phase comparison | 0.1–30/80/150 m | ±2–5 mm | RS232/RS422 | Quote-only | **Rejected / verify per-SKU** — the ILR118x sub-parts' principle is not cleanly confirmed as phase; do not treat this line as a phase-shift candidate (see §3.2) |
| **WayCon LDI** ⭐ | Hybrid: coarse runtime + fine phase-shift | 0.05–100 m (natural surfaces) / up to 500 m (reflective foil) | ±1 mm linearity, ±0.3 mm repeatability, 50 Hz | 0–20/4–20 mA analog, RS232/RS422/RS485/SSI, optional Profinet/EtherNet/EtherCAT swap-cap | Quote-only | WayCon Positionsmesstechnik (Germany); compact IP65 housing (140×78×48 mm), –40…+60°C — best-specified industrial candidate of the addendum |
| **Jenoptik LDM41 / LDM4x series** | Phase comparison (AMCW) | 150 m (reflector) / **~30 m natural surfaces ⚠** — the 150 m headline needs a reflective target | ≤3 mm flat | RS232/RS422/Profibus/SSI, up to 50 Hz | **~$1,500 / ~70,245 TRY (ESTIMATE, 2026-07-08)** | Jenoptik (Germany), traces to the MEL Mikroelektronik acquisition; Edmund Optics / global. Reflector dependency is a near-miss risk for a flat 0–40 m bar |
| **FAE LS 121 FA / LS 122 FA** **[NEW]** | Comparative phase measurement | 50 m | ±3 mm | LS 121: RS232 / LS 122: RS422 (ASCII, M18 12-pole connector) | **~$1,400 / ~65,562 TRY (ESTIMATE, 2026-07-08)** | FAE Srl (Italy), rugged IP65 aluminium; EU import (Customs-Union tariff advantage over Asian imports), 50 Hz |
| **Scantron SLS** | Comparative phase measurement | 0.1–30 m (natural) / 100+ m (reflector) | ±3 mm (+15…+30°C) / ±5 mm (wide temp) / best-case ±2 mm | RS232/RS422 + 4–20 mA analog + switching output | Quote-only | Scantron Industrial Products (UK) — specs closely mirror the Jenoptik/MEL-class devices, possibly a rebadge of a German OEM core; worth confirming before ordering |

⭐ = notable: **Micro-Epsilon ILR2250/ILR3800** is the best pure-accuracy industrial pick found (±1 mm linearity to 100–150 m, roughly matching Dimetix but from a different manufacturer — useful as a second-source/backup quote). **WayCon LDI** is the most flexible industrial candidate — compact IP65 housing, the widest interface menu of anything in this study (analog, three serial standards, and swappable industrial fieldbus caps), and a documented hybrid measurement approach that explains its tight ±1 mm/±0.3 mm spec despite covering 100–500 m.

### 3.1 Flagged — Phase-Based but Fails the Accuracy Spec

| Device | Tech | Why it's flagged, not recommended |
|---|---|---|
| **Leuze ODSL 30** | Phase + propagation-time hybrid (genuinely phase-based) | Published accuracy is **percentage-of-full-scale** (2% close range / 1% long range), not flat mm — at 10–30 m that's ≈±100–300 mm, an order of magnitude over the ≤10 mm budget. Included here as a caution: not every "phase-based" industrial sensor is flat-mm accurate — the measurement *principle* alone doesn't guarantee the spec, the *published accuracy figure* does. Widely stocked and cheaper than Dimetix, which makes it a tempting near-miss — don't order it for this application. |

### 3.2 Rejected Manufacturers/Product Lines (documented so they aren't re-researched)

| Manufacturer / Line | Confirmed reality | Verdict |
|---|---|---|
| SICK (DT35/DT50/DL100/Dx100/DME3000/DME4000) | HDDM+ — SICK's own statistical *pulsed* ToF technology (multi-pulse averaging), explicitly not phase/AMCW per SICK's own whitepaper; **Dx100 = ToF cross-confirmed 2026-07-08** | Reject — brand has no phase-shift product in this catalog generation |
| **Micro-Epsilon optoNCDT ILR1171 / ILR1191** (2026-07-08 correction) | Pulsed ToF / pulse-runtime, **not** phase comparison — corrects an earlier assumption that the ILR11xx line was phase-shift | Reject — wrong tech; use the phase-comparison **ILR2250 / ILR3800** (§3) instead |
| SICK OD Value / OD Precision | Short-range laser triangulation, 24–700 mm | Reject — wrong range class |
| Banner Engineering (LT3, LTF) | Pulsed ToF ("one million pulses/second, averages 1000 pulses") | Reject |
| Wenglor | Long-range line is transit-time (pulsed ToF); high-precision line is triangulation capped ≤1 m; no "OCT" family actually exists in their catalog | Reject |
| Balluff BOD | BOD6K/BOD23K = time-of-flight; BOD21M/BOD63M = triangulation, capped 2–6 m | Reject |
| Contrinex | "Laser distance" products are photoelectric presence/switching sensors, not distance-measurement instruments | Reject — wrong product category entirely |
| Riftek RF603/RF605 | Optical triangulation, 2–1250 mm | Reject — already-excluded category |
| di-soric LAT-45 | Tops out at 10 m; technology not confirmed as phase-based in the literature | Reject — range |
| Acuity / Schmitt Industries AR700 | Triangulation, short range | Reject — already-excluded category |
| Pepperl+Fuchs VDM28 | "Pulse Ranging Technology" (PRT), ±25 mm absolute accuracy | Reject — tech and accuracy |
| Baumer OM70 | High-precision triangulation, 30–1500 mm | Reject — tech and range |
| ifm O1D | Genuinely phase-of-modulated-light (pmd) — architecturally close to AMCW — but the clean-reading SKU (O1D300) caps at 10 m, and longer-range 75 m-class SKUs suffer phase-wraparound ambiguity beyond ~19.2 m on most parts | **Inconclusive, not a confirmed candidate** — would need per-SKU datasheet verification before treating as viable |
| Jenoptik LDM7x | Also phase-based (same brand as the LDM4x candidate above) | Reject — published accuracy is only ≤60 mm, too coarse |
| Jenoptik LDM301/302 | Despite adjacent naming to the LDM4x winner, confirmed pulsed transit-time, not phase | Reject — same-family-different-tech trap, worth remembering when evaluating any vendor's product range |

## 4. Third Option: Reuse a Version A Bare Module as a Fixed Sensor

As noted in `version_a_handheld_devices.md` §5, the **Meskernel LDL-T** (confirmed phase-shift, ±1 mm to 80 m, RS232/RS485/USART, **100 Hz**, ~$68–87.50) and **JRT B605B / M88B** (±1–2.6 mm at 40 m, RS232 TTL, ~$43–90 — *flagged: phase-shift unconfirmed*) are bare OEM modules with no inherent "handheld" packaging — either can simply be panel-mounted on the phi head as a permanent Version B installation instead of docked in a housing. This is **the pragmatic budget path**: it meets the spec at roughly 1–5% of the Dimetix/Micro-Epsilon/WayCon price, at the cost of a less industrially-hardened enclosure and a less mature support ecosystem.

**Recommendation ranking for Version B (revised 2026-07-08):**
1. **Meskernel LDL-T** — cheapest device whose phase-shift principle *and* price are both confirmed. The default budget lead.
2. **Dimetix DBN-50-050 (±5 mm, ~$1,332)** — if the *documented* protocol matters more than absolute price: it's the only candidate with a fully public byte-level ASCII spec, i.e. the lowest integration risk. **DAE-10-050 (±1 mm, ~$2,700)** if you want the tighter accuracy.
3. **JRT B605B / M88B** — cheapest of all (~$43), but **only after confirming its measurement principle** (flag).
4. **Micro-Epsilon ILR2250/3800 (~$1,800+), WayCon LDI, or FAE LS 121/122 FA (~$1,400)** — only if IP rating / industrial certification / documented long-term reliability becomes a hard requirement (request quotes in parallel — roughly comparable on spec).

## 5. Wiring Notes

### 5.1 RS232 path (JRT B605B, FAE LS 121 FA, Dimetix/Jenoptik/Scantron single-device RS232 mode)

Needs a MAX3232-class level shifter (RS232 swings ±5–12V, not GPIO-safe) — see `firmware_integration.md` §1 for the as-built GPIO options (AUX header GPIO 11/12/13/14, or the freed wire-encoder pins 15/16).

### 5.2 RS422/RS485 path (Meskernel LDL-T RS485 mode, FAE LS 122 FA, Dimetix/Micro-Epsilon/WayCon multi-drop RS422 mode)

RS422 and RS-485 are both differential-signaling standards but are **not identical** — RS422 is typically full-duplex point-to-point or multi-drop-from-one-master, while RS-485 is half-duplex multi-drop. A MAX485-class transceiver handles RS-485; a true RS422 link wants an RS422-specific transceiver (e.g., MAX3095/MAX489 family) if more than one device will share the line. For a single Meskernel LDL-T in RS485 mode, the same MAX485 wiring already discussed for the (now-excluded) TF02-i plan still applies:

**As-built GPIO correction (unchanged from the prior pass — still the authoritative wiring for this carrier):** the brief's original GPIO 13/14/18 plan is from the archived `12v_legacy/v2` pin map. The current as-built 5V v2 board (`pcb_design/EVKA_position_v2/docs/circuit_schematic.md`) wires GPIO 13/14 as general-purpose AUX header pins and GPIO 18 as BTN2 (already committed). Recommended actual wiring: **GPIO 13 (AUX3) = TX/DI, GPIO 14 (AUX4) = RX/RO, GPIO 15 (freed Wire A, draw-wire removed in this variant) = DE/RE.** A MAX485 (or RS422-appropriate transceiver) breakout module is a new hardware addition, not currently on the carrier PCB — open item for PCB-owner review, no `.kicad_sch` edits made here.

### 5.3 Analog 4-20mA path (WayCon LDI, Scantron SLS)

Both of these support a straightforward 4-20mA current-loop output as an alternative to serial — simplest possible integration (one ADC channel, no UART framing/parsing) if the extra ~1-4mm of quantization error from a typical 12-bit ADC across the loop's span is acceptable. Not pursued in `firmware_integration.md`'s API sketch (which assumes a serial `LaserRadiusSensor`), but worth keeping in mind if the RS232/RS422 protocol for either device proves hard to get documentation for.

## Open Risks

1. ~~Dimetix's exact current-catalog model number needs confirmation~~ — **RESOLVED (2026-07-08):** the 40 m-class SKUs are **DAE-10-050** (P/N 500633, ±1 mm, ~$2,700) and **DBN-50-050** (P/N 500635, ±5 mm, ~$1,332), both confirmed on `shop.dimetix.com`. Only a shipping quote to Turkey remains open.
2. **Every §3 addendum candidate is quote-only** — none of Micro-Epsilon, WayCon, Jenoptik, or Scantron have public pricing; a real cost comparison against Dimetix requires requesting quotes from all four.
3. **Dimetix/Jenoptik/Scantron protocols are proprietary ASCII, not Modbus** — if a Modbus-based fixed sensor is later preferred for consistency with other industrial equipment, this is a gap; no Modbus RTU phase-shift sensor meeting the price and ≤10mm/40m spec was identified in either research pass.
4. **JRT B605B / Meskernel LDL-T environmental rating (dust/moisture) for a fixed outdoor-style installation is unconfirmed** — the industrial-tier candidates (Dimetix, Micro-Epsilon, WayCon) likely have real IP ratings; the OEM modules' bare-PCB form factor may need a custom enclosure for anything beyond a benchtop/indoor deployment.
5. **RS422 vs RS-485 transceiver distinction (§5.2) has not been resolved against any specific SKU's exact electrical spec** — confirm from the datasheet before ordering a transceiver.
6. **ifm O1D's phase-wraparound behavior (§3.2) means it should not be revisited as a candidate without per-SKU datasheet verification**, despite being architecturally the closest "inconclusive" case to a genuine finding.

## Next Physical Test Steps

1. Bench-test the JRT B605B or Meskernel LDL-T (whichever ships first, per `procurement_and_bom.md`) mounted in a fixed/panel orientation rather than a handheld dock, to validate the "convergence" claim in §4 — confirm mounting and cabling work the same way as the Version A bench test.
2. Request firm quotes from Dimetix, Micro-Epsilon, WayCon, and Jenoptik in parallel for a 40 m-capable unit, to settle the pricing gap (Open Risk #1/#2) and get a real cost comparison across industrial vendors instead of relying on one manufacturer's public shop pricing.
3. Only after the cheap OEM-module path is bench-validated, decide whether an industrial housing/certification premium (any of the §3 vendors) is actually needed for the deployment environment.

---

*Part of the [laser radius detailed study](README.md). Docs-only — no firmware or PCB changes.*
