#include "WebDashboard.h"

#if ENABLE_WIFI

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
</style>
</head>
<body>
<div id="app">
<div id="hdr">
 <span id="hdr-title">EVKAPOSITION</span>
 <div id="conn-led"></div>
 <button id="btn-freeze" onclick="toggleFreeze()">FREEZE</button>
 <button id="btn-axes" onclick="toggleAxes()">AXES</button>
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
  <div class="vcard-label">X AXIS</div>
  <div class="vcard-row"><span class="vcard-value" id="vx">--</span><span class="vcard-unit">mm</span></div>
 </div>
 <div class="vcard" id="card-y">
  <div class="vcard-label">Y AXIS</div>
  <div class="vcard-row"><span class="vcard-value" id="vy">--</span><span class="vcard-unit">mm</span></div>
 </div>
 <div class="vcard" id="card-z">
  <div class="vcard-label">Z AXIS</div>
  <div class="vcard-row"><span class="vcard-value" id="vz">--</span><span class="vcard-unit">mm</span></div>
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
  <button onclick="sendCmd('ZERO')">ZERO</button>
  <button onclick="sendCmd('PING')">PING</button>
  <button onclick="clearTrail()">CLEAR</button>
 </div>
 <div id="status">Connecting...</div>
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
 setText("vx",x.toFixed(1));setText("vy",y.toFixed(1));setText("vz",z.toFixed(1));
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
   _dirty2d=true;
  }
 } else if(line.startsWith("ACK:")){
  setStatus(line);
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
 if(origin)csv="ORIGIN,"+ox.toFixed(3)+","+oy.toFixed(3)+","+oz.toFixed(3)+",0,0,0\r\n"+csv;
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
    WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASSWORD);
    Serial.print("[WiFi] AP started: ");
    Serial.print(WIFI_AP_SSID);
    Serial.print(" @ ");
    Serial.println(WiFi.softAPIP());

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
