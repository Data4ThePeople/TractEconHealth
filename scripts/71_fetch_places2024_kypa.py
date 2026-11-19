"""CDC PLACES 2024 release, census tract data (data.cdc.gov ai6z-tcin), Kentucky and Pennsylvania only.
PLACES 2025 has no health estimates for these two states; the spotlight screen uses 2024 for them.
Output: data/raw/places/places_tract_2024_kypa.parquet
"""
import io, requests, pandas as pd
from common import RAW
URL = "https://data.cdc.gov/resource/ai6z-tcin.csv"
COLS = "year,stateabbr,countyfips,countyname,locationname,measureid,data_value_type,data_value,totalpopulation"
parts = []
for st in ["KY", "PA"]:
    off = 0
    while True:
        r = requests.get(URL, params={"$select": COLS, "$where": f"stateabbr='{st}'", "$order": "locationname,measureid",
                                      "$limit": 50000, "$offset": off}, timeout=300)
        r.raise_for_status(); d = pd.read_csv(io.StringIO(r.text), dtype={"locationname": str, "countyfips": str})
        parts.append(d); off += len(d)
        if len(d) < 50000: break
a = pd.concat(parts)
if a.duplicated(["locationname", "measureid", "data_value_type"]).any(): raise ValueError("duplicate rows")
a.to_parquet(RAW / "places" / "places_tract_2024_kypa.parquet")
print(len(a), "rows;", a.locationname.nunique(), "tracts;", sorted(a.year.unique()), a.measureid.nunique(), "measures")
