# EVKA Hardware Power Design Comparison

This folder compares the EVKA carrier-board hardware variants and explains which one to build. It covers the legacy 5V board, the Wemos-era 12V boards, the ESP32-S3 V2/V3 explorations, the optional V3-D onboard-charging branch, and the selected Final Design.

## Primary Deliverables

| File | Role |
|---|---|
| [`HARDWARE_COMPARISON.md`](HARDWARE_COMPARISON.md) | Full English engineering reference and decision guide with Mermaid diagrams |
| [`presentation/index.html`](presentation/index.html) | Reveal.js visual companion slide deck |

Serve the presentation from the repository root:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080/docs/hardware_design/12v_legacy/comparison/presentation/`.

## Important Correction

Older 12V source documents describe a `TP5100` path as a 3S / 12.6V charger. This comparison treats that path as unsafe or unverified for 3S LiPo charging. A fact check of common TP5100 datasheets/modules indicates TP5100 is a 1S/2S charger family, not a credible standalone 3S charger basis.

Practical result: do not choose the Original 12V or 12V All-THT designs because of their documented onboard TP5100 3S charging path. If a Wemos-compatible 12V prototype is unavoidable, do not rely on that onboard charging path for unattended 3S charging.

## Designs Compared

| Design | Folder | Short Description | Current Role |
|---|---|---|---|
| Legacy 5V + 1S LiPo | [`../5v/`](../5v/) | Wemos D1 R32, 5V input, 1S backup, TP4056, MT3608 boost | Historical baseline and signal-conditioning reference |
| Original 12V + 3S LiPo | [`../12v/`](../12v/) | Wemos D1 R32, 12V input, 3S backup, MP1584 buck, MT3608 + TP5100 path | First 12V conversion package; not recommended for new builds |
| 12V All-THT | [`../12v_tht/`](../12v_tht/) | Same 12V topology as original, but SMD discretes replaced with through-hole parts | Transitional Wemos-compatible 12V prototype option |
| V2 Industrial 12V | [`../v2/`](../v2/) | ESP32-S3, 12V input, 3S backup, external charging only, RS-485, I2C, watchdog | Industrial-feature branch |
| V3-A Simple 12V | [`../v3/`](../v3/) | ESP32-S3, 12V input, 3S backup, no onboard charger, core sensor only | Source baseline for the Final Design |
| V3-B Simple 15V + CN3722 | [`../v3/`](../v3/) | V3 with 15V input and CN3722 onboard 3S charger populated | Optional future onboard-charging branch |
| V3-C Simple 15V + XL4016 | [`../v3/`](../v3/) | V3 with 15V input and XL4016 CC/CV module populated | Supervised lab fallback only |
| V3-D Onboard 3S Module | Comparison-only branch | ESP32-S3 core with Final-style `Q_BATT + D_ADAPT`, verified 12.6V charger/BMS options, Type-C/PD alternatives, and load-isolated charging | Optional onboard-charging branch when battery service is not acceptable |
| Final Design | [`../final_design/`](../final_design/) | ESP32-S3, 12V only, 3S backup, external balance charging only, `Q_BATT` + `D_ADAPT` | Recommended new core sensor build |

The old V3 ready-made power-path module interface is not treated as an active design. [`../v3/power_path_module_interface_v3.md`](../v3/power_path_module_interface_v3.md) is explicitly marked superseded by the discrete `Q_BATT` circuit.

## High-Level Matrix

| Category | 5V Legacy | Original 12V | 12V All-THT | V2 Industrial | V3-A | V3-B | V3-C | V3-D | Final Design |
|---|---|---|---|---|---|---|---|---|---|
| MCU | Wemos D1 R32 | Wemos D1 R32 | Wemos D1 R32 | ESP32-S3 | ESP32-S3 | ESP32-S3 | ESP32-S3 | ESP32-S3 | ESP32-S3 |
| Main input | 5V | 12V | 12V | 12V | 12V | 15V | 15V | 15V or USB-C PD/module-specific | 12V |
| Battery | 1S LiPo | 3S LiPo | 3S LiPo | 3S LiPo | 3S LiPo | 3S LiPo | 3S LiPo | 3S LiPo, 5000mAh target branch | 3S LiPo |
| Charging | TP4056 onboard | TP5100 path, unsafe/unverified for 3S | Same TP5100 concern | External balance only | External balance only | CN3722 onboard plus balancing policy | XL4016 CC/CV supervised only | Verified 12.6V 1A/2A/4A or Type-C/PD charger module + BMS; validation required | External balance only |
| Source selection | Schottky OR on 5V rail | Schottky OR at buck input | Schottky OR at buck input | Active `Q_BATT` | Active `Q_BATT` | Active `Q_BATT` | Active `Q_BATT` | `Q_BATT + D_ADAPT`, charger isolated from load | `Q_BATT` + `D_ADAPT` |
| Encoder conditioning | Proven | Same as 5V | Same as 5V | Same electrical design, new pins | Same as V2 | Same as V2 | Same as V2 | Same as V3-A/Final | Same as V3-A |
| Firmware readiness | Current Wemos | Current Wemos | Current Wemos | Needs S3 migration | Needs S3 migration | Needs S3 migration | Needs S3 migration | Needs S3 migration | Needs S3 migration |
| Build difficulty | Medium | Hard | Medium | Hard | Medium | Medium-high | Hard | Medium-high | Medium |
| Best strength | Signal baseline | First 12V conversion | Hand solderability | Industrial interfaces | Simple safe core | Dedicated charger IC | Generic sourcing fallback | Onboard 3S charging branch with practical module/BMS options | Single corrected build baseline |

## Evaluation Criteria

| Criterion | Meaning |
|---|---|
| Electrical safety | Reverse polarity protection, fusing, battery fault containment, charging risk |
| Power reliability | 5V rail stability, switchover behavior, buck filtering, source priority |
| Manufacturing fit | Suitability for LPKF S63, pertinax/FR4 milling, hand soldering, no soldermask |
| Firmware readiness | How close the hardware is to the current active PlatformIO firmware |
| Maintainability | Ease of debugging, replacing parts, and validating in the field |
| Scope control | Whether the board contains only necessary functions or adds expansion complexity |
| Future value | Whether the design supports the longer-term ESP32-S3 direction |

## Individual Evaluations

### 1. Legacy 5V + 1S LiPo

**Summary:** Original Wemos D1 R32 carrier using 5V input, 1S LiPo backup, TP4056/DW01A, MT3608 boost, and the original encoder signal-conditioning network.

**Best strength:** proven encoder signal conditioning: 10k/20k dividers, 1nF filters, TVS diodes, and ferrites.

**Main weakness:** the boosted battery path can sit above the adapter path after Schottky drop, so source priority is not controlled.

**Evaluation:** useful for firmware development and as the signal-conditioning reference, but not the default for new machine-powered hardware.

### 2. Original 12V + 3S LiPo

**Summary:** First 12V redesign using Wemos D1 R32, 12V input protection, MP1584EN buck, 3S backup, Schottky OR source selection, MT3608 boost, and a TP5100 charging path.

**Best strength:** established the 12V input plus MP1584EN buck direction while keeping current firmware compatibility.

**Main weakness:** the TP5100 + 3S charging path is unsafe or unverified, and Schottky OR does not guarantee adapter priority against a full 3S pack.

**Evaluation:** valuable history, not a recommended new build.

### 3. 12V + 3S LiPo All-THT

**Summary:** Package-level rework of the original 12V design. It keeps the topology but replaces SMD discretes with through-hole equivalents such as IRF4905, P6KE18A, and axial Schottkys.

**Best strength:** easiest Wemos-compatible 12V design to hand-solder and inspect.

**Main weakness:** through-hole packages do not fix the TP5100 charging concern or Schottky source-priority ambiguity.

**Evaluation:** reasonable only as a transitional Wemos-compatible 12V prototype. Do not use its onboard TP5100 path as an unattended 3S charger.

### 4. V2 Industrial 12V

**Summary:** ESP32-S3 redesign with 12V input, 3S backup, active `Q_BATT`, external balance charging only, RS-485, I2C, watchdog, spare GPIOs, and DIN-rail planning.

**Best strength:** RS-485/Modbus, hardware watchdog, and industrial expansion on one board.

**Main weakness:** highest complexity and still no active ESP32-S3 firmware migration in the repository.

**Evaluation:** choose V2 only when industrial interfaces are real requirements.

### 5. V3-A Simple 12V

**Summary:** Simplified ESP32-S3 core board that keeps V2-style `Q_BATT`, 12V input, 3S backup, MP1584EN buck, and proven encoder conditioning while removing industrial expansion.

**Best strength:** clean simple 12V core before the final correction.

**Main weakness:** no Final Design `D_ADAPT`; V3 docs also retain optional charger branches and gate-clamp variants.

**Evaluation:** source baseline for Final Design, but superseded for new builds.

### 6. V3-B Simple 15V + CN3722 Onboard Charging

**Summary:** V3 core board with a CN3722 3S charger module and a 15V adapter requirement.

**Best strength:** most credible onboard 3S charging branch because CN3722 is a dedicated charger controller with CC/CV behavior and charge-status output.

**Main weakness:** no onboard cell balancing, 15V adapter dependency, charger module verification, and extra validation burden.

**Evaluation:** keep as a future onboard-charging option only if product requirements force onboard charging.

### 7. V3-C Simple 15V + XL4016 CC/CV Charging

**Summary:** V3 core board with a generic XL4016 CC/CV buck module configured as a 12.60V current-limited source.

**Best strength:** generic module sourcing and supervised bench adjustability.

**Main weakness:** no automatic LiPo charge termination; float risk if left connected.

**Evaluation:** lab fallback only, not field hardware.

### 8. V3-D Onboard 3S Charger Module

**Summary:** Optional ESP32-S3 branch that keeps Final-style `Q_BATT + D_ADAPT` source selection but adds a verified 12.6V CC/CV 3S charger path and a documented 3S BMS/protection board. The practical module set includes 1A slow-charge, 2A first-prototype, 4A fast-charge, Type-C 2A, and IP2369/IP2326-style USB-C PD branches, all exact-module dependent.

**Best strength:** practical onboard charging for a 5000mAh-class 3S pack, with charge-only mode as the safest first integrated version and power-path/load-sharing as the clean final run-while-charging architecture.

**Main weakness:** charger module quality, Type-C/PD configuration, termination, thermal behavior, BMS balancing, adapter sizing, and load isolation all become required validation gates. Parallel battery-load charging should be avoided.

**Evaluation:** use only when onboard charging is mandatory. It is safer than generic CC/CV fallback because it requires a real 3S charger and load isolation, but it is still more complex and riskier than Final Design with external balance charging.

### 9. Final Design

**Summary:** Final selected 12V-only ESP32-S3 core board based on V3-A. It removes onboard charging branches, adds `D_ADAPT`, documents `Q_BATT` OFF-state margin, and requires external 3S balance charging.

**Best strength:** single unambiguous build package with corrected source selection and no onboard charging ambiguity.

**Main weakness:** still needs ESP32-S3 firmware migration and first-board validation.

**Evaluation:** recommended new EVKA core sensor build.

## Use-Case Fit

| Use Case | Best-Fit Design | Reason |
|---|---|---|
| New core sensor build | Final Design | Selected 12V-only baseline with `Q_BATT`, `D_ADAPT`, and external balance charging |
| Historical Wemos bench reference | 5V Legacy | Lowest software risk for legacy bench work |
| Historical Wemos 12V prototype | 12V All-THT | Wemos-compatible and easier to hand-solder, but charging path must be avoided/reworked |
| Industrial/PLC integration | V2 Industrial | RS-485, I2C, watchdog, status LEDs, spare GPIOs |
| Onboard charging required | V3-D Onboard 3S Module | Best comparison branch for verified charger module + BMS + load isolation |
| CN3722-specific onboard charge | V3-B + CN3722 | Dedicated charger branch, subject to module and balancing policy validation |
| Lab fallback onboard charge | V3-C + XL4016 | Supervised CC/CV source only; not unattended LiPo charging |
| Historical reference | 5V Legacy, Original 12V | Useful for signal conditioning and design evolution |

## LiPo Charging Method Summary

| Pack | Recommended method | Notes |
|---|---|---|
| 1S | TP4056 module or external 1S charger | Correct for the 5V Legacy architecture; no balancing problem because there is only one cell |
| 2S | TP5100 in 2S mode or external 2S balance charger | Correct TP5100 use at 8.4V, but EVKA would lose 3S energy margin |
| 3S | External 3S balance charger | Recommended for Final Design; handles termination and balancing off-board |
| 3S onboard required | V3-D verified 12.6V charger module + BMS, or CN3722-specific V3-B | Requires charge-only or power-path architecture, load isolation, charger/BMS validation, thermal testing, and balancing/service policy |
| 3S lab fallback | XL4016/XL4015 CC/CV buck | Supervised only; no automatic LiPo charge termination |
| 3S rejected paths | TP5100 path labeled as 3S, BMS-only/direct adapter charging | Unsafe or unverified charge control; do not use for new builds |

## Onboard-Charging Branch Guidance

V3-D is the branch to develop only when onboard charging is mandatory. The practical recommendation is **3S 12.6V 2A charger module + 3S 25A or 40A balanced BMS + 15V / 3A adapter**. Use the 40A BMS only when the wiring, connector, fuse, and expected startup peaks justify it; the BMS current rating is the load/discharge class, not the charge-current target.

| Option | Stack | Best Use | Caution |
|---|---|---|---|
| Option A - simple prototype | 3S 12.6V 2A charger module + 25A/40A balanced BMS + 15V / 3A adapter | Best cheap/practical onboard branch for a 5000mAh pack | Verify CC/CV termination, heat, adapter headroom, BMS thresholds, and load isolation |
| Option B - clean connector | 3S Type-C 2A charger module + 25A/40A balanced BMS + required USB-C PD/QC adapter | Best when USB-C is important for the enclosure | Verify real 3S / 12.60V output; a Type-C connector alone does not prove PD or 3S support |
| Option C - professional custom PCB | TI `BQ24170` charger/power-path circuit + 3S BMS/protection + separated system load path | Best engineered future onboard-charging path | Requires SMD layout, thermal design, validation, and still does not replace cell protection/balancing policy |

| Architecture | Can Run While Charging? | Recommendation |
|---|---:|---|
| Charge-only mode | No | Best first integrated onboard-charging prototype; disconnect the system while charging |
| Power-path / load-sharing | Yes | Best final onboard-charging architecture; adapter powers system while charger sees battery path only |
| Parallel battery-load charging | Yes | Avoid because system load can confuse charger termination |
| Docking-style charging | Optional | Good enclosure/user-experience variant when dock detect can stop high-current loads |
| Smart MCU-supervised charging | Optional | Useful safety/control layer; does not replace charger or BMS |
| Removable battery / external balance charging | No | Safest development workflow and the selected Final Design policy |

## Key Design Lessons

| Lesson | Designs Affected | Conclusion |
|---|---|---|
| Schottky OR is simple but not priority-safe | 5V, Original 12V, 12V All-THT | It selects the higher post-diode voltage, not the source you prefer |
| 3S LiPo charging dominates safety risk | Original 12V, 12V All-THT, V3-B, V3-C | External balance charging is the lowest-risk default |
| Onboard charging requires load isolation | V3-B, V3-D | The system must run from adapter while the charger sees only the battery path |
| Parallel load charging corrupts termination | Onboard-charging branches | Avoid tying charger, battery, and system load to one uncontrolled node |
| `Q_BATT` makes adapter priority explicit | V2, V3, Final | Adapter present turns the battery path off by design |
| `D_ADAPT` closes the remaining backfeed issue | Final | Battery-powered `BUCK_VIN` cannot raise the adapter-sense rail |
| ESP32-S3 is the future direction but not firmware-ready yet | V2, V3, Final | Hardware docs are ahead of active firmware |
| Simpler boards are easier to validate | V3-A, Final | Removing unused expansion and charger branches reduces bring-up risk |

## Final Recommendation

For the next new EVKA core sensor board, choose **Final Design**.

Reasons:

- It keeps the safer active `Q_BATT` adapter-priority source selection.
- It adds `D_ADAPT`, preventing battery-powered `BUCK_VIN` from backfeeding adapter sense/gate drive.
- It removes all onboard LiPo charger branches and requires an external 3S balance charger.
- It is simpler to build and validate than V2 because RS-485, I2C, watchdog, and spare GPIOs are intentionally excluded.
- It is a better long-term platform than Wemos-based boards because it targets ESP32-S3.
- It preserves the proven encoder signal-conditioning network used throughout the project.

Use **V2** instead only if the final product truly needs RS-485/Modbus, I2C expansion, external watchdog, spare GPIOs, or DIN-rail industrial features on the main board.

Use **V3-D** instead only if onboard charging is mandatory. Start with Option A: verified 12.6V/2A charger module, 3S 25A or 40A balanced BMS, and 15V / 3A adapter. Use Option B only when USB-C enclosure convenience matters and the exact module proves 3S / 12.60V behavior. Use Option C (`BQ24170` power-path charger) for a future professional custom PCB. Keep `Q_BATT + D_ADAPT` load isolation and validate termination, balancing behavior, thermal rise, adapter sizing, and backfeed behavior.

Use **12V All-THT** only when intentionally rebuilding the historical Wemos-compatible 12V prototype, and do not rely on the TP5100 path for unattended 3S charging.

Avoid choosing **Original 12V** or **V3-C** as default new builds. They remain useful references, but their charging and validation burden is higher than the benefit they provide.
