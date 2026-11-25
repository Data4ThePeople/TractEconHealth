"""North Birmingham: people living in the four tracts (1980 to 2020-2024) and the share below 200% of the poverty line
(1990 to 2020-2024, with the U.S. share), as two stacked panels on one time axis. Two panels, not a second y-axis.
Inputs: analysis/spotlight/history_final.csv (population, same as chart 02) and analysis/spotlight/below200.csv (same as chart 03).
Output: posts/spotlight-north-birmingham/images/02-people-income.png
"""
import sys
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE, MAGENTA, SURFACE

use_house_style()
X = {"1980": 1980, "1990": 1990, "2000": 2000, "2008-2012": 2010, "2010": 2010, "2020-2024": 2022}
H = pd.read_csv(ROOT / "analysis/spotlight/history_final.csv", dtype={"year": str})
pop = H[(H.cand_id == "U034") & (H.measure == "population")].assign(x=lambda d: d.year.map(X)).dropna(subset=["x"]).sort_values("x")
B = pd.read_csv(ROOT / "analysis/spotlight/below200.csv", dtype={"area": str, "year": str})
lw = B[B.area == "U034"].assign(x=lambda d: d.year.map(X)).sort_values("x")
us = B[B.area == "US"].assign(x=lambda d: d.year.map(X)).sort_values("x")

fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[1, 1], hspace=0.38))
fig.subplots_adjust(left=0.1, right=0.86, top=0.8, bottom=0.11)
a1.plot(pop.x, pop.value, color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
for x, v in zip(pop.x, pop.value):
    a1.annotate(f"{v:,.0f}", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=10)
a1.set_ylim(0, pop.value.max() * 1.25); a1.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
a1.set_title("People living in the four tracts", loc="left", color=INK, fontsize=11)
a2.plot(us.x, us.value, color=INK_DIM, lw=2, ls="--")
a2.plot(lw.x, lw.value, color=MAGENTA, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
for x, v in zip(lw.x, lw.value):
    a2.annotate(f"{v:.0f}%", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=10)
for s, lab in ((lw, "North\nBirmingham"), (us, "U.S.")):
    a2.annotate(f"{lab}", (2022, s.value.iloc[-1]), xytext=(2024, s.value.iloc[-1]), textcoords="data", va="center", color=INK, fontsize=10, annotation_clip=False)
    if lab == "U.S.": a2.annotate(f"{s.value.iloc[-1]:.0f}%", (2022, s.value.iloc[-1]), xytext=(0, -16), textcoords="offset points", ha="center", color=INK, fontsize=10)
a2.set_ylim(0, 100); a2.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
a2.set_title("Share of people below 200% of the poverty line", loc="left", color=INK, fontsize=11)
for a in (a1, a2):
    a.grid(axis="y", color=GRID, linewidth=0.6); a.tick_params(length=0)
    for sp in ("left", "bottom"): a.spines[sp].set_color(GRID)
a2.set_xlim(1976, 2026); xt = [1980, 1990, 2000, 2010, 2022]; a2.set_xticks(xt); a2.set_xticklabels(["1980", "1990", "2000", "2010", "2020-24"])
ch = 100 * (pop.value.iloc[-1] / pop.value.iloc[0] - 1)
titleblock(fig, f"{abs(ch):.0f}% fewer people, and most still have low incomes",
           f"People living in North Birmingham's four census tracts, 1980 to 2020-2024, and the share below 200% of the poverty\n"
           "line, 1990 to 2020-2024, with the U.S. share dashed. Income for 2010 is from the 2008-2012 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census tract counts, 1980-2010, matched to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates.")
fig.savefig(ROOT / "posts/spotlight-north-birmingham/images/02-people-income.png"); plt.close(fig)
print(pop[["year", "value"]].to_string(index=False)); print(lw[["year", "value"]].to_string(index=False)); print(us[["year", "value"]].to_string(index=False)); print(round(ch, 1))
