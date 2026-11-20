"""Social GIF for income-health-viz: four square charts in the house dark style, one headline each,
sized for phone feeds (1080x1080). Every value is read from data/processed at render time, with the same
20-group median line as the interactive chart. Headline numbers are the line's end values, all quoted in the post.
  1. Tracts: health index against median household income, with the bend at about $110,000.
  2. Tracts: obesity.  3. Tracts: diabetes.  4. Counties: life expectancy (death records).
Tracts at the Census income cap ($250,001) are not drawn but stay in the line, as in the post.
Usage: python scripts/90_social_gif.py
Output: posts/income-health-viz/social/income-health.gif (and frame PNGs alongside, for checking)
"""
import io, json, os, sys
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np, pandas as pd
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from common import PROC, ROOT
from plot_style import BLUE, INK, INK_DIM, MUTED, SURFACE, use_house_style

ORANGE = "#f08a4b"   # the interactive chart's dark-theme line color
HOLD_MS, LAST_MS = 3200, 5000
OUT = ROOT / "posts/income-health-viz/social"; OUT.mkdir(parents=True, exist_ok=True)
use_house_style()


def median_line(x, y, groups=20):
    order = np.argsort(x, kind="stable"); xs, ys = x[order], y[order]
    return np.array([(np.median(xs[lo:hi]), np.median(ys[lo:hi])) for lo, hi in
                     ((int(b * len(xs) / groups), int((b + 1) * len(xs) / groups)) for b in range(groups))])


def frame(df, ycol, title, sub, ylabel, fmt, unit_note, s, alpha, bend=None, ylim=None):
    d = df[df.med_hh_income.notna() & df[ycol].notna()]
    x, y = d.med_hh_income.to_numpy(float), d[ycol].to_numpy(float)
    line = median_line(x, y); drawn = x < 250001
    fig = plt.figure(figsize=(6.75, 6.75), dpi=160)          # 1080 x 1080
    ax = fig.add_axes([0.12, 0.15, 0.83, 0.56])
    ax.scatter(x[drawn] / 1000, y[drawn], s=s, color=BLUE, alpha=alpha, linewidths=0, rasterized=True)
    ax.plot(line[:, 0] / 1000, line[:, 1], color=ORANGE, lw=4, solid_capstyle="round")
    if fmt:
        # start label sits off the line's first point, on the side away from the line and the y tick labels
        rising = line[-1, 1] > line[0, 1]
        start = ("right", "top", (-6, -8)) if rising else ("left", "bottom", (6, 8))
        for (lx, ly), ha, va, off in [(line[0], *start), (line[-1], "left", "center", (10, 0))]:
            ax.annotate(fmt(ly), (lx / 1000, ly), xytext=off, textcoords="offset points", color="#E4E5E7", fontsize=17,
                        fontweight="bold", ha=ha, va=va, path_effects=[pe.withStroke(linewidth=5, foreground=SURFACE)])
    if bend:
        ax.axvline(bend / 1000, color=INK_DIM, lw=1.5, ls=(0, (4, 4)))
        ax.text(bend / 1000 + 4, ax.get_ylim()[0] + 0.06 * np.ptp(ax.get_ylim()), f"Gains slow above\nabout ${round(bend, -4):,.0f}",
                color=INK, fontsize=13, va="bottom", path_effects=[pe.withStroke(linewidth=5, foreground=SURFACE)])
    if ylim:
        ax.set_ylim(*ylim)
        n_out = int(((y < ylim[0]) | (y > ylim[1])).sum())
        unit_note = unit_note.replace("OUTSIDE", f"\n{n_out} counties fall outside the range shown." if n_out else "")
    ax.set_xlim(0, min(255, np.ceil(x[drawn].max() / 10000) * 10 + 5))
    ax.xaxis.set_major_formatter(lambda v, _: f"${int(v)}k" if v else "$0")
    ax.set_xlabel("Median household income", color=INK_DIM, fontsize=13)
    ax.set_ylabel(ylabel, color=INK_DIM, fontsize=13)
    ax.tick_params(labelsize=12); ax.yaxis.grid(True); ax.set_axisbelow(True)
    fig.text(0.05, 0.955, title, color="#E4E5E7", fontsize=24, fontweight="bold", va="top", linespacing=1.15)
    fig.text(0.05, 0.835, sub, color=INK_DIM, fontsize=14, va="top", linespacing=1.35)
    fig.text(0.05, 0.03, unit_note, color=MUTED, fontsize=10.5, va="bottom", linespacing=1.35)
    fig.text(0.95, 0.03, "data4thepeople.com", color=INK_DIM, fontsize=11.5, ha="right", va="bottom", fontweight="bold")
    buf = io.BytesIO(); fig.savefig(buf, format="png", dpi=160); plt.close(fig)
    print(title.replace("\n", " "), [round(v, 1) for v in line[[0, -1], 1]])
    return Image.open(buf).convert("RGB")


t = pd.read_parquet(PROC / "tracts.parquet"); c = pd.read_parquet(PROC / "counties.parquet")
k = json.loads((ROOT / "analysis/results.json").read_text())["national"]["k"]
TR = "Each dot is a U.S. census tract. Orange line: the middle tract\nin each of 20 equal-size income groups."
SRC = "Census Bureau ACS 2020-2024;\nCDC PLACES 2025 (model estimates)."
frames = [
    frame(t, "health_index", "Health rises with income,\nneighborhood by neighborhood",
          "Steepest at the bottom, still rising at the top.\n" + TR, "Health index (0 to 100, higher is better)",
          None, SRC + " Index of 14 measures.", 1.2, 0.18, bend=k, ylim=(0, 100)),
    frame(t, "obesity", "Obesity falls from 45.8% to 23.6%\nof adults as income rises",
          "Lowest-income tracts against the highest.\n" + TR, "Adults with obesity (%)",
          lambda v: f"{v:.1f}%", SRC, 1.2, 0.18),
    frame(t, "diabetes", "Diabetes falls from 20.2% to 8.6%\nof adults as income rises",
          "Lowest-income tracts against the highest.\n" + TR, "Adults with diabetes (%)",
          lambda v: f"{v:.1f}%", SRC, 1.2, 0.18),
    frame(c, "life_expectancy", "Life expectancy rises from\n70.7 to 80.8 years with income",
          "Counted from death records, not modeled.\nEach dot is a county. Orange line: the middle county in each\nof 20 equal-size income groups.",
          "Life expectancy at birth (years)", lambda v: f"{v:.1f}", "County Health Rankings 2021-2023; Census Bureau ACS 2020-2024.OUTSIDE",
          7, 0.45, ylim=(60, 90)),
]
for i, f in enumerate(frames): f.save(OUT / f"frame-{i + 1}.png")
pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
gif = OUT / "income-health.gif"
pal[0].save(gif, save_all=True, append_images=pal[1:], loop=0, optimize=True,
            duration=[HOLD_MS] * (len(pal) - 1) + [LAST_MS])
print(gif, f"{gif.stat().st_size / 1e6:.1f} MB", frames[0].size)
