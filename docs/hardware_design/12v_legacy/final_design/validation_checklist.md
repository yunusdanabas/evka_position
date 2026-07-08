# Validation Checklist - Final EVKA Hardware

Use this checklist for every first article build and after any power-section rework.

Do not insert the ESP32-S3 DevKitC until the 5V rail has passed validation.

## 1. Pre-Power Inspection

- [ ] PCB is clean and free of milling burrs.
- [ ] No solder bridges are visible under magnification.
- [ ] All wire-through vias are soldered on both sides.
- [ ] `J12V_TERM` polarity is labeled.
- [ ] `F1` is installed.
- [ ] `TVS_IN` polarity is correct.
- [ ] Q_RPP pinout is correct: Gate, Drain, Source verified.
- [ ] Q_RPP tab cannot contact grounded metal.
- [ ] `D_ADAPT` cathode band faces `BUCK_VIN`.
- [ ] `D_GATE` cathode band faces Q_BATT gate.
- [ ] Q_BATT pinout is correct: Source=battery, Drain=`BUCK_VIN`, Gate=gate node.
- [ ] Q_BATT tab cannot contact grounded metal.
- [ ] `F_BAT` is installed close to battery positive.
- [ ] No unfused battery positive trace crosses the PCB.
- [ ] BMS/protection board wiring is correct.
- [ ] Electrolytic capacitors have correct polarity.
- [ ] Encoder divider resistors are 10k top and 20k bottom.
- [ ] Encoder signal capacitors are 1nF, not 100nF.
- [ ] ESP32-S3 DevKitC is not inserted.

## 2. Cold Resistance Checks

Measure with no power connected.

- [ ] `J12V+` to GND is not shorted.
- [ ] `V_PROT` to GND is not shorted.
- [ ] `BUCK_VIN` to GND is not shorted.
- [ ] `5V_RAIL` to GND is not shorted.
- [ ] `3V3` header pin to GND is not shorted.
- [ ] Battery positive to GND is not shorted.
- [ ] Q_RPP tab to GND is open.
- [ ] Q_BATT tab to GND is open.

## 3. Adapter Input Test, ESP32 Not Inserted

Use a current-limited bench supply if available.

- [ ] Set supply to 12V and 100mA current limit.
- [ ] Connect adapter input with correct polarity.
- [ ] Current limit does not trip.
- [ ] `TP_IN` reads about 12V.
- [ ] `TP_PROT` reads about 12V.
- [ ] `TP_BV` reads about adapter voltage minus `D_ADAPT` drop.
- [ ] `TP_GATE` reads about 11.5V to 11.8V.
- [ ] No component heats.
- [ ] Disconnect adapter.
- [ ] `TP_PROT` falls to 0V.
- [ ] `TP_GATE` falls to 0V.

## 4. Reverse Polarity Test

Use current limit.

- [ ] Set supply to 12V and 50mA current limit.
- [ ] Reverse adapter polarity briefly.
- [ ] Current remains near zero.
- [ ] `TP_PROT` does not rise.
- [ ] `TP_BV` does not rise.
- [ ] No component heats.
- [ ] Restore correct polarity.

## 5. Buck Converter Test, ESP32 Not Inserted

- [ ] Buck module was preset on the bench before installation.
- [ ] Adapter input is connected correctly.
- [ ] `TP5` reads 4.9V to 5.1V.
- [ ] `TP5` never exceeds 5.2V.
- [ ] 25 ohm / 2W dummy load on 5V rail does not collapse output.
- [ ] Buck module is warm but not hot after 10 minutes.
- [ ] LC filter components do not heat.

Stop immediately if `TP5` exceeds 5.2V. Do not insert ESP32-S3.

## 6. Battery-Only Power Path Test, ESP32 Not Inserted

- [ ] Disconnect adapter.
- [ ] Connect a charged 3S LiPo through `F_BAT` and BMS/protection board.
- [ ] `TP_BAT` reads battery voltage.
- [ ] `TP_PROT` remains 0V.
- [ ] `TP_GATE` remains 0V.
- [ ] `TP_BV` rises to battery voltage through Q_BATT.
- [ ] `TP5` reads 4.9V to 5.1V.
- [ ] `D_ADAPT` blocks battery from backfeeding `V_PROT`.
- [ ] No component heats after 10 minutes with dummy load.

This test specifically verifies the final design extension. If `TP_PROT` rises during battery-only operation, `D_ADAPT` is missing, reversed, or bypassed.

## 7. Both-Sources Priority Test, ESP32 Not Inserted

- [ ] Battery is connected.
- [ ] Adapter is connected.
- [ ] `TP_PROT` reads about 12V.
- [ ] `TP_GATE` reads about 11.5V to 11.8V.
- [ ] Q_BATT is off.
- [ ] `TP_BV` is supplied by adapter through `D_ADAPT`.
- [ ] Battery current is near zero if measured.
- [ ] Disconnect adapter.
- [ ] `TP_PROT` falls to 0V.
- [ ] `TP_GATE` falls to 0V.
- [ ] Q_BATT turns on.
- [ ] `TP_BV` remains powered from battery.
- [ ] Reconnect adapter.
- [ ] Adapter priority is restored.

Repeat adapter disconnect/reconnect 10 times. The 5V dummy load must remain powered.

## 8. DevKitC Power Test

Only start this section after Sections 1-7 pass.

- [ ] Disconnect adapter and battery.
- [ ] Insert ESP32-S3 DevKitC with USB-C facing board edge.
- [ ] Verify no bent pins.
- [ ] Reconnect adapter.
- [ ] `TP5` remains 4.9V to 5.1V.
- [ ] `TP33` reads 3.25V to 3.35V.
- [ ] ESP32-S3 enumerates over USB-C.
- [ ] No part overheats after 5 minutes.

## 9. Firmware Smoke Test

Firmware migration must be completed before this section can fully pass.

- [ ] PlatformIO environment targets `esp32-s3-devkitc-1`.
- [ ] Pin map matches [`firmware/pin_assignment_final.h`](firmware/pin_assignment_final.h).
- [ ] Serial monitor opens over USB-C.
- [ ] Boot log appears.
- [ ] `PING` returns expected response.
- [ ] `STATUS` returns without watchdog reset.
- [ ] ADC reading on GPIO1 changes when adapter/battery voltage changes.
- [ ] WiFi AP/STA behavior is retested on ESP32-S3.

## 10. Encoder Electrical Test

Test one encoder at a time.

- [ ] Encoder VCC at connector is about 5V.
- [ ] Encoder GND continuity is good.
- [ ] A/B divider output toggles 0V to about 3.3V.
- [ ] No signal line exceeds 3.6V.
- [ ] Theta A/B counts change on GPIO 4/5.
- [ ] Phi A/B counts change on GPIO 6/7.
- [ ] Wire A/B counts change on GPIO 15/16.
- [ ] Wire Z pulse is visible on GPIO 17 if used.
- [ ] No phantom counts occur while stationary.
- [ ] Direction matches firmware convention or is documented for inversion.

## 11. Full Switchover Test With ESP32 And Encoders

- [ ] Adapter connected.
- [ ] Battery connected.
- [ ] ESP32-S3 running migrated firmware.
- [ ] All encoders connected.
- [ ] Position stream is active.
- [ ] Disconnect adapter.
- [ ] ESP32-S3 stays running.
- [ ] Position stream continues.
- [ ] No encoder count jump occurs.
- [ ] Reconnect adapter.
- [ ] ESP32-S3 stays running.
- [ ] Repeat 10 cycles.

If the ESP32 resets during switchover:

- Increase `C_BV` at `BUCK_VIN`.
- Check Q_BATT gate routing.
- Check `D_ADAPT` orientation.
- Shorten battery and buck input wiring.

## 12. 30-Minute Endurance Test

- [ ] Adapter connected.
- [ ] Battery connected.
- [ ] ESP32-S3 WiFi active.
- [ ] All encoders connected.
- [ ] Position output updates at expected rate.
- [ ] No phantom counts while stationary.
- [ ] Buck module is warm but not hot.
- [ ] `D_ADAPT` is warm but not hot.
- [ ] Q_RPP and Q_BATT are not hot.
- [ ] Battery fuse holder remains cool.
- [ ] `5V_RAIL` remains within range.
- [ ] `TP_PROT`, `TP_BV`, and ADC readings remain plausible.

## 13. Acceptance Criteria

The board is acceptable for machine-side testing only if all of these are true:

- [ ] Adapter-only operation passes.
- [ ] Battery-only operation passes.
- [ ] Both-sources adapter priority passes.
- [ ] Reverse polarity test passes.
- [ ] 5V rail is verified before ESP32 insertion.
- [ ] ESP32-S3 boots and remains stable.
- [ ] All encoder channels pass electrical and firmware tests.
- [ ] Switchover does not reset ESP32.
- [ ] 30-minute endurance test passes.
- [ ] Charging procedure is documented for the operator.
