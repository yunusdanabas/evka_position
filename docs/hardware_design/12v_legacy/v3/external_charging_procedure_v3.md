# External Charging Procedure — V3 Internal 3S LiPo

> V3-A has no onboard charger. V3-B/C have optional onboard charging but no balancing.  
> Always use an external 3S balance charger for balancing. This procedure applies to all three configs.

---

## 1. Supported Charging Methods

V3 documents two mechanical/service options.

### Option A — Removable Battery

The battery is unplugged from the PCB/enclosure and charged outside the machine.

This is the recommended method for prototypes because it is easiest to inspect and safest to troubleshoot.

### Option B — Panel Charge Leads

The enclosure exposes:

- XT60 main battery connector
- JST-XH-4P balance connector

The battery remains mounted, but the external charger connects directly to the battery leads.

This is convenient, but the panel connectors must be clearly labeled and protected from accidental shorts.

---

## 2. Required Charger

Use a charger that explicitly supports:

- LiPo chemistry
- 3S pack voltage
- Balance charging through JST-XH-4P
- Charge current suitable for the pack capacity

Examples:

- iMax B3 class 3S balance charger
- SkyRC E3S class 3S balance charger
- Any RC charger configured for `LiPo BALANCE`, `3S`, and appropriate current

---

## 3. Voltage Limits

| State | Pack Voltage | Per-Cell Voltage |
|---|---:|---:|
| Full | 12.60V | 4.20V |
| Nominal | 11.10V | 3.70V |
| Low warning target | 10.50V | 3.50V |
| Graceful shutdown target | 9.90V | 3.30V |
| Absolute minimum | 9.00V | 3.00V |

Do not intentionally run the battery to BMS cutoff. BMS cutoff is an emergency backstop.

---

## 4. Removable Battery Charging Steps

1. Power down the EVKA unit.
2. Disconnect the 12V adapter.
3. Open the battery access area.
4. Disconnect the battery XT60/main connector from J_XT60 on the V3 board.
5. Disconnect the JST-XH balance lead from the panel or access connector if fitted.
6. Remove the battery from the enclosure.
7. Inspect the pack for swelling, damage, hot spots, or damaged insulation.
8. Connect XT60/main lead to the external charger.
9. Connect JST-XH-4P balance lead to the charger balance port.
10. Select `LiPo 3S balance charge`.
11. Set charge current at or below the pack manufacturer's recommended rate.
12. Charge in a LiPo-safe area or LiPo charging bag.
13. After charge completion, verify pack voltage is about 12.6V.
14. Reinstall and reconnect the battery.
15. Verify polarity before powering the V3 board.

---

## 5. Panel Charge Lead Steps

1. Power down the EVKA unit.
2. Disconnect the 12V adapter.
3. Q_BATT is OFF while the adapter is disconnected — battery is isolated from BUCK_VIN. The charger connects to the battery side only via J_BAL and panel XT60; no current flows into the PCB load path.
4. Connect charger main lead to the panel XT60.
5. Connect charger balance plug to the panel JST-XH-4P.
6. Select `LiPo 3S balance charge`.
7. Charge at the correct current.
8. Do not operate the machine during charging.
9. Disconnect charger after completion.
10. Cover panel connectors if they are exposed.

---

## 6. Storage Rule

For long-term storage:

- Store LiPo near 3.75-3.85V per cell, about 11.25-11.55V pack voltage.
- Disconnect the battery from J_XT60 on the V3 board if quiescent drain is unknown.
- Do not store fully charged for weeks.
- Do not store below 3.3V per cell.

---

## 7. Safety Warnings

- Never charge a swollen, punctured, crushed, or overheated LiPo pack.
- Never charge through the normal 12V adapter input.
- Never short XT60 pins; a 3S LiPo can deliver very high fault current.
- Always use the balance connector during charging.
- Do not rely on a generic BMS board for balancing.
- Keep battery wiring strain-relieved and away from milled copper edges.
