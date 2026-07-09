# Version A — Detachable Handheld / Wired-Serial Laser Shortlist

**Parent doc:** [`README.md`](README.md) — Version A use case (quick-disconnect dock on the phi head, tool doubles as a standalone field instrument).

**Fixed requirement (2026-07-01, revised):** range ≤ 40 m, laser device accuracy ≤ 10 mm (target sub-cm) across that full range. No tiers — this is the one bar every candidate below is measured against. This is the *device's own datasheet accuracy*, not the combined-system XYZ accuracy (see [`kinematics_and_calibration.md`](kinematics_and_calibration.md) for why the rotary encoders separately contribute error that isn't fixed by laser choice).

**2026-07-01 addendum:** extended research pass (assisted by a Copilot CLI research agent) found 8 additional candidates beyond the original 4 — see §3. The shortlist is now 12 qualifying devices across 4 mounting/interface classes (bare wired module, BLE consumer handheld, BLE-or-wired premium survey tool).

---

## 1. The Physics That Actually Filters This List

±10 mm at 40 m is a real dividing line, not an arbitrary number. It separates two measurement techniques:

- **Phase-shift (AMCW) laser distance meters** modulate the beam and measure the phase difference of the reflected signal. This gives flat, distance-independent accuracy — a device rated ±1–2 mm typically holds that figure from near-field out to its full rated range. This is how every handheld laser meter (Bosch, Leica, Hilti, Stanley, most OEM "laser distance sensor modules" marketed for surveying/machine tooling) works.
- **Pulsed time-of-flight (ToF) LIDAR** modules measure direct round-trip pulse timing. Achieving mm-class timing resolution over a 40 m round trip (~267 ns) requires precision electronics most low-cost ToF modules don't have — which is why the entire Benewake TF-series and similar cheap ToF modules land at ±5 cm–±1% of reading, not mm-class. **None of them meet this spec** — see `version_b_integrated_modules.md` for why they're demoted there.

Every candidate below is phase-shift based. That's not a coincidence — it's the only technology in this price/size class that can hit ±10 mm at 40 m.

## 2. Original Shortlist (Detailed)

### 2.1 JRT B605B / M88B Laser Distance Sensor Module (flagged — phase-shift unconfirmed)

> **⚠ Flagged (2026-07-08):** the stricter of the two price surveys could not surface a current, public, primary-source statement that unambiguously tags JRT's current modules as phase-shift (rather than some other ranging method), so JRT is **held out of the certified pass list** until the measurement principle is confirmed from a datasheet. It is *not* excluded (it is not ToF or %-of-reading, and the Istanbul survey lists the M88B as phase-shift ±1 mm) — but do not treat it as certified. The Istanbul survey did add a firm price anchor: the 40 m **JRT M88B / M703A** (UART TTL / USB, ±1 mm, 3–8 Hz) at **~$43 / ~2,013 TRY (ESTIMATE, 2026-07-08)** — the cheapest module in the entire study.


| Spec | Value |
|---|---|
| Range | 0.03–150 m (100–150 m class SKUs) |
| Accuracy | ±1 mm typical; ±1 mm + 40 ppm in poor lighting |
| **Accuracy at 40 m** | **≈ ±2.6 mm** (±1 mm + 40×10⁻⁶ × 40,000 mm = ±1 mm + ±1.6 mm) — **comfortably meets the ≤10 mm spec** |
| Interface | RS232 (TTL/CMOS levels); RS485 variant also sold |
| Max sample rate | ~8 Hz fast mode; 0.125–4 s per sample in high-accuracy mode |
| Laser class | Class II, 635 nm, <1 mW |
| Power | DC 2.0–3.3 V |
| Size / weight | 72×40×18 mm, ~25 g |
| Price ballpark | B605B: not published, est. $30–90; **40 m M88B/M703A sibling: ~$43 / ~2,013 TRY (ESTIMATE, 2026-07-08 Istanbul survey)** |
| Turkey / LCSC / AliExpress | Sold via jrt-measure.com direct, Alibaba, AliExpress (listings confirmed). No confirmed Turkish domestic stock — import only, 15–30 day lead. |

**Pros:** best price-to-accuracy ratio of any candidate here; TTL variant wires straight into an ESP32-S3 UART, no level shifter; bare-module form factor works equally well docked in a Version A housing *or* panel-mounted as a Version B fixed sensor (see §5).
**Cons:** 8 Hz max rate needs firmware hold-last-value gap-filling to keep the 20 Hz loop non-blocking (see `firmware_integration.md`); import-only, no fast domestic sourcing; exact protocol bytes not published, must be requested from JRT.

### 2.2 Meskernel LDL-T (primary confirmed-phase-shift pick)

Both 2026-07-08 surveys confirm the LDL-T family as **phase-shift (AMCW)** — this is now the cheapest device whose measurement principle *and* a real street price are both confirmed, which makes it the recommended bench lead (see §Next Physical Test Steps).

| Spec | Value |
|---|---|
| Range | 0.03–80 m (LDL-T-80); 40 m LDL-T 40 and ±2 mm/40 m LDK-40 siblings also sold |
| Accuracy | ±1 mm — **comfortably meets spec at 40 m**, with 2× margin left on range |
| Interface | Selectable USART / RS232 / RS485 |
| Max sample rate | **100 Hz** (corrected 2026-07-08 from an earlier 30 Hz figure) — far exceeds the system's 20 Hz loop, no gap-filling needed |
| Laser class | Class II |
| Size / weight | 17.5×17.1×7.1 mm, 2 g — smallest candidate in this study by far |
| Certifications | CE / FCC / RoHS / FDA |
| Price | **LDL-T-80: ~$87.50 / ~4,097 TRY (CONFIRMED, 2026-07-08)**; LDL-T 40: ~$68–80 / ~3,206–3,771 TRY (est.); LDK-40 (40 m, ±2 mm, 3 Hz): ~$70 / ~3,278 TRY (est.) |
| Turkey / LCSC / AliExpress | No confirmed domestic stock — direct import (Alibaba/AliExpress/meskernel.net), 15–30 day lead |

**Pros:** the only wired candidate whose native sample rate beats the firmware's 20 Hz loop outright; tiny form factor is the easiest of all candidates to dock/hide in a compact housing; interface flexibility (pick USART/RS232/RS485 per board design) is unique in this shortlist.
**Cons:** the byte-level command spec is still not cleanly surfaced publicly (survey-2's one caveat — request the protocol datasheet before firmware work); import-lead-time risk (15–30 days), no confirmed domestic stock.

### 2.3 Bosch PLR 40 C — flagged (measurement principle unconfirmed; Bluetooth type now confirmed)

> **⚠ Flagged (2026-07-01, revised 2026-07-09):** one flag remains:
> 1. **Measurement principle unconfirmed** — the stricter 2026-07-08 survey could not surface a primary-source statement that Bosch's PLR/GLM line uses phase-shift/AMCW (vs. some other method). Bosch's *accuracy* (±2 mm across the full range) is confirmed from the spec sheet; it is the *technology gate* that is unverified.
> 2. ~~**Bluetooth type discrepancy**~~ — **RESOLVED (2026-07-09):** Bosch's own PLR 30 C / PLR 40 C manual explicitly states **"Bluetooth 4.2 (Low Energy)"** and that compatible devices **"must support the GATT profile."** Community evidence (nRF Connect scans, WebBluetooth demos, Stack Overflow) all confirm BLE GATT. The archived philipptrenz library (classic SPP) was for older GLM models; the PLR 40 C is BLE-only. ESP32-S3 compatibility confirmed (ESP32-S3 is BLE-only). Protocol decrypted from GLM family (CRC-8, IEEE 754 float parsing), but byte-level traces are from GLM 50C/120C — **one real-device capture session on PLR 40 C still required** before firmware work. See [`bosch_plr_40c_integration.md`](bosch_plr_40c_integration.md) for full details.

| Spec | Value |
|---|---|
| Range | 0.05–40 m |
| Accuracy | **±2 mm across the full 0.05–40 m range** — confirmed via the official spec sheet, not just near-field. (Degrades to ±4 mm / ±0.15 mm·m⁻¹ under unfavorable conditions — strong ambient light, altitude, poor-reflectivity surfaces — still within the ≤10 mm spec even in the worst case.) |
| Interface | **BLE 4.2 GATT (confirmed)** — no wired output, no USB port. Service UUID `02a6c0d0-0451-4000-b000-fb3210111989`, characteristic `02a6c0d1-0451-4000-b000-fb3210111989`. ESP32-S3 compatible (BLE-only chip matches BLE-only device). See [`bosch_plr_40c_integration.md`](bosch_plr_40c_integration.md) §2. |
| Protocol | Bosch GLM/PLR BLE GATT protocol (decrypted from GLM family, **not yet verified on PLR 40 C**). CRC-8 (polynomial 0xA6, init 0xAA). Distance: bytes 7-10 of 20-byte response, little-endian IEEE 754 float (meters). Commands: continuous sync `C0 55 02 01 00 1A`, single measure `C0 40 00 EE`. **One real-device capture session required** before firmware work. Full details: [`bosch_plr_40c_integration.md`](bosch_plr_40c_integration.md) §3. |
| Max sample rate | Manual-trigger, human-paced (~1/4 s measurement time, but a human has to aim and fire it) |
| Laser class | Class 2 |
| Power | 2× AAA |
| Price (Turkey) | **Confirmed, best availability in this study**: ~3,865–4,275 TL (~$110–125) — Hepsiburada, Trendyol, N11, Amazon.tr, Tekzen |

**Pros:** meets the *accuracy* spec at its absolute max range with margin, cheapest fast-to-acquire option, best local stock of anything in this document.
**Cons:** **one remaining flag** — (1) measurement principle unconfirmed (must be verified before certifying); (2) BLE protocol decrypted from GLM family but not yet verified on physical PLR 40 C (one capture session required); (3) no USB port, no wired fallback; (4) manual-trigger pacing suits verification/spot-checks better than continuous automated tracking; (5) BLE latency jitter + WiFi coexistence on ESP32-S3's single 2.4 GHz radio; (6) 5-minute auto-power-off cannot be permanently disabled; (7) power supply fragility (must solder to battery springs for continuous operation).

### 2.4 Leica DISTO X4/D810-class (premium option, genuine wired path via accessory)

| Spec | Value |
|---|---|
| Range | 150–200 m depending on model (X4: 150 m, D810: 200 m) — far exceeds the 40 m requirement |
| Accuracy | ±1 mm across the full rated range — best accuracy of the original four candidates |
| Interface | Bluetooth Smart (v4.0+) native; **an official RS232 accessory exists** — Leica data transfer cable p/n `725078` / `GEV160` (LEMO-0 to 9-pin RS232), used for real-time streaming to survey data collectors when the device's serial mode is set to "passive" tracking mode |
| Laser class | Class 2 |
| Price | X4 discontinued; current-gen replacements now **confirmed** (§3): D5 ~$311–708, X6 ~$2,263, S910 ~$1,916–2,132. The RS232 accessory cable itself is a separate ~$50–80 purchase |
| Turkey / LCSC / AliExpress | Not checked — Leica sells through geosystems dealers, not general electronics retail |

**Pros:** strong accuracy margin (±1 mm vs. a ±10 mm budget — 10× headroom), and unlike Bosch, has a **genuine official wired RS232 path**, not just BLE.
**Cons:** most expensive of the original four by a wide margin; the RS232 "passive tracking" protocol isn't fully documented in this pass; superseded by the Leica DISTO S910 below, which has a *native* wired USB port (no accessory cable needed) and better accuracy.

## 3. Extended Shortlist — 2026-07-01 Research Addendum

Found via a broader manufacturer sweep (Hilti, Leica's other DISTO models, Bosch's other GLM/PLR models, Stanley, RS PRO/CEM, ADA Instruments). Construction-grade laser distance meters near-uniformly use phase-shift/AMCW (see Leica's own [measuring-technique FAQ](https://shop.leica-geosystems.com/measurement-tools/disto/blog/measuring-techniques-faq)), unlike the pulsed-ToF traps common in the drone/robotics rangefinder market — but "near-uniformly" is not "confirmed per model": the 2026-07-08 survey could confirm the principle for Leica but **not** for the Bosch GLM/PLR line, which is why the Bosch rows carry a ⚠flag (§2.3).

Prices/SKUs marked **CONFIRMED** were verified in the 2026-07-08 Istanbul survey; the rest remain ESTIMATE. Where two sources gave different confirmed prices, the range spans both.

| Brand/Model | Range | Accuracy (flat) | Interface | Price (USD / TRY) | Availability |
|---|---|---|---|---|---|
| **Leica DISTO S910** (SKU 805080) ⭐ | 0.05–300 m | ±1.0 mm, 0.1 mm resolution | BLE 4.0+, **WLAN, native USB** | **~$1,916–2,132 / ~89,780–99,855 TRY (CONFIRMED)** — corrected up from earlier ~$900–1,200 est. | Leica dealer network incl. Turkey; in TR channel stock |
| **Leica DISTO X6** (SKU 950909) **[NEW]** ⭐ | 0.05–250 m | ±1.0 mm | BLE + USB-C; P2P via DST 360-X | **~$2,263 / 106,000 TRY (CONFIRMED)** | Trendyol TR listing — current rugged X-series flagship (practical X4 successor) |
| **Leica DISTO D5** (SKU 950879/950908) | 0.05–200 m | ±1.0 mm | BLE 5.0, USB-C | **~$311–708 / ~14,595–33,200 TRY (CONFIRMED, price spread across sources)** | Confirmed in TR (Amazon.com.tr / Optet Makina via Hepsiburada) |
| **Leica DISTO D2** (986858 refresh; older 838725) | 0.05–**150 m** (838725 = 100 m) | ±1.5 mm | BLE (v6.0 on refresh), NFC | **~$270–309 / ~14,500 TRY (CONFIRMED)** | Wide Amazon/EU retail; Leica TR dealer network |
| **Hilti PD-I** | 0.05–100 m | ±1.5 mm | Bluetooth (partner apps) | ~$400–500 (est.) | Hilti direct-channel dealer network incl. Turkey; not on AliExpress/Amazon |
| **Bosch GLM 50-27 CG** (SKU 0601072U00) ⚠flagged | 0.05–50 m | ±1.5 mm | Bluetooth (MeasureOn app) | **$175 / 8,200 TRY (CONFIRMED)** | Hepsiburada/Trendyol — same Bosch Professional TR channel as PLR 40 C; **phase-shift unconfirmed (§2.3)** |
| **Bosch GLM 165-27 C/CG** ⚠flagged | 0.15–50 m | ±1.6 mm | Bluetooth 4.2 (MeasureOn app) | ~$200–250 (est.) | Amazon US/EU; **phase-shift unconfirmed** |
| **Stanley TLM165i / TLM165SI FatMax** | 0.05–60 m | ±1.5 mm | Bluetooth | ~$110–115 (est.) | Amazon EU/UK confirmed |
| **RS PRO ILDM-150H** (OEM: CEM iLDM-150) ⭐ | 0.05–70 m | ±1.5 mm | Bluetooth 4.0 + Meterbox Pro app | ~$90–130 (est.) | **Cheapest BLE handheld found** — RS Components has a Turkey branch (rsonline.com.tr); CEM-branded twin also on Amazon/eBay/Newegg |
| **ADA Instruments COSMO 60 GREEN** | 0.05–60 m | ±1.5 mm | Bluetooth (ADA PHOTO PLAN app) | Quote-only | CIS/Eastern Europe distribution; Turkey/AliExpress not confirmed |

⭐ = notable: **Leica DISTO S910** is the best-specified handheld in the Version A shortlist — best accuracy (±1.0 mm), longest range (300 m, 7.5× the requirement), and the *only* handheld with a native wired USB port (no accessory cable needed, unlike the X4/D810). At its **now-confirmed ~$1,916–2,132** (not the earlier ~$900–1,200 estimate) it sits squarely in the industrial Dimetix price tier, so it's a "budget allows *and* a handheld/dockable form factor is preferred over Dimetix's Version B housing" pick. The **[NEW] Leica DISTO X6** (~$2,263, rugged, 250 m) is the current X-series flagship and the practical successor to the discontinued X4 — pick it over the S910 if ruggedness matters more than the S910's P2P/scanning workflow. **RS PRO/CEM iLDM-150H** is the opposite end — if it holds up on the bench, it undercuts even the Bosch PLR 40 C on price while offering a similar BLE spec, and RS Components' Turkey branch means it could match Bosch's domestic-availability advantage.

### 3.1 Rejected During This Pass (documented so they aren't re-checked later)

| Device | Why rejected |
|---|---|
| DeWalt DW099S | Phase-shift, BLE — but only 30 m range, can't cover the 0–40 m requirement |
| Makita LD050P | ±1.98 mm / 50 m would qualify, but **no Bluetooth/USB/serial output found anywhere** (manual, spec sheet, retail listings) — same no-automated-output failure as the UNI-T LM50A |
| Skil ME981901 | No confirmed Bluetooth, and only 30 m range — doubly disqualified |
| Trimble/Spectra Precision QM75, QM20, HD360 | Accuracy (±1.5–3 mm) and range (50–70 m) look right, but no datasheet/manual/retailer listing shows any wireless or wired data interface for any of the three — appear to be display-only contractor tools |
| Nikon Forestry Pro II (and hunting/golf rangefinders generally) | **Wrong technology entirely** — pulsed ToF, not phase-shift. Accuracy ±0.3 yards (~274 mm), 27–90× over budget. Confirms that "laser rangefinder" branding in the hunting/forestry market is a different device class, not a phase-shift instrument, regardless of stated range. |

## 4. Why the UNI-T LM50A (and Makita LD050P) Are Still Unsuitable

This is an interface problem, not an accuracy problem, and the spec revision doesn't change it. Both devices' accuracy would meet the ≤10 mm spec comfortably, but neither has **any Bluetooth, USB, or RS232 output** — confirmed absent from official manuals and every retail spec sheet checked. Data only exists on the device's own LCD or in internal memory slots. A device with no automated output cannot feed a continuous firmware loop, no matter how accurate it is. The LM50A remains useful as a cheap, locally-available (robotistan.com) hand reference for manual spot-checks during bench testing.

## 5. A Convergence Worth Naming

At this accuracy bar, Version A and Version B stop being different *technologies* and become different *packaging* of the same underlying phase-shift sensor. JRT B605B and Meskernel LDL-T are bare modules — nothing stops either one from being panel-mounted permanently (a Version B installation) instead of docked in a handheld housing (Version A). The real differentiator at this point is price/robustness tier (JRT/Meskernel/RS-PRO-class OEM modules vs. Dimetix/Micro-Epsilon/WayCon industrial-grade, see `version_b_integrated_modules.md`) and whether a human-operable standalone tool (Bosch/Leica/Hilti/Stanley) is worth paying for, not accuracy — every candidate on this page already clears the spec.

## Open Risks

1. **Bosch PLR 40 C has one remaining flag** — measurement principle unconfirmed (must verify on physical unit). Bluetooth type is now **confirmed** (BLE 4.2 GATT). Protocol decrypted from GLM family but not yet verified on PLR 40 C specifically (one capture session required). See [`bosch_plr_40c_integration.md`](bosch_plr_40c_integration.md) for full details.
2. **JRT measurement principle is unconfirmed** — the stricter of the two price surveys could not surface a current, public, primary-source statement that unambiguously tags JRT's current modules as phase-shift (rather than some other ranging method), so JRT is **held out of the certified pass list** until the measurement principle is confirmed from a datasheet.
3. **Meskernel byte-level protocol still not cleanly public** — pricing is now confirmed, but the command spec must be requested from the manufacturer before firmware work.
4. **Leica handhelds (D2/D5/X6/S910) expose app/BLE transfer, not a documented raw serial command set** — the S910's native USB and the older X4's RS232 "passive tracking" accessory are the closest to a wired path; the exact streaming protocol should be reconfirmed against a physical unit.
5. **Leica DISTO X4 is discontinued**; the confirmed current picks are **D5** (mainline), **X6** (rugged flagship), and **S910** (native USB) — all priced in §3.
6. **Remaining ESTIMATE-only §3 prices** (Hilti PD-I, Stanley, RS PRO, ADA) still need direct confirmation — Leica D2/D5/X6/S910 and Bosch GLM are now CONFIRMED.
7. **Hilti PD-I's Bluetooth protocol is undocumented publicly** — its partner-app ecosystem (magicplan, ImageMeter) suggests a GATT profile exists, but no public reference implementation was found.
8. **None of the wired candidates (JRT, Meskernel) have confirmed Turkish stock** — import only (15–30 day lead). Only the BLE handhelds (Leica in TR channel, Bosch, likely RS PRO) are domestically stocked.

## Next Physical Test Steps

1. Request the Meskernel LDL-T command datasheet (meskernel.net), then order one LDL-T (confirmed phase-shift, ~$68–87.50) and bench-test actual accuracy at 5 m / 20 m / 40 m against a known reference — this is the confirmed-phase-shift lead.
2. For a confirmed domestically-stocked handheld reference, order a **Leica DISTO D5** (in TR channel) and validate its BLE read path; use it as a known-±1 mm hand reference for later sensor comparisons.
3. **Before** ordering any Bosch or JRT unit, obtain a primary-source datasheet confirming the measurement principle is phase-shift/AMCW (the open flag). Only then treat them as candidates rather than reference tools.
4. Order one RS PRO ILDM-150H via rsonline.com.tr in parallel — if genuinely in-stock domestically and its Meterbox Pro BLE protocol is crackable, it's the cheapest confirmed-availability BLE reference.
5. Only pursue the Leica S910/X6 (native USB / rugged) path if the cheaper confirmed options fall short — they're the most expensive way to meet a spec the Meskernel/D5 path already clears.

---

*Part of the [laser radius detailed study](README.md). Docs-only — no firmware or PCB changes.*
