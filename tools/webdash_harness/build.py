"""Extract the dashboard blob from WebDashboard.cpp and make it drivable in a browser.

The firmware serves this HTML from PROGMEM over a real WebSocket. Here we stub the
WebSocket so the page can be exercised without hardware: window.__feed(line) pushes a
protocol line at the page exactly as the firmware would.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]   # tools/webdash_harness/ -> repo root
OUT = Path(__file__).parent / "dash.html"

src = (REPO / "firmware/src/WebDashboard.cpp").read_text(encoding="utf-8")
m = re.search(r'R"rawliteral\((.*?)\)rawliteral";', src, re.S)
assert m, "could not find the INDEX_HTML raw string"
html = m.group(1)

SHIM = """
<script>
// Mock WebSocket: the page thinks it is talking to the device.
(function(){
  let inst = null;
  class FakeWS {
    constructor(url){
      this.url = url; this.readyState = 0;
      inst = this;
      window.__sent = [];
      setTimeout(() => { this.readyState = 1; this.onopen && this.onopen(); }, 10);
    }
    send(data){ window.__sent.push(data); }
    close(){ this.readyState = 3; this.onclose && this.onclose(); }
  }
  window.WebSocket = FakeWS;
  window.__feed = function(line){
    if (inst && inst.onmessage) inst.onmessage({ data: line });
  };
  // A spiral sweep over a spherical cap: the operator's hand motion, holding the pen
  // tip on a hidden target at P with the wire attached L away on the handle.
  window.__sweep = function(P, L, n, halfAngleDeg){
    const ax = [0.3, 0.2, 1.0];
    const an = Math.hypot(ax[0], ax[1], ax[2]);
    const a = ax.map(v => v / an);
    const tmp = Math.abs(a[0]) < 0.9 ? [1,0,0] : [0,1,0];
    let e1 = [a[1]*tmp[2]-a[2]*tmp[1], a[2]*tmp[0]-a[0]*tmp[2], a[0]*tmp[1]-a[1]*tmp[0]];
    const e1n = Math.hypot(e1[0], e1[1], e1[2]);
    e1 = e1.map(v => v / e1n);
    const e2 = [a[1]*e1[2]-a[2]*e1[1], a[2]*e1[0]-a[0]*e1[2], a[0]*e1[1]-a[1]*e1[0]];
    const ha = halfAngleDeg * Math.PI / 180;
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < n; i++) {
      const t = ha * Math.sqrt((i + 0.5) / n);
      const ph = i * golden;
      const ct = Math.cos(t), st = Math.sin(t);
      const cp = Math.cos(ph), sp = Math.sin(ph);
      const d = [ ct*a[0] + st*(cp*e1[0] + sp*e2[0]),
                  ct*a[1] + st*(cp*e1[1] + sp*e2[1]),
                  ct*a[2] + st*(cp*e1[2] + sp*e2[2]) ];
      const x = P[0] + L*d[0], y = P[1] + L*d[1], z = P[2] + L*d[2];
      const r = Math.hypot(x, y, z);
      const th = Math.atan2(y, x) * 180 / Math.PI;
      const phi = Math.asin(z / r) * 180 / Math.PI;
      window.__feed("DATA," + x.toFixed(2) + "," + y.toFixed(2) + "," + z.toFixed(2) + "," +
                    r.toFixed(2) + "," + th.toFixed(3) + "," + phi.toFixed(3) +
                    ",1," + (i+1) + "," + (i*50));
    }
  };
  window.__errors = [];
  window.addEventListener("error", e => window.__errors.push(String(e.message)));
})();
</script>
"""

# The shim must define window.WebSocket before the page's own script runs.
html = html.replace("</head>", SHIM + "</head>", 1)
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT} ({len(html)} bytes)")
