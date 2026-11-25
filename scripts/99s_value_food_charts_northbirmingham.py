"""Two North Birmingham charts.
05-home-values.png: typical (median) owner home value, 2024 dollars, North Birmingham vs. Jefferson County, 1980 to 2020-2024
  (analysis/spotlight/value_northbirmingham.csv from scripts/99j_value_spotlight.py).
06-food-insecurity.png: share of adults food insecure in the past year (CDC PLACES 2025 release, 2023 estimates), North
  Birmingham, West Baltimore, West Dayton and U.S. tracts in the 40 states with the measure
  (analysis/spotlight/transport_<area>.csv from scripts/92_transport_westdayton.py).
"""
import sys
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE, SURFACE, MUTED

use_house_style(); OUT = ROOT / "posts/spotlight-north-birmingham/images"
X = {"1980": 1980, "1990": 1990, "2000": 2000, "2008-2012": 2010, "2020-2024": 2022}
v = pd.read_csv(ROOT / "analysis/spotlight/value_northbirmingham.csv", dtype={"year": str}); v["x"] = v.year.map(X)
nb, co = v[v.area == "North Birmingham"].sort_values("x"), v[v.area == "Jefferson County"].sort_values("x")
fig, ax = plt.subplots(figsize=(10, 6)); fig.subplots_adjust(left=0.1, right=0.84, top=0.76, bottom=0.14)
ax.plot(co.x, co.median_2024usd, color=INK_DIM, lw=2, ls="--", marker="o", ms=7, mec=SURFACE, mew=2)
ax.plot(nb.x, nb.median_2024usd, color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
for s in (nb, co):
    for x, val in zip(s.x, s.median_2024usd):
        ax.annotate(f"${val/1000:,.0f}K", (x, val), xytext=(0, 11), textcoords="offset points", ha="center", color=INK, fontsize=10)
for s, lab in ((nb, "North Birmingham"), (co, "Jefferson County")):
    ax.annotate(lab, (2022, s.median_2024usd.iloc[-1]), xytext=(2025, s.median_2024usd.iloc[-1]), textcoords="data", va="center", color=INK, fontsize=10.5, annotation_clip=False)
ax.set_ylim(0, 280000); ax.set_xlim(1976, 2025); xt = [1980, 1990, 2000, 2010, 2022]; ax.set_xticks(xt); ax.set_xticklabels(["1980", "1990", "2000", "2010", "2020-24"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"${val/1000:,.0f}K")); ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
titleblock(fig, "Home values here have not grown since 1980",
           "Typical value of an owner's home, in 2024 dollars, North Birmingham's four census tracts and Jefferson County.\nValues are owners' own estimates. The 2010 point is from the 2008-2012 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census, 1980-2000, fitted to today's tracts; ACS 2008-2012 and 2020-2024; CPI-U.")
fig.savefig(OUT / "05-home-values.png"); plt.close(fig)

F = {}
for name, f in (("North Birmingham", "northbirmingham"), ("West Baltimore", "westbaltimore"), ("West Dayton", "westdayton")):
    t = pd.read_csv(ROOT / f"analysis/spotlight/transport_{f}.csv"); F[name] = float(t[(t.area == name) & (t.measure == "FOODINSECU")].value.iloc[0])
    us = float(t[(t.area.str.startswith("PLACES")) & (t.measure == "FOODINSECU")].value.iloc[0])
F["U.S."] = us
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.08, right=0.95, top=0.78, bottom=0.14)
names = list(F); vals = [F[k] for k in names]
cols = [BLUE, MUTED, MUTED, INK_DIM]
ax.bar(range(len(names)), vals, color=cols, width=0.6)
for i, val in enumerate(vals): ax.annotate(f"{val:.0f}%", (i, val), xytext=(0, 6), textcoords="offset points", ha="center", color=INK, fontsize=11)
ax.set_xticks(range(len(names))); ax.set_xticklabels(names, color=INK, fontsize=11)
ax.set_ylim(0, 70); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val:.0f}%")); ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0); ax.set_axisbelow(True)
for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
titleblock(fig, "About half of adults in all three neighborhoods were food insecure",
           "Share of adults who were food insecure at some point in the past year, 2023. U.S. means census tracts in the 40 states\nwhere CDC has this measure, weighted by population.")
credit(fig, "Source: CDC PLACES 2025 release, model estimates for 2023, weighted by tract population.")
fig.savefig(OUT / "06-food-insecurity.png"); plt.close(fig)
print(F)
