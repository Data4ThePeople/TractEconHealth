"""Getting around in North Birmingham: households with no vehicle, how workers get to work, and how long it takes.
ACS 5-year: B25044 (no vehicle = 003 + 010 over 001), B08303 (travel time to work, workers 16+ who do not work at home;
45+ minutes = 011-013), B08013 (aggregate travel time) / B08303_001 = average minutes, B08301 (means: 010 public transit,
019 walked, 021 worked at home, 003 drove alone, 004 carpooled). 2008-2012 on the 2010 tracts, 2020-2024 on the 2020 tracts.
CDC PLACES measures come from scripts/92_transport_westdayton.py U034.
Output: analysis/spotlight/commute_northbirmingham.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process")); sys.path.insert(0, str(Path(__file__).parent))
from d4tp_env import read_env_file
from common import RAW, ROOT
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U034"].tracts.split(";")
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig", usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
p = rel[rel.GEOID_TRACT_20.isin(T20)]; sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
S10 = list(sh.index[sh >= 0.5])
V = ["B25044_001E", "B25044_003E", "B25044_010E", "B08303_001E", "B08303_011E", "B08303_012E", "B08303_013E", "B08013_001E",
     "B08301_001E", "B08301_003E", "B08301_004E", "B08301_010E", "B08301_019E", "B08301_021E"]
def get(year, geo, within=None):
    prm = {"get": ",".join(V), "for": geo, "key": KEY}
    if within: prm["in"] = within
    r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params=prm, timeout=120); r.raise_for_status()
    d = pd.DataFrame(r.json()[1:], columns=r.json()[0]); d[V] = d[V].apply(pd.to_numeric); return d
rows = []
for year, tracts, lab in ((2012, S10, "2008-2012"), (2024, T20, "2020-2024")):
    tr = get(year, "tract:*", "state:01 county:073"); tr["geoid"] = "01073" + tr.tract
    for area, s in (("North Birmingham", tr[tr.geoid.isin(tracts)][V].sum()), ("Jefferson County", tr[V].sum()), ("United States", get(year, "us:1")[V].sum())):
        rows.append(dict(year=lab, area=area,
                         no_vehicle=round(100 * (s.B25044_003E + s.B25044_010E) / s.B25044_001E, 1),
                         avg_commute_min=round(s.B08013_001E / s.B08303_001E, 1),
                         commute_45plus=round(100 * (s.B08303_011E + s.B08303_012E + s.B08303_013E) / s.B08303_001E, 1),
                         drove_alone=round(100 * s.B08301_003E / s.B08301_001E, 1), carpool=round(100 * s.B08301_004E / s.B08301_001E, 1),
                         transit=round(100 * s.B08301_010E / s.B08301_001E, 1), walked=round(100 * s.B08301_019E / s.B08301_001E, 1),
                         workers=int(s.B08301_001E)))
out = pd.DataFrame(rows)
out.to_csv(ROOT / "analysis/spotlight/commute_northbirmingham.csv", index=False); print(out.to_string(index=False))
