# Procurement & Bench-Test BOM — Laser Radius Variant

**Parent doc:** [`README.md`](README.md). Rough costs, suppliers, and a recommended bench-test order sequence.

**Fixed requirement (2026-07-01, revised):** ≤40 m range, ≤10 mm laser accuracy — every device below meets this spec (the previously-considered ToF modules that don't are omitted; see `version_b_integrated_modules.md` §1 if that history is needed).

**2026-07-01 addendum:** extended research pass added 13 more candidates (8 handheld, 5 industrial) — see §1.1/§1.2 below.

**2026-07-08 price-survey addendum:** a targeted Istanbul price/model survey (two independent passes) converted many estimates into **CONFIRMED** prices/SKUs, added new models (Leica **X6**, Dimetix **DBN-50-050**, Meskernel **LDK-40**, JRT **M88B**, **FAE LS 121/122 FA**), and **demoted Bosch and JRT to a flagged tier** (measurement principle not independently confirmed — see `version_a_handheld_devices.md` §2.1/§2.3). FX used (2026-07-08): **USD/TRY 46.85, EUR/USD 1.141, CHF/USD 1.238, GBP/USD 1.336**. TL prices move with FX/VAT — treat as sensitive.

---

## 1. Cost & Supplier Summary

All prices are as retrieved during this research pass (2026-07-01) — **verify live pricing/stock before ordering**, especially TL prices (move with FX/VAT) and quote-only items.

### 1.1 Original Shortlist

| Device | Role | Price | Supplier | Lead time class |
|---|---|---|---|---|
| **Meskernel LDL-T** | **Confirmed-phase-shift lead** — cheapest device with principle + price both confirmed | **LDL-T-80: ~$87.50 / ~4,097 TRY (CONFIRMED)**; LDL-T 40: ~$68–80 (est.); LDK-40: ~$70 (est.) | Alibaba/AliExpress/meskernel.net | Slow — import, 2–4 wk class |
| **Dimetix DBN-50-050** (P/N 500635) | Confirmed-protocol budget lead — ±5 mm, public ASCII spec | **CHF 1,076 / ~$1,332 (CONFIRMED)** | shop.dimetix.com; TR dealers Megasensor/Ulusat | Slow — EU order |
| **Dimetix DAE-10-050** (P/N 500633) | Industrial precise option — ±1 mm, public ASCII spec | **CHF 2,298–2,699 / ~$2,700–2,844 / ~126,394 TRY (CONFIRMED)** | shop.dimetix.com, Laser-View/Eurolase | Slow — EU order |
| **Leica DISTO D5** | Confirmed domestically-stocked handheld reference (±1 mm, BLE) | **~$311–708 / ~14,595–33,200 TRY (CONFIRMED, source spread)** | Amazon.com.tr / Optet Makina (Hepsiburada) | Fast–Medium — TR channel |
| JRT B605B / M88B ⚠flagged | Cheapest wired module — *phase-shift unconfirmed, verify first* | M88B: ~$43 / ~2,013 TRY (est.); B605B: $30–90 (est.) | jrt-measure.com, Alibaba, AliExpress | Slow — import, 2–4 wk |
| Bosch PLR 40 C ⚠flagged | Fast local BLE reference — *phase-shift unconfirmed, verify first* | ~3,865–4,275 TL (~$110–125, CONFIRMED price) | Hepsiburada, Trendyol, N11, Amazon.tr, Tekzen | Fast — domestic, multiple retailers |
| UNI-T LM50A | Reference tool only (not a candidate — no data interface) | Cheap, in stock | robotistan.com | Fast — domestic |

### 1.2 Extended Shortlist (2026-07-01 addendum)

**More handheld/BLE options** — full detail in `version_a_handheld_devices.md` §3:

| Device | Price | Supplier | Lead time class |
|---|---|---|---|
| RS PRO ILDM-150H (OEM: CEM iLDM-150) | **Cheapest BLE handheld found**: ~$90–130 (est.) | RS Components' Turkey branch (rsonline.com.tr); CEM-branded twin on Amazon/eBay/Newegg | Fast — domestic (RS TR) or Amazon |
| Stanley TLM165i / TLM165SI FatMax | ~$110–115 (est.) | Amazon EU/UK confirmed | Medium — international shipping |
| Leica DISTO D2 (986858 refresh / 838725) | **~$270–309 / ~14,500 TRY (CONFIRMED)** | Wide Amazon/EU retail; Leica TR dealer network | Fast–Medium |
| Bosch GLM 50-27 CG ⚠flagged | **$175 / 8,200 TRY (CONFIRMED price; principle unconfirmed)** | Same Bosch Professional TR channel as PLR 40 C | Fast — domestic |
| Bosch GLM 165-27 C/CG ⚠flagged | ~$200–250 (est.) | Amazon US/EU | Medium |
| ADA Cosmo 60 Green | Quote-only | CIS/Eastern Europe distribution | Slow — quote + import |
| Hilti PD-I | Est. $400–500 | Hilti direct-channel dealer network incl. Turkey | Medium — dealer order |
| **Leica DISTO X6** (SKU 950909) **[NEW]** | **~$2,263 / 106,000 TRY (CONFIRMED)** — rugged X-series flagship, 250 m | Trendyol TR / Leica dealer network | Medium — dealer/marketplace |
| Leica DISTO S910 (SKU 805080) | **~$1,916–2,132 / ~89,780–99,855 TRY (CONFIRMED)** — corrected up from earlier ~$900–1,200 est.; best accuracy/range/native-USB in Version A | Leica dealer network / TR channel stock | Medium — dealer order |

**More industrial/fixed-mount options** — full detail in `version_b_integrated_modules.md` §3:

| Device | Price | Supplier | Lead time class |
|---|---|---|---|
| Micro-Epsilon optoNCDT ILR2250 / ILR3800 | **ILR2250: ~$1,800 / ~84,294 TRY (ESTIMATE)**; ILR3800 quote-only | Micro-Epsilon direct (Germany); TR dealers İmaj Teknik, Simtekno | Slow — quote + EU import |
| **FAE LS 121 / LS 122 FA** **[NEW]** | **~$1,400 / ~65,562 TRY (ESTIMATE)** | FAE Srl (Italy); EU import (Customs-Union advantage) | Slow — quote + EU import |
| Jenoptik LDM41 / LDM4x series | **~$1,500 / ~70,245 TRY (ESTIMATE)** — 150 m range is reflector-dependent (~30 m natural) | Jenoptik direct (Germany); Edmund Optics | Slow — quote + EU import |
| WayCon LDI | Quote-only | WayCon Positionsmesstechnik direct (Germany) | Slow — quote + EU import |
| Scantron SLS | Quote-only | Scantron Industrial Products (UK) | Slow — quote + EU import |
| ~~Micro-Epsilon ILR1171/1181/1191~~ | **Rejected** — older branch is pulsed ToF (2026-07-08), not phase | — | — |

**MAX3232 (RS232) and MAX485/RS422 transceiver breakout modules** — needed depending on which device/interface is chosen (see `firmware_integration.md` §1) — are cheap (~$1–3 class), widely available on direnc.net/AliExpress, and not itemized per-device since they're shared infrastructure, not sensor cost.

## 2. Recommended Bench-Test Order

Revised 2026-07-08 to a **confirmed-phase-shift-first** ordering (the earlier draft led with Bosch/JRT, now flagged for unconfirmed measurement principle):

1. **Meskernel LDL-T** (~$68–87.50, import, 2–4 wk) — order first. Cheapest device with **both** a confirmed phase-shift principle and a confirmed street price; ±1 mm, 100 Hz native (exceeds the 20 Hz loop, no gap-filling). Request the command datasheet from Meskernel *before* ordering (its byte-level protocol is the one open gap). Bench-test both mounting styles (Version A dock / Version B panel) with the same unit.
2. **Dimetix DBN-50-050** (CHF 1,076 / ~$1,332, EU order) — order alongside step 1. It's the only candidate with a fully public ASCII protocol, so it de-risks the firmware parsing path independently of Meskernel's datasheet; ±5 mm still clears the ≤10 mm spec. Step up to **DAE-10-050** (±1 mm, ~$2,700) only if the tighter accuracy is wanted.
3. **Leica DISTO D5** (~$311–708, TR channel) — order for a confirmed, domestically-stocked ±1 mm handheld reference and to validate the BLE read path with a *confirmed-phase-shift* device (unlike the flagged Bosch).
4. **(Flagged — verify principle first) Bosch PLR 40 C + RS PRO ILDM-150H + JRT B605B/M88B** — cheap and fast/domestic (Bosch, RS PRO) or cheapest of all (JRT ~$43), but only worth ordering *after* a primary-source datasheet confirms their measurement principle is phase-shift. Until then, keep the Bosch as a hand reference only.
5. **(Conditional) Industrial tier — Micro-Epsilon ILR2250 (~$1,800), WayCon LDI, or FAE LS 121/122 FA (~$1,400)** — only if steps 1–3 fail to meet the ≤10 mm spec in real bench conditions (unlikely, given the margin) or if an IP rating / certified housing becomes a hard requirement. Request quotes in parallel rather than defaulting to one vendor.
6. **(Optional) Leica DISTO S910 or X4 + RS232 accessory** — only worth pursuing if the industrial-tier budget is available *and* a handheld/dockable form factor is preferred over the industrial candidates' fixed housings. Otherwise redundant with steps 1–5.

## Open Risks

1. **Bosch and JRT measurement principle is unconfirmed** — both are flagged (see the tables) and must not be treated as certified until a primary-source datasheet confirms phase-shift.
2. **Confirmed prices are FX-sensitive** — the CONFIRMED TL figures move with USD/TRY (46.85 as of 2026-07-08) and VAT; re-check before ordering.
3. **Import lead times (2–4 weeks) for Meskernel/JRT are estimates**, not confirmed shipping quotes.
4. ~~Dimetix SKU needs confirmation~~ **RESOLVED** — DAE-10-050 / DBN-50-050 confirmed. Only a TR shipping quote remains open.
5. **Still-estimated prices** — Micro-Epsilon ILR2250 (~$1,800), Jenoptik LDM41 (~$1,500), FAE LS 121/122 (~$1,400), Hilti, Stanley, RS PRO, ADA. WayCon and Scantron remain fully quote-only. Confirm before a hard budget.

## Next Physical Test Steps

1. Request the Meskernel LDL-T command datasheet, then place the Meskernel LDL-T and Dimetix DBN-50-050 orders — the two confirmed-phase-shift leads (one cheapest, one public-protocol).
2. Order a Leica DISTO D5 from the TR channel for a confirmed-phase-shift ±1 mm handheld reference and BLE-path validation.
3. Once a confirmed lead arrives, run the accuracy spot-check from `kinematics_and_calibration.md` §3.2 at 5 m / 20 m / 40 m before deciding whether an industrial-tier sensor is ever needed.
4. Obtain primary-source phase-shift confirmation for Bosch/JRT **before** ordering either for anything beyond a hand reference.
5. If the industrial tier does become necessary, request quotes from Micro-Epsilon, WayCon, and FAE in parallel — roughly comparable on paper; only a real quote reveals which is cheapest/fastest.

---

*Part of the [laser radius detailed study](README.md). Docs-only — no firmware or PCB changes.*
