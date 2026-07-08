# 12V + 3S LiPo PCB — All Through-Hole Version

> **All-THT variant** of the [12V + 3S LiPo design](../12v/README.md).  
> Same circuit topology — only component packages changed from SMD to through-hole for easier hand soldering on pertinax.

---

## Files

| File | Role |
|------|------|
| [bill_of_materials_12v_tht.md](bill_of_materials_12v_tht.md) | Complete BOM — every part is THT or a pre-assembled module |
| [circuit_schematic_12v_tht.md](circuit_schematic_12v_tht.md) | Package-level changes to the schematic (TO-220 RPP, axial diodes) |
| [pcb_layout_guide_12v_tht.md](pcb_layout_guide_12v_tht.md) | Updated zone map, TO-220 mounting, assembly sequence |
| [../12v/power_supply_12v_spec.md](../12v/power_supply_12v_spec.md) | Power spec (shared — electrical design unchanged) |
| [../12v/kicad/](../12v/kicad/) | KiCad project (shared — update footprints for THT packages) |

---

## What changed vs the SMD version

The [original 12V design](../12v/) uses several SMD parts that require dead-bug soldering or breakout boards on pertinax. This variant replaces **all SMD discretes** with through-hole equivalents:

| SMD Part | Package | THT Replacement | Package |
|----------|---------|-----------------|---------|
| AO4407A (P-FET RPP) | SOIC-8 | **IRF4905** | TO-220AB |
| SMBJ18A (12V TVS) | DO-214AA (SMB) | **P6KE18A** | DO-15 (axial) |
| SS34 Schottky (×3–4) | SMA (DO-214AB) | **SS34 / 1N5822** | DO-201 (axial) |
| 100nF X7R ceramic (×2) | 0805 | **100nF ceramic disc** | Radial 5mm THT |
| 10µF X7R ceramic (×1) | 0805 | **10µF electrolytic** | Radial THT |

**Modules** (MP1584EN, MT3608, TP5100, 3S BMS) are unchanged — they mount via pin headers and are already THT-compatible.

**Signal section** (dividers, TVS, ferrites, encoder terminals, ESP32 headers) is unchanged — the [5V BOM](../5v/bill_of_materials.md) parts are already through-hole.

---

## When to use this version

- **Pertinax PCB** with no SMD rework station — all components solder with a standard iron
- **Prototype / hand-built** boards where ease of assembly matters more than board density
- **Repair-friendly** builds — TO-220 and axial parts are easy to desolder and replace

Use the [SMD version](../12v/) if you have a reflow oven / hot-air station, want smaller board area, or prefer the lower Rds(on) of the AO4407A (12mΩ vs 20mΩ — negligible at 1.5A).

> **For new builds:** The current recommended simple 12V design is [V3](../v3/). V3 uses the ESP32-S3-DevKitC-1, removes onboard charging, and uses a ready-made power-path module interface for the internal 3S battery backup. The 12v_tht topology is still valid but V3 is simpler and better-documented for new LPKF S63 builds.

---

## Board specification

| Parameter | Value |
|-----------|-------|
| Dimensions | **120mm × 80mm** (same as SMD version) |
| Material | Double-sided pertinax |
| Copper weight | 1 oz (35µm) |
| Vias | 0.8mm tinned copper wire, solder both sides |
| Components | **100% through-hole** + pre-assembled modules |
