"""Who holds the jobs located inside a spotlight's tracts: LEHD LODES 8 origin-destination (OD main, in-state, all jobs JT00).
For jobs whose workplace block is in the tracts: how many are held by people who live in the tracts.
SI01 = goods-producing industries (NAICS 11, 21, 23, 31-33), the closest OD split to manufacturing.
Main file counts workers who live and work in the same state; out-of-state commuters are in the aux file and are not
needed here (the question is how many local residents hold the local jobs).
Run: python scripts/99g_lodes_od_spotlight.py U034   Output: analysis/spotlight/lodes_od_<out>.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/lodes"
AREAS = {"U034": dict(name="North Birmingham", st="al", out="northbirmingham")}
CID = sys.argv[1] if len(sys.argv) > 1 else "U034"; A = AREAS[CID]
T = set(pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[CID].tracts.split(";"))
rows = []
for y in [2002, 2008, 2015, 2022]:
    f = RAW / f"{A['st']}_od_main_{y}.csv.gz"
    if not f.exists():
        r = requests.get(f"https://lehd.ces.census.gov/data/lodes/LODES8/{A['st']}/od/{A['st']}_od_main_JT00_{y}.csv.gz", timeout=600); r.raise_for_status(); f.write_bytes(r.content)
    d = pd.read_csv(f, dtype={"w_geocode": str, "h_geocode": str}, usecols=["w_geocode", "h_geocode", "S000", "SI01"])
    w = d[d.w_geocode.str[:11].isin(T)]; loc = w.h_geocode.str[:11].isin(T)
    rows.append(dict(year=y, jobs_in_tracts=int(w.S000.sum()), held_by_residents=int(w[loc].S000.sum()),
                     goods_jobs_in_tracts=int(w.SI01.sum()), goods_held_by_residents=int(w[loc].SI01.sum())))
out = pd.DataFrame(rows)
out["pct_held_by_residents"] = (100 * out.held_by_residents / out.jobs_in_tracts).round(1)
out["pct_goods_held_by_residents"] = (100 * out.goods_held_by_residents / out.goods_jobs_in_tracts).round(1)
out.to_csv(ROOT / f"analysis/spotlight/lodes_od_{A['out']}.csv", index=False); print(out.to_string(index=False))
