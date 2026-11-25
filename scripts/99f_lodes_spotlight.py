"""Jobs held by a spotlight's residents (RAC) and jobs located inside its tracts (WAC), LEHD LODES 8, all jobs (S000, JT00).
C000 = all jobs; CNS05 = manufacturing (NAICS 31-33; coke ovens are NAICS 324199 and iron pipe foundries 331, both manufacturing).
LODES 8 uses 2020 census blocks for every year, so the tracts are the same land each year. Counts are jobs, not people.
RAC counts jobs by where the worker lives; WAC counts jobs by where the workplace is.
Files: https://lehd.ces.census.gov/data/lodes/LODES8/<st>/{rac,wac}/<st>_{rac,wac}_S000_JT00_<year>.csv.gz -> data/raw/lodes/
Run: python scripts/99f_lodes_spotlight.py U034
Output: analysis/spotlight/lodes_jobs_<out>.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/lodes"; RAW.mkdir(parents=True, exist_ok=True)
AREAS = {"U034": dict(name="North Birmingham", st="al", county="01073", cname="Jefferson County", out="northbirmingham")}
CID = sys.argv[1] if len(sys.argv) > 1 else "U034"; A = AREAS[CID]
T = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[CID].tracts.split(";")
rows = []
for kind, geo in (("rac", "h_geocode"), ("wac", "w_geocode")):
    for y in [2002, 2005, 2008, 2010, 2012, 2015, 2019, 2022]:
        f = RAW / f"{A['st']}_{kind}_{y}.csv.gz"
        if not f.exists():
            r = requests.get(f"https://lehd.ces.census.gov/data/lodes/LODES8/{A['st']}/{kind}/{A['st']}_{kind}_S000_JT00_{y}.csv.gz", timeout=300)
            if r.status_code == 404: continue
            r.raise_for_status(); f.write_bytes(r.content)
        d = pd.read_csv(f, dtype={geo: str}, usecols=[geo, "C000", "CNS05"]); d["tr"] = d[geo].str[:11]
        for area, m in ((A["name"], d.tr.isin(T)), (A["cname"], d.tr.str[:5] == A["county"])):
            w = d[m]; rows.append(dict(kind=kind, year=y, area=area, jobs=int(w.C000.sum()), mfg_jobs=int(w.CNS05.sum()), mfg_share=round(100 * w.CNS05.sum() / w.C000.sum(), 1)))
out = pd.DataFrame(rows); out.to_csv(ROOT / f"analysis/spotlight/lodes_jobs_{A['out']}.csv", index=False); print(out.to_string(index=False))
