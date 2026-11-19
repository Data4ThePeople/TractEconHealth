"""Hero image for the post, 1680x1080: the interactive chart's default view (median household income against
the health index, one dot per tract, median line through 20 equal-size groups), redrawn with hero-size type.
Every number is read from data/processed and analysis/results.json at render time. Writes an HTML page next to
the image and screenshots it with headless Chrome.

Output: posts/income-health-viz/images/income-health-viz-hero-source.html and income-health-viz-hero-1680x1080.png
"""
import json, os, subprocess, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import PROC, ROOT

OUT = ROOT / "posts" / "income-health-viz" / "images"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

t = pd.read_parquet(PROC / "tracts.parquet")
t = t[t.med_hh_income.notna()]
x, y = t.med_hh_income.to_numpy(float), t.health_index.to_numpy(float)
res = json.loads((ROOT / "analysis" / "results.json").read_text())["national"]
rho = float(np.corrcoef(pd.Series(x).rank(), pd.Series(y).rank())[0, 1])
assert abs(rho - res["spearman_all"]) < 1e-9

# median line: same rule as the viz (20 equal-count groups, median x and median y)
o = np.argsort(x, kind="stable"); xs, ys = x[o], y[o]
line = []
for b in range(20):
    lo, hi = int(np.floor(b * len(xs) / 20)), int(np.floor((b + 1) * len(xs) / 20))
    line.append([float(np.median(xs[lo:hi])), float(np.median(ys[lo:hi]))])

bend = round(res["k"] / 10000) * 10000           # about $110,000
ratio = res["slope_above"] / res["slope_below"]  # about 27%
pts = np.column_stack([np.round(x).astype(int), np.round(y * 10).astype(int)]).ravel().tolist()

html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}
body{{width:1680px;height:1080px;background:#181A1B;color:#BBBDC0;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;overflow:hidden;position:relative}}
h1{{position:absolute;left:90px;top:66px;font:700 54px/1.08 Georgia,serif;color:#EDEEEF;white-space:nowrap}}
.sub{{position:absolute;left:90px;top:156px;font-size:28px;color:#BBBDC0}}
.stats{{position:absolute;left:90px;top:300px;width:400px}}
.n{{font-size:76px;font-weight:700;color:#EDEEEF;line-height:1}}
.l{{font-size:25px;line-height:1.35;margin:10px 0 44px}}
.o{{color:#f08a4b;font-weight:700}}.b{{color:#6aa6e8;font-weight:700}}
canvas{{position:absolute;left:520px;top:240px}}
.foot{{position:absolute;left:90px;right:90px;bottom:40px;display:flex;justify-content:space-between;font-size:19px;color:#8A9098}}
.brand{{font-weight:700;color:#BBBDC0}}
</style></head><body>
<h1>Income and health, neighborhood by neighborhood</h1>
<div class="sub"><span class="b">Each dot</span> is one of {len(x):,} U.S. census tracts. The <span class="o">orange line</span> follows the middle of the cloud.</div>
<div class="stats">
 <div class="n">{rho:.2f}</div><div class="l">rank correlation between median household income and a health index built from 14 CDC measures</div>
 <div class="n">${bend:,.0f}</div><div class="l">where gains slow: above it, the health index rises about {ratio*100:.0f}% as fast, but it keeps rising</div>
</div>
<canvas id="c" width="1090" height="700"></canvas>
<div class="foot"><span>Income: Census Bureau, ACS 2020-2024. Health: CDC PLACES 2025, model estimates. Kentucky and Pennsylvania not shown.</span><span class="brand">Data 4 The People</span></div>
<script>
const P={json.dumps(pts)}, L={json.dumps(line)};
const cv=document.getElementById('c'), g=cv.getContext('2d'), W=cv.width, H=cv.height;
const m={{l:90,r:20,t:10,b:84}}, pw=W-m.l-m.r, ph=H-m.t-m.b, XMAX=250001;
const px=v=>m.l+v/XMAX*pw, py=v=>m.t+ph-(v/100)*ph;
g.font='22px Helvetica Neue,Helvetica,Arial'; g.fillStyle='#8A9098'; g.strokeStyle='#2A2D2F'; g.lineWidth=1;
for(let v=0;v<=100;v+=20){{const yy=py(v); g.beginPath(); g.moveTo(m.l,yy); g.lineTo(W-m.r,yy); g.stroke(); g.textAlign='right'; g.textBaseline='middle'; g.fillText(v,m.l-14,yy);}}
for(let v=0;v<=250000;v+=50000){{const xx=px(v); g.beginPath(); g.moveTo(xx,m.t); g.lineTo(xx,m.t+ph); g.stroke(); g.textAlign=v===250000?'right':'center'; g.textBaseline='top'; g.fillText(v?'$'+(v/1000)+'k':'$0',v===250000?xx+4:xx,m.t+ph+12);}}
g.fillStyle='#BBBDC0'; g.font='24px Helvetica Neue,Helvetica,Arial'; g.textAlign='center'; g.fillText('Median household income',m.l+pw/2,m.t+ph+50);
g.save(); g.translate(26,m.t+ph/2); g.rotate(-Math.PI/2); g.textBaseline='middle'; g.fillText('Health index (higher is healthier)',0,0); g.restore();
g.fillStyle='rgba(106,166,232,0.16)';
for(let i=0;i<P.length;i+=2){{g.fillRect(px(P[i])-1.4,py(P[i+1]/10)-1.4,2.8,2.8);}}
g.strokeStyle='#181A1B'; g.lineWidth=9; g.lineJoin='round'; g.lineCap='round'; g.beginPath(); L.forEach((p,i)=>i?g.lineTo(px(p[0]),py(p[1])):g.moveTo(px(p[0]),py(p[1]))); g.stroke();
g.strokeStyle='#f08a4b'; g.lineWidth=5; g.beginPath(); L.forEach((p,i)=>i?g.lineTo(px(p[0]),py(p[1])):g.moveTo(px(p[0]),py(p[1]))); g.stroke();
</script></body></html>"""

OUT.mkdir(parents=True, exist_ok=True)
src = OUT / "income-health-viz-hero-source.html"
src.write_text(html)
png = OUT / "income-health-viz-hero-1680x1080.png"
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                "--window-size=1680,1080", "--virtual-time-budget=10000", f"--screenshot={png}", f"file://{src}"],
               check=True, capture_output=True)
print(png, len(x), round(rho, 3), bend, round(ratio * 100))
