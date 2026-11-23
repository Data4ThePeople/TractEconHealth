"""Jobs held by West Dayton residents, by year, from LEHD LODES 8 residence area characteristics (RAC), Ohio, all jobs (S000, JT00).
C000 = all jobs held by residents of the block; CNS05 = manufacturing (NAICS 31-33). LODES 8 uses 2020 census blocks for every year,
so the six 2020 tracts are the same land each year. Counts are jobs, not people (a person with two jobs counts twice).
Files: https://lehd.ces.census.gov/data/lodes/LODES8/oh/rac/oh_rac_S000_JT00_<year>.csv.gz -> data/raw/lodes/oh_rac_<year>.csv.gz
Output: analysis/spotlight/lodes_westdayton.csv
"""
from pathlib import Path
import pandas as pd, requests
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/lodes"; RAW.mkdir(parents=True, exist_ok=True)
T = ["39113165100", "39113003800", "39113003900", "39113004100", "39113000200", "39113070300"]
rows = []
for y in [2002, 2005, 2007, 2010, 2012, 2015, 2022]:
    f = RAW / f"oh_rac_{y}.csv.gz"
    if not f.exists():
        r = requests.get(f"https://lehd.ces.census.gov/data/lodes/LODES8/oh/rac/oh_rac_S000_JT00_{y}.csv.gz", timeout=300); r.raise_for_status(); f.write_bytes(r.content)
    d = pd.read_csv(f, dtype={"h_geocode": str}, usecols=["h_geocode", "C000", "CNS05"]); d["tr"] = d.h_geocode.str[:11]
    for area, m in (("West Dayton", d.tr.isin(T)), ("Montgomery County", d.tr.str[:5] == "39113")):
        w = d[m]; rows.append(dict(year=y, area=area, jobs=int(w.C000.sum()), mfg_jobs=int(w.CNS05.sum()), mfg_share=round(100 * w.CNS05.sum() / w.C000.sum(), 1)))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/lodes_westdayton.csv", index=False); print(out.to_string(index=False))
