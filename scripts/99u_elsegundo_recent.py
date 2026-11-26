"""El Segundo Barrio (U028) recent-year measures for the story-first analyses, with El Paso County for comparison.

Decennial counts (100% data), for the homes-vs-household-size split:
  2010 SF1: H001001 housing units, H003002 occupied, P016001 persons in households (2010 tracts S10)
  2020 DHC: H1_001N housing units, H3_002N occupied, P15_001N persons in households (2020 tracts T20)
ACS 5-year, 2008-2012 on S10 and 2020-2024 on T20:
  B25014 occupants per room (crowded = more than 1.00), B25047 plumbing (lacking complete), B05002 nativity
  (foreign born = _013), B17025 poverty by nativity, B07003 same house 1 year ago (2020-2024 only),
  B05005 year of entry (2020-2024 only), B25038 year householder moved in (2020-2024 only)
S10: 2010 tracts with half or more of their land inside the 2020 outline (same rule as scripts/99h_industry_spotlight.py).
Output: analysis/spotlight/recent_elsegundo.csv (area, period, measure, num, den, value)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw"
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
ST, CO, NAME, CMP = "48", "141", "El Segundo Barrio", "El Paso County"
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U028"].tracts.split(";")
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
p = rel[rel.GEOID_TRACT_20.isin(T20)]; sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
S10 = list(sh.index[sh >= 0.5])


def get(path, vars_):
    r = requests.get(f"https://api.census.gov/data/{path}", params={"get": ",".join(vars_), "for": "tract:*", "in": f"state:{ST} county:{CO}", "key": KEY}, timeout=120)
    r.raise_for_status(); j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d["geoid"] = ST + CO + d.tract
    for v in vars_: d[v] = pd.to_numeric(d[v])
    return d


rows = []
def add(period, d, tracts, measure, num, den):
    for area, dd in ((NAME, d[d.geoid.isin(tracts)]), (CMP, d)):
        n, t = dd[num].sum().sum(), dd[den].sum().sum()
        row = dict(area=area, period=period, measure=measure, num=round(float(n)), den=round(float(t)),
                   value=round(100 * n / t, 3) if measure.endswith("_pct") else None)  # 3 decimals: round once, at display
        mn_c, md_c = [c[:-1] + "M" for c in num], [c[:-1] + "M" for c in den]
        if measure.endswith("_pct") and all(c in dd for c in mn_c + md_c):
            # ACS margins for summed tracts: root sum of squares, then the Census proportion formula
            # (ratio formula if the term under the root is negative)
            mn, md = np.sqrt((dd[mn_c] ** 2).sum().sum()), np.sqrt((dd[md_c] ** 2).sum().sum()); pr = n / t
            q = mn ** 2 - pr ** 2 * md ** 2
            row["moe_pts"] = round(100 * np.sqrt(q if q >= 0 else mn ** 2 + pr ** 2 * md ** 2) / t, 2)
        rows.append(row)

for period, path, tr, (hu, occ, hhp) in (("2010", "2010/dec/sf1", S10, ("H001001", "H003002", "P016001")),
                                          ("2020", "2020/dec/dhc", T20, ("H1_001N", "H3_002N", "P15_001N"))):
    d = get(path, [hu, occ, hhp])
    for area, dd in ((NAME, d[d.geoid.isin(tr)]), (CMP, d)):
        rows += [dict(area=area, period=period, measure=m, num=int(dd[v].sum())) for m, v in (("housing_units", hu), ("occupied_units", occ), ("household_pop", hhp))]

crowd = [f"B25014_{k:03d}E" for k in (5, 6, 7, 11, 12, 13)]
for period, year, tr in (("2008-2012", 2012, S10), ("2020-2024", 2024, T20)):
    v = crowd + ["B25014_001E", "B25047_001E", "B25047_003E", "B05002_001E", "B05002_013E", "B17025_001E", "B17025_002E",
                 "B17025_004E", "B17025_006E", "B17025_011E", "B17025_013E", "B25001_001E", "B25002_002E", "B25008_001E"]
    d = get(f"{year}/acs/acs5", v + [c[:-1] + "M" for c in v])
    add(period, d, tr, "crowded_pct", crowd, ["B25014_001E"])
    add(period, d, tr, "lacking_plumbing_pct", ["B25047_003E"], ["B25047_001E"])
    add(period, d, tr, "foreign_born_pct", ["B05002_013E"], ["B05002_001E"])
    add(period, d, tr, "poverty_pct", ["B17025_002E"], ["B17025_001E"])
    add(period, d, tr, "poverty_us_born_pct", ["B17025_004E"], ["B17025_004E", "B17025_011E"])
    add(period, d, tr, "poverty_foreign_born_pct", ["B17025_006E"], ["B17025_006E", "B17025_013E"])
    for m, c in (("housing_units", "B25001_001E"), ("occupied_units", "B25002_002E"), ("household_pop", "B25008_001E")):
        add(period, d, tr, m, [c], [c])
d = get("2024/acs/acs5", ["B07003_001E", "B07003_004E", "B07003_016E", "B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E",
                          "B25038_001E", "B25038_008E", "B25038_015E", "B25038_007E", "B25038_014E"])
add("2020-2024", d, T20, "same_house_1yr_pct", ["B07003_004E"], ["B07003_001E"])
add("2020-2024", d, T20, "moved_from_abroad_1yr_pct", ["B07003_016E"], ["B07003_001E"])
add("2020-2024", d, T20, "foreign_born_entered_2010_on_pct", ["B05005_004E"], ["B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E"])
add("2020-2024", d, T20, "foreign_born_entered_before_1990_pct", ["B05005_019E"], ["B05005_004E", "B05005_009E", "B05005_014E", "B05005_019E"])
add("2020-2024", d, T20, "householder_moved_in_before_2000_pct", ["B25038_008E", "B25038_015E", "B25038_007E", "B25038_014E"], ["B25038_001E"])
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/recent_elsegundo.csv", index=False)
print("S10:", S10); print(out.to_string(index=False))
