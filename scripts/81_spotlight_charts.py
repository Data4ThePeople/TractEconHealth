"""Charts for one spotlight post. Usage: python scripts/81_spotlight_charts.py U047

  01-map.png         the neighborhood outline on the 1930s HOLC map, with the freeways (TIGER primary roads)
  02-population.png  people living in the neighborhood, 1970 to 2020-2024 (history_final.csv)
  03-poverty-vacancy.png  poverty rate and share of homes vacant over time (history_final.csv)
  04-overdose.png    county drug overdose death rate vs. the middle U.S. county, 2003-2021 (CDC NCHS model rates)
Years whose old-tract fit is under 0.8 are left out, as in the tables. Output: posts/<slug>/images/
"""
import json, sys
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, GRID, YELLOW, BLUE, MAGENTA, SURFACE

CFG = {
    "U047": dict(slug="spotlight-west-dayton", name="West Dayton", county="39113", county_name="Montgomery County",
                 city="Dayton", roads=["I- 75", "US Hwy 35", "I- 75 N", "I- 75 S", "US Hwy 35 E", "US Hwy 35 W"],
                 labels=[("Downtown", 39.7589, -84.1916)], pad=0.012, holc_year="1937"),
}
cid = sys.argv[1]; C = CFG[cid]
OUTD = ROOT / "posts" / C["slug"] / "images"; OUTD.mkdir(parents=True, exist_ok=True)
use_house_style()
sets = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id")
tracts = sets.loc[cid, "tracts"].split(";")
h = pd.read_csv(ROOT / "analysis/spotlight/history_final.csv", dtype={"year": str})
h = h[(h.cand_id == cid) & (h.fit.isna() | (h.fit >= 0.8))]
YX = {"1970": 1970, "1980": 1980, "1990": 1990, "2000": 2000, "2010": 2010, "2020-2024": 2022}

def axes_style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)

# ---------- 01 map ----------
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").set_index("GEOID")
hood = g20.loc[tracts].to_crs(4326)
outline = hood.dissolve()
minx, miny, maxx, maxy = outline.total_bounds; p = C["pad"]
holc = gpd.read_file(RAW / "holc" / "mappinginequality.json", bbox=(minx - 0.08, miny - 0.06, maxx + 0.08, maxy + 0.06)).to_crs(4326)
holc = holc[holc.city == C["city"]] if "city" in holc.columns else holc
GC = {"A": "#5a9e6f", "B": "#4f8fc0", "C": "#c9a227", "D": "#c4554d"}
roads = gpd.read_file(RAW / "tiger" / "roads" / f"tl_2024_{C['county']}_roads.shp").to_crs(4326)
roads = roads[(roads.MTFCC == "S1100")]
fig, ax = plt.subplots(figsize=(10, 8.6)); fig.subplots_adjust(left=0.03, right=0.97, top=0.84, bottom=0.08)
for gr, col in GC.items():
    sub = holc[holc.grade == gr]
    if len(sub): sub.plot(ax=ax, color=col, alpha=0.55, edgecolor=SURFACE, linewidth=0.6)
holc[~holc.grade.isin(GC)].plot(ax=ax, color=MUTED, alpha=0.25, edgecolor=SURFACE, linewidth=0.6)
roads.plot(ax=ax, color=INK_DIM, linewidth=1.6)
outline.boundary.plot(ax=ax, color=INK, linewidth=2.4)
for lab, la, lo in C["labels"]:
    ax.annotate(lab, (lo, la), color=INK, fontsize=10, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec="none", alpha=0.8))
ax.set_xlim(minx - p - 0.03, maxx + p + 0.03); ax.set_ylim(miny - p, maxy + p)
ax.set_axis_off(); ax.set_aspect(1 / np.cos(np.radians((miny + maxy) / 2)))
leg = [Patch(fc=GC[g], alpha=0.55, label=l) for g, l in
       [("A", "A, \"best\""), ("B", "B, \"still desirable\""), ("C", "C, \"declining\""), ("D", "D, \"hazardous\"")]]
leg += [Line2D([], [], color=INK, lw=2.4, label=f"{C['name']} (this story)"), Line2D([], [], color=INK_DIM, lw=1.6, label="Freeways today")]
ax.legend(handles=leg, loc="lower left", frameon=True, facecolor=SURFACE, edgecolor=GRID, labelcolor=INK, fontsize=9.5)
yr = C["holc_year"]  # Mapping Inequality city record for this city
titleblock(fig, f"{C['name']} on the {yr} federal mortgage map",
           f"Home Owners' Loan Corporation grades for {C['city']}, with the {len(tracts)} census tracts in this story outlined\nand today's freeways drawn in gray.")
credit(fig, "Source: Mapping Inequality, University of Richmond Digital Scholarship Lab; U.S. Census Bureau TIGER/Line 2024 roads and 2020 tracts.")
fig.savefig(OUTD / "01-map.png"); plt.close(fig)

# ---------- 02 population ----------
pop = h[h.measure == "population"].assign(x=lambda d: d.year.map(YX)).dropna(subset=["x"]).sort_values("x")
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.16)
ax.plot(pop.x, pop.value, color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
for x, v in zip(pop.x, pop.value):
    ax.annotate(f"{v:,.0f}", (x, v), xytext=(0, 11), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_ylim(0, pop.value.max() * 1.18); ax.set_xlim(1966, 2026)
ax.set_xticks(list(pop.x)); ax.set_xticklabels([("2020-24" if x == 2022 else str(int(x))) for x in pop.x])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}")); axes_style(ax)
first, last = pop.value.iloc[0], pop.value.iloc[-1]
titleblock(fig, f"{C['name']} has {100 * (1 - last / first):.0f}% fewer people than in {int(pop.x.iloc[0])}",
           f"People living in the {len(tracts)} census tracts, counted on today's tract lines.")
credit(fig, "Source: NHGIS (IPUMS) decennial census tract counts, 1970-2010, matched to today's tracts; ACS 2020-2024 five-year estimates.")
fig.savefig(OUTD / "02-population.png"); plt.close(fig)

# ---------- 03 poverty and vacancy ----------
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.08, right=0.83, top=0.8, bottom=0.16)
for m, col, lab in [("poverty_rate", MAGENTA, "In poverty"), ("vacancy_rate", YELLOW, "Homes vacant")]:
    d = h[h.measure == m].assign(x=lambda d: d.year.map(YX)).dropna(subset=["x"]).sort_values("x")
    ax.plot(d.x, d.value, color=col, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(d.x, d.value):
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    ax.annotate(lab, (d.x.iloc[-1], d.value.iloc[-1]), xytext=(14, 0), textcoords="offset points", va="center", color=INK, fontsize=10.5)
ax.set_ylim(0, 55); ax.set_xlim(1966, 2026)
ax.set_xticks([1970, 1980, 1990, 2000, 2010, 2022]); ax.set_xticklabels(["1970", "1980", "1990", "2000", "2010", "2020-24"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); axes_style(ax)
ax.legend(handles=[Line2D([], [], color=MAGENTA, lw=2, marker="o", label="People in poverty"),
                   Line2D([], [], color=YELLOW, lw=2, marker="o", label="Homes vacant")],
          loc="upper left", frameon=False, labelcolor=INK, fontsize=9.5)
titleblock(fig, "More people in poverty, more homes empty",
           f"Share of people below the poverty line and share of homes vacant, {C['name']}. The 2010 census did not\nask about income, and vacancy before 1990 is not in our tract data.")
credit(fig, "Source: NHGIS (IPUMS) decennial census, 1970-2010; ACS 2020-2024 five-year estimates.")
fig.savefig(OUTD / "03-poverty-vacancy.png"); plt.close(fig)

# ---------- 04 overdose ----------
od = pd.read_parquet(RAW / "cdc" / "overdose_county_model.parquet")
od["fips"] = od.fips.astype(str).str.zfill(5); od["year"] = od.year.astype(int); od["r"] = pd.to_numeric(od.model_based_death_rate, errors="coerce")
here = od[od.fips == C["county"]].sort_values("year"); mid = od.groupby("year").r.median()
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.08, right=0.8, top=0.8, bottom=0.16)
ax.plot(here.year, here.r, color=MAGENTA, lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5)
ax.plot(mid.index, mid.values, color=INK, lw=2, ls="--")
for d, lab in [(here.set_index("year").r, C["county_name"]), (mid, "Middle U.S. county")]:
    ax.annotate(f"{lab}\n{d.iloc[-1]:.0f} per 100,000", (d.index[-1], d.iloc[-1]), xytext=(10, 0), textcoords="offset points", va="center", color=INK, fontsize=10)
for y in (2003, 2017):
    v = here.set_index("year").r[y]; ax.annotate(f"{v:.0f}", (y, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
ax.set_ylim(0, here.r.max() * 1.15); ax.set_xticks(range(2003, 2022, 3)); axes_style(ax)
titleblock(fig, f"Overdose deaths in {C['county_name']} rose far above the typical county",
           f"Drug overdose deaths per 100,000 people, CDC model estimates, {C['county_name']} and the middle U.S. county,\n2003-2021. County-wide, not {C['name']} alone.")
credit(fig, "Source: CDC National Center for Health Statistics, Drug Poisoning Mortality by County (model-based rates), data.cdc.gov.")
fig.savefig(OUTD / "04-overdose.png"); plt.close(fig)
print("charts in", OUTD, "| HOLC year", yr, "| 2021 rates:", round(here.r.iloc[-1], 1), round(mid.iloc[-1], 1))
