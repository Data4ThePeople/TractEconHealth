"""Dayton's 1937 HOLC areas, then and now: the gap between D areas and the rest of the graded city in 1940 and in
the ACS 2020-2024.

Same method both years. Counts (people, homes, workers) are split across HOLC areas by each tract's share of land
in the area (EPSG 5070) and pooled by grade. Medians (home value, rent) are the median of tract medians among tracts
assigned to the grade that covers most of their land, using tracts at least 30% covered by graded areas.
  1940 (NHGIS 1940_tPH_Major, 1940 tract lines): homeownership NT27; median home value NT36; median contract rent NT39;
       jobless = public emergency work + seeking work over the labor force, both sexes, NT22; nonwhite NT2.
  Employed share of adults: 1940 employed (not counting emergency work) over persons 14+, NT22; ACS employed over
       persons 16+, B23025.
  2020-2024 (ACS 5-year, 2020 tract lines, cb_2020): homeownership B25003; median home value B25077; median contract
       rent B25058; unemployment B23025 (unemployed over civilian labor force); Black alone B02001; population B01003.
Dollar medians are compared as a ratio (D over the rest), so inflation drops out.
Output: analysis/spotlight/holc_then_now_dayton.csv
"""
import json, sys
import geopandas as gpd, numpy as np, pandas as pd, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from common import RAW, ROOT
from d4tp_env import read_env_file

g = json.loads((RAW / "holc" / "mappinginequality.json").read_text())
H = gpd.GeoDataFrame.from_features([f for f in g["features"] if f["properties"]["city"] == "Dayton" and f["properties"]["state"] == "OH"], crs=4326).to_crs(5070)
H = H[H.grade.isin(list("ABCD"))][["grade", "geometry"]]
H["grp"] = np.where(H.grade == "D", "D", "A-C")


def overlay(tr, key):
    tr = tr.copy(); tr["ta"] = tr.area
    x = gpd.overlay(tr, H, how="intersection", keep_geom_type=True); x["w"] = x.area / x.ta
    cov = x.groupby(key).w.sum()
    maj = x.sort_values("w").drop_duplicates(key, keep="last"); maj = maj[maj[key].map(cov) >= 0.3]
    return x, maj


# ---- 1940 ----
N = RAW / "nhgis"
def read(d):
    t = pd.read_csv(next((N / d).rglob("*_1940_tract.csv")), encoding="latin-1", low_memory=False, skiprows=[1])
    return t[(t.STATEA.astype(int) == 39) & (t.COUNTYA.astype(int) == 113)]
a, b = read("extract_1940"), read("extract_1940b")
t = a.merge(b[["GISJOIN"] + [c for c in b.columns if c[:2] in ("BU", "BV") and c not in a.columns]], on="GISJOIN")
num = [c for c in t.columns if c[:2] in ("BU", "BV")]; t[num] = t[num].apply(pd.to_numeric, errors="coerce")
t["own_n"], t["occ_n"] = t.BU2001, t.BU2001 + t.BU2002
t["jl_n"] = t[["BUX002", "BUX003", "BUX010", "BUX011"]].sum(axis=1)
t["lf_n"] = t[["BUX001", "BUX002", "BUX003", "BUX009", "BUX010", "BUX011"]].sum(axis=1)
t["race_n"], t["pop_n"] = t.BUQ002, t.BUB001
t["emp_n"] = t.BUX001 + t.BUX009   # employed, not counting public emergency work
t["adult_n"] = t[[f"BUX{i:03d}" for i in range(1, 17)]].sum(axis=1)   # persons 14+
t["value"], t["rent"] = t.BVC001.replace(0, np.nan), t.BVF001.replace(0, np.nan)
s40 = gpd.read_file(next((N / "extract_1940").rglob("US_tract_1940_conflated.shp")))
s40 = s40[s40.GISJOIN.isin(t.GISJOIN)].to_crs(5070).merge(t, on="GISJOIN")

# ---- 2020-2024 ----
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
V = {"B25003_001E": "occ_n", "B25003_002E": "own_n", "B25077_001E": "value", "B25058_001E": "rent",
     "B23025_003E": "lf_n", "B23025_005E": "jl_n", "B23025_001E": "adult_n", "B23025_004E": "emp_n", "B02001_003E": "race_n", "B01003_001E": "pop_n"}
r = requests.get("https://api.census.gov/data/2024/acs/acs5", params={"get": ",".join(V), "for": "tract:*", "in": "state:39 county:113", "key": KEY}, timeout=120)
r.raise_for_status(); j = r.json(); acs = pd.DataFrame(j[1:], columns=j[0]).rename(columns=V)
acs["GEOID"] = acs.state + acs.county + acs.tract
for c in V.values(): acs[c] = pd.to_numeric(acs[c], errors="coerce")
for c in ("value", "rent"): acs.loc[acs[c] < 0, c] = np.nan   # Census annotation codes
s20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp")
s20 = s20[s20.GEOID.str[:5] == "39113"].to_crs(5070).merge(acs, on="GEOID")

rows = []
for yr, tr, key in (("1940", s40, "GISJOIN"), ("2020-2024", s20, "GEOID")):
    x, maj = overlay(tr, key)
    for grp in ("D", "A-C"):
        xx = x[x.grp == grp]; cnt = {c: (xx[c] * xx.w).sum() for c in ("own_n", "occ_n", "jl_n", "lf_n", "race_n", "pop_n", "emp_n", "adult_n")}
        mm = maj[maj.grp == grp]
        rows.append(dict(year=yr, group=grp, people=cnt["pop_n"], pct_black=100 * cnt["race_n"] / cnt["pop_n"],
                         own=100 * cnt["own_n"] / cnt["occ_n"], jobless=100 * cnt["jl_n"] / cnt["lf_n"], employed=100 * cnt["emp_n"] / cnt["adult_n"],
                         median_value=mm.value.median(), median_rent=mm.rent.median(), tracts=len(mm)))
o = pd.DataFrame(rows).set_index(["year", "group"]).round(1)
o.to_csv(ROOT / "analysis/spotlight/holc_then_now_dayton.csv")
print(o.to_string()); print()
for yr in ("1940", "2020-2024"):
    d, rest = o.loc[(yr, "D")], o.loc[(yr, "A-C")]
    print(yr, f"own gap {d.own - rest.own:+.1f} pts | jobless gap {d.jobless - rest.jobless:+.1f} pts | "
              f"value D/rest {d.median_value / rest.median_value:.2f} | rent D/rest {d.median_rent / rest.median_rent:.2f} | "
              f"Black share D {d.pct_black:.0f}% vs {rest.pct_black:.0f}%")

# ---- West Dayton's six tracts vs. the rest of the 1940 tracted area, same territory both years ----
sets = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id")
wd = s20[s20.GEOID.isin(sets.loc["U047"].tracts.split(";"))].dissolve()[["geometry"]]
area40 = s40.dissolve()[["geometry"]]
Z = gpd.GeoDataFrame({"zone": ["West Dayton", "rest"]}, geometry=[wd.geometry.iloc[0], area40.geometry.iloc[0].difference(wd.geometry.iloc[0])], crs=5070)
rows = []
for yr, tr, key in (("1940", s40, "GISJOIN"), ("2020-2024", s20, "GEOID")):
    tr = tr.copy(); tr["ta"] = tr.area
    x = gpd.overlay(tr, Z, how="intersection", keep_geom_type=True); x["w"] = x.area / x.ta
    cov = x.groupby([key, "zone"]).w.sum().reset_index().sort_values("w").drop_duplicates(key, keep="last")
    cov = cov[cov.w >= 0.5]
    for zn in ("West Dayton", "rest"):
        xx = x[x.zone == zn]; cnt = {c: (xx[c] * xx.w).sum() for c in ("own_n", "occ_n", "jl_n", "lf_n", "race_n", "pop_n", "emp_n", "adult_n")}
        med = tr[tr[key].isin(cov[cov.zone == zn][key])]
        rows.append(dict(year=yr, zone=zn, people=cnt["pop_n"], pct_black=100 * cnt["race_n"] / cnt["pop_n"],
                         own=100 * cnt["own_n"] / cnt["occ_n"], jobless=100 * cnt["jl_n"] / cnt["lf_n"], employed=100 * cnt["emp_n"] / cnt["adult_n"],
                         median_value=med.value.median(), median_rent=med.rent.median(), tracts=len(med)))
w = pd.DataFrame(rows).set_index(["year", "zone"]).round(1)
w.to_csv(ROOT / "analysis/spotlight/west_dayton_then_now.csv")
print("\nWest Dayton footprint vs. rest of the 1940 tracted area\n", w.to_string())
for yr in ("1940", "2020-2024"):
    d, rest = w.loc[(yr, "West Dayton")], w.loc[(yr, "rest")]
    print(yr, f"own gap {d.own - rest.own:+.1f} | employed gap {d.employed - rest.employed:+.1f} | jobless gap {d.jobless - rest.jobless:+.1f} | value ratio {d.median_value / rest.median_value:.2f} | rent ratio {d.median_rent / rest.median_rent:.2f}")

# ---- Three groups for the post: the west side D areas (D10, D11, the D areas that reach into West Dayton), the other
# D areas (each 12% nonwhite or less in 1940), and the A-C areas. Same land in both years.
WEST_D = ["D10", "D11"]
HL = gpd.GeoDataFrame.from_features([f for f in g["features"] if f["properties"]["city"] == "Dayton" and f["properties"]["state"] == "OH"], crs=4326).to_crs(5070)
HL = HL[HL.grade.isin(list("ABCD"))]
HL["zone"] = np.where(HL.label.isin(WEST_D), "West side D areas", np.where(HL.grade == "D", "Other D areas", "A, B and C areas"))
Z3 = HL.dissolve("zone").reset_index()[["zone", "geometry"]]
rows = []
for yr, tr, key in (("1940", s40, "GISJOIN"), ("2020-2024", s20, "GEOID")):
    tr = tr.copy(); tr["ta"] = tr.area
    x = gpd.overlay(tr, Z3, how="intersection", keep_geom_type=True); x["w"] = x.area / x.ta
    best = x.sort_values("w").drop_duplicates(key, keep="last")
    for zn in ("West side D areas", "Other D areas", "A, B and C areas"):
        xx = x[x.zone == zn]; cnt = {c: (xx[c] * xx.w).sum() for c in ("own_n", "occ_n", "race_n", "pop_n")}
        med = best[(best.zone == zn) & (best.w >= 0.3)]
        rows.append(dict(year=yr, zone=zn, people=cnt["pop_n"], pct_black=100 * cnt["race_n"] / cnt["pop_n"],
                         own=100 * cnt["own_n"] / cnt["occ_n"], median_value=med.value.median(), tracts=len(med),
                         value_tracts=";".join(med[key].astype(str))))
z = pd.DataFrame(rows)
base = z[z.zone == "A, B and C areas"].set_index("year").median_value
z["value_vs_ABC"] = 100 * z.median_value / z.year.map(base)
z = z.round(1); z.to_csv(ROOT / "analysis/spotlight/holc_zones_then_now.csv", index=False)
print(z.drop(columns="value_tracts").to_string(index=False))

# ---- Chart for the West Dayton post: homeownership and people, 1940 and 2020-2024, by HOLC group ----
import matplotlib.pyplot as plt
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, BLUE, SURFACE
use_house_style()
G = ["West side D areas", "Other D areas", "A, B and C areas"]
LBL = {"West side D areas": "West side D areas\n(48% Black in 1940)", "Other D areas": "Other D areas\n(4% Black in 1940)", "A, B and C areas": "A, B and C areas\n(under 1% Black)"}
zz = z.set_index(["zone", "year"])
fig, axs = plt.subplots(1, 2, figsize=(10, 5.8)); fig.subplots_adjust(left=0.07, right=0.97, top=0.74, bottom=0.2, wspace=0.28)
import numpy as np
xs = np.arange(len(G)); bw = 0.36
for ax, col, ttl, fmt in ((axs[0], "own", "Homes owned by the people living in them", lambda v: f"{v:.0f}%"),
                          (axs[1], "people", "People living there", lambda v: f"{round(v, -2):,.0f}")):
    for k, (yr, colr) in enumerate((("1940", MUTED), ("2020-2024", BLUE))):
        vals = [zz.loc[(gg, yr), col] for gg in G]
        bars = ax.bar(xs + (k - 0.5) * bw, vals, width=bw - 0.04, color=colr, label=yr)
        for xb, v in zip(xs + (k - 0.5) * bw, vals):
            ax.annotate(fmt(v), (xb, v), xytext=(0, 4), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    ax.set_xticks(xs); ax.set_xticklabels([LBL[gg] for gg in G], fontsize=9.5, color=INK)
    ax.set_yticks([]); [ax.spines[s_].set_visible(False) for s_ in ("left",)]
    ax.set_title(ttl, color=INK, fontsize=12, loc="left")
    ax.set_ylim(0, max(zz[col]) * 1.18)
axs[1].yaxis.set_visible(False)
axs[0].legend(frameon=False, loc="upper left", fontsize=10, labelcolor=INK)
titleblock(fig, "Homeownership rose far more in Dayton's other D areas than on the west side",
           "Dayton's 1937 HOLC areas, same land in both years. The west side D areas (D10 and D11 on the HOLC map) held most of the\ncity's Black residents in 1940; the other D areas were mostly white.")
credit(fig, "Sources: 1940 census tracts (NHGIS, IPUMS); Census Bureau, American Community Survey 2020-2024; HOLC map, Mapping Inequality.\nTract counts are split by the share of each tract's land in each area.")
fig.savefig(ROOT / "posts/spotlight-west-dayton/images/01c-then-now.png"); plt.close(fig)
