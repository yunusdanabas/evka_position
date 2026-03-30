#include "WebDashboard.h"

#if ENABLE_WIFI

#include <Preferences.h>

// ============================================================================
// Embedded HTML dashboard (PROGMEM)
// ============================================================================

static const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EvkaPosition</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#e0e0e0;font-family:monospace;overflow:hidden;touch-action:none}
#app{display:grid;height:100vh;grid-template-rows:32px 1fr;grid-template-columns:1fr 220px 300px}
#hdr{grid-column:1/-1;grid-row:1;display:flex;align-items:center;height:32px;padding:0 10px;
     background:#0d1226;border-bottom:1px solid #2a3550;font-size:12px;gap:10px}
#hdr-title{color:#00ffff;font-size:13px;font-weight:bold;letter-spacing:2px;flex:1}
#conn-led{width:9px;height:9px;border-radius:50%;background:#ff3333;box-shadow:0 0 6px #ff3333;
          flex-shrink:0;transition:background .3s,box-shadow .3s}
#conn-led.ok  {background:#00ff88;box-shadow:0 0 6px #00ff88}
#conn-led.warn{background:#ffd700;box-shadow:0 0 6px #ffd700}
#hdr-ts{color:#556677;font-size:11px}
#hdr button{min-height:24px;padding:2px 8px;font-size:11px;border:1px solid #446;color:#8899aa;
            background:transparent;border-radius:3px;touch-action:manipulation;cursor:pointer}
#hdr button.active{border-color:#00ffff;color:#00ffff}
#btn-freeze.active{border-color:#ff8c00;color:#ff8c00}
#cv{grid-column:1;grid-row:2;background:#0f0f23;touch-action:none;display:block;width:100%;height:100%}
#views2d{grid-column:2;grid-row:2;display:flex;flex-direction:column;gap:2px;background:#0a0a1a}
.v2d-section{flex:1;min-height:0;display:flex;flex-direction:column}
.v2d-title{font-size:10px;color:#8899aa;text-align:center;padding:2px 0;flex-shrink:0}
#views2d canvas{flex:1;width:100%;min-height:0;display:block;background:#0f0f23}
#panel{grid-column:3;grid-row:2;padding:10px;overflow-y:auto;background:#16213e}
.sep{border-top:1px solid #2a3550;margin:6px 0}
.section-lbl{font-size:10px;color:#8899aa;letter-spacing:1px;margin:4px 0 3px;font-weight:bold}
.row{display:flex;justify-content:space-between;padding:2px 0;font-size:12px}
.lbl{color:#8899aa}.val{color:#eef;font-weight:bold;font-variant-numeric:tabular-nums}
.vcard{padding:7px 10px;background:#111828;border:1px solid #2a3550;border-radius:6px;margin:3px 0}
.vcard-label{font-size:10px;color:#8899aa;letter-spacing:1px;margin-bottom:2px}
.vcard-row{display:flex;align-items:baseline;gap:6px}
.vcard-value{font-size:20px;font-weight:bold;color:#00ffff;font-variant-numeric:tabular-nums}
.vcard-unit{font-size:11px;color:#556677}
.vcard.invalid .vcard-value{color:#ff3333}
.btn-row{display:flex;gap:6px;margin-top:8px}
.btn-row button{flex:1;min-height:48px;padding:0 8px;font-size:12px;font-family:monospace;
  border:1px solid #00ffff;color:#00ffff;background:transparent;border-radius:5px;
  touch-action:manipulation;-webkit-tap-highlight-color:transparent;cursor:pointer}
.btn-row button:active{background:#00ffff;color:#000}
button.btn-amber{border-color:#ffd700;color:#ffd700}
button.btn-amber:active{background:#ffd700;color:#000}
button.btn-danger{border-color:#ff4444;color:#ff4444}
button.btn-danger:active{background:#ff4444;color:#000}
button.is-set{border-color:#44ff44;color:#44ff44;opacity:0.65}
button:disabled{opacity:0.35;pointer-events:none}
#status{font-size:11px;color:#8899aa;margin-top:6px;min-height:16px}
@media(orientation:portrait),(max-width:767px){
 #app{grid-template-rows:32px 55vh 1fr;grid-template-columns:1fr 1fr}
 #cv{grid-column:1/-1;grid-row:2}
 #views2d{grid-column:1;grid-row:3;flex-direction:row}
 #panel{grid-column:2;grid-row:3}
}
#cal-view{grid-column:1/-1;grid-row:2;display:none;overflow-y:auto;
  background:#0f0f23;padding:16px;touch-action:pan-y}
.cal-tabs{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.cal-tab{flex:1;min-width:80px;min-height:48px;font-size:13px;font-family:monospace;
  border:1px solid #446;color:#8899aa;background:transparent;border-radius:5px;
  touch-action:manipulation;-webkit-tap-highlight-color:transparent;cursor:pointer}
.cal-tab.active{border-color:#00ffff;color:#00ffff}
.cal-step{background:#111828;border:1px solid #2a3550;border-radius:8px;padding:14px;margin-bottom:12px}
.cal-step-title{font-size:10px;color:#8899aa;letter-spacing:1px;margin-bottom:10px;font-weight:bold}
.cal-step input[type=number]{width:100%;padding:10px;font-size:16px;font-family:monospace;
  background:#0a0a1a;border:1px solid #446;color:#eef;border-radius:4px;
  margin-bottom:8px;box-sizing:border-box}
.cal-row{display:flex;gap:8px;margin-bottom:8px}
.cal-row input[type=number]{flex:1;padding:10px;font-size:14px;font-family:monospace;
  background:#0a0a1a;border:1px solid #446;color:#eef;border-radius:4px;box-sizing:border-box}
.cal-row label{font-size:11px;color:#8899aa;align-self:center;min-width:20px}
.cal-result{font-size:13px;color:#00ff88;font-family:monospace;margin:8px 0;min-height:18px;word-break:break-all}
.cal-warn{color:#ffd700}
.cal-turns{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.cal-turns input[type=number]{width:80px;padding:8px;font-size:18px;font-family:monospace;text-align:center;
  background:#0a0a1a;border:1px solid #446;color:#eef;border-radius:4px}
.cal-turns button{min-height:40px;width:40px;font-size:20px;border:1px solid #446;
  color:#8899aa;background:transparent;border-radius:4px;cursor:pointer;touch-action:manipulation}
.cal-constants{background:#0a0a1a;border:1px solid #2a3550;border-radius:6px;
  padding:10px;font-size:12px;font-family:monospace;color:#8899aa;margin-bottom:12px}
.cal-constants span{color:#eef}
.cal-table{width:100%;font-size:11px;border-collapse:collapse;margin-top:8px}
.cal-table th,.cal-table td{padding:4px 6px;border:1px solid #2a3550;text-align:right;font-family:monospace}
.cal-table th{color:#8899aa;background:#0a0a1a;font-size:10px}
.cal-table td:first-child{color:#8899aa;text-align:center}
.cal-live{background:#0a1520;border:1px solid #1a3550;border-radius:6px;padding:10px 12px;font-family:monospace;margin-bottom:12px}
.cal-live-row{display:flex;flex-wrap:wrap;gap:6px 20px;align-items:baseline;margin-bottom:4px}
.cal-live-row:last-child{margin-bottom:0}
.cal-live-lbl{font-size:11px;color:#8899aa;min-width:14px}
.cal-live-val{font-size:17px;font-weight:bold;color:#00ffff;font-variant-numeric:tabular-nums;min-width:58px;display:inline-block}
.cal-live-unit{font-size:10px;color:#556677}
.cal-live-sep{color:#2a3550;font-size:12px;align-self:center}
.sz-btn{float:right;padding:1px 6px;font-size:9px;font-family:monospace;border:1px solid #446;
  color:#8899aa;background:transparent;border-radius:3px;cursor:pointer;touch-action:manipulation}
.sz-btn:active{background:#00ffff;color:#000}
.minmax-row{display:flex;gap:4px;font-size:10px;margin-top:2px;padding-top:2px;border-top:1px solid #1a2540}
.minmax-row .lbl{color:#556677}.minmax-row .val{color:#aabbcc;font-variant-numeric:tabular-nums}
</style>
</head>
<body>
<div id="app">
<div id="hdr">
 <span id="hdr-title">EVKAPOSITION</span>
 <div id="conn-led"></div>
 <button id="btn-freeze" onclick="toggleFreeze()">FREEZE</button>
 <button id="btn-axes" onclick="toggleAxes()">AXES</button>
 <button id="btn-cal" onclick="toggleCal()">CALIBRATE</button>
 <span id="hdr-ts"></span>
</div>
<canvas id="cv"></canvas>
<div id="views2d">
 <div class="v2d-section"><div class="v2d-title">XY</div><canvas id="cv_xy"></canvas></div>
 <div class="v2d-section"><div class="v2d-title">XZ</div><canvas id="cv_xz"></canvas></div>
 <div class="v2d-section"><div class="v2d-title">YZ</div><canvas id="cv_yz"></canvas></div>
</div>
<div id="panel">
 <div class="section-lbl">POSITION</div>
 <div class="vcard" id="card-x">
  <div class="vcard-label">X AXIS <button class="sz-btn" onclick="softZero('x')">X=0</button></div>
  <div class="vcard-row"><span class="vcard-value" id="vx">--</span><span class="vcard-unit">mm</span></div>
  <div class="minmax-row"><span class="lbl">Min:</span><span class="val" id="mm-x-min">--</span><span class="lbl">Max:</span><span class="val" id="mm-x-max">--</span></div>
 </div>
 <div class="vcard" id="card-y">
  <div class="vcard-label">Y AXIS <button class="sz-btn" onclick="softZero('y')">Y=0</button></div>
  <div class="vcard-row"><span class="vcard-value" id="vy">--</span><span class="vcard-unit">mm</span></div>
  <div class="minmax-row"><span class="lbl">Min:</span><span class="val" id="mm-y-min">--</span><span class="lbl">Max:</span><span class="val" id="mm-y-max">--</span></div>
 </div>
 <div class="vcard" id="card-z">
  <div class="vcard-label">Z AXIS <button class="sz-btn" onclick="softZero('z')">Z=0</button></div>
  <div class="vcard-row"><span class="vcard-value" id="vz">--</span><span class="vcard-unit">mm</span></div>
  <div class="minmax-row"><span class="lbl">Min:</span><span class="val" id="mm-z-min">--</span><span class="lbl">Max:</span><span class="val" id="mm-z-max">--</span></div>
 </div>
 <div class="sep"></div>
 <div class="section-lbl">SENSOR READINGS</div>
 <div class="row"><span class="lbl">R (draw-wire)</span><span class="val" id="sr_r">--</span></div>
 <div class="row"><span class="lbl">&theta; theta</span><span class="val" id="sr_t">--</span></div>
 <div class="row"><span class="lbl">&phi; phi</span><span class="val" id="sr_p">--</span></div>
 <div class="row"><span class="lbl">Valid</span><span class="val" id="vv">--</span></div>
 <div class="row"><span class="lbl">Frame</span><span class="val" id="vf">--</span></div>
 <div class="sep"></div>
 <div class="section-lbl">DISTANCE</div>
 <div class="row"><span class="lbl">&#8599; From Origin</span><span class="val" id="v_dist_origin">--</span></div>
 <div class="row"><span class="lbl">&#8596; Last 2 Pts</span><span class="val" id="v_dist_pp">--</span></div>
 <div class="sep"></div>
 <div class="section-lbl">SESSION STATS</div>
 <div class="row"><span class="lbl">Points saved</span><span class="val" id="vn">0</span></div>
 <div class="row"><span class="lbl">Min R</span><span class="val" id="stat_min_r">--</span></div>
 <div class="row"><span class="lbl">Max R</span><span class="val" id="stat_max_r">--</span></div>
 <div class="row"><span class="lbl">Origin</span><span class="val" id="origin_label">not set</span></div>
 <div class="sep"></div>
 <div class="section-lbl">SESSION</div>
 <div class="btn-row">
  <button id="btn-origin" onclick="saveOrigin()" class="btn-amber">SAVE ORIGIN</button>
  <button id="btn-point" onclick="savePoint()" disabled>SAVE POINT</button>
 </div>
 <div class="btn-row">
  <button id="btn-export" onclick="endSession()" class="btn-danger" disabled>END &amp; EXPORT CSV</button>
 </div>
 <div id="sessionInfo" style="font-size:11px;color:#8899aa;margin-top:5px">No session active</div>
 <div id="savedList" style="max-height:100px;overflow-y:auto;font-size:11px;color:#7fffd4;
      font-family:monospace;line-height:1.7;margin-top:3px"></div>
 <div class="sep"></div>
 <div class="section-lbl">CONTROL</div>
 <div class="btn-row">
  <button onclick="sendCmd('ZERO')">ZERO (HW)</button>
  <button onclick="softZeroAll()">ZERO (SW)</button>
  <button onclick="clearTrail()">CLEAR</button>
 </div>
 <div class="btn-row">
  <button onclick="resetMinMax()" class="btn-amber">RESET MIN/MAX</button>
  <button onclick="sendCmd('PING')">PING</button>
 </div>
 <div class="sep"></div>
 <div class="section-lbl">SNAPSHOTS</div>
 <div class="btn-row">
  <button onclick="captureSnapshot()">CAPTURE</button>
  <button onclick="exportSnapshots()" class="btn-amber" id="btn-snap-export" disabled>EXPORT CSV</button>
  <button onclick="clearSnapshots()" class="btn-danger">CLEAR</button>
 </div>
 <div id="snap-count" style="font-size:11px;color:#8899aa;margin-top:3px">0 snapshots</div>
 <div id="snap-list" style="max-height:100px;overflow-y:auto;font-size:10px;color:#7fffd4;
      font-family:monospace;line-height:1.6;margin-top:3px"></div>
 <div class="sep"></div>
 <div class="section-lbl">WIFI SETTINGS</div>
 <div class="vcard">
  <div class="row"><span class="lbl">Router IP</span><span class="val" id="v-router-ip">--</span></div>
  <div class="row"><span class="lbl">RSSI</span><span class="val" id="v-rssi">--</span></div>
 </div>
 <div style="display:flex;gap:4px;margin:4px 0">
  <input type="text" id="wifi-ssid" placeholder="Network SSID" style="flex:1;padding:6px;font-size:11px;font-family:monospace;background:#0a0a1a;border:1px solid #446;color:#eef;border-radius:3px">
  <input type="password" id="wifi-pass" placeholder="Password" style="flex:1;padding:6px;font-size:11px;font-family:monospace;background:#0a0a1a;border:1px solid #446;color:#eef;border-radius:3px">
 </div>
 <div class="btn-row">
  <button onclick="saveWifi()" class="btn-amber">SAVE &amp; REBOOT</button>
  <button onclick="forgetWifi()" class="btn-danger">FORGET</button>
 </div>
 <div class="sep"></div>
 <div class="section-lbl">SYSTEM INFO</div>
 <div class="row"><span class="lbl">Free Heap</span><span class="val" id="v-heap">--</span></div>
 <div class="row"><span class="lbl">Uptime</span><span class="val" id="v-uptime">--</span></div>
 <div class="row"><span class="lbl">TCP Clients</span><span class="val" id="v-tcp">--</span></div>
 <div id="status">Connecting...</div>
</div>
<!-- Calibration view — full width, shown when CALIBRATE tab active -->
<div id="cal-view">
 <div class="cal-tabs">
  <button class="cal-tab active" onclick="showCalStage('wire')">WIRE</button>
  <button class="cal-tab" onclick="showCalStage('theta')">THETA</button>
  <button class="cal-tab" onclick="showCalStage('phi')">PHI</button>
  <button class="cal-tab" onclick="showCalStage('endpoint')">ENDPOINT</button>
 </div>
 <div class="cal-constants">
  PPR_R: <span id="const-ppr-r">--</span> &nbsp;
  PPR_W: <span id="const-ppr-w">--</span> &nbsp;
  mm/pulse: <span id="const-mm-pp">--</span> &nbsp;
  deg/pulse: <span id="const-deg-pp">--</span>
 </div>
 <div class="cal-live">
  <div class="cal-live-row">
   <span class="cal-live-lbl">R</span><span class="cal-live-val" id="cl-r">--</span><span class="cal-live-unit">mm</span>
   <span class="cal-live-sep">|</span>
   <span class="cal-live-lbl">&theta;</span><span class="cal-live-val" id="cl-t">--</span><span class="cal-live-unit">deg</span>
   <span class="cal-live-sep">|</span>
   <span class="cal-live-lbl">&phi;</span><span class="cal-live-val" id="cl-p">--</span><span class="cal-live-unit">deg</span>
  </div>
  <div class="cal-live-row">
   <span class="cal-live-lbl">X</span><span class="cal-live-val" id="cl-x">--</span><span class="cal-live-unit">mm</span>
   <span class="cal-live-sep">|</span>
   <span class="cal-live-lbl">Y</span><span class="cal-live-val" id="cl-y">--</span><span class="cal-live-unit">mm</span>
   <span class="cal-live-sep">|</span>
   <span class="cal-live-lbl">Z</span><span class="cal-live-val" id="cl-z">--</span><span class="cal-live-unit">mm</span>
  </div>
 </div>
 <!-- WIRE stage -->
 <div id="cal-wire">
  <div class="cal-step">
   <div class="cal-step-title">FOR EACH TRIAL: ZERO WIRE → PULL → RECORD</div>
   <div class="cal-row">
    <button style="flex:0 0 110px;min-height:44px;border:1px solid #446;color:#8899aa;background:transparent;border-radius:5px;font-family:monospace;touch-action:manipulation;cursor:pointer" onclick="sendCmd('ZERO_W')">ZERO WIRE</button>
    <input type="number" id="wire-dist" placeholder="dist mm" min="50" max="2000">
    <button style="flex:0 0 90px;min-height:44px;border:1px solid #00ffff;color:#00ffff;background:transparent;border-radius:5px;font-family:monospace;touch-action:manipulation;cursor:pointer" onclick="calWireTrial()">RECORD</button>
   </div>
   <div class="cal-result" id="wire-trial-result">—</div>
  </div>
  <div class="cal-step">
   <div class="cal-step-title">TRIALS: <span id="wire-n">0</span> &nbsp;|&nbsp; MEAN PPR_WIRE: <span id="wire-mean" style="color:#00ffff">—</span> &nbsp;|&nbsp; SPREAD: <span id="wire-spread">—</span></div>
   <table class="cal-table" id="wire-table">
    <tr><th>#</th><th>Actual mm</th><th>Factor</th><th>PPR_WIRE</th></tr>
   </table>
   <div class="btn-row" style="margin-top:8px">
    <button onclick="clearWireTrials()" class="btn-danger">CLEAR TRIALS</button>
   </div>
  </div>
  <div class="cal-step">
   <div class="cal-step-title">APPLY MEAN VALUE</div>
   <div class="btn-row">
    <button id="btn-apply-wire" onclick="applyWireMean(false)" disabled>APPLY (RAM)</button>
    <button id="btn-save-wire" onclick="applyWireMean(true)" disabled class="btn-amber">APPLY + SAVE (NVS)</button>
   </div>
   <div class="cal-result cal-warn" id="wire-apply-status">—</div>
  </div>
 </div>
 <!-- THETA stage -->
 <div id="cal-theta" style="display:none">
  <div class="cal-step">
   <div class="cal-step-title">STEP 1 — RESET THETA ENCODER</div>
   <div class="btn-row"><button onclick="sendCmd('ZERO_T')">ZERO THETA</button></div>
  </div>
  <div class="cal-step">
   <div class="cal-step-title">STEP 2 — ROTATE N FULL TURNS (same direction)</div>
   <div class="cal-turns">
    <button onclick="adjTurns('theta',-1)">&#8722;</button>
    <input type="number" id="rot-theta-turns" value="5" min="1" max="20">
    <button onclick="adjTurns('theta',1)">+</button>
    <span style="color:#8899aa;font-size:12px">turns</span>
   </div>
   <div class="btn-row"><button onclick="calRotary('theta')">COMPUTE</button></div>
   <div class="cal-result" id="theta-result">—</div>
  </div>
  <div class="cal-step">
   <div class="cal-step-title">STEP 3 — APPLY (RAM ONLY)</div>
   <div class="btn-row"><button id="btn-apply-theta" onclick="applyRotaryCal('theta')" disabled>APPLY PPR_ROTARY</button></div>
   <div class="cal-result cal-warn" id="theta-apply-status">—</div>
  </div>
 </div>
 <!-- PHI stage -->
 <div id="cal-phi" style="display:none">
  <div class="cal-step">
   <div class="cal-step-title">STEP 1 — RESET PHI ENCODER</div>
   <div class="btn-row"><button onclick="sendCmd('ZERO_P')">ZERO PHI</button></div>
  </div>
  <div class="cal-step">
   <div class="cal-step-title">STEP 2 — ROTATE N FULL TURNS (same direction)</div>
   <div class="cal-turns">
    <button onclick="adjTurns('phi',-1)">&#8722;</button>
    <input type="number" id="rot-phi-turns" value="5" min="1" max="20">
    <button onclick="adjTurns('phi',1)">+</button>
    <span style="color:#8899aa;font-size:12px">turns</span>
   </div>
   <div class="btn-row"><button onclick="calRotary('phi')">COMPUTE</button></div>
   <div class="cal-result" id="phi-result">—</div>
  </div>
  <div class="cal-step">
   <div class="cal-step-title">STEP 3 — APPLY (RAM ONLY)</div>
   <div class="btn-row"><button id="btn-apply-phi" onclick="applyRotaryCal('phi')" disabled>APPLY PPR_ROTARY</button></div>
   <div class="cal-result cal-warn" id="phi-apply-status">—</div>
  </div>
 </div>
 <!-- ENDPOINT stage -->
 <div id="cal-endpoint" style="display:none">
  <div class="cal-step">
   <div class="cal-step-title">STEP 1 — MOVE PROBE TO WORLD ORIGIN (0,0,0) THEN SET</div>
   <div class="btn-row"><button id="btn-ep-origin" onclick="setEndpointOrigin()" class="btn-amber">SET ORIGIN</button></div>
   <div class="cal-result" id="ep-origin-status">Origin not set</div>
  </div>
  <div class="cal-step" id="ep-step-points" style="display:none">
   <div class="cal-step-title">STEP 2 — MOVE TO KNOWN OFFSET FROM ORIGIN, THEN RECORD</div>
   <div class="cal-row">
    <label>X</label><input type="number" id="ep-x" placeholder="mm" value="0">
    <label>Y</label><input type="number" id="ep-y" placeholder="mm" value="0">
    <label>Z</label><input type="number" id="ep-z" placeholder="mm" value="0">
   </div>
   <div class="btn-row"><button onclick="recordEndpointPt()">RECORD POINT</button></div>
   <div class="cal-result" id="ep-status">0 points recorded</div>
  </div>
  <div class="cal-step">
   <table class="cal-table" id="ep-table">
    <tr><th>#</th><th>Wx</th><th>Wy</th><th>Wz</th><th>Sx</th><th>Sy</th><th>Sz</th></tr>
   </table>
  </div>
  <div class="btn-row">
   <button id="btn-ep-export" onclick="exportEndpointCSV()" disabled>EXPORT CSV</button>
   <button onclick="clearEndpointPts()" class="btn-danger">CLEAR</button>
  </div>
 </div>
</div>
</div>
<script>
"use strict";
const MAX_TRAIL=200;
let trail=[];
let rotX=-30,rotY=45,zoom=1.0;
let activePointers=new Map();
let frozen=false,showAxes=true;
let origin=null,savedPts=[],lastPos={x:0,y:0,z:0},_saveBusy=false;
let _dirty2d=false,_last2d=0;

// Software zero offsets
let szOff={x:0,y:0,z:0},szActive=false;
// Min/Max tracking
let mmMin={x:Infinity,y:Infinity,z:Infinity},mmMax={x:-Infinity,y:-Infinity,z:-Infinity};
// Snapshots
let snapshots=[];

const cv=document.getElementById("cv");
const ctx=cv.getContext("2d");
const cv_xy=document.getElementById("cv_xy");
const cv_xz=document.getElementById("cv_xz");
const cv_yz=document.getElementById("cv_yz");

function setText(id,v){const el=document.getElementById(id);if(el)el.textContent=v;}
function setLed(s){const el=document.getElementById("conn-led");el.className=s==="ok"?"ok":s==="warn"?"warn":"";}
function setStatus(s){setText("status",s);}

// Clock
setInterval(()=>setText("hdr-ts",new Date().toLocaleTimeString()),1000);

// Resize
function resize(){
 cv.width=cv.clientWidth;cv.height=cv.clientHeight;
 [cv_xy,cv_xz,cv_yz].forEach(c=>{if(c.clientWidth>0&&c.clientHeight>0){c.width=c.clientWidth;c.height=c.clientHeight;}});
}
window.addEventListener("resize",resize);resize();

// Multi-pointer: 1-finger rotate, 2-finger pinch-zoom
cv.addEventListener("pointerdown",e=>{
 activePointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
 cv.setPointerCapture(e.pointerId);e.preventDefault();
});
cv.addEventListener("pointermove",e=>{
 if(!activePointers.has(e.pointerId))return;
 const prev=activePointers.get(e.pointerId),cur={x:e.clientX,y:e.clientY};
 if(activePointers.size===1){rotY+=(cur.x-prev.x)*0.4;rotX+=(cur.y-prev.y)*0.4;}
 else if(activePointers.size===2){
  const oid=[...activePointers.keys()].find(id=>id!==e.pointerId);
  const other=activePointers.get(oid);
  if(other){
   const pd=Math.hypot(prev.x-other.x,prev.y-other.y);
   const cd=Math.hypot(cur.x-other.x,cur.y-other.y);
   if(pd>10)zoom=Math.max(0.2,Math.min(6,zoom*cd/pd));
  }
 }
 activePointers.set(e.pointerId,cur);e.preventDefault();
});
cv.addEventListener("pointerup",    e=>activePointers.delete(e.pointerId));
cv.addEventListener("pointercancel",e=>activePointers.delete(e.pointerId));

// 3D projection
function project(x,y,z){
 const ry=rotY*Math.PI/180,rx=rotX*Math.PI/180;
 const cy=Math.cos(ry),sy=Math.sin(ry),cx=Math.cos(rx),sx=Math.sin(rx);
 const x1=x*cy-z*sy,z1=x*sy+z*cy;
 const y1=y*cx-z1*sx,z2=y*sx+z1*cx;
 const s=cv.width*0.6*zoom/(z2+800);
 return [cv.width/2+x1*s,cv.height/2-y1*s,z2];
}

// Range ring helper
function drawRangeRing(r,color){
 const N=48;ctx.strokeStyle=color;ctx.lineWidth=0.5;ctx.setLineDash([4,4]);ctx.beginPath();
 for(let i=0;i<=N;i++){
  const a=i/N*Math.PI*2,p=project(r*Math.cos(a),0,r*Math.sin(a));
  i===0?ctx.moveTo(p[0],p[1]):ctx.lineTo(p[0],p[1]);
 }
 ctx.stroke();ctx.setLineDash([]);
 const lp=project(r,0,0);ctx.fillStyle=color;ctx.font="9px monospace";
 ctx.fillText(r+"mm",lp[0]+3,lp[1]-2);
}

// 3D render loop (continuous rAF)
function drawScene(){
 ctx.clearRect(0,0,cv.width,cv.height);
 // Axes
 if(showAxes){
  const al=400;
  const axes=[{c:"#ff4444",p:[[0,0,0],[al,0,0]],l:"X"},
              {c:"#44ff44",p:[[0,0,0],[0,0,al]],l:"Y"},
              {c:"#4488ff",p:[[0,0,0],[0,al,0]],l:"Z"}];
  for(const a of axes){
   const p0=project(...a.p[0]),p1=project(...a.p[1]);
   ctx.strokeStyle=a.c;ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(p0[0],p0[1]);ctx.lineTo(p1[0],p1[1]);ctx.stroke();
   ctx.fillStyle=a.c;ctx.font="12px monospace";ctx.fillText(a.l,p1[0]+4,p1[1]-4);
  }
 }
 // Ground grid
 ctx.strokeStyle="rgba(255,255,255,0.08)";ctx.lineWidth=0.5;
 for(let i=-600;i<=600;i+=200){
  const a=project(i,0,-600),b=project(i,0,600);ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();
  const c=project(-600,0,i),d=project(600,0,i);ctx.beginPath();ctx.moveTo(c[0],c[1]);ctx.lineTo(d[0],d[1]);ctx.stroke();
 }
 // Range rings
 [[200,"rgba(80,80,120,0.5)"],[500,"rgba(80,80,120,0.5)"],[1000,"rgba(100,100,160,0.6)"],[2000,"rgba(120,120,180,0.7)"]].forEach(function(rc){drawRangeRing(rc[0],rc[1]);});
 // Trail
 if(trail.length>1){
  ctx.lineWidth=2;ctx.beginPath();
  for(let i=0;i<trail.length;i++){
   const t=trail[i],p=project(t[0],t[2],t[1]);
   const alpha=0.2+0.8*(i/trail.length);
   if(i===0)ctx.moveTo(p[0],p[1]);
   else{ctx.strokeStyle="rgba(30,200,120,"+alpha+")";ctx.lineTo(p[0],p[1]);ctx.stroke();ctx.beginPath();ctx.moveTo(p[0],p[1]);}
  }
 }
 // Origin crosshair (magenta)
 if(origin){
  const op=project(origin.x,origin.z,origin.y);
  ctx.strokeStyle="#cc44ff";ctx.lineWidth=1.5;
  ctx.beginPath();ctx.arc(op[0],op[1],10,0,Math.PI*2);ctx.stroke();
  ctx.beginPath();ctx.moveTo(op[0]-15,op[1]);ctx.lineTo(op[0]+15,op[1]);
  ctx.moveTo(op[0],op[1]-15);ctx.lineTo(op[0],op[1]+15);ctx.stroke();
 }
 // Saved points — amber diamonds, depth-sorted
 const proj=savedPts.map(function(p){const pr=project(p.x,p.z,p.y);return{px:pr[0],py:pr[1],depth:pr[2],n:p.n};});
 proj.sort(function(a,b){return b.depth-a.depth;});
 proj.forEach(function(item){
  const px=item.px,py=item.py,n=item.n;
  ctx.strokeStyle="#ffd700";ctx.fillStyle="rgba(255,215,0,0.15)";ctx.lineWidth=1.5;
  const s=7;ctx.beginPath();ctx.moveTo(px,py-s);ctx.lineTo(px+s,py);ctx.lineTo(px,py+s);ctx.lineTo(px-s,py);ctx.closePath();
  ctx.fill();ctx.stroke();
  ctx.fillStyle="#ffd700";ctx.font="9px monospace";ctx.fillText("P"+n,px+s+2,py+3);
 });
 // Live position head (cyan)
 if(trail.length>0){
  const h=trail[trail.length-1],hp=project(h[0],h[2],h[1]);
  ctx.fillStyle="#00ffff";ctx.beginPath();ctx.arc(hp[0],hp[1],10,0,Math.PI*2);ctx.fill();
  ctx.fillStyle="#003333";ctx.beginPath();ctx.arc(hp[0],hp[1],4,0,Math.PI*2);ctx.fill();
 }
 requestAnimationFrame(drawScene);
}
drawScene();

// 2D plot
function draw2D(canvas,pts,ai,bi,la,lb){
 const W=canvas.clientWidth,H=canvas.clientHeight;
 if(W<1||H<1)return;
 if(canvas.width!==W)canvas.width=W;
 if(canvas.height!==H)canvas.height=H;
 const c=canvas.getContext("2d");
 c.fillStyle="#0f0f23";c.fillRect(0,0,W,H);
 const ML=28,MR=6,MT=6,MB=18;
 const PW=W-ML-MR,PH=H-MT-MB;
 if(pts.length<1){
  c.fillStyle="#334455";c.font="10px monospace";c.textAlign="center";
  c.fillText("no data",W/2,H/2);return;
 }
 const as=pts.map(function(p){return p[ai];}),bs=pts.map(function(p){return p[bi];});
 const pad=40;
 const minA=Math.min.apply(null,as)-pad,maxA=Math.max.apply(null,as)+pad;
 const minB=Math.min.apply(null,bs)-pad,maxB=Math.max.apply(null,bs)+pad;
 const rA=maxA-minA||1,rB=maxB-minB||1;
 const toX=function(v){return ML+(v-minA)/rA*PW;};
 const toY=function(v){return MT+PH-(v-minB)/rB*PH;};
 c.strokeStyle="rgba(255,255,255,0.07)";c.lineWidth=0.5;
 for(let g=0;g<=4;g++){
  const gx=ML+g*PW/4,gy=MT+g*PH/4;
  c.beginPath();c.moveTo(gx,MT);c.lineTo(gx,MT+PH);c.stroke();
  c.beginPath();c.moveTo(ML,gy);c.lineTo(ML+PW,gy);c.stroke();
 }
 c.fillStyle="#556677";c.font="9px monospace";c.textAlign="center";
 c.fillText(la,ML+PW/2,H-2);
 c.fillText(minA.toFixed(0),ML,H-2);
 c.fillText(maxA.toFixed(0),ML+PW,H-2);
 c.save();c.translate(10,MT+PH/2);c.rotate(-Math.PI/2);c.fillText(lb,0,0);c.restore();
 for(let i=1;i<pts.length;i++){
  const alpha=0.2+0.8*(i/pts.length);
  c.strokeStyle="rgba(30,200,120,"+alpha.toFixed(2)+")";c.lineWidth=1.5;
  c.beginPath();c.moveTo(toX(pts[i-1][ai]),toY(pts[i-1][bi]));c.lineTo(toX(pts[i][ai]),toY(pts[i][bi]));c.stroke();
 }
 const last=pts[pts.length-1];
 const hx=toX(last[ai]),hy=toY(last[bi]);
 c.fillStyle="#00ffff";c.beginPath();c.arc(hx,hy,5,0,Math.PI*2);c.fill();
 c.fillStyle="#003333";c.beginPath();c.arc(hx,hy,2,0,Math.PI*2);c.fill();
 c.fillStyle="#00ffff";c.font="9px monospace";c.textAlign="left";
 c.fillText(last[ai].toFixed(0)+","+last[bi].toFixed(0),hx+7,hy+3);
}

// 2D throttled loop (10 Hz)
function render2DLoop(ts){
 if(_dirty2d&&ts-_last2d>100){
  draw2D(cv_xy,trail,0,1,"X","Y");draw2D(cv_xz,trail,0,2,"X","Z");draw2D(cv_yz,trail,1,2,"Y","Z");
  _dirty2d=false;_last2d=ts;
 }
 requestAnimationFrame(render2DLoop);
}
requestAnimationFrame(render2DLoop);

// Update panel live values + distance from origin
function updatePanelValues(x,y,z){
 lastPos={x:x,y:y,z:z};
 // Apply software zero offsets
 const dx=szActive?(x-szOff.x):x, dy=szActive?(y-szOff.y):y, dz=szActive?(z-szOff.z):z;
 setText("vx",dx.toFixed(1));setText("vy",dy.toFixed(1));setText("vz",dz.toFixed(1));
 // Min/Max tracking
 if(dx<mmMin.x)mmMin.x=dx; if(dx>mmMax.x)mmMax.x=dx;
 if(dy<mmMin.y)mmMin.y=dy; if(dy>mmMax.y)mmMax.y=dy;
 if(dz<mmMin.z)mmMin.z=dz; if(dz>mmMax.z)mmMax.z=dz;
 setText("mm-x-min",mmMin.x===Infinity?"--":mmMin.x.toFixed(1));
 setText("mm-x-max",mmMax.x===-Infinity?"--":mmMax.x.toFixed(1));
 setText("mm-y-min",mmMin.y===Infinity?"--":mmMin.y.toFixed(1));
 setText("mm-y-max",mmMax.y===-Infinity?"--":mmMax.y.toFixed(1));
 setText("mm-z-min",mmMin.z===Infinity?"--":mmMin.z.toFixed(1));
 setText("mm-z-max",mmMax.z===-Infinity?"--":mmMax.z.toFixed(1));
 if(origin){
  const d=Math.sqrt((x-origin.x)*(x-origin.x)+(y-origin.y)*(y-origin.y)+(z-origin.z)*(z-origin.z));
  setText("v_dist_origin",d.toFixed(1)+" mm");
 }
}

// WebSocket — exponential backoff reconnect
let ws=null,wsDelay=1000,wsConnecting=false;
function connect(){
 if(wsConnecting)return;
 wsConnecting=true;
 ws=new WebSocket("ws://"+location.host+"/ws");
 ws.onopen=function(){wsConnecting=false;wsDelay=1000;setLed("ok");setStatus("Connected");};
 ws.onclose=function(){wsConnecting=false;ws=null;setLed("warn");
  setStatus("Reconnecting in "+(wsDelay/1000).toFixed(0)+"s\u2026");
  setTimeout(connect,wsDelay);wsDelay=Math.min(wsDelay*2,30000);};
 ws.onerror=function(){ws.close();};
 ws.onmessage=onWsMessage;
}
function sendCmd(cmd){
 if(ws&&ws.readyState===1){ws.send(cmd);if(navigator.vibrate)navigator.vibrate(30);}
}
function onWsMessage(e){
 const line=e.data.trim();
 if(line.startsWith("DATA,")){
  if(frozen)return;
  const p=line.substring(5).split(",");
  if(p.length>=9){
   const x=parseFloat(p[0]),y=parseFloat(p[1]),z=parseFloat(p[2]);
   const r=parseFloat(p[3]),th=parseFloat(p[4]),ph=parseFloat(p[5]);
   const v=parseInt(p[6]),fr=parseInt(p[7]);
   trail.push([x,y,z]);
   if(trail.length>MAX_TRAIL)trail.shift();
   updatePanelValues(x,y,z);
   setText("sr_r",r.toFixed(1)+" mm");
   setText("sr_t",(th>=0?"+":"")+th.toFixed(2)+"\u00b0");
   setText("sr_p",(ph>=0?"+":"")+ph.toFixed(2)+"\u00b0");
   setText("vv",v?"YES":"NO");
   const cardX=document.getElementById("card-x");
   if(cardX)cardX.classList.toggle("invalid",!v);
   setText("vf",fr);
   setText("cl-r",r.toFixed(1));
   setText("cl-t",(th>=0?"+":"")+th.toFixed(2));
   setText("cl-p",(ph>=0?"+":"")+ph.toFixed(2));
   setText("cl-x",x.toFixed(1));
   setText("cl-y",y.toFixed(1));
   setText("cl-z",z.toFixed(1));
   _dirty2d=true;
  }
 } else if(line.startsWith("ACK:")){
  setStatus(line);
 } else if(line.startsWith("CAL:WIRE,")){
  const p=line.substring(9).split(",");
  const factor=parseFloat(p[0]),ppr=parseFloat(p[2]);
  wireTrials.push({actual:_pendingActualMm,factor:factor,ppr:ppr});
  const tr=document.getElementById("wire-table").insertRow();
  [wireTrials.length,_pendingActualMm+" mm",factor.toFixed(4),ppr.toFixed(1)].forEach(function(v){
   const td=tr.insertCell();td.textContent=v;
  });
  setText("wire-trial-result","Trial "+wireTrials.length+": factor="+factor.toFixed(4)+"  PPR_WIRE="+ppr.toFixed(1));
  updateWireStats();
 } else if(line.startsWith("CAL:THETA,")){
  const p=line.substring(10).split(",");
  pendingRotaryPPR.theta=parseFloat(p[1]);
  setText("theta-result","Counts: "+p[0]+"  \u2192 PPR: "+pendingRotaryPPR.theta.toFixed(1));
  document.getElementById("btn-apply-theta").disabled=false;
 } else if(line.startsWith("CAL:PHI,")){
  const p=line.substring(8).split(",");
  pendingRotaryPPR.phi=parseFloat(p[1]);
  setText("phi-result","Counts: "+p[0]+"  \u2192 PPR: "+pendingRotaryPPR.phi.toFixed(1));
  document.getElementById("btn-apply-phi").disabled=false;
 } else if(line.startsWith("CONSTANTS,")){
  const p=line.substring(10).split(",");
  setText("const-ppr-r",p[0]);setText("const-ppr-w",p[1]);
  setText("const-mm-pp",p[2]);setText("const-deg-pp",p[3]);
 } else if(line.startsWith("STA_IP:")){
  const ip=line.substring(7).trim();
  setText("v-router-ip",ip==="NOT_CONNECTED"?"Not Connected":ip);
 } else if(line.startsWith("SYSINFO,")){
  const p=line.substring(8).split(",");
  if(p.length>=4){
   const rssi=parseInt(p[0]),heap=parseInt(p[1]),up=parseInt(p[2]),tcp=parseInt(p[3]);
   setText("v-rssi",rssi+" dBm");
   setText("v-heap",(heap/1024).toFixed(0)+" KB");
   const h=Math.floor(up/3600),m=Math.floor((up%3600)/60),s=up%60;
   setText("v-uptime",(h<10?"0":"")+h+":"+(m<10?"0":"")+m+":"+(s<10?"0":"")+s);
   setText("v-tcp",tcp);
  }
 }
}
connect();

// Freeze toggle
function toggleFreeze(){
 frozen=!frozen;
 document.getElementById("btn-freeze").classList.toggle("active",frozen);
 cv.style.outline=frozen?"2px solid #ff8c00":"none";
}

// Axes toggle
function toggleAxes(){
 showAxes=!showAxes;
 document.getElementById("btn-axes").classList.toggle("active",showAxes);
}

// Clear trail
function clearTrail(){trail=[];_dirty2d=true;}

// Software zero
function softZero(axis){szOff[axis]=lastPos[axis];szActive=true;resetMinMax();}
function softZeroAll(){szOff.x=lastPos.x;szOff.y=lastPos.y;szOff.z=lastPos.z;szActive=true;resetMinMax();}

// Min/Max
function resetMinMax(){
 mmMin={x:Infinity,y:Infinity,z:Infinity};mmMax={x:-Infinity,y:-Infinity,z:-Infinity};
 ["x","y","z"].forEach(function(a){setText("mm-"+a+"-min","--");setText("mm-"+a+"-max","--");});
}

// Snapshots
function captureSnapshot(){
 const dx=szActive?(lastPos.x-szOff.x):lastPos.x;
 const dy=szActive?(lastPos.y-szOff.y):lastPos.y;
 const dz=szActive?(lastPos.z-szOff.z):lastPos.z;
 const n=snapshots.length+1;
 snapshots.push({n:n,x:dx,y:dy,z:dz,ts:new Date().toLocaleTimeString()});
 document.getElementById("snap-list").innerHTML+="#"+n+": "+dx.toFixed(1)+","+dy.toFixed(1)+","+dz.toFixed(1)+"<br>";
 document.getElementById("snap-list").scrollTop=99999;
 setText("snap-count",snapshots.length+" snapshots");
 document.getElementById("btn-snap-export").disabled=false;
 if(navigator.vibrate)navigator.vibrate(40);
}
function clearSnapshots(){
 snapshots=[];
 document.getElementById("snap-list").innerHTML="";
 setText("snap-count","0 snapshots");
 document.getElementById("btn-snap-export").disabled=true;
}
function exportSnapshots(){
 if(!snapshots.length)return;
 let csv="#,X_mm,Y_mm,Z_mm,Time\r\n";
 snapshots.forEach(function(s){csv+=s.n+","+s.x.toFixed(3)+","+s.y.toFixed(3)+","+s.z.toFixed(3)+","+s.ts+"\r\n";});
 const blob=new Blob([csv],{type:"text/csv;charset=utf-8;"});
 const url=URL.createObjectURL(blob);
 const a=document.createElement("a");a.href=url;a.download="snapshots_"+Date.now()+".csv";
 document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
}

// WiFi settings
function saveWifi(){
 const ssid=document.getElementById("wifi-ssid").value.trim();
 const pass=document.getElementById("wifi-pass").value;
 if(!ssid||pass.length<8){setStatus("SSID required, password min 8 chars");return;}
 sendCmd("WIFI_SET:"+ssid+","+pass);
 setStatus("WiFi credentials sent. Device will reboot...");
}
function forgetWifi(){
 sendCmd("WIFI_SET:,");
 setStatus("WiFi credentials cleared. Device will reboot...");
}

// Request system info periodically
setInterval(function(){if(ws&&ws.readyState===1){sendCmd("SYSINFO");sendCmd("GET_IP");}},5000);

// Session — Save Origin
function saveOrigin(){
 origin={x:lastPos.x,y:lastPos.y,z:lastPos.z};
 const b=document.getElementById("btn-origin");
 b.textContent="ORIGIN SET";b.classList.add("is-set");
 document.getElementById("btn-point").disabled=false;
 document.getElementById("btn-export").disabled=false;
 setText("origin_label",origin.x.toFixed(0)+","+origin.y.toFixed(0)+","+origin.z.toFixed(0));
 setText("sessionInfo","Session active");
 if(navigator.vibrate)navigator.vibrate([30,50,30]);
}

// Session — Save Point (debounced)
function savePoint(){
 if(_saveBusy)return;_saveBusy=true;
 const b=document.getElementById("btn-point");b.disabled=true;
 setTimeout(function(){b.disabled=false;_saveBusy=false;},200);
 const n=savedPts.length+1;
 savedPts.push({n:n,x:lastPos.x,y:lastPos.y,z:lastPos.z});
 document.getElementById("savedList").innerHTML+="#"+n+": "+lastPos.x.toFixed(1)+","+lastPos.y.toFixed(1)+","+lastPos.z.toFixed(1)+" mm<br>";
 document.getElementById("savedList").scrollTop=99999;
 updateSessionStats();
 if(navigator.vibrate)navigator.vibrate(60);
}

// Session — End & Export CSV
function endSession(){
 if(!savedPts.length)return;
 const ox=origin?origin.x:0,oy=origin?origin.y:0,oz=origin?origin.z:0;
 let csv="label,x_mm,y_mm,z_mm,rel_x_mm,rel_y_mm,rel_z_mm\r\n";
 if(origin)csv+="ORIGIN,"+ox.toFixed(3)+","+oy.toFixed(3)+","+oz.toFixed(3)+",0,0,0\r\n";
 savedPts.forEach(function(p){
  csv+="P"+p.n+","+p.x.toFixed(3)+","+p.y.toFixed(3)+","+p.z.toFixed(3)+","+(p.x-ox).toFixed(3)+","+(p.y-oy).toFixed(3)+","+(p.z-oz).toFixed(3)+"\r\n";
 });
 const blob=new Blob([csv],{type:"text/csv;charset=utf-8;"});
 const url=URL.createObjectURL(blob);
 const a=document.createElement("a");a.href=url;a.download="evka_"+Date.now()+".csv";
 document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);
 // Reset session state
 savedPts=[];origin=null;
 document.getElementById("btn-origin").textContent="SAVE ORIGIN";
 document.getElementById("btn-origin").classList.remove("is-set");
 document.getElementById("btn-point").disabled=true;
 document.getElementById("btn-export").disabled=true;
 document.getElementById("savedList").innerHTML="";
 setText("origin_label","not set");setText("vn","0");
 setText("stat_min_r","--");setText("stat_max_r","--");
 setText("v_dist_pp","--");setText("v_dist_origin","--");
 setText("sessionInfo","No session active");
 if(navigator.vibrate)navigator.vibrate([30,50,30,50,30]);
}

// ---- Calibration tab ----
let calActive=false,calStage="wire";
let wireTrials=[],_pendingActualMm=0,pendingRotaryPPR={theta:0,phi:0};
let endpointPts=[],endpointOriginSensor=null;

function toggleCal(){
 calActive=!calActive;
 document.getElementById("btn-cal").classList.toggle("active",calActive);
 document.getElementById("cv").style.display=calActive?"none":"";
 document.getElementById("views2d").style.display=calActive?"none":"";
 document.getElementById("panel").style.display=calActive?"none":"";
 document.getElementById("cal-view").style.display=calActive?"block":"none";
 if(calActive)sendCmd("CONSTANTS");
}
function showCalStage(stage){
 calStage=stage;
 ["wire","theta","phi","endpoint"].forEach(function(s){
  document.getElementById("cal-"+s).style.display=(s===stage)?"":"none";
 });
 document.querySelectorAll(".cal-tab").forEach(function(b,i){
  b.classList.toggle("active",["wire","theta","phi","endpoint"][i]===stage);
 });
}
function adjTurns(axis,delta){
 const el=document.getElementById("rot-"+axis+"-turns");
 el.value=Math.max(1,Math.min(20,(parseInt(el.value)||5)+delta));
}
function calWireTrial(){
 const mm=parseFloat(document.getElementById("wire-dist").value);
 if(!mm||mm<=0)return;
 _pendingActualMm=mm;
 sendCmd("CAL_W "+mm);
}
function applyWireMean(permanent){
 if(!wireTrials.length)return;
 const mean=wireTrials.reduce(function(s,t){return s+t.ppr;},0)/wireTrials.length;
 sendCmd("SET_PPR_WIRE "+mean.toFixed(2));
 if(permanent)sendCmd("SAVE_PPR");
 setText("wire-apply-status",(permanent?"SAVED to NVS":"RAM only")+": PPR_WIRE="+mean.toFixed(2));
}
function clearWireTrials(){
 wireTrials=[];
 const tbl=document.getElementById("wire-table");
 while(tbl.rows.length>1)tbl.deleteRow(1);
 setText("wire-n","0");setText("wire-mean","—");setText("wire-spread","—");
 setText("wire-trial-result","—");
 document.getElementById("btn-apply-wire").disabled=true;
 document.getElementById("btn-save-wire").disabled=true;
}
function updateWireStats(){
 const n=wireTrials.length;
 setText("wire-n",n);
 if(!n)return;
 const pprs=wireTrials.map(function(t){return t.ppr;});
 const mean=pprs.reduce(function(s,v){return s+v;},0)/n;
 setText("wire-mean",mean.toFixed(1));
 const spread=n>1?(Math.max.apply(null,pprs)-Math.min.apply(null,pprs))/mean*100:0;
 setText("wire-spread",n>1?spread.toFixed(2)+"%":"—");
 document.getElementById("btn-apply-wire").disabled=false;
 document.getElementById("btn-save-wire").disabled=false;
}
function calRotary(axis){
 const n=parseInt(document.getElementById("rot-"+axis+"-turns").value)||0;
 if(n<=0)return;
 sendCmd("CAL_"+(axis==="theta"?"T":"P")+" "+n);
}
function applyRotaryCal(axis){
 const ppr=pendingRotaryPPR[axis];
 if(ppr>0){
  sendCmd("SET_PPR_ROTARY "+ppr.toFixed(2));
  setText(axis+"-apply-status","Sent: SET_PPR_ROTARY "+ppr.toFixed(2));
 }
}
function setEndpointOrigin(){
 endpointOriginSensor={x:lastPos.x,y:lastPos.y,z:lastPos.z};
 const btn=document.getElementById("btn-ep-origin");
 btn.textContent="ORIGIN SET";btn.classList.remove("btn-amber");btn.classList.add("is-set");
 setText("ep-origin-status","S=("+lastPos.x.toFixed(1)+", "+lastPos.y.toFixed(1)+", "+lastPos.z.toFixed(1)+") mm → world (0, 0, 0)");
 // Clear table and add origin row
 endpointPts=[];
 const tbl=document.getElementById("ep-table");
 while(tbl.rows.length>1)tbl.deleteRow(1);
 const tr=tbl.insertRow();
 ["O","0","0","0",lastPos.x.toFixed(1),lastPos.y.toFixed(1),lastPos.z.toFixed(1)].forEach(function(v){
  const td=tr.insertCell();td.textContent=v;
 });
 tr.style.color="#cc44ff";
 document.getElementById("ep-step-points").style.display="";
 document.getElementById("btn-ep-export").disabled=true;
 setText("ep-status","0 points recorded");
 if(navigator.vibrate)navigator.vibrate([30,50,30]);
}
function recordEndpointPt(){
 if(!endpointOriginSensor)return;
 const wx=parseFloat(document.getElementById("ep-x").value)||0;
 const wy=parseFloat(document.getElementById("ep-y").value)||0;
 const wz=parseFloat(document.getElementById("ep-z").value)||0;
 const pt={n:endpointPts.length+1,wx:wx,wy:wy,wz:wz,
           sx:lastPos.x,sy:lastPos.y,sz:lastPos.z};
 endpointPts.push(pt);
 const tr=document.getElementById("ep-table").insertRow();
 [pt.n,wx,wy,wz,pt.sx.toFixed(1),pt.sy.toFixed(1),pt.sz.toFixed(1)].forEach(function(v){
  const td=tr.insertCell();td.textContent=v;
 });
 setText("ep-status",endpointPts.length+" point"+(endpointPts.length===1?"":"s")+" recorded");
 document.getElementById("btn-ep-export").disabled=false;
 if(navigator.vibrate)navigator.vibrate(40);
}
function exportEndpointCSV(){
 if(!endpointOriginSensor)return;
 let csv="label,world_x,world_y,world_z,sensor_x,sensor_y,sensor_z\r\n";
 csv+="ORIGIN,0,0,0,"+endpointOriginSensor.x.toFixed(3)+","+endpointOriginSensor.y.toFixed(3)+","+endpointOriginSensor.z.toFixed(3)+"\r\n";
 endpointPts.forEach(function(p){
  csv+="P"+p.n+","+p.wx+","+p.wy+","+p.wz+","+
       p.sx.toFixed(3)+","+p.sy.toFixed(3)+","+p.sz.toFixed(3)+"\r\n";
 });
 const a=document.createElement("a");
 a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
 a.download="endpoint_cal_"+Date.now()+".csv";
 document.body.appendChild(a);a.click();document.body.removeChild(a);
}
function clearEndpointPts(){
 endpointPts=[];endpointOriginSensor=null;
 const tbl=document.getElementById("ep-table");
 while(tbl.rows.length>1)tbl.deleteRow(1);
 const btn=document.getElementById("btn-ep-origin");
 btn.textContent="SET ORIGIN";btn.classList.remove("is-set");btn.classList.add("btn-amber");
 setText("ep-origin-status","Origin not set");
 setText("ep-status","0 points recorded");
 document.getElementById("ep-step-points").style.display="none";
 document.getElementById("btn-ep-export").disabled=true;
}

// Update session stats after each saved point
function updateSessionStats(){
 setText("vn",savedPts.length);
 if(!savedPts.length)return;
 const rs=savedPts.map(function(p){return Math.sqrt(p.x*p.x+p.y*p.y+p.z*p.z);});
 setText("stat_min_r",Math.min.apply(null,rs).toFixed(1)+" mm");
 setText("stat_max_r",Math.max.apply(null,rs).toFixed(1)+" mm");
 if(savedPts.length>=2){
  const a=savedPts[savedPts.length-2],b=savedPts[savedPts.length-1];
  const d=Math.sqrt((b.x-a.x)*(b.x-a.x)+(b.y-a.y)*(b.y-a.y)+(b.z-a.z)*(b.z-a.z));
  setText("v_dist_pp",d.toFixed(1)+" mm");
 }
}
</script>
</body>
</html>
)rawliteral";

// ============================================================================
// WebDashboard implementation
// ============================================================================

WebDashboard::WebDashboard()
    : _server(WIFI_WEB_PORT), _ws("/ws") {}

void WebDashboard::begin() {
    // AP+STA mode: AP config BEFORE STA to avoid DHCP conflict
    WiFi.mode(WIFI_AP_STA);

    IPAddress apIP(WIFI_AP_IP_O1, WIFI_AP_IP_O2, WIFI_AP_IP_O3, WIFI_AP_IP_O4);
    IPAddress apGW(WIFI_AP_IP_O1, WIFI_AP_IP_O2, WIFI_AP_IP_O3, 1);
    IPAddress apSubnet(255, 255, 255, 0);
    WiFi.softAPConfig(apIP, apGW, apSubnet);
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD);

    Serial.print("[WiFi] AP started: ");
    Serial.print(WIFI_AP_SSID);
    Serial.print(" @ ");
    Serial.println(WiFi.softAPIP());

    // Load STA credentials from NVS and connect if available
    {
        Preferences prefs;
        prefs.begin("wifi_cfg", true);  // read-only
        String staSsid = prefs.getString("ssid", "");
        String staPass = prefs.getString("pass", "");
        prefs.end();

        if (staSsid.length() > 0) {
            WiFi.begin(staSsid.c_str(), staPass.c_str());
            Serial.printf("[WiFi] STA connecting to '%s'...\n", staSsid.c_str());
        } else {
            Serial.println("[WiFi] No STA credentials stored");
        }
    }

    _ws.onEvent([this](AsyncWebSocket* s, AsyncWebSocketClient* c,
                       AwsEventType t, void* a, uint8_t* d, size_t l) {
        onWsEvent(s, c, t, a, d, l);
    });
    _server.addHandler(&_ws);

    _server.on("/", HTTP_GET, serveIndex);

    _server.begin();
    Serial.println("[WiFi] Web server started");
}

void WebDashboard::broadcast(const char* dataLine) {
    if (_ws.count() > 0) {
        _ws.textAll(dataLine);
    }
}

void WebDashboard::onWsEvent(AsyncWebSocket* server, AsyncWebSocketClient* client,
                              AwsEventType type, void* arg, uint8_t* data, size_t len) {
    if (type == WS_EVT_CONNECT) {
        Serial.printf("[WiFi] Client #%u connected\n", client->id());
    } else if (type == WS_EVT_DISCONNECT) {
        Serial.printf("[WiFi] Client #%u disconnected\n", client->id());
    } else if (type == WS_EVT_DATA) {
        // Client can send commands (e.g. ZERO, PING) — forward to serial handler
        AwsFrameInfo* info = (AwsFrameInfo*)arg;
        if (info->opcode == WS_TEXT && len > 0) {
            char cmd[32];
            size_t n = (len < sizeof(cmd) - 1) ? len : sizeof(cmd) - 1;
            memcpy(cmd, data, n);
            cmd[n] = '\0';

            String cmdStr(cmd);
            cmdStr.trim();
            // Store for main loop to process (Serial TX ≠ Serial RX on ESP32)
            _pendingCmd = cmdStr;
        }
    }
    _ws.cleanupClients();
}

String WebDashboard::takePendingCommand() {
    String cmd = _pendingCmd;
    _pendingCmd = "";
    return cmd;
}

void WebDashboard::serveIndex(AsyncWebServerRequest* request) {
    request->send_P(200, "text/html", INDEX_HTML);
}

#endif // ENABLE_WIFI
