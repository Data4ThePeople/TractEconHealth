"""North and East Flint (U013): which 2015 city wards the eight tracts sit in, and city demolition permits inside them.

Inputs (data/raw/flint/):
- flint_old_wards_2012.geojson: "City of Flint - Old Wards" (Genesee County GIS with City of Flint, boundaries of 2012,
  in effect in 2015), ArcGIS item 47808bf632e043d995516693c1697064.
- flint_demolition_permits_2015_2019.geojson: Genesee County GIS "Building Permits 2015-2019" (item
  f61da1745517400c93af76217795f35d), demolition categories, City of Flint.
Ward lead figures are typed from Hanna-Attisha et al. 2016, AJPH, Table 2 (share of water samples over 15 ppb; share of
tested children under 5 with elevated blood lead before and after the switch).
Output: analysis/spotlight/wards_demolitions_northflint.csv
"""
import sys
from pathlib import Path
import geopandas as gpd, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW

CRS = "EPSG:32617"
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U013"].tracts.split(";")
tr = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").query("GEOID in @T20").to_crs(CRS)
hood = tr.union_all()
w = gpd.read_file(RAW / "flint/flint_old_wards_2012.geojson").to_crs(CRS)
HA = {1: (10, 0.0, 2.8), 2: (25, 0.0, 1.4), 3: (18, 1.0, 4.5), 4: (6, 3.1, 1.7), 5: (32, 4.9, 15.7),
      6: (28, 2.2, 9.3), 7: (28, 5.4, 5.9), 8: (20, 2.7, 1.4), 9: (20, 3.4, 1.6)}
rows = []
for _, r in w.iterrows():
    n = int(r.Number); s = r.geometry.intersection(hood).area / hood.area
    rows.append(dict(kind="ward", key=f"Ward {n}", share_of_tract_land=round(s, 3), water_over15_pct=HA[n][0],
                     ebll_pre_pct=HA[n][1], ebll_post_pct=HA[n][2]))
w345 = w.set_index("Number")
pt = (w345.loc[3].geometry.buffer(50).intersection(w345.loc[4].geometry.buffer(50)).intersection(w345.loc[5].geometry.buffer(50))).centroid
rows.append(dict(kind="ward", key="Wards 3-4-5 meeting point inside tracts", value=float(hood.buffer(1).contains(pt))))
p = gpd.read_file(RAW / "flint/flint_demolition_permits_2015_2019.geojson").to_crs(CRS)
p["here"] = p.within(hood)
for y, g in p.groupby("Year"):
    rows.append(dict(kind="demolition_permits", key=str(y), value=int(g.here.sum()), city_total=len(g)))
rows.append(dict(kind="demolition_permits", key="2015-2019", value=int(p.here.sum()), city_total=len(p)))
rows.append(dict(kind="demolition_permits", key="2015-2019 single family", value=int((p.here & (p.Category == "Demolition Single Family")).sum()),
                 city_total=int((p.Category == "Demolition Single Family").sum())))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/wards_demolitions_northflint.csv", index=False)
print(out.to_string())
