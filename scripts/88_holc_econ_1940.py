"""Economic conditions by 1937 HOLC grade in Dayton, from 1940 census tracts, and whether race lines up with the grade
beyond those conditions.

Tract measures (NHGIS 1940_tPH_Major, extracts extract_1940 and extract_1940b):
  median home value (NT36), median contract rent (NT39), share of homes needing major repairs (NT43),
  share of homes without a private bath and toilet (NT44), homeownership (NT27), share of the male labor force
  jobless (on public emergency work or seeking work, NT22), male median years of school (NT16), share nonwhite (NT2).
Each tract is assigned to the HOLC grade covering most of its land (and only tracts at least 30% covered by graded
areas are used). Grade values: medians of tract medians (rent, value, school) and pooled counts for shares.
Then D tracts are split into majority-Black (50%+ nonwhite) and mostly white, to compare with C tracts.
Output: analysis/spotlight/holc_econ_dayton_1940.csv (tract level) and printed summary.
"""
import json, sys
import geopandas as gpd, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT

N = RAW / "nhgis"
def read(d):
    t = pd.read_csv(next((N / d).rglob("*_1940_tract.csv")), encoding="latin-1", low_memory=False, skiprows=[1])
    return t[(t.STATEA.astype(int) == 39) & (t.COUNTYA.astype(int) == 113)]
a, b = read("extract_1940"), read("extract_1940b")
t = a.merge(b[["GISJOIN"] + [c for c in b.columns if c[:2] in ("BU", "BV") and c not in a.columns]], on="GISJOIN")
num = [c for c in t.columns if c[:2] in ("BU", "BV")]; t[num] = t[num].apply(pd.to_numeric, errors="coerce")
t["pct_nonwhite"] = 100 * t.BUQ002 / t.BUB001
t["own"] = 100 * t.BU2001 / (t.BU2001 + t.BU2002)
t["repair"] = 100 * t.BVK002 / (t.BVK001 + t.BVK002)
t["no_bath"] = 100 * t[["BVL002", "BVL003", "BVL004", "BVL006", "BVL007", "BVL008"]].sum(axis=1) / t[[f"BVL00{i}" for i in range(1, 9)]].sum(axis=1)
lf = t[["BUX001", "BUX002", "BUX003"]].sum(axis=1)
t["jobless_m"] = 100 * (t.BUX002 + t.BUX003) / lf
t["value"] = t.BVC001.replace(0, np.nan); t["rent"] = t.BVF001.replace(0, np.nan); t["school_m"] = t.BUI001.replace(0, np.nan)

shp = gpd.read_file(next((N / "extract_1940").rglob("US_tract_1940_conflated.shp")))
tr = shp[shp.GISJOIN.isin(t.GISJOIN)].to_crs(5070); tr["ta"] = tr.area
g = json.loads((RAW / "holc" / "mappinginequality.json").read_text())
h = gpd.GeoDataFrame.from_features([f for f in g["features"] if f["properties"]["city"] == "Dayton" and f["properties"]["state"] == "OH"], crs=4326).to_crs(5070)
x = gpd.overlay(tr, h[h.grade.isin(list("ABCD"))][["grade", "geometry"]], how="intersection", keep_geom_type=True)
x["w"] = x.area / x.ta
cov = x.groupby("GISJOIN").w.sum()
maj = x.sort_values("w").drop_duplicates("GISJOIN", keep="last")[["GISJOIN", "grade", "w"]]
maj = maj[maj.GISJOIN.map(cov) >= 0.3]
d = maj.merge(t, on="GISJOIN")
d["group"] = np.where(d.grade != "D", d.grade, np.where(d.pct_nonwhite >= 50, "D, majority Black", "D, mostly white"))
d.to_csv(ROOT / "analysis/spotlight/holc_econ_dayton_1940.csv", index=False)


def summ(x):
    return pd.Series({"tracts": len(x), "pct_nonwhite": 100 * x.BUQ002.sum() / x.BUB001.sum(),
                      "median_value": x.value.median(), "median_rent": x.rent.median(),
                      "own": 100 * x.BU2001.sum() / (x.BU2001.sum() + x.BU2002.sum()),
                      "repair": 100 * x.BVK002.sum() / (x.BVK001.sum() + x.BVK002.sum()),
                      "no_bath": 100 * x[["BVL002", "BVL003", "BVL004", "BVL006", "BVL007", "BVL008"]].sum().sum() / x[[f"BVL00{i}" for i in range(1, 9)]].sum().sum(),
                      "jobless_m": 100 * (x.BUX002.sum() + x.BUX003.sum()) / x[["BUX001", "BUX002", "BUX003"]].sum().sum(),
                      "school_m": x.school_m.median()})
pd.set_option("display.width", 200)
print(d.groupby("grade").apply(summ).round(1).to_string()); print()
print(d.groupby("group").apply(summ).round(1).to_string()); print()
print(d[d.grade.isin(["C", "D"])].sort_values("rent")[["GISJOIN", "grade", "pct_nonwhite", "value", "rent", "own", "repair", "no_bath", "jobless_m"]].round(1).to_string(index=False))
