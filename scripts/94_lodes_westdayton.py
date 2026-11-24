"""Jobs held by West Dayton residents, by year, from LEHD LODES 8 residence area characteristics (RAC), Ohio, all jobs (S000, JT00).
C000 = all jobs held by residents of the block; CNS05 = manufacturing (NAICS 31-33). LODES 8 uses 2020 census blocks for every year,
so the six 2020 tracts are the same land each year. Counts are jobs, not people (a person with two jobs counts twice).
Files: https://lehd.ces.census.gov/data/lodes/LODES8/oh/rac/oh_rac_S000_JT00_<year>.csv.gz -> data/raw/lodes/oh_rac_<year>.csv.gz
Run: python scripts/94_lodes_westdayton.py [U047|U039]  (default U047; U039 West Baltimore uses the Maryland files and Baltimore city)
Output: analysis/spotlight/lodes_<area>.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/lodes"; RAW.mkdir(parents=True, exist_ok=True)
AREAS = {"U047": dict(name="West Dayton", st="oh", county="39113", cname="Montgomery County", out="westdayton"),
         "U039": dict(name="West Baltimore", st="md", county="24510", cname="Baltimore city", out="westbaltimore")}
CID = sys.argv[1] if len(sys.argv) > 1 else "U047"; A = AREAS[CID]
T = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[CID].tracts.split(";")
rows = []
for y in [2002, 2005, 2007, 2010, 2012, 2015, 2022]:
    f = RAW / f"{A['st']}_rac_{y}.csv.gz"
    if not f.exists():
        r = requests.get(f"https://lehd.ces.census.gov/data/lodes/LODES8/{A['st']}/rac/{A['st']}_rac_S000_JT00_{y}.csv.gz", timeout=300); r.raise_for_status(); f.write_bytes(r.content)
    d = pd.read_csv(f, dtype={"h_geocode": str}, usecols=["h_geocode", "C000", "CNS05"]); d["tr"] = d.h_geocode.str[:11]
    for area, m in ((A["name"], d.tr.isin(T)), (A["cname"], d.tr.str[:5] == A["county"])):
        w = d[m]; rows.append(dict(year=y, area=area, jobs=int(w.C000.sum()), mfg_jobs=int(w.CNS05.sum()), mfg_share=round(100 * w.CNS05.sum() / w.C000.sum(), 1)))
out = pd.DataFrame(rows); out.to_csv(ROOT / f"analysis/spotlight/lodes_{A['out']}.csv", index=False); print(out.to_string(index=False))
