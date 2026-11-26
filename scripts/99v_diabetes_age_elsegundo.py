"""Is El Segundo Barrio's diabetes rate an older population? Indirect age standardization.

CDC PLACES gives only crude (not age-adjusted) prevalence for tracts. So we ask: if adults here had Texas's diabetes rate
for their age group, what share would have diabetes? Expected = sum over age groups of (share of adults in group) x
(Texas BRFSS 2023 rate for that group). Compare with the PLACES 2025 release (2023) crude estimate, weighted by adult
population. Same calculation for El Paso County as a check on the method.
BRFSS suppresses Texas ages 18-24 in 2023; that group gets the 25-34 rate (2.9%), which can only raise the expected value.
Inputs: ACS 2020-2024 B01001 (adults by age), CDC BRFSS prevalence data (data.cdc.gov dttw-5yxu: Texas, 2023, "Ever told
you have diabetes", response Yes, break out by age group), CDC PLACES 2025 (data/raw/places/places_tract_2025.parquet, DIABETES crude prevalence, weighted by
PLACES adult population as in chart 04).
Output: analysis/spotlight/diabetes_age_elsegundo.csv
"""
import sys
from pathlib import Path
import pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
ROOT = Path(__file__).resolve().parents[1]
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U028"].tracts.split(";")
# B01001 rows by age group (male 3-25, female 27-49); adult groups matching BRFSS breaks
G = {"18-24": (7, 8, 9, 10), "25-34": (11, 12), "35-44": (13, 14), "45-54": (15, 16), "55-64": (17, 18, 19), "65+": (20, 21, 22, 23, 24, 25)}
cols = {g: [f"B01001_{k:03d}E" for k in ks] + [f"B01001_{k + 24:03d}E" for k in ks] for g, ks in G.items()}
allc = sorted({c for v in cols.values() for c in v})
r = requests.get("https://api.census.gov/data/2024/acs/acs5", params={"get": ",".join(allc), "for": "tract:*", "in": "state:48 county:141", "key": KEY}, timeout=120)
j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d["geoid"] = "48141" + d.tract; d[allc] = d[allc].apply(pd.to_numeric)

b = requests.get("https://data.cdc.gov/resource/dttw-5yxu.json", params={"$where": "locationabbr='TX' and year='2023' and break_out_category='Age Group' and response='Yes' and question like '%diabetes%'", "$limit": 50}, timeout=120).json()
tx = {x["break_out"]: float(x["data_value"]) for x in b if x.get("data_value")}
tx.setdefault("18-24", tx["25-34"])  # 18-24 is suppressed (11 yes answers); use the 25-34 rate, which can only raise the expected value
print("Texas BRFSS 2023 diabetes, by age:", tx, "| question:", b[0]["question"])

pl = pd.read_parquet(ROOT / "data/raw/places/places_tract_2025.parquet", columns=["locationname", "measureid", "data_value", "totalpop18plus"])
pl = pl[(pl.measureid == "DIABETES") & (pl.locationname.str[:5] == "48141")].copy()
pl["geoid"] = pl.locationname; pl["v"] = pd.to_numeric(pl.data_value); pl["w"] = pd.to_numeric(pl.totalpop18plus)  # same weights as chart 04

rows = []
for area, dd in (("El Segundo Barrio", d[d.geoid.isin(T20)]), ("El Paso County", d)):
    n = {g: dd[c].sum().sum() for g, c in cols.items()}; tot = sum(n.values())
    exp = sum(n[g] / tot * tx[g] for g in G)
    p = pl[pl.geoid.isin(dd.geoid)]
    obs = (p.v * p.w).sum() / p.w.sum()
    rows.append(dict(area=area, adults=int(tot), share_65plus=round(100 * n["65+"] / tot, 1), share_55plus=round(100 * (n["55-64"] + n["65+"]) / tot, 1),
                     expected_at_texas_rates=round(exp, 1), places_observed=round(obs, 1), ratio=round(obs / exp, 2)))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/diabetes_age_elsegundo.csv", index=False); print(out.to_string(index=False))
