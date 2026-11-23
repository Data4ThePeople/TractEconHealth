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
