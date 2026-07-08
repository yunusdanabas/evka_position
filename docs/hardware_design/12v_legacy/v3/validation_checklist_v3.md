# Validation Checklist — EVKA Position V3

> Bring-up sequence for the V3 12V ESP32-S3 carrier.  
> Do not insert the ESP32-S3 DevKitC until the 5V rail is verified.

---

## 1. Pre-Power Inspection

- [ ] PCB is clean; no copper burrs from milling.
- [ ] No shorts between `12V`, `BAT+`, `BUCK_VIN`, `5V_RAIL`, `3V3`, and `GND`.
- [ ] All wire vias are soldered on both sides.
- [ ] IRF4905 orientation is correct: Gate, Drain, Source verified.
- [ ] IRF4905 tab cannot touch grounded metal.
- [ ] TVS diode polarity is correct.
- [ ] Electrolytic capacitors have correct polarity.
- [ ] Encoder divider resistors are 10k top and 20k bottom.
- [ ] Encoder filter capacitors are 1nF, not 100nF.
- [ ] Battery fuse is installed close to battery positive.
- [ ] Power-path module wiring matches its own documentation.
- [ ] ESP32-S3 DevKitC is not inserted yet.

---

## 2. Adapter Input Test

Use a current-limited bench supply if possible.

- [ ] Set bench supply to 12V and 100mA current limit.
- [ ] Connect adapter input with correct polarity.
- [ ] Current limit does not trip.
- [ ] `TP12 / V12_PROT` reads about 12V.
- [ ] Reverse-polarity test with current limit confirms no significant current.
- [ ] Increase current limit to 1A after basic checks pass.

---

## 3. Power-Path Module Test

Run these before connecting the buck output to ESP32.

- [ ] Adapter-only module output is stable.
- [ ] Battery-only module output is stable.
- [ ] Both-sources mode does not drain battery unexpectedly.
- [ ] Removing adapter switches to battery without dangerous voltage drop.
- [ ] Reconnecting adapter restores adapter source.
- [ ] Module temperature is acceptable after 10 minutes under dummy load.

Use [`power_path_module_interface_v3.md`](power_path_module_interface_v3.md) for detailed tests.

---

## 4. Buck Converter Test

- [ ] Buck module was pre-set on the bench with dummy load.
- [ ] `BUCK_VIN` is connected to selected source.
- [ ] `5V_RAIL` is 5.05V target before final load, or 4.9-5.1V under real load.
- [ ] 5V rail does not exceed 5.2V.
- [ ] Buck module does not overheat after 10 minutes with 25 ohm / 2W or equivalent load.
- [ ] LC filter output is wired correctly.

Stop immediately if `5V_RAIL` is above 5.5V.

---

## 5. DevKitC Power Test

Only after the previous sections pass:

- [ ] Disconnect power.
- [ ] Insert ESP32-S3 DevKitC into female headers.
- [ ] Verify orientation: USB-C faces board edge.
- [ ] Reconnect 12V adapter.
- [ ] `TP5 / 5V_RAIL` stays in range.
- [ ] DevKitC `3V3` pin reads 3.25-3.35V.
- [ ] ESP32-S3 enumerates over USB-C.
- [ ] No component overheats after 5 minutes.

---

## 6. Encoder Electrical Test

Test one encoder at a time.

- [ ] Encoder VCC at connector is about 5V.
- [ ] Encoder GND continuity is good.
- [ ] A/B signal at divider junction is 0-3.3V logic, not 5V.
- [ ] No signal line exceeds 3.6V during manual motion.
- [ ] Counts change in firmware when the encoder is moved.
- [ ] Direction matches mechanical convention or is documented for firmware inversion.
- [ ] No phantom counts while encoder is still.

Repeat for Theta, Phi, and Wire.

---

## 7. Backup Switchover Test

- [ ] Connect adapter and charged 3S LiPo.
- [ ] Run ESP32-S3 + all encoders.
- [ ] Confirm adapter source is powering the module if the module exposes status.
- [ ] Unplug adapter.
- [ ] ESP32-S3 should remain running.
- [ ] `BUCK_VIN` follows battery voltage.
- [ ] Reconnect adapter.
- [ ] ESP32-S3 should remain running.
- [ ] Repeat 10 cycles.
- [ ] No encoder count jump occurs during switching.

If ESP32 resets, add more `BUCK_VIN` bulk capacitance, improve module selection, or reduce wiring length.

---

## 8. 30-Minute System Test

- [ ] Adapter connected.
- [ ] Battery connected.
- [ ] ESP32-S3 WiFi active.
- [ ] All encoders connected.
- [ ] Position output updates at expected rate.
- [ ] No phantom counts while stationary.
- [ ] Buck module is warm but not hot.
- [ ] Power-path module is warm but not hot.
- [ ] Battery fuse holder remains cool.
- [ ] No voltage sag below acceptable range.

Record results in the project validation log before using the board in a machine.
