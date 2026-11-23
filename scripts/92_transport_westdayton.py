"""Getting to food in West Dayton: households with no vehicle (ACS) and adults lacking reliable transportation (CDC PLACES).

ACS 2020-2024 5-year B25044 (tenure by vehicles available): no vehicle = owner (003) + renter (010) over total (001),
summed across the six tracts; Montgomery County and U.S. for comparison.
CDC PLACES 2025 release (data.cdc.gov cwsq-ngmh), 2023 survey year: LACKTRPT (lack of reliable transportation in the past
12 months) and FOODINSECU (food insecurity in the past 12 months), crude prevalence for adults, averaged across the six
tracts weighted by tract population; comparison is all PLACES tracts with the measure (40 states), weighted by tract population.
Output: analysis/spotlight/transport_westdayton.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
ROOT = Path(__file__).resolve().parents[1]
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
T = ["165100", "003800", "003900", "004100", "000200", "070300"]
V = ["B25044_001E", "B25044_003E", "B25044_010E"]
U = "https://api.census.gov/data/2024/acs/acs5"


def acs(geo, within=None):
    p = {"get": ",".join(V), "for": geo, "key": KEY}
    if within: p["in"] = within
    r = requests.get(U, params=p, timeout=120); r.raise_for_status()
    d = pd.DataFrame(r.json()[1:], columns=r.json()[0]); d[V] = d[V].astype(int); return d


rows = []
t = acs("tract:*", "state:39 county:113"); t = t[t.tract.isin(T)]
for name, d in (("West Dayton", t), ("Montgomery County", acs("county:113", "state:39")), ("United States", acs("us:1"))):
    nv, tot = (d.B25044_003E + d.B25044_010E).sum(), d.B25044_001E.sum()
    rows.append(dict(area=name, measure="households_no_vehicle_pct", value=round(100 * nv / tot, 1), n=int(nv), total=int(tot)))

q = requests.get("https://data.cdc.gov/resource/cwsq-ngmh.json",
                 params={"$where": "countyfips='39113' and measureid in('LACKTRPT','FOODINSECU')", "$limit": 5000}, timeout=120).json()
p = pd.DataFrame(q); p = p[p.locationname.str[-6:].isin(T)]
p["v"] = p.data_value.astype(float); p["pop"] = p.totalpopulation.astype(float)
for m, g in p.groupby("measureid"):
    rows.append(dict(area="West Dayton", measure=m, value=round((g.v * g["pop"]).sum() / g["pop"].sum(), 1), n=len(g), total=None, year=g.year.iloc[0]))
    for r in g.itertuples(): rows.append(dict(area="tract " + r.locationname[-6:], measure=m, value=r.v, year=r.year))
for m in ("LACKTRPT", "FOODINSECU"):  # tracts in the 40 states PLACES covers for these measures, weighted by tract population
    a = requests.get("https://data.cdc.gov/resource/cwsq-ngmh.json", params={"$select": "sum(data_value*totalpopulation) as s, sum(totalpopulation) as p, count(*) as n",
                     "$where": f"measureid='{m}' and data_value_type='Crude prevalence'"}, timeout=120).json()[0]
    rows.append(dict(area="PLACES tracts (40 states)", measure=m, value=round(float(a["s"]) / float(a["p"]), 1), n=int(a["n"]), year="2023"))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/transport_westdayton.csv", index=False)
print(out.to_string(index=False))
