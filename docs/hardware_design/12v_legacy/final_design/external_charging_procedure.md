# External Charging Procedure - Final EVKA 3S LiPo

The final hardware design has no onboard charger. Charging is done with an external 3S LiPo balance charger.

This procedure is mandatory for the final design.

## 1. Required Charger

Use a charger that explicitly supports:

- LiPo chemistry
- 3S pack voltage
- Balance charging through JST-XH-4P
- Charge current appropriate for the battery capacity

Examples:

- iMax B3 class 3S balance charger
- SkyRC E3S class 3S balance charger
- RC charger configured for `LiPo BALANCE`, `3S`, and the correct current

## 2. Voltage Limits

| State | Pack Voltage | Per Cell |
|---|---:|---:|
| Full | 12.60V | 4.20V |
| Storage target | 11.25V to 11.55V | 3.75V to 3.85V |
| Nominal | 11.10V | 3.70V |
| Low warning | 10.50V | 3.50V |
| Shutdown target | 9.90V | 3.30V |
| Absolute minimum | 9.00V | 3.00V |

Do not intentionally discharge to BMS cutoff. BMS cutoff is an emergency backstop only.

## 3. Preferred Method - Remove Battery For Charging

This is the safest prototype and service method.

1. Stop EVKA operation.
2. Power down the board.
3. Disconnect the 12V adapter from `J12V_TERM`.
4. Open the battery access area.
5. Disconnect the battery main connector from the board.
6. Disconnect the balance connector or panel balance lead.
7. Remove the battery from the enclosure.
8. Inspect the pack for swelling, punctures, crushed corners, hot spots, or damaged insulation.
9. Place the battery in a LiPo-safe area or LiPo charging bag.
10. Connect the main battery lead to the external charger.
11. Connect the JST-XH-4P balance lead to the charger balance port.
12. Select `LiPo 3S balance charge`.
13. Set charge current at or below the pack manufacturer's recommended rate.
14. Charge until the charger reports completion.
15. Verify pack voltage is about 12.6V and cells are balanced.
16. Reinstall the battery.
17. Reconnect main and balance leads with correct polarity.
18. Power the EVKA board and verify normal startup.

## 4. Alternate Method - Panel Charge Leads

Use this only if the enclosure exposes protected battery-side XT60 and JST-XH connectors **and** provides a way to disconnect the battery from the EVKA load path during charging.

Without a battery disconnect switch or service plug, adapter-off charging will still let Q_BATT turn on and power `BUCK_VIN` from the battery. Do not use panel charging in that configuration; remove the battery instead.

1. Stop EVKA operation.
2. Power down the board.
3. Disconnect the 12V adapter.
4. Confirm `TP_PROT` is 0V.
5. Open the battery service switch or unplug the battery load connector.
6. Confirm `BUCK_VIN` is 0V.
7. Connect charger main lead to the panel XT60.
8. Connect charger balance plug to the panel JST-XH-4P.
9. Select `LiPo 3S balance charge`.
10. Charge at the correct current.
11. Do not operate the machine during charging.
12. Disconnect the charger after completion.
13. Cover or cap exposed panel connectors.
14. Reconnect the battery load path only after charging is complete.

Panel charging must connect to the battery side only. Never charge through `J12V_TERM`, `BUCK_VIN`, or the ESP32 board.

## 5. Storage Rule

For storage longer than a few days:

- Store near 3.75V to 3.85V per cell.
- Disconnect the battery from the board if quiescent drain is unknown.
- Do not store fully charged for weeks.
- Do not store below 3.3V per cell.

## 6. Safety Warnings

- Never charge a swollen or damaged LiPo.
- Never charge unattended.
- Never short XT60 pins.
- Never bypass `F_BAT` for testing.
- Never charge through the 12V adapter input.
- Always use the balance connector during charging.
- Do not rely on a generic BMS for balancing.
- Keep battery wiring strain-relieved and away from milled copper edges.
