"""Key measures table for each spotlight post: 5 economic and 5 health measures, neighborhood vs. U.S.

Neighborhood = the pick's tract set in analysis/spotlight/final_sets.csv.

Economic (ACS 2020-2024 5-year, Census API; counts summed over the tracts, then the rate computed):
  Median household income   B19001 household income bins, median by linear interpolation within the bin
                            (the Census Bureau's method for derived medians); U.S. = B19013 for the nation
  Poverty rate              B17001_002 / B17001_001
  Unemployment rate         B23025_005 / B23025_003 (civilian labor force)
  Households on SNAP        B22003_002 / B22003_001
  Homes vacant              B25002_003 / B25002_001
Health:
  Life expectancy           USALEEP 2010-2015, tracts weighted by 2010 population (from history_final.csv);
                            U.S. 78.7. Where USALEEP covers under 80% of the 2010 population (Pine Ridge: 21%), the row uses County Health
                            Rankings 2021-2023 for Oglala Lakota County, with the U.S. value from the same source.
                            McDowell (R007) also uses the county figure: its tract estimate (76.7, 2010-2015) is far
                            above County Health Rankings (65.5) and IHME 2014 (men 67.0, women 73.8).
  Fair or poor health, diabetes, high blood pressure, frequent mental distress
                            CDC PLACES 2025 tract crude prevalence (adults), weighted by adult population;
                            Kentucky uses PLACES 2024 weighted by total population (2025 left Kentucky out).
                            U.S. = the same weighted average over all PLACES 2025 tracts (Kentucky and
                            Pennsylvania are not in that release).
Output: analysis/spotlight/key_measures.csv
"""
import sys
import numpy as np, pandas as pd, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
from common import RAW, ROOT

KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
OUT = ROOT / "analysis" / "spotlight"
PICKS = ["U047", "U034", "U039", "U028", "U013", "M016", "R007", "R046", "R004", "M014"]
sets = pd.read_csv(OUT / "final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[PICKS]

BINS = [f"B19001_{i:03d}E" for i in range(2, 18)]
EDGES = [0, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000, 60000, 75000, 100000, 125000, 150000, 200000, None]
V = ["B19001_001E"] + BINS + ["B17001_001E", "B17001_002E", "B23025_003E", "B23025_005E", "B22003_001E", "B22003_002E",
     "B25002_001E", "B25002_003E"]

def get(geo_for, geo_in=None, extra=()):
    p = {"get": ",".join(list(V) + list(extra)), "for": geo_for, "key": KEY}
    if geo_in: p["in"] = geo_in
    r = requests.get("https://api.census.gov/data/2024/acs/acs5", params=p, timeout=120); r.raise_for_status()
    j = r.json(); d = pd.DataFrame(j[1:], columns=j[0])
    cols = [c for c in d.columns if c.endswith("E")]
    d[cols] = d[cols].apply(pd.to_numeric, errors="coerce")
    return d

def interp_median(counts):
    n = counts.sum(); half = n / 2; cum = 0
    for i, c in enumerate(counts):
        if cum + c >= half:
            lo, hi = EDGES[i], EDGES[i + 1]
            if hi is None: return float(lo)  # median in the open top bin: report the bin floor
            return lo + (half - cum) / c * (hi - lo)
        cum += c
    return np.nan

def econ(t):
    return {"Median household income": interp_median(t[BINS].to_numpy(float)),
            "Poverty rate (%)": 100 * t.B17001_002E / t.B17001_001E,
            "Unemployment rate (%)": 100 * t.B23025_005E / t.B23025_003E,
            "Households on SNAP (%)": 100 * t.B22003_002E / t.B22003_001E,
            "Homes vacant (%)": 100 * t.B25002_003E / t.B25002_001E}

# ---- economic ----
counties = sorted({(g[:2], g[2:5]) for tr in sets.tracts for g in tr.split(";")})
acs = pd.concat([get("tract:*", f"state:{s} county:{c}") for s, c in counties])
acs.index = acs.state + acs.county + acs.tract
us = get("us:1", extra=["B19013_001E"]).iloc[0]
us_econ = econ(us); us_econ["Median household income"] = us.B19013_001E
rows = []
for cid, r in sets.iterrows():
    tr = r.tracts.split(";")
    t = acs.reindex(tr)[V].sum(min_count=1)
    for m, v in econ(t).items():
        rows.append(dict(cand_id=cid, side="economic", measure=m, value=v, us_value=us_econ[m],
                         source="ACS 2020-2024 5-year"))

# ---- health ----
HM = {"GHLTH": "Fair or poor health (%)", "DIABETES": "Diabetes (%)", "BPHIGH": "High blood pressure (%)",
      "MHLTH": "Frequent mental distress (%)"}
p25 = pd.read_parquet(RAW / "places" / "places_tract_2025.parquet", columns=["locationname", "measureid", "data_value", "totalpop18plus"])
p25 = p25[p25.measureid.isin(HM)]
p25["w"] = pd.to_numeric(p25.totalpop18plus, errors="coerce"); p25["v"] = pd.to_numeric(p25.data_value, errors="coerce")
p24 = pd.read_parquet(RAW / "places" / "places_tract_2024_kypa.parquet")
p24 = p24[p24.measureid.isin(HM) & (p24.data_value_type == "Crude prevalence")].copy()
p24["w"] = pd.to_numeric(p24.totalpopulation, errors="coerce"); p24["v"] = pd.to_numeric(p24.data_value, errors="coerce")
def wavg(d): d = d.dropna(subset=["v", "w"]); return float((d.v * d.w).sum() / d.w.sum())
us_h = {HM[m]: wavg(g) for m, g in p25.groupby("measureid")}
h = pd.read_csv(OUT / "history_final.csv", dtype={"year": str})
le = h[(h.measure == "life_expectancy") & (h.fit >= 0.8)].set_index("cand_id").value  # tract estimate must cover 80% of 2010 population
chr_ = pd.read_csv(RAW / "chr" / "analytic_supplement_20260325.csv", dtype={"fipscode": str}, low_memory=False).set_index("fipscode")
chr_le = pd.to_numeric(chr_["v147_rawvalue"], errors="coerce")
# Picks whose table row uses the county figure instead of the tract estimate
COUNTY_LE = {"R046": ("46102", "Oglala Lakota County (no tract estimate)"),
             "R007": ("54047", "McDowell County (tract estimate 76.7 conflicts with county figures)")}
for cid, r in sets.iterrows():
    tr = r.tracts.split(";")
    if cid in le.index and cid not in COUNTY_LE:
        rows.append(dict(cand_id=cid, side="health", measure="Life expectancy (years)", value=le[cid], us_value=78.7,
                         source="USALEEP 2010-2015 tract estimates"))
    else:  # county figure (Pine Ridge: no tract estimate; McDowell: Eric's call, Nov. 19, 2026)
        f, why = COUNTY_LE[cid]
        rows.append(dict(cand_id=cid, side="health", measure="Life expectancy (years)", value=chr_le[f],
                         us_value=chr_le["00000"], source=f"County Health Rankings 2021-2023, {why}"))
    src = p24 if tr[0].startswith("21") else p25
    for m, lab in HM.items():
        d = src[(src.measureid == m) & src.locationname.isin(tr)]
        rows.append(dict(cand_id=cid, side="health", measure=lab, value=wavg(d), us_value=us_h[lab],
                         source="CDC PLACES 2024 (Kentucky)" if src is p24 else "CDC PLACES 2025"))
k = pd.DataFrame(rows)
k.to_csv(OUT / "key_measures.csv", index=False)
pd.set_option("display.width", 200)
print(k.pivot_table(index="measure", columns="cand_id", values="value").round(1)[PICKS].to_string())
print(k.drop_duplicates("measure").set_index("measure").us_value.round(1).to_string())
