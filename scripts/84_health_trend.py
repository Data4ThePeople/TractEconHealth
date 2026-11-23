"""Tract health over time for a spotlight pick, from every CDC 500 Cities and PLACES release.

The earliest tract-level health estimates anywhere are CDC's 500 Cities project (first release 2016, survey
year 2014). Before that, no source estimates these measures for census tracts, so there is no tract health
series for the 1970s through 2000s. Life expectancy by tract exists only for 2010-2015 (USALEEP).

  Release (survey year): 500 Cities 2016 (2014*), 2017 (2015), 2018 (2016), 2019 (2017); PLACES 2020 (2018),
  2021 (2019), 2022 (2020), 2023 (2021), 2024 (2022), 2025 (2023). *Some 2016-release measures use 2013.
  Crude prevalence, adults. Area value = population-weighted mean over the pick's tracts (500 Cities and PLACES
  2020-2023 publish 2010 tracts; 2024-2025 publish 2020 tracts; West Dayton's six tracts did not change).
  U.S. comparison: PLACES releases, population-weighted mean over every tract in that release (computed by the
  CDC API, server side); 500 Cities releases, the release's own U.S. row (BRFSS, not tract-based).
  CDC notes that model and survey changes between releases limit trend comparisons; the U.S. line from the
  same release is shown so the gap can be read release by release.
Usage: python scripts/84_health_trend.py U047
Output: analysis/spotlight/health_trend_<id>.csv
"""
import sys, time
import pandas as pd, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT

REL = [("9z78-nsfp", "500 Cities 2016", "c"), ("vurf-k5wr", "500 Cities 2017", "c"), ("rja3-32tc", "500 Cities 2018", "c"),
       ("6vp6-wxuq", "500 Cities 2019", "c"), ("4ai3-zynv", "PLACES 2020", "p"), ("373s-ayzu", "PLACES 2021", "p"),
       ("nw2y-v4gm", "PLACES 2022", "p"), ("em5e-5hvn", "PLACES 2023", "p"), ("ai6z-tcin", "PLACES 2024", "p"),
       ("cwsq-ngmh", "PLACES 2025", "p")]
M = ["DIABETES", "OBESITY", "BPHIGH", "CHD", "COPD", "CSMOKING", "MHLTH", "PHLTH", "LPA", "SLEEP", "GHLTH", "DEPRESSION"]
cid = sys.argv[1] if len(sys.argv) > 1 else "U047"
sets = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id")
tracts = sets.loc[cid].tracts.split(";")


def get(ds, params):
    for i in range(4):
        r = requests.get(f"https://data.cdc.gov/resource/{ds}.json", params=params, timeout=300)
        if r.ok: return pd.DataFrame(r.json())
        time.sleep(5 * (i + 1))
    r.raise_for_status()


mlist = ",".join(f"'{m}'" for m in M); tlist = ",".join(f"'{t}'" for t in tracts)
rows = []
for ds, lab, kind in REL:
    geo = "tractfips" if kind == "c" else "locationname"
    popc = {"500 Cities 2016": "population2010", "500 Cities 2017": "population2010"}.get(lab, "populationcount" if kind == "c" else "totalpopulation")
    if lab == "500 Cities 2017":   # this release has no tractfips column; uniqueid is "<placefips>-<tract>"
        geo = "uniqueid"
        ids = ",".join(f"'{t}'" for t in tracts) + "," + ",".join(f"'{t}'" for t in tracts)
        where = f"datavaluetypeid='CrdPrv' AND measureid in ({mlist}) AND geographiclevel='Census Tract' AND (" + \
                " OR ".join(f"uniqueid like '%{t}'" for t in tracts) + ")"
    else:
        where = f"datavaluetypeid='CrdPrv' AND measureid in ({mlist}) AND {geo} in ({tlist})"
    d = get(ds, {"$select": f"year,measureid,{geo},data_value,{popc}", "$limit": 5000, "$where": where})
    d["v"] = pd.to_numeric(d.data_value); d["w"] = pd.to_numeric(d[popc])
    for (m, y), g in d.dropna(subset=["v"]).groupby(["measureid", "year"]):
        rows.append(dict(release=lab, year=int(y), measure=m, area=cid, value=(g.v * g.w).sum() / g.w.sum(), n_tracts=len(g)))
    if kind == "c":
        u = get(ds, {"$select": "year,measureid,data_value", "$limit": 5000,
                     "$where": f"datavaluetypeid='CrdPrv' AND measureid in ({mlist}) AND geographiclevel='US'"})
        for r in u.itertuples():
            rows.append(dict(release=lab, year=int(r.year), measure=r.measureid, area="US", value=float(r.data_value), n_tracts=None))
    else:
        u = get(ds, {"$select": f"year,measureid,sum(data_value*{popc}) as s,sum(case(data_value IS NOT NULL,{popc},true,0)) as w,count(*) as n",
                     "$group": "year,measureid", "$limit": 5000,
                     "$where": f"datavaluetypeid='CrdPrv' AND measureid in ({mlist})"})
        for r in u.itertuples():
            rows.append(dict(release=lab, year=int(r.year), measure=r.measureid, area="US", value=float(r.s) / float(r.w), n_tracts=int(r.n)))
    print(lab, len(d), "rows")
o = pd.DataFrame(rows); o["value"] = o.value.round(2)
out = ROOT / f"analysis/spotlight/health_trend_{cid}.csv"; o.to_csv(out, index=False)
print(o.pivot_table(index=["measure", "area"], columns="year", values="value").round(1).to_string())
