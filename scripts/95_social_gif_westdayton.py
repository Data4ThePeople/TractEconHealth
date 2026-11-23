"""Animated GIF of West Dayton chart 03 (poverty, low income and vacant homes) for social posts.

The lines draw in from 1970 to 2020-2024 over about 8 seconds, then the finished chart holds for about 5.
Same data, colors, labels and title as chart 03 in scripts/81_spotlight_charts.py (West Dayton, pov_line).
A value label appears only when a line reaches a real data point, so no in-between values are shown.
Output: posts/spotlight-west-dayton/social/poverty-since-1970.gif
"""
import io, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, GRID, YELLOW, BLUE, MAGENTA, SURFACE

use_house_style()
OUT = ROOT / "posts/spotlight-west-dayton/social"; OUT.mkdir(parents=True, exist_ok=True)
LX = {"1970": 1970, "1980": 1980, "1990": 1990, "2000": 2000, "2008-2012": 2010, "2010": 2010, "2020-2024": 2022}
H = pd.read_csv(ROOT / "analysis/spotlight/history_final.csv", dtype={"year": str}); H = H[(H.cand_id == "U047") & (H.fit.isna() | (H.fit >= 0.8))]
B = pd.read_csv(ROOT / "analysis/spotlight/below200.csv", dtype={"area": str})
lw = B[B.area == "U047"].assign(x=lambda d: d.year.map(LX)).sort_values("x")
vc = H[(H.measure == "vacancy_rate") & (H.year != "2008-2012")].assign(x=lambda d: d.year.map(LX)).dropna(subset=["x"]).sort_values("x")
pv = H[H.measure == "poverty_rate"].assign(x=lambda d: d.year.map(LX)).dropna(subset=["x"]).sort_values("x")
SER = [(pv, BLUE, (0, 10), "Poverty"), (lw, MAGENTA, (0, 10), "Low income"), (vc, YELLOW, (0, -17), "Homes vacant")]
SECONDS, HOLD, FRAME_MS = 8.0, 5.0, 80


def clip(d, xc):
    """Points up to xc, plus an interpolated end point so the line grows smoothly (no label on it)."""
    x, y = d.x.to_numpy(float), d.value.to_numpy(float)
    keep = x <= xc
    if keep.all() or not keep.any(): return x[keep], y[keep], x[keep], y[keep]
    i = keep.sum()
    return np.append(x[:i], xc), np.append(y[:i], np.interp(xc, x[i - 1:i + 1], y[i - 1:i + 1])), x[:i], y[:i]


def frame(xc):
    fig, ax = plt.subplots(figsize=(10, 6.0)); fig.subplots_adjust(left=0.08, right=0.8, top=0.72, bottom=0.15)
    for d, col, off, _ in SER:
        lx, ly, px, py = clip(d, xc)
        if len(lx) > 1: ax.plot(lx, ly, color=col, lw=2)
        ax.plot(px, py, "o", color=col, ms=8, mec=SURFACE, mew=2)
        for x, v in zip(px, py):
            ax.annotate(f"{v:.0f}%", (x, v), xytext=off, textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    if xc >= 2022:  # end labels only on the finished chart, as in the published version
        ends = sorted([(lw.value.iloc[-1], "Low income"), (vc.value.iloc[-1], "Homes vacant"), (pv.value.iloc[-1], "Poverty")])
        gapu = 80 * 0.06; pos = []
        for v, l in ends:
            y = v if not pos or v - pos[-1] >= gapu else pos[-1] + gapu; pos.append(y)
            ax.annotate(l, (2022, v), xytext=(2026.5, y), textcoords="data", va="center", color=INK, fontsize=10.5, annotation_clip=False)
    ax.set_ylim(0, 80); ax.set_xlim(1966, 2026)
    xt = [1970, 1980, 1990, 2000, 2010, 2022]; ax.set_xticks(xt); ax.set_xticklabels([str(x) for x in xt[:-1]] + ["2020-24"])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.legend(handles=[Line2D([], [], color=MAGENTA, lw=2, marker="o", label="People below 200% of the poverty line"),
                       Line2D([], [], color=YELLOW, lw=2, marker="o", label="Homes vacant"),
                       Line2D([], [], color=BLUE, lw=2, marker="o", label="People below the poverty line")],
              loc="upper left", frameon=False, labelcolor=INK, fontsize=9.5, ncol=3, bbox_to_anchor=(0, 1.11))
    titleblock(fig, "Poverty here more than doubled since 1970, and more homes are empty",
               "Share of people below the poverty line (1970 on) and below 200% of it (1990 on), and share of homes vacant, West Dayton.\n"
               "Income for 2010 is from the 2008-2012 survey; vacancy is from the 2010 census.")
    credit(fig, "Source: NHGIS (IPUMS) decennial census, 1970-2010, fitted to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates.")
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=120); plt.close(fig); buf.seek(0)
    return Image.open(buf).convert("RGB")


n = int(SECONDS * 1000 / FRAME_MS)
frames = [frame(1970 + (2022 - 1970) * k / (n - 1)) for k in range(n)]
frames[-1] = frame(2022)
pal = frames[-1].quantize(colors=128)
q = [f.quantize(palette=pal) for f in frames]
durs = [FRAME_MS] * (len(q) - 1) + [int(HOLD * 1000)]
q[0].save(OUT / "poverty-since-1970.gif", save_all=True, append_images=q[1:], duration=durs, loop=0, optimize=True)
frames[-1].save(OUT / "poverty-since-1970-last.png")
print("frames", len(q), "size", frames[-1].size)
