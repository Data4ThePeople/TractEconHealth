"""North and East Flint (U013): food insecurity and food access (2026-11-26).

Replaces the county overdose chart with tract-level measures.
Inputs:
- CDC PLACES 2025 tract file (data/raw/places/places_tract_2025.parquet), 2023 BRFSS-based model estimates for adults:
  FOODINSECU (food insecurity in the past 12 months), FOODSTAMP (received food stamps in the past 12 months),
  LACKTRPT (lack of reliable transportation in the past 12 months). Areas are weighted by each tract's adult
  population (totalpop18plus), the same as the table at the top of the post. Genesee County, Michigan and the U.S.
  are all tracts in each.
- USDA Food Access Research Atlas, 2019 (data/raw/usda_fara): LILATracts_halfAnd10, LILATracts_1And10 (low income and
  low access at 1/2 mile or 1 mile urban), lahunvhalfshare (share of housing units with no vehicle and more than
  1/2 mile from a supermarket). Atlas tracts are 2010 tracts; the eight 2020 tract codes match 2010 codes here.
- USDA SNAP retailer historical file 2005-2025: Supermarket, Super Store and Large Grocery Store records in Flint
  within 1 mile of the eight tracts, with authorization and end dates.
Outputs: analysis/spotlight/food_northflint.csv, analysis/spotlight/grocers_northflint.csv,
posts/spotlight-north-flint/images/04-food.png
"""
import sys, zipfile
from pathlib import Path
import geopandas as gpd, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW
from plot_style import use_house_style, titleblock, credit, INK, GRID, BLUE, MAGENTA, YELLOW

use_house_style(); A = ROOT / "analysis/spotlight"
T = pd.read_csv(A / "final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U013"].tracts.split(";")

# PLACES
p = pd.read_parquet(RAW / "places/places_tract_2025.parquet")
p = p[p.measureid.isin(["FOODINSECU", "FOODSTAMP", "LACKTRPT"])].copy()
p["v"] = pd.to_numeric(p.data_value); p["w"] = pd.to_numeric(p.totalpop18plus); p["geo"] = p.locationname.astype(str)
NF = "North and East Flint"
AREAS = {NF: p.geo.isin(T), "Genesee County": p.countyfips.astype(str) == "26049", "Michigan": p.stateabbr == "MI",
         "United States": p.geo.notna()}
rows = []
for m in ["FOODINSECU", "FOODSTAMP", "LACKTRPT"]:
    d = p[p.measureid == m]
    for a, sel in AREAS.items():
        x = d[sel.loc[d.index]]
        rows.append(dict(area=a, measure=m, value=round((x.v * x.w).sum() / x.w.sum(), 2), n_tracts=len(x)))
    h = d[d.geo.isin(T)]
    rows.append(dict(area=NF, measure=m + "_min", value=h.v.min(), n_tracts=len(h)))
    rows.append(dict(area=NF, measure=m + "_max", value=h.v.max(), n_tracts=len(h)))
    rows.append(dict(area=NF, measure=m + "_median_tract_us_pctile", value=round(100 * (d.v < h.v.median()).mean(), 1), n_tracts=len(d)))

# USDA Food Access Research Atlas
f = pd.read_csv(RAW / "usda_fara/Food Access Research Atlas.csv", dtype={"CensusTract": str})
f = f[f.CensusTract.isin(T)]
rows += [dict(area=NF, measure="lila_half_tracts", value=int(f.LILATracts_halfAnd10.sum()), n_tracts=len(f)),
         dict(area=NF, measure="lila_1mile_tracts", value=int(f.LILATracts_1And10.sum()), n_tracts=len(f)),
         dict(area=NF, measure="tracts_novehicle_far_over20pct", value=int((f.lahunvhalfshare > 20).sum()), n_tracts=len(f))]
out = pd.DataFrame(rows); out.to_csv(A / "food_northflint.csv", index=False)
print(out.to_string())

# SNAP grocers near the tracts
z = zipfile.ZipFile(RAW / "snap/snap-retailer-locator-data2005-2025.zip")
s = pd.read_csv(z.open(z.namelist()[0]), dtype=str, encoding="latin-1")
s.columns = [c.replace("﻿", "").replace("ï»¿", "") for c in s.columns]
s = s[(s.State == "MI") & (s.City.str.upper().str.strip() == "FLINT") & s["Store Type"].isin(["Supermarket", "Super Store", "Large Grocery Store"])]
g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.Longitude.astype(float), s.Latitude.astype(float)), crs=4326).to_crs(5070)
H = gpd.read_file(RAW / "tiger/cb_2020_us_tract_500k.shp").query("GEOID in @T").to_crs(5070).union_all()
g["miles_from_tracts"] = (g.distance(H) / 1609.34).round(2)
g = g[g.miles_from_tracts <= 1].sort_values("miles_from_tracts")
cols = ["Store Name", "Store Type", "Street Number", "Street Name", "Authorization Date", "End Date", "miles_from_tracts"]
g[cols].to_csv(A / "grocers_northflint.csv", index=False); print(g[cols].to_string())

# chart
V = out.set_index(["area", "measure"]).value
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.16)
w = 0.26; areas = [(NF, "North and\nEast Flint"), ("Genesee County", "Genesee\nCounty"), ("Michigan", "Michigan"), ("United States", "United\nStates")]
for j, (m, col, lab) in enumerate((("FOODINSECU", MAGENTA, "Food insecure"), ("FOODSTAMP", BLUE, "Got food stamps"),
                                   ("LACKTRPT", YELLOW, "Lacked reliable transportation"))):
    for i, (a, _) in enumerate(areas):
        v = V[(a, m)]; x = i + (j - 1) * w * 1.08
        ax.bar(x, v, width=w, color=col, label=lab if i == 0 else None)
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 5), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_xticks(range(4)); ax.set_xticklabels([a[1] for a in areas], color=INK, fontsize=10.5); ax.set_ylim(0, 65)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
ax.legend(loc="upper right", frameon=False, labelcolor=INK, fontsize=10)
titleblock(fig, "Nearly half the adults here were food insecure",
           "Share of adults who, in the past 12 months, were food insecure, got food stamps, or lacked reliable\n"
           "transportation. CDC model estimates, weighted by each tract's adult population.")
credit(fig, "Source: CDC PLACES 2025 release (2023 survey data), census tract estimates.")
fig.savefig(ROOT / "posts/spotlight-north-flint/images/04-food.png"); plt.close(fig)
