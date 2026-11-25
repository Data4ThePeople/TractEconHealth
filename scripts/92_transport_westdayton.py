"""Getting to food in West Dayton: households with no vehicle (ACS) and adults lacking reliable transportation (CDC PLACES).

ACS 2020-2024 5-year B25044 (tenure by vehicles available): no vehicle = owner (003) + renter (010) over total (001),
summed across the six tracts; Montgomery County and U.S. for comparison.
CDC PLACES 2025 release (data.cdc.gov cwsq-ngmh), 2023 survey year: LACKTRPT (lack of reliable transportation in the past
12 months) and FOODINSECU (food insecurity in the past 12 months), crude prevalence for adults, averaged across the six
tracts weighted by tract population; comparison is all PLACES tracts with the measure (40 states), weighted by tract population.
Run: python scripts/92_transport_westdayton.py [U047|U039]  (default U047, West Dayton; U039 is West Baltimore)
Output: analysis/spotlight/transport_<area>.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
ROOT = Path(__file__).resolve().parents[1]
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
AREAS = {"U047": dict(name="West Dayton", st="39", co="113", county="Montgomery County", out="westdayton"),
         "U039": dict(name="West Baltimore", st="24", co="510", county="Baltimore city", out="westbaltimore"),
         "U034": dict(name="North Birmingham", st="01", co="073", county="Jefferson County", out="northbirmingham")}
A = AREAS[sys.argv[1] if len(sys.argv) > 1 else "U047"]
T = [t[5:] for t in pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[[k for k, v in AREAS.items() if v is A][0]].tracts.split(";")]
V = ["B25044_001E", "B25044_003E", "B25044_010E"]
U = "https://api.census.gov/data/2024/acs/acs5"


def acs(geo, within=None):
    p = {"get": ",".join(V), "for": geo, "key": KEY}
    if within: p["in"] = within
    r = requests.get(U, params=p, timeout=120); r.raise_for_status()
    d = pd.DataFrame(r.json()[1:], columns=r.json()[0]); d[V] = d[V].astype(int); return d


rows = []
t = acs("tract:*", f"state:{A['st']} county:{A['co']}"); t = t[t.tract.isin(T)]
for name, d in ((A["name"], t), (A["county"], acs(f"county:{A['co']}", f"state:{A['st']}")), ("United States", acs("us:1"))):
    nv, tot = (d.B25044_003E + d.B25044_010E).sum(), d.B25044_001E.sum()
    rows.append(dict(area=name, measure="households_no_vehicle_pct", value=round(100 * nv / tot, 1), n=int(nv), total=int(tot)))

q = requests.get("https://data.cdc.gov/resource/cwsq-ngmh.json",
                 params={"$where": f"countyfips='{A['st']}{A['co']}' and measureid in('LACKTRPT','FOODINSECU')", "$limit": 5000}, timeout=120).json()
p = pd.DataFrame(q); p = p[p.locationname.str[-6:].isin(T)]
p["v"] = p.data_value.astype(float); p["pop"] = p.totalpopulation.astype(float)
for m, g in p.groupby("measureid"):
    rows.append(dict(area=A["name"], measure=m, value=round((g.v * g["pop"]).sum() / g["pop"].sum(), 1), n=len(g), total=None, year=g.year.iloc[0]))
    for r in g.itertuples(): rows.append(dict(area="tract " + r.locationname[-6:], measure=m, value=r.v, year=r.year))
for m in ("LACKTRPT", "FOODINSECU"):  # tracts in the 40 states PLACES covers for these measures, weighted by tract population
    a = requests.get("https://data.cdc.gov/resource/cwsq-ngmh.json", params={"$select": "sum(data_value*totalpopulation) as s, sum(totalpopulation) as p, count(*) as n",
                     "$where": f"measureid='{m}' and data_value_type='Crude prevalence'"}, timeout=120).json()[0]
    rows.append(dict(area="PLACES tracts (40 states)", measure=m, value=round(float(a["s"]) / float(a["p"]), 1), n=int(a["n"]), year="2023"))
out = pd.DataFrame(rows); out.to_csv(ROOT / f"analysis/spotlight/transport_{A['out']}.csv", index=False)
print(out.to_string(index=False))
