"""Food access in North Birmingham's four tracts: SNAP stores today, full grocery stores over time, USDA food access flags.

Live stores: USDA SNAP retailer locator live feed (FNS ArcGIS FeatureServer), box around the area, pulled at run time.
History: USDA SNAP retailer historical file 2005-2025. Full grocery store = USDA type Supermarket, Super Store or Large
Grocery Store. A store counts as open in a year if authorized on or before July 1 of that year and not ended before it.
Counted inside the four tracts and within 1 mile of them. Food Access Research Atlas 2019 (2010 tracts) flags.
Output: analysis/spotlight/food_northbirmingham.csv (store history), printed summaries.
"""
import json, sys, zipfile
import geopandas as gpd, numpy as np, pandas as pd, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT
T = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U034"].tracts.split(";")
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"])
W = g20[g20.GEOID.isin(T)].to_crs(5070).unary_union
BOX = (-86.90, 33.50, -86.70, 33.65)
live_f = RAW / "snap" / "snap_live_northbirmingham.json"
if not live_f.exists():
    u = "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0/query"
    r = requests.get(u, params={"where": "1=1", "geometry": ",".join(map(str, BOX)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "outSR": 4326, "f": "json", "resultRecordCount": 2000}, timeout=120)
    r.raise_for_status(); live_f.write_text(r.text)
L = pd.DataFrame([f["attributes"] for f in json.loads(live_f.read_text())["features"]])
L = gpd.GeoDataFrame(L, geometry=gpd.points_from_xy(L.Longitude, L.Latitude), crs=4326).to_crs(5070)
L["mi"] = L.distance(W) / 1609.34
print("Live SNAP stores inside the four tracts, by USDA type:"); print(L[L.mi == 0].Store_Type.value_counts().to_string())
full = L[L.Store_Type.isin(["Super Store", "Supermarket"])].sort_values("mi")
print("\nNearest full grocery stores (live):"); print(full[["Store_Name", "Store_Street_Address", "City", "Store_Type", "mi"]].head(6).round(2).to_string(index=False))

z = zipfile.ZipFile(RAW / "snap" / "snap-retailer-locator-data2005-2025.zip")
H = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
H = H[(H.State == "AL") & H.County.str.upper().str.contains("JEFFERSON", na=False) & H["Store Type"].isin(["Supermarket", "Super Store", "Large Grocery Store"])].copy()
H["start"] = pd.to_datetime(H["Authorization Date"], errors="coerce", format="mixed"); H["end"] = pd.to_datetime(H["End Date"], errors="coerce", format="mixed")
H = gpd.GeoDataFrame(H, geometry=gpd.points_from_xy(H.Longitude, H.Latitude), crs=4326).to_crs(5070); H["mi"] = H.distance(W) / 1609.34
rows = []
for y in range(2005, 2026):
    d = pd.Timestamp(f"{y}-07-01"); o = H[(H.start <= d) & (H.end.isna() | (H.end >= d))]
    rows.append(dict(year=y, inside=int((o.mi == 0).sum()), within_1mi=int((o.mi <= 1).sum())))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/food_northbirmingham.csv", index=False); print("\nFull grocery stores open (July 1):"); print(out.to_string(index=False))
print("\nFull grocery store records within 1 mile:"); print(H[H.mi <= 1][["Store Name", "Street Number", "Street Name", "Store Type", "start", "end", "mi"]].sort_values("start").round(2).to_string(index=False))
F = pd.read_csv(RAW / "usda_fara" / "Food Access Research Atlas.csv", dtype={"CensusTract": str}, low_memory=False)
F["CensusTract"] = F.CensusTract.str.zfill(11)
print("\nFARA 2019:"); print(F[F.CensusTract.isin(T)][["CensusTract", "LILATracts_halfAnd10", "LILATracts_1And10", "LowIncomeTracts", "LA1and10", "LAhalfand10", "lapophalfshare", "lapop1share"]].to_string(index=False))
