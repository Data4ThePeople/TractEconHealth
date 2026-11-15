"""CDC PLACES 2025 release, county data (data.cdc.gov swc5-untb) -> data/raw/places/places_county_2025.parquet."""
import io
from pathlib import Path
import pandas as pd, requests
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "places"
URL = "https://data.cdc.gov/resource/swc5-untb.csv"
COLS = ("year,stateabbr,locationid,locationname,measureid,measure,data_value_type,data_value,"
        "low_confidence_limit,high_confidence_limit,totalpopulation,totalpop18plus")
r = requests.get(URL, params={"$select": COLS, "$limit": 1_000_000, "$order": "locationid,measureid,data_value_type"}, timeout=300)
r.raise_for_status()
d = pd.read_csv(io.StringIO(r.text), dtype={"locationid": str})
d = d[d.stateabbr != "US"]
if d.duplicated(["locationid", "measureid", "data_value_type"]).any(): raise ValueError("duplicate county-measure rows")
d.to_parquet(OUT / "places_county_2025.parquet", index=False)
print(len(d), "rows;", d.locationid.nunique(), "counties;", d.measureid.nunique(), "measures")
