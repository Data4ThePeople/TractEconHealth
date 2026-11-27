"""North and East Flint chart 03 without the vacancy line (Eric, 2b, 2026-11-27).

Share of people below 200% of the poverty line, North and East Flint (U013) and the U.S., 1990, 2000, 2008-2012,
2020-2024, from analysis/spotlight/below200.csv (NHGIS 1990-2000, ACS C17002 after; built by scripts/81_spotlight_charts.py
inputs). Output: posts/spotlight-north-flint/images/03-low-income.png
"""
import sys
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, GRID, MAGENTA, SURFACE
use_house_style()
LX = {"1990": 1990, "2000": 2000, "2008-2012": 2010, "2020-2024": 2022}
B = pd.read_csv(ROOT / "analysis/spotlight/below200.csv", dtype={"area": str})
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.08, right=0.82, top=0.74, bottom=0.12)
for a, col, ls, lab, mk in (("U013", MAGENTA, "-", "North and East Flint", "o"), ("US", INK, "--", "United States", None)):
    d = B[B.area == a].assign(x=lambda d: d.year.map(LX)).sort_values("x")
    ax.plot(d.x, d.value, color=col, lw=2, ls=ls, marker=mk, ms=8, mec=SURFACE, mew=2)
    for x, v in zip(d.x, d.value): ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=10)
    ax.annotate(lab, (2022, d.value.iloc[-1]), xytext=(2024.5, d.value.iloc[-1]), textcoords="data", va="center", color=INK, fontsize=10.5, annotation_clip=False)
ax.set_xlim(1986, 2024); ax.set_ylim(0, 100); ax.set_xticks([1990, 2000, 2010, 2022]); ax.set_xticklabels(["1990", "2000", "2008-12", "2020-24"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
titleblock(fig, "Nearly three in four people here live below 200% of the poverty line",
           "Share of people below 200% of the federal poverty line, North and East Flint and the U.S.\nIncome for 2010 is from the 2008-2012 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census, 1990-2000; ACS 2008-2012 and 2020-2024 five-year estimates.")
fig.savefig(ROOT / "posts/spotlight-north-flint/images/03-low-income.png"); plt.close(fig)
