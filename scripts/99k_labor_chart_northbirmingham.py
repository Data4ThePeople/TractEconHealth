"""Chart for the North Birmingham post: share of adults with a job and share in the labor force, 1980 to 2020-2024,
the four tracts, with Jefferson County's share with a job for comparison. Years before 1980 are left out: the old tract
lines fit today's at 0.48-0.70, under the 0.8 rule.
Reads analysis/spotlight/labor_northbirmingham.csv (scripts/99e_labor_spotlight.py U034).
Output: posts/spotlight-north-birmingham/images/02c-work.png
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
d = pd.read_csv(ROOT / "analysis/spotlight/labor_northbirmingham.csv", dtype={"year": str}); d["x"] = d.year.map(X)
d = d[d.x >= 1980]
get = lambda a, m: d[(d.area == a) & (d.measure == m)].sort_values("x")
lfp, ep, cep = get("North Birmingham", "lfp"), get("North Birmingham", "epop"), get("Jefferson County", "epop")
fig, ax = plt.subplots(figsize=(10, 6.4)); fig.subplots_adjust(left=0.08, right=0.83, top=0.72, bottom=0.15)
ax.plot(cep.x, cep.value, color=INK_DIM, lw=2, ls="--")
for s, col, off in ((lfp, MAGENTA, -16), (ep, BLUE, -17)):
    ax.plot(s.x, s.value, color=col, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(s.x, s.value):
        o = off
        if col == MAGENTA:  # labor force labels go above unless the county line is close above, then below
            gap = cep.set_index("x").value.get(x, 99) - v; o = 10 if gap > 6 else -16
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, o), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
for s, lab in ((lfp, "In the labor force"), (ep, "With a job"), (cep, "Jefferson County,\nwith a job")):
    ax.annotate(lab, (2022, s.value.iloc[-1]), xytext=(2026.5, s.value.iloc[-1] + {"In the labor force": 2.5, "With a job": -2.5}.get(lab, 3)), textcoords="data", va="center",
                color=INK, fontsize=10, annotation_clip=False)
ax.set_ylim(0, 75); ax.set_xlim(1976, 2026)
xt = [1980, 1990, 2000, 2010, 2022]; ax.set_xticks(xt); ax.set_xticklabels([str(x) for x in xt[:-1]] + ["2020-24"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
ax.legend(handles=[Line2D([], [], color=MAGENTA, lw=2, marker="o", label="North Birmingham, in the labor force"),
                   Line2D([], [], color=BLUE, lw=2, marker="o", label="North Birmingham, with a job"),
                   Line2D([], [], color=INK_DIM, lw=2, ls="--", label="Jefferson County, with a job")],
          loc="upper left", frameon=False, labelcolor=INK, fontsize=9.5, ncol=3, bbox_to_anchor=(0, 1.11))
titleblock(fig, "Since 1980, fewer than half of adults here have had a job",
           "Share of adults 16 and over working or looking for work, and share with a job, North Birmingham's four tracts,\n"
           "with Jefferson County for comparison. The 2010 point is from the 2008-2012 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census tract counts, 1980-2000, fitted to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates.")
fig.savefig(ROOT / "posts/spotlight-north-birmingham/images/02c-work.png"); plt.close(fig)
