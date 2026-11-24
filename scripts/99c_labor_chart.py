"""Chart for the West Baltimore post: share of adults with a job and share in the labor force, 1940 to 2020-2024,
West Baltimore's nine tracts, with Baltimore city's share with a job for comparison.
Reads analysis/spotlight/labor_westbaltimore.csv (scripts/99_labor_westbaltimore.py).
Adults are 14 and over before 1970 and 16 and over from 1970 on (census definitions).
Output: posts/spotlight-west-baltimore/images/02c-work.png
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, GRID, BLUE, MAGENTA, INK_DIM, SURFACE

use_house_style()
X = {"1940": 1940, "1950": 1950, "1960": 1960, "1970": 1970, "1980": 1980, "1990": 1990, "2000": 2000, "2008-2012": 2010, "2020-2024": 2022}
d = pd.read_csv(ROOT / "analysis/spotlight/labor_westbaltimore.csv", dtype={"year": str}); d["x"] = d.year.map(X)
get = lambda a, m: d[(d.area == a) & (d.measure == m)].sort_values("x")
lfp, ep, cep = get("West Baltimore", "lfp"), get("West Baltimore", "epop"), get("Baltimore city", "epop")
fig, ax = plt.subplots(figsize=(10, 6.4)); fig.subplots_adjust(left=0.08, right=0.83, top=0.72, bottom=0.15)
ax.axvspan(1964, 1966, color=GRID, alpha=0.5, lw=0)
ax.plot(cep.x, cep.value, color=INK_DIM, lw=2, ls="--")
for s, col, off in ((lfp, MAGENTA, 10), (ep, BLUE, -17)):
    ax.plot(s.x, s.value, color=col, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(s.x, s.value):
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, off), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
for s, lab in ((lfp, "In the labor force"), (ep, "With a job"), (cep, "Baltimore city,\nwith a job")):
    ax.annotate(lab, (2022, s.value.iloc[-1]), xytext=(2026.5, s.value.iloc[-1] + (3 if "city" in lab else 0)), textcoords="data", va="center",
                color=INK, fontsize=10, annotation_clip=False)
ax.set_ylim(0, 75); ax.set_xlim(1936, 2026)
xt = [1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2022]; ax.set_xticks(xt); ax.set_xticklabels([str(x) for x in xt[:-1]] + ["2020-24"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
ax.legend(handles=[Line2D([], [], color=MAGENTA, lw=2, marker="o", label="West Baltimore, in the labor force"),
                   Line2D([], [], color=BLUE, lw=2, marker="o", label="West Baltimore, with a job"),
                   Line2D([], [], color=INK_DIM, lw=2, ls="--", label="Baltimore city, with a job")],
          loc="upper left", frameon=False, labelcolor=INK, fontsize=9.5, ncol=3, bbox_to_anchor=(0, 1.11))
titleblock(fig, "By 1980, only about a third of adults here had a job",
           "Share of adults working or looking for work, and share with a job, West Baltimore's nine tracts. Adults are 14 and over\n"
           "through 1960 and 16 and over from 1970 (shaded break). The 2010 point is from the 2008-2012 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census tract counts, 1940-2000, fitted to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates.")
fig.savefig(ROOT / "posts/spotlight-west-baltimore/images/02c-work.png"); plt.close(fig)
