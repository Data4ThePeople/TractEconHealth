"""Public schools located inside North Birmingham's four tracts, by school year, from the NCES Common Core of Data school
directory as served by the Urban Institute Education Data Portal (https://educationdata.urban.org, schools/ccd/directory).
A school counts if its latitude/longitude falls inside the four 2020 tracts or within half a mile of them.
Coordinates are missing or rough in early years; each row lists the school so it can be checked by hand.
Output: analysis/spotlight/schools_northbirmingham.csv
"""
import sys, time
from pathlib import Path
import geopandas as gpd, pandas as pd, requests
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT
T = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U034"].tracts.split(";")
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]); W = g20[g20.GEOID.isin(T)].to_crs(5070).unary_union
rows = []
for y in (1990, 1995, 2000, 2005, 2010, 2015, 2020, 2022):
    u = f"https://educationdata.urban.org/api/v1/schools/ccd/directory/{y}/?fips=1&county_code=1073"
    res = []
    while u:
        j = requests.get(u, timeout=120).json(); res += j.get("results", []); u = j.get("next"); time.sleep(0.5)
    d = pd.DataFrame(res)
    if d.empty or "latitude" not in d: print(y, "no data"); continue
    d = d.dropna(subset=["latitude", "longitude"]); d = d[(d.latitude != 0)]
    g = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.longitude, d.latitude), crs=4326).to_crs(5070); g["mi"] = g.distance(W) / 1609.34
    near = g[g.mi <= 0.5]
    for _, r in near.iterrows():
        rows.append(dict(year=y, school=r.school_name, address=r.get("street_location"), status=r.get("school_status"), enrollment=r.get("enrollment"), mi=round(r.mi, 2)))
    print(y, "inside:", int((near.mi == 0).sum()), "within 0.5 mi:", len(near), "| county total:", len(g))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/schools_northbirmingham.csv", index=False)
print(out.pivot_table(index="school", columns="year", values="enrollment", aggfunc="first").to_string())
