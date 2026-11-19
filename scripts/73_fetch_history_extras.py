"""Extra history inputs for spotlight finalists.
  NHGIS 2000-2010 tract crosswalk (population weights)      -> data/raw/nhgis/nhgis_tr2000_tr2010.csv
  ACS 2008-2012 5-year tract counts (Census API, 2010 tracts) -> data/raw/acs/acs2012_tract_history.parquet
     poverty (B17001_001, _002), labor force (B23025_003 civilian LF, _005 unemployed), total and Black alone
     population (B02001_001, _003), housing occupancy (B25002_001-003), tenure (B25003_001-002)
  ACS 2020-2024 5-year tract counts, same variables (2020 tracts) -> data/raw/acs/acs2024_tract_history.parquet
"""
import io, sys, zipfile, requests, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
from common import RAW, STATES
env = read_env_file(Path.home() / ".claude/d4tp-process/.env")
r = requests.get("https://api.ipums.org/supplemental-data/nhgis/crosswalks/nhgis_tr2000_tr2010.zip",
                 headers={"Authorization": env["IPUMS_API_KEY"]}, timeout=600)
r.raise_for_status()
with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    name = [n for n in z.namelist() if n.endswith(".csv")][0]
    (RAW / "nhgis" / "nhgis_tr2000_tr2010.csv").write_bytes(z.read(name))
print("crosswalk 2000-2010 saved")
V = ["B17001_001E", "B17001_002E", "B23025_003E", "B23025_005E", "B02001_001E", "B02001_003E",
     "B25002_001E", "B25002_002E", "B25002_003E", "B25003_001E", "B25003_002E"]
for yr, out in [(2012, "acs2012_tract_history.parquet"), (2024, "acs2024_tract_history.parquet")]:
    parts = []
    for st in STATES:
        q = requests.get(f"https://api.census.gov/data/{yr}/acs/acs5", timeout=300, params={
            "get": ",".join(V), "for": "tract:*", "in": f"state:{st}", "key": env["CENSUS_API_KEY"]})
        q.raise_for_status(); j = q.json()
        parts.append(pd.DataFrame(j[1:], columns=j[0]))
    d = pd.concat(parts)
    d.index = d.state + d.county + d.tract
    d = d[V].apply(pd.to_numeric, errors="coerce")
    d[d < 0] = pd.NA
    d.to_parquet(RAW / "acs" / out)
    print(yr, len(d), "tracts")
