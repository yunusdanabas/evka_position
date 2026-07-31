/* Run the real dashboard page and exercise the new features end to end.
   jsdom has no canvas, so getContext is stubbed with a no-op recorder — the drawing
   calls still execute (catching TypeErrors and bad DOM ids), they just paint nowhere. */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const html = fs.readFileSync(path.join(__dirname, "dash.html"), "utf8");

const ctxStub = new Proxy({}, {
  get(_t, prop) {
    if (prop === "canvas") return { width: 300, height: 200 };
    if (prop === "measureText") return () => ({ width: 10 });
    if (prop === "setLineDash") return () => {};
    return (typeof prop === "string") ? (() => {}) : undefined;
  },
  set() { return true; },
});

const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,        // gives requestAnimationFrame
  beforeParse(win) {
    win.HTMLCanvasElement.prototype.getContext = () => ctxStub;
    win.navigator.vibrate = () => true;
    win.URL.createObjectURL = () => "blob:stub";
    win.URL.revokeObjectURL = () => {};
    win.__downloads = [];
    // Intercept the download so we can inspect what a recording/export actually emits.
    const origCreate = win.document.createElement.bind(win.document);
    win.document.createElement = (tag) => {
      const el = origCreate(tag);
      if (tag === "a") el.click = function () { win.__downloads.push({ name: this.download }); };
      return el;
    };
    win.Blob = class { constructor(parts) { win.__lastBlob = parts.join(""); } };
  },
});

const win = dom.window;
const peek = (expr) => win.eval(expr);   // let-bindings live in page global scope, not on window
const fail = [];
const ok = [];
function check(name, cond, detail) {
  (cond ? ok : fail).push(name + (detail ? "  [" + detail + "]" : ""));
}

setTimeout(() => {
  const errs = (win.__errors || []).concat();
  check("page loads with no uncaught JS errors", errs.length === 0, errs.join("; "));

  // ---- IPT: the whole point. Solve a known hidden target through the real UI. ----
  const P_true = [1200, -450, 300], L_true = 400;
  win.toggleIpt();
  check("IPT mode activates", peek("iptActive") === true);
  check("IPT panel is shown", win.getComputedStyle(win.document.getElementById("ipt-panel")).display !== "none");
  check("main panel is hidden in IPT mode",
        win.getComputedStyle(win.document.getElementById("panel-main")).display === "none");

  // FREEZE first: arming must un-freeze, or capture silently gets nothing.
  win.toggleFreeze();
  check("frozen before ARM", peek("frozen") === true);
  win.iptArm();
  check("ARM auto-unfreezes", peek("frozen") === false);
  check("armed", peek("iptArmed") === true);

  win.__sweep(P_true, L_true, 14, 35);
  check("sweep captured >= 8 points", peek("iptPts").length >= 8, "n=" + peek("iptPts").length);

  win.iptStop();
  check("SOLVE enabled after STOP",
        win.document.getElementById("btn-ipt-solve").disabled === false);

  win.document.getElementById("ipt-l-input").value = "";   // auto / self-calibrating
  win.iptSolveUI();
  const s = peek("iptSol");
  check("solve succeeded", s && s.ok === true);
  if (s && s.ok) {
    const err = Math.hypot(s.P[0]-P_true[0], s.P[1]-P_true[1], s.P[2]-P_true[2]);
    check("recovers the hidden target < 0.5 mm", err < 0.5, "err=" + err.toFixed(4) + " mm");
    check("recovers pen length L", Math.abs(s.L_hat - L_true) < 0.5,
          "L_hat=" + s.L_hat.toFixed(3));
    check("fit is graded ok", s.slip_warning === "ok" && s.geom_warning === "ok",
          s.slip_warning + "/" + s.geom_warning);
    check("P is rendered to the panel",
          win.document.getElementById("ipt-p").textContent.includes("1200"),
          win.document.getElementById("ipt-p").textContent);
    check("ADD TO SNAPSHOTS enabled on a good fit",
          win.document.getElementById("btn-ipt-snap").disabled === false);
  }

  // Known-L path (uses the differencing seed + fixed-radius Gauss-Newton)
  win.document.getElementById("ipt-l-input").value = String(L_true);
  win.iptSolveUI();
  check("known-L solve also recovers the target",
        peek("iptSol").ok && Math.hypot(peek("iptSol").P[0]-P_true[0], peek("iptSol").P[1]-P_true[1],
                                    peek("iptSol").P[2]-P_true[2]) < 0.5);

  // IPT point goes to snapshots tagged sensor-frame
  win.iptAddSnapshot();
  const snap = peek("snapshots")[peek("snapshots").length - 1];
  check("IPT snapshot is tagged sensor-frame", snap && snap.frame === "sensor");

  // A degenerate sweep must be refused, not silently trusted.
  win.iptClear();
  win.iptArm();
  win.__sweep(P_true, L_true, 14, 1.5);     // near-straight pull
  win.iptStop();
  win.document.getElementById("ipt-l-input").value = "";
  win.iptSolveUI();
  check("degenerate sweep is flagged, not trusted",
        !peek("iptSol").ok || peek("iptSol").geom_warning !== "ok",
        peek("iptSol").ok ? ("geom=" + peek("iptSol").geom_warning + " cond=" + peek("iptSol").cond.toFixed(0)) : "rejected");

  // ---- Recording: taps the wire, and keeps recording while frozen ----
  win.iptClear();
  win.toggleIpt();                          // back to the main panel
  win.toggleRecord();
  check("recording starts", peek("recOn") === true);
  win.__feed("DATA,1.00,2.00,3.00,900.00,25.000,10.000,1,1,100");
  win.toggleFreeze();                       // freeze the VIEW
  win.__feed("DATA,4.00,5.00,6.00,901.00,26.000,11.000,1,2,150");
  win.toggleFreeze();
  check("freezing the view does not punch a hole in the recording",
        peek("recBuf").length === 2, "frames=" + peek("recBuf").length);
  win.toggleRecord();                       // stop -> download
  check("stopping the recording downloads a file", win.__downloads.length > 0);
  const blob = win.__lastBlob || "";
  check("recorded file is raw DATA lines (replayable as-is)",
        blob.split("\n")[0].startsWith("DATA,1.00,2.00,3.00"), blob.split("\n")[0]);

  // ---- Exports carry the encoder readings, not just the derived x/y/z ----
  // The IPT snapshot above was added before any DATA frame reached the main panel,
  // so it doubles as the "no reading available" case.
  win.exportSnapshots();
  let csv = win.__lastBlob || "";
  check("snapshot CSV header ends with the sensor columns",
        csv.split("\r\n")[0].endsWith("wire_mm,theta_deg,phi_deg"), csv.split("\r\n")[0]);
  check("IPT-derived snapshot has blank sensor cells (a fit is not a sample)",
        csv.split("\r\n")[1].endsWith(",,,"), csv.split("\r\n")[1]);

  win.__feed("DATA,120.50,-40.10,88.30,412.30,15.240,-3.110,1,884,12043");
  win.captureSnapshot();
  win.exportSnapshots();
  csv = win.__lastBlob || "";
  const snapRow = csv.trim().split("\r\n").pop();
  check("captured snapshot carries the latched wire/theta/phi",
        snapRow.endsWith(",412.30,15.240,-3.110"), snapRow);

  win.__feed("POINT,0,120.50,-40.10,88.30,0,0,0");
  win.endSession();
  csv = win.__lastBlob || "";
  check("session CSV header ends with the sensor columns",
        csv.split("\r\n")[0].endsWith("wire_mm,theta_deg,phi_deg"), csv.split("\r\n")[0]);
  check("saved point carries the latched wire/theta/phi",
        csv.split("\r\n")[1].endsWith(",412.30,15.240,-3.110"), csv.split("\r\n")[1]);

  // ---- Protocol log ----
  win.__feed("ACK:PONG");
  win.__feed("ERR:UNKNOWN_CMD");
  const kinds = peek("logBuf").map(e => e.k);
  check("log captures ACK and ERR", kinds.includes("ack") && kinds.includes("err"));
  check("log drops 20 Hz DATA while the DATA filter is off",
        !kinds.includes("data"), kinds.join(","));

  // ---- RAW_COUNTS ----
  win.__feed("RAW,100,200,300");
  check("RAW counts render", win.document.getElementById("v-raw").textContent.includes("100"),
        win.document.getElementById("v-raw").textContent);

  // ---- Calibration: the Phase 1 data-loss fix, driven through the real handlers ----
  win.__sent = [];
  win.__feed("CAL:THETA,100000,20000.00");
  check("unsolicited theta calibration reply is ignored",
        peek("pendingRotaryPPR.theta") === 0 &&
        win.document.getElementById("btn-save-theta").disabled === true);

  win.calRotary("theta");
  check("theta COMPUTE sends the real CAL_T command",
        win.__sent.includes("CAL_T 5"), win.__sent.join(" | "));
  check("theta request records matching pending state",
        peek("pendingRotaryCal") && peek("pendingRotaryCal.axis") === "theta" &&
        peek("pendingRotaryCal.timer") !== null);
  win.__feed("CAL:PHI,100000,20000.00");
  check("wrong-axis rotary reply is ignored",
        peek("pendingRotaryPPR.phi") === 0 && peek("pendingRotaryCal.axis") === "theta");
  win.__feed("CAL:THETA,100000,20000.00");
  check("matching theta reply clears pending request", peek("pendingRotaryCal") === null);
  check("theta APPLY+SAVE button enabled after COMPUTE",
        win.document.getElementById("btn-save-theta").disabled === false);
  win.applyRotaryCal("theta", true);
  check("theta APPLY+SAVE waits for SET acknowledgement",
        !win.__sent.includes("SAVE_PPR"), win.__sent.join(" | "));
  win.__feed("ACK:PPR_ROTARY,20000.00");
  check("theta APPLY+SAVE persists after SET acknowledgement",
        win.__sent.includes("SAVE_PPR"), win.__sent.join(" | "));
  win.__feed("ACK:SAVE_PPR");
  check("saved PPR requests active-value confirmation",
        win.__sent.includes("CONSTANTS"), win.__sent.join(" | "));
  win.__feed("CONSTANTS,20000.00,8000.00,0.025000,0.018000");
  win.__sent = [];
  win.applyRotaryCal("theta", false);
  check("theta APPLY (RAM) does NOT send SAVE_PPR",
        !win.__sent.includes("SAVE_PPR"), win.__sent.join(" | "));
  win.__feed("ACK:PPR_ROTARY,20000.00");
  win.__feed("CONSTANTS,20000.00,8000.00,0.025000,0.018000");

  // Lost replies must not wedge COMPUTE or allow a late broadcast to become valid.
  win.__sent = [];
  win.calRotary("phi");
  check("phi request arms a reply timeout",
        peek("pendingRotaryCal") && peek("pendingRotaryCal.timer") !== null);
  win.expireRotaryCalRequest();
  check("lost rotary reply recovers COMPUTE",
        peek("pendingRotaryCal") === null &&
        win.document.getElementById("btn-cal-phi").disabled === false);
  win.__feed("CAL:PHI,100000,20000.00");
  check("late rotary reply after timeout is ignored",
        peek("pendingRotaryPPR.phi") === 0 &&
        win.document.getElementById("btn-save-phi").disabled === true);

  const wireCountBefore = peek("wireTrials").length;
  win.document.getElementById("wire-dist").value = "500";
  win.calWireTrial();
  check("wire trial arms a reply timeout",
        peek("wireTrialPending") === true && peek("wireTrialTimer") !== null);
  win.expireWireTrialRequest();
  check("lost wire reply recovers RECORD",
        peek("wireTrialPending") === false &&
        win.document.getElementById("btn-record-wire").disabled === false);
  win.__feed("CAL:WIRE,1.0000,0.025000,8000.00");
  check("late wire reply after timeout is ignored",
        peek("wireTrials").length === wireCountBefore);

  // ---- Modes are mutually exclusive ----
  win.toggleIpt();
  win.toggleCal();
  check("entering CALIBRATE exits IPT", peek("iptActive") === false && peek("calActive") === true);
  win.toggleCal();

  // Disconnect cleanup uses the actual WebSocket callback and clears both request locks.
  win.calRotary("theta");
  win.calWireTrial();
  check("calibration requests are pending before disconnect",
        peek("pendingRotaryCal") !== null && peek("wireTrialPending") === true);
  peek("ws.onclose()");
  check("disconnect clears rotary and wire pending state",
        peek("pendingRotaryCal") === null && peek("wireTrialPending") === false);
  check("disconnect re-enables calibration controls",
        win.document.getElementById("btn-cal-theta").disabled === false &&
        win.document.getElementById("btn-record-wire").disabled === false);

  console.log("\n=== PASS (" + ok.length + ") ===");
  ok.forEach(l => console.log("  ok   " + l));
  if (fail.length) {
    console.log("\n=== FAIL (" + fail.length + ") ===");
    fail.forEach(l => console.log("  FAIL " + l));
  }
  console.log(fail.length ? "\nRESULT: FAILED" : "\nRESULT: ALL PASSED");
  process.exit(fail.length ? 1 : 0);
}, 300);
