"""North and East Flint story-first charts (2026-11-26).

02-loss-by-decade.png  percent change in people per decade, 1990-2000, 2000-2010, 2010-2020: here, rest of Flint, county
02b-homes.png          two stacked panels, 1990-2020: all homes, and vacant homes, in the eight tracts (no second y-axis)
02c-race.png           Black and white residents, 1990-2020, in the eight tracts
07-medicaid.png        ages 19 to 64: share on Medicaid and share uninsured, here, Genesee County, Michigan, U.S.
Inputs: analysis/spotlight/people_homes_northflint.csv (scripts/99ab), insurance_northflint.csv (scripts/99ac).
"""
import sys
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE, MAGENTA, YELLOW, SURFACE, MUTED

use_house_style(); OUT = ROOT / "posts/spotlight-north-flint/images"; A = ROOT / "analysis/spotlight"
P = pd.read_csv(A / "people_homes_northflint.csv", dtype={"year": str}).set_index(["area", "measure", "year"]).value
NF, RF, GC = "North and East Flint", "Rest of Flint", "Genesee County"
YEARS = ["1990", "2000", "2010", "2020"]
SRC = "Source: NHGIS (IPUMS) census counts, 1990-2020, on 2010 tract lines; city of Flint from Census Bureau 2020 place boundaries."


def style(a):
    a.grid(axis="y", color=GRID, linewidth=0.6); a.tick_params(length=0)
    for sp in ("left", "bottom"): a.spines[sp].set_color(GRID)


# 02: change in people per decade
dec = ["1990-2000", "2000-2010", "2010-2020"]
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.09, right=0.97, top=0.74, bottom=0.12)
w = 0.26
for j, (a, col, lab) in enumerate(((NF, MAGENTA, "North and East Flint"), (RF, BLUE, "Rest of Flint"), (GC, INK_DIM, "Genesee County"))):
    for i, d in enumerate(dec):
        v = P[(a, "people_change_pct", d)]; x = i + (j - 1) * w * 1.08
        ax.bar(x, v, width=w, color=col, label=lab if i == 0 else None)
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, -14 if v < 0 else 5), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.axhline(0, color=INK_DIM, lw=0.8)
ax.set_xticks(range(3)); ax.set_xticklabels(["1990 to 2000", "2000 to 2010", "2010 to 2020"], color=INK, fontsize=11); ax.set_ylim(-35, 5)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); style(ax)
ax.legend(loc="lower left", frameon=False, labelcolor=INK, fontsize=10)
titleblock(fig, "The loss of people sped up in each decade",
           "Percent change in the number of people living in each area over each decade. Census counts.")
credit(fig, SRC)
fig.savefig(OUT / "02-loss-by-decade.png"); plt.close(fig)

# 02b: homes and vacant homes
fig, axs = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True, gridspec_kw=dict(hspace=0.45))
fig.subplots_adjust(left=0.1, right=0.95, top=0.80, bottom=0.09)
xs = [int(y) for y in YEARS]
for a_, m, col, ttl, top in ((axs[0], "homes", MAGENTA, "All homes (housing units)", 12500), (axs[1], "vacant_homes", YELLOW, "Vacant homes", 2600)):
    ys = [P[(NF, m, y)] for y in YEARS]
    a_.plot(xs, ys, color=col, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(xs, ys): a_.annotate(f"{v:,.0f}", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=10)
    a_.set_ylim(0, top); a_.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}")); a_.set_title(ttl, loc="left", color=INK, fontsize=11); style(a_)
axs[1].set_xlim(1985, 2025); axs[1].set_xticks(xs)
ch = 100 * (1 - P[(NF, "homes", "2020")] / P[(NF, "homes", "1990")])
titleblock(fig, f"{ch:.0f}% fewer homes than in 1990, and fewer standing empty",
           "Housing units in the eight tracts in each census, and how many were vacant. Census counts on 2010 tract lines.")
credit(fig, "Source: NHGIS (IPUMS) census counts, 1990-2020, standardized to 2010 tracts.")
fig.savefig(OUT / "02b-homes.png"); plt.close(fig)

# 02c: Black and white residents
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.1, right=0.86, top=0.74, bottom=0.1)
for m, col, lab, dy in (("white", BLUE, "White", -18), ("black", MAGENTA, "Black", 10)):
    ys = [P[(NF, m, y)] for y in YEARS]
    ax.plot(xs, ys, color=col, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(xs, ys): ax.annotate(f"{v:,.0f}", (x, v), xytext=(0, {"white": {1990: 10, 2000: -18, 2010: 10, 2020: -18}, "black": {1990: 10, 2000: 10, 2010: -18, 2020: 10}}[m][x]), textcoords="offset points", ha="center", color=INK, fontsize=10)
    ax.annotate(lab, (xs[-1], ys[-1]), xytext=(16, -12 if m == "white" else 4), textcoords="offset points", color=INK, fontsize=11)
ax.set_xlim(1985, 2025); ax.set_xticks(xs); ax.set_ylim(0, 17000)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}")); style(ax)
titleblock(fig, "White residents declined first. In the 2010s, Black residents declined too",
           "People in the eight tracts by race, census counts. White and Black alone; other groups are not shown.")
credit(fig, "Source: NHGIS (IPUMS) census counts, 1990-2020, standardized to 2010 tracts.")
fig.savefig(OUT / "02c-race.png"); plt.close(fig)

# 07: Medicaid and uninsured, ages 19 to 64
I = pd.read_csv(A / "insurance_northflint.csv").set_index(["area", "measure"])
areas = [(NF, "North and\nEast Flint"), (GC, "Genesee\nCounty"), ("Michigan", "Michigan"), ("United States", "United\nStates")]
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.16)
w = 0.36
for j, (m, col, lab) in enumerate((("medicaid_19_64_pct", BLUE, "Medicaid"), ("uninsured_19_64_pct", YELLOW, "No health insurance"))):
    for i, (a, _) in enumerate(areas):
        v = I.loc[(a, m), "pct"]; x = i + (j - 0.5) * w * 1.08
        ax.bar(x, v, width=w, color=col, label=lab if i == 0 else None)
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 6), textcoords="offset points", ha="center", color=INK, fontsize=11)
ax.set_xticks(range(4)); ax.set_xticklabels([a[1] for a in areas], color=INK, fontsize=10.5); ax.set_ylim(0, 80)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); style(ax)
ax.legend(loc="upper right", frameon=False, labelcolor=INK, fontsize=10)
m1, m2 = I.loc[(NF, "medicaid_19_64_pct"), "moe_pts"], I.loc[(NF, "uninsured_19_64_pct"), "moe_pts"]
titleblock(fig, "Two in three working-age adults here have Medicaid",
           f"Share of people ages 19 to 64 with Medicaid or other means-tested coverage, and with no health insurance, 2020-2024.\n"
           f"In the eight tracts the margins of error are about {m1:.0f} points (Medicaid) and {m2:.0f} points (uninsured).")
credit(fig, "Source: Census Bureau, American Community Survey 2020-2024 five-year estimates, tables C27007 and B27010.")
fig.savefig(OUT / "07-medicaid.png"); plt.close(fig)
print("homes drop %", round(ch, 1))
