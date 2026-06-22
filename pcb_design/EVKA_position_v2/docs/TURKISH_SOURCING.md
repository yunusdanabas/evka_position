# Turkish Domestic Sourcing — 5V PCB v2

Research date: 2026-05-08. **Yurtdışı tedarik sayılmaz** — only Turkish domestic suppliers (in-country stock, domestic shipping) are counted. Suppliers checked: direnc.net, robotistan.com, robolinkmarket.com, motorobit.com, ozdisan.com, arkotekelektronik.com, ersinelektronik.com, f1depo.com, robotpark.com.

---

## TL;DR

| Status | Count | Action |
|---|---|---|
| AVAILABLE (in stock now) | 22 | Order from direnc.net + motorobit + robotistan |
| PARTIAL (substitute or OOS) | 10 | Substitute, or wait for restock |
| NOT FOUND (must import) | 3 | LCSC / Mouser / DigiKey |

**Three parts that MUST be imported (yurtdışı zorunlu):**
1. **USB-C Female THT** (HRO TYPE-C-31-M-12) — no Turkish THT USB-C in stock at any supplier
2. **LTC4412 SOT-23-6** ideal diode controller — Analog Devices specialty IC, no domestic stock
3. ~~**1.5KE3.9CA** bidirectional TVS (×6)~~ — **resolved 2026-06-19:** no import needed. The TVS footprint is now a flexible large-axial THT pad (`D_DO-201AD_P15.24mm`) that takes any proper THT TVS; reuse the on-hand 1.5KE3.3CA from the old board (works, leaks slightly) or import 1.5KE3.9CA only if ideal signal integrity is required.

---

## Hard Parts — Detailed Findings

### MUST IMPORT

**USB-C Female THT 16-pin (J_USB)**
- No Turkish supplier carries a THT USB-C receptacle. direnc.net only lists USB-A/micro/mini/B THT.
- Ozdisan has SMD USB-C (L-KLS1-5407, 24-pin SMD) — would require board layout change.
- Workaround if domestic-only is mandatory: use a Pololu USB-C breakout board (robotistan, currently OOS, ~286 TL).
- **Recommendation:** Import from LCSC (~$0.10–0.20/pc).

**LTC4412 SOT-23-6 (U_IDEAL)**
- Not stocked at direnc.net, ozdisan, robotistan, robolinkmarket. Specialty Analog Devices IC.
- No equivalents (LM66100, TPS2117) found in Turkey either.
- Workaround if domestic-only is mandatory: replace with two 1N5822 Schottky diodes for OR-ing (loses ~0.4V vs LTC4412's 20mV — efficiency penalty, but functional).
- **Recommendation:** Import from LCSC/Digikey, OR redesign the OR-ing section.

**Encoder TVS ×6 — general THT, flexible footprint (part TBD)**
- Footprint is now `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` (large-axial) — takes any proper THT TVS, so no specific part must be sourced.
- Preferred: reuse **on-hand 1.5KE3.3CA** from the old 5 V board (works on this divider, slight leakage at the 3.33 V HIGH). Ideal: 1.5KE3.9CA (V_RWM 3.34 V) — import-only. SMBJ3V6CA (SMD) at ozdisan only if you switch to an SMD footprint.
- Engineering note: For 3.3V logic with resistive divider already limiting voltage, a 5.1V unidirectional TVS could substitute, OR omit entirely (divider already provides protection).
- **Recommendation:** Either import the exact part, or redesign with SMD substitute or simpler ESD network.

### PARTIAL — Substitute Available

**AO3401 P-MOSFET SOT-23 (Q_RPP, Q_SWITCH)**
- Substitute: **PJA3441** (Panjit, 40V/3.1A, Rds 74mΩ) — direnc.net 4.99 TL, **99,999 in stock**. URL: https://www.direnc.net/pja3441-31a-40v-p-kanal-mosfet-sot23-en
- Verify Vgs threshold compatibility with LTC4412 application before swapping.

**SS34 Schottky DO-201 axial (D_BAR, D_USB, D_BOOST)**
- Note: SS34 is technically the SMD designation. The axial DO-201 equivalent is **1N5822**.
- direnc.net stocks **1N5822-HT** (Hottech), 40V/3A, **99,999 in stock**, 5.31 TL. URL: https://www.direnc.net/1n5822-ht-30-amp-schottky-barrier-rectifiers-hottech
- Drop-in replacement.

**KF128V 3.5mm 2-pin terminal (J6)**
- direnc.net 2-pin 3.5mm currently OOS.
- Substitute: **KF350-2P** at motorobit.com (3.5mm pitch) — same function, different brand.

**~~KF301-5P (J3 wire encoder, 5-pin)~~ — superseded 2026-06-19**
- No longer needed: the wire encoder's Z/index line is unused, so J3 is now a **single KF301-4P**
  (GND/VCC/A/B), same part as J1/J2 (in stock at direnc.net). The 5P-OOS / 2P+3P-ganged workaround is moot.

### PARTIAL — Currently Out of Stock (Restock Watch)

| Part | RefDes | Suppliers (all OOS at research date) |
|------|--------|--------------------------------------|
| TP4056+DW01A LiPo charger module | MOD_TP4056 | direnc.net, robotistan, robolinkmarket — all OOS, restocks every 2–4 weeks |
| 74HC14N DIP-14 | U_SCHM | direnc.net, robotistan OOS; try arkotekelektronik, ersinelektronik, f1depo (6.30 TL) |
| ESP32 Wemos D1 R32 | U1 | direnc.net 323 TL OOS; check Trendyol/hepsiburada third-party resellers |
| 1S LiPo 3.7V 2000mAh JST-PH | BAT1 | robotistan OOS; try robotpark.com or RC hobby shops |

### PARTIAL — Specification Risk

**10nF C0G/NP0 50V ceramic THT 5mm (×6) — C_FILT**
- direnc.net stocks 10nF 63V ceramic at 0.38 TL (99,999 in stock), but **dielectric not specified** on the listing.
- C0G/NP0 is required for stable RC filter behavior; X7R will work but with worse temperature/voltage drift.
- **Action:** Email direnc.net to confirm dielectric before bulk-ordering, OR accept X7R if 10nF tolerance/drift isn't critical (this design's RC corner at 2.38kHz is forgiving).

**Ferrite bead 600Ω@100MHz axial THT (×3) — FB1/FB2/FB3**
- No Turkish supplier stocks axial THT ferrites with this specific spec.
- direnc.net has 1206 SMD 600R/100MHz (currently OOS).
- **Substitute options:**
  1. SMD 0805/1206 ferrite + adapter pads on the THT footprint
  2. Series 33–100Ω 1/4W resistor (degraded but functional decoupling for encoder VCC at low frequencies)
  3. Import from TME / Mouser

---

## Commodity Parts — All Available at direnc.net

These are stocked by every Turkish supplier; no concern:

- All resistors 1/4W metal film 1% (5.1k, 10k, 20k, 100k, 300k, 1k) — full E96 range, ~0.15–0.35 TL each
- 100nF / 10µF / 22µF / 220µF capacitors (THT)
- 5mm green and red LEDs
- 6×6mm tactile button (4-pin, multiple stem heights)
- Female pin header strips 1×40 (cut to 1×15 / 1×19) — 4.31 TL plain, 13.48 TL precision
- KF301 4-pin screw terminal (5mm pitch)
- DC barrel jack 5.5×2.1mm THT
- SMAJ5.0A TVS (DO-214AC/SMA) — direnc.net 4.17 TL (×111 stock), ozdisan multi-brand
- 10µH 1A radial THT inductor (ABCO brand) — direnc.net 9.71 TL, 99,999 in stock
- MT3608 boost module — direnc.net 20.49 TL, **4,948 in stock**
- JST-PH 2.0mm 2-pin male PCB header — motorobit.com, in stock 10,000+

---

## Order Strategy

**Phase 1 — Place now at direnc.net (one cart):**
- 1N5822-HT (×4) — replaces all SS34 positions
- PJA3441 (×2) — replaces AO3401
- SMAJ5.0A (×2)
- MT3608 module
- 10µH 1A inductor
- All resistors (0.15–0.35 TL each — buy 10× of each value for spares)
- All ceramic and electrolytic caps
- LEDs, headers, tactile button, KF301-4P (×2), barrel jack

**Phase 2 — Place at motorobit.com:**
- JST-PH 2-pin male THT
- KF350-2P 3.5mm terminal (J6 substitute)
- ~~KF301-3P (to combine with 2P → 5-pin J3)~~ — **not needed** (J3 is now a single KF301-4P; Z unused)

**Phase 3 — Watch for restock (weekly check):**
- TP4056+DW01A module (direnc.net, robolinkmarket)
- 74HC14N DIP-14 (try ersinelektronik, f1depo first; they may have stock)
- Wemos D1 R32 (Trendyol resellers fastest)
- 1S LiPo 2000mAh (robotpark.com, RC shops)

**Phase 4 — Import (pick one parcel from LCSC):**
- USB-C Female THT (HRO TYPE-C-31-M-12) ×3 — buy spares
- LTC4412HMS6#PBF ×3 — buy spares
- ~~1.5KE3.9CA ×15~~ — **not required** (TVS footprint is general THT; reuse on-hand 1.5KE3.3CA. Import 1.5KE3.9CA only if you want the ideal-standoff part.)
- Optional: original Bourns RLB0914-100KL inductor for matched performance

---

## Sources

| Supplier | Strength |
|----------|----------|
| direnc.net | Best for resistors, caps, semiconductors, MT3608, modules |
| motorobit.com | Best for connectors (JST-PH, KF301/KF350) |
| robotistan.com | Modules + ESP32 boards (often OOS) |
| robolinkmarket.com | Charger modules + battery cells |
| ozdisan.com | SMD parts (TVS, USB-C SMD), low-volume professional |
| arkotekelektronik.com / ersinelektronik.com / f1depo.com | Logic ICs (74HC series) |

Key URLs:
- 1N5822-HT axial Schottky: https://www.direnc.net/1n5822-ht-30-amp-schottky-barrier-rectifiers-hottech
- PJA3441 P-MOSFET: https://www.direnc.net/pja3441-31a-40v-p-kanal-mosfet-sot23-en
- SMAJ5.0A TVS: https://www.direnc.net/smaj50a-e3-61t-smd-transil-diyot-en
- MT3608 module: https://www.direnc.net/mt3608-2a-max-dc-dc-step-up-power-module-arduino-en
- 10µH inductor: https://www.direnc.net/10uh-1a-kontipi-bobin
- JST-PH 2-pin male: https://www.motorobit.com/2-pin-jst-ph-20-tunik-konnektor-erkek
- 74HC14N (arkotek): https://arkotekelektronik.com/sn74hc14n-74hc14-dip-14
- 74HC14N (ersinelektronik): https://www.ersinelektronik.com/urun/74hc14-74hc14n-hex-inverting-schmitt-trigger
