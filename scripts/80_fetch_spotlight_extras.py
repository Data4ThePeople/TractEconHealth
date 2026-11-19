"""Extra inputs for the spotlight posts.
  Mapping Inequality (University of Richmond) national HOLC polygons -> data/raw/holc/mappinginequality.json
  TIGER/Line 2024 roads for each pick's main county (primary and secondary roads drawn on maps) -> data/raw/tiger/roads/
  CDC NCHS Drug Poisoning Mortality by County, 2003-2021 model rates (data.cdc.gov rpvx-m2md) -> data/raw/cdc/overdose_county_model.parquet
"""
import io, sys, zipfile, requests, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW

(RAW / "holc").mkdir(exist_ok=True)
r = requests.get("https://dsl.richmond.edu/panorama/redlining/static/mappinginequality.json", timeout=600); r.raise_for_status()
(RAW / "holc" / "mappinginequality.json").write_bytes(r.content); print("holc", len(r.content) // 1_000_000, "MB")

COUNTIES = ["39113", "01073", "24510", "48141", "26049", "28027", "54047", "46102", "21189", "48387"]
(RAW / "tiger" / "roads").mkdir(parents=True, exist_ok=True)
for c in COUNTIES:
    z = requests.get(f"https://www2.census.gov/geo/tiger/TIGER2024/ROADS/tl_2024_{c}_roads.zip", timeout=300); z.raise_for_status()
    zipfile.ZipFile(io.BytesIO(z.content)).extractall(RAW / "tiger" / "roads")
print("roads", len(COUNTIES))

(RAW / "cdc").mkdir(exist_ok=True)
rows, off = [], 0
while True:
    q = requests.get("https://data.cdc.gov/resource/rpvx-m2md.json", params={"$limit": 50000, "$offset": off}, timeout=300); q.raise_for_status()
    j = q.json()
    if not j: break
    rows += j; off += len(j)
d = pd.DataFrame(rows)
d.to_parquet(RAW / "cdc" / "overdose_county_model.parquet"); print("overdose rows", len(d), list(d.columns))
