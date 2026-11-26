"""Health insurance in North and East Flint (U013) vs. Genesee County, Michigan and the U.S., ACS 2020-2024 5-year.
Same method as scripts/99z_insurance_elsegundo.py (nativity measures dropped); shares stored to three decimals.

C27007: Medicaid/means-tested public coverage by age (under 19, 19-64, 65+), both sexes.
B27010: no health insurance coverage by age (under 19 _017, 19-34 _033, 35-64 _050, 65+ _066), and working-age adults
  (19-64) with employer-based coverage alone (_020, _036) as a rough marker of job-based insurance.
Tract values are summed across the eight tracts; margins of error: root sum of squares, then the Census proportion formula.
Output: analysis/spotlight/insurance_northflint.csv
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
ROOT = Path(__file__).resolve().parents[1]
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U013"].tracts.split(";")
c = lambda t, ks: [f"{t}_{k:03d}" for k in ks]
M = {  # measure: (numerator cells, denominator cells)
    "medicaid_under19_pct": (c("C27007", (4, 14)), c("C27007", (3, 13))),
    "medicaid_19_64_pct": (c("C27007", (7, 17)), c("C27007", (6, 16))),
    "medicaid_65plus_pct": (c("C27007", (10, 20)), c("C27007", (9, 19))),
    "medicaid_all_pct": (c("C27007", (4, 7, 10, 14, 17, 20)), c("C27007", (1,))),
    "uninsured_under19_pct": (c("B27010", (17,)), c("B27010", (2,))),
    "uninsured_19_64_pct": (c("B27010", (33, 50)), c("B27010", (18, 34))),
    "uninsured_65plus_pct": (c("B27010", (66,)), c("B27010", (51,))),
    "uninsured_all_pct": (c("B27010", (17, 33, 50, 66)), c("B27010", (1,))),
    "employer_only_19_64_pct": (c("B27010", (20, 36)), c("B27010", (18, 34))),
}
cells = sorted({x for n, d in M.values() for x in n + d})
U = "https://api.census.gov/data/2024/acs/acs5"


def get(geo, within=None):
    out = []
    for i in range(0, len(cells), 24):
        part = cells[i:i + 24]; p = {"get": ",".join(x + s for x in part for s in "EM"), "for": geo, "key": KEY}
        if within: p["in"] = within
        r = requests.get(U, params=p, timeout=120); r.raise_for_status(); j = r.json()
        out.append(pd.DataFrame(j[1:], columns=j[0]))
    d = pd.concat(out, axis=1); d = d.loc[:, ~d.columns.duplicated()]
    for x in cells:
        for s in "EM": d[x + s] = pd.to_numeric(d[x + s]).clip(lower=0)
    return d


t = get("tract:*", "state:26 county:049"); t = t[("26049" + t.tract).isin(T20)]
areas = [("North and East Flint", t), ("Genesee County", get("county:049", "state:26")), ("Michigan", get("state:26")), ("United States", get("us:1"))]
rows = []
for name, d in areas:
    for m, (num, den) in M.items():
        n = d[[x + "E" for x in num]].sum().sum(); dd = d[[x + "E" for x in den]].sum().sum()
        mn = np.sqrt((d[[x + "M" for x in num]] ** 2).sum().sum()); md = np.sqrt((d[[x + "M" for x in den]] ** 2).sum().sum())
        p = n / dd; moe = np.sqrt(max(mn ** 2 - p ** 2 * md ** 2, mn ** 2 * 0.0 + 0)) / dd if mn ** 2 >= p ** 2 * md ** 2 else np.sqrt(mn ** 2 + p ** 2 * md ** 2) / dd
        rows.append(dict(area=name, measure=m, num=round(n), den=round(dd), pct=round(100 * p, 3), moe_pts=round(100 * moe, 2)))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/insurance_northflint.csv", index=False)
print(out.pivot(index="measure", columns="area", values="pct")[["North and East Flint", "Genesee County", "Michigan", "United States"]].to_string())
print(out[out.area == "North and East Flint"][["measure", "num", "den", "pct", "moe_pts"]].to_string(index=False))
