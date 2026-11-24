"""Unemployment rate in West Baltimore's nine tracts, 1970 to 2020-2024, for the jobs section of the post.

Reads analysis/spotlight/history_final.csv (cand_id U039, measure unemployment_rate), the same series and fit rule as the
other then-and-now charts (years with fit under 0.8 hidden; 1970 and 1980 fit 0.92, 1990 fit 0.99). 2010 is the ACS 2008-2012
estimate. Unemployed as a share of people in the labor force.
Output: posts/spotlight-west-baltimore/images/02b-unemployment.png
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, GRID, BLUE, SURFACE

use_house_style()
YX = {"1970": 1970, "1980": 1980, "1990": 1990, "2000": 2000, "2008-2012": 2010, "2020-2024": 2022}
H = pd.read_csv(ROOT / "analysis/spotlight/history_final.csv", dtype={"year": str})
u = H[(H.cand_id == "U039") & (H.measure == "unemployment_rate") & (H.fit.isna() | (H.fit >= 0.8))]
u = u.assign(x=u.year.map(YX)).dropna(subset=["x"]).sort_values("x")
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.16)
ax.plot(u.x, u.value, color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
for x, v in zip(u.x, u.value):
    ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 11), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_ylim(0, 30); ax.set_xlim(1966, 2026)
ax.set_xticks(list(u.x)); ax.set_xticklabels([("2010" if x == 2010 else "2020-24" if x == 2022 else str(int(x))) for x in u.x])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
titleblock(fig, "Unemployment here rose from 8% to 22% in the 1970s",
           "Share of people in the labor force who were unemployed, West Baltimore's nine census tracts.\nThe 2010 point is from the 2008-2012 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census, 1970-2000, fitted to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates.")
fig.savefig(ROOT / "posts/spotlight-west-baltimore/images/02b-unemployment.png"); plt.close(fig)
print(u[["year", "value", "fit"]].to_string(index=False))
