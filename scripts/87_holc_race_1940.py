"""Who lived in each 1937 HOLC grade in Dayton: 1940 census tracts overlaid on the HOLC map.

1940 tract counts (NHGIS 1940_tPH_Major, scripts/86_fetch_nhgis_1940.py): total population (NT1), white and
nonwhite population (NT2), and occupied homes by tenure by race (NT28: white, Negro, other nonwhite).
Each tract's counts are split across the HOLC areas it touches by share of the tract's land area (equal-area
projection, EPSG 5070), assuming people are spread evenly within a tract. Areas of a tract outside any graded area
are left out. Output: analysis/spotlight/holc_race_dayton_1940.csv and printed summary.
"""
import json, sys
import geopandas as gpd, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT

E = RAW / "nhgis" / "extract_1940"
t = pd.read_csv(next(E.rglob("*_1940_tract.csv")), encoding="latin-1", low_memory=False, skiprows=[1])  # row 2 holds labels
t = t[(t.STATEA.astype(int) == 39) & (t.COUNTYA.astype(int) == 113)]
shp = gpd.read_file(next(E.rglob("US_tract_1940_conflated.shp")))
shp = shp[shp.GISJOIN.isin(t.GISJOIN)].to_crs(5070)
tr = shp.merge(t, on="GISJOIN")
tr["tract_area"] = tr.area
g = json.loads((RAW / "holc" / "mappinginequality.json").read_text())
holc = gpd.GeoDataFrame.from_features([f for f in g["features"] if f["properties"]["city"] == "Dayton" and f["properties"]["state"] == "OH"],
                                      crs=4326).to_crs(5070)
holc = holc[holc.grade.isin(list("ABCD"))][["grade", "label", "geometry"]]
x = gpd.overlay(tr, holc, how="intersection", keep_geom_type=True)
x["w"] = x.area / x.tract_area
cols = {"pop": "BUB001", "white": "BUQ001", "nonwhite": "BUQ002",
        "hh_black": ["BU3002", "BU3005"], "hh_all": ["BU2001", "BU2002"], "own_black": "BU3002", "own_white": "BU3001",
        "hh_white": ["BU3001", "BU3004"]}
for k, c in cols.items():
    x[k] = (x[c].sum(axis=1) if isinstance(c, list) else x[c]) * x.w
s = x.groupby("grade")[list(cols)].sum()
s["pct_nonwhite"] = 100 * s.nonwhite / s["pop"]
s["pct_black_households"] = 100 * s.hh_black / s.hh_all
s["share_of_city_graded_nonwhite"] = 100 * s.nonwhite / s.nonwhite.sum()
s["share_of_city_graded_pop"] = 100 * s["pop"] / s["pop"].sum()
s["own_rate_white"] = 100 * s.own_white / s.hh_white
s = s.round(1)
out = ROOT / "analysis/spotlight/holc_race_dayton_1940.csv"; s.to_csv(out)
print(f"1940 Dayton-area tracts: {len(tr)}; county 1940 population {t.BUB001.sum():,}, nonwhite {t.BUQ002.sum():,}")
print(f"graded area holds {s['pop'].sum():,.0f} people, {s.nonwhite.sum():,.0f} nonwhite")
print(s[["pop", "nonwhite", "pct_nonwhite", "pct_black_households", "share_of_city_graded_nonwhite", "share_of_city_graded_pop"]].to_string())
# robustness: assign each tract wholly to the grade covering most of it
maj = x.sort_values("w").drop_duplicates("GISJOIN", keep="last")
mm = maj.groupby("grade")[["BUB001", "BUQ002"]].sum(); mm["pct_nonwhite"] = (100 * mm.BUQ002 / mm.BUB001).round(1)
print("majority-grade check:\n", mm.to_string())
