"""Source coverage check -> analysis/coverage.json.

For each source: how much of what we use is a direct measurement, how much the publisher filled in or modeled,
how that changes between the two ACS periods, and how large the publisher's own uncertainty is.
Run on the 77,918 tracts in the analysis (data/processed/tracts.parquet) unless noted."""
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import RAW, PROC, ROOT
import importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(os.path.dirname(__file__), "10_build.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

T = pd.read_parquet(PROC / "tracts.parquet")
IDX = T.index
Q = pd.qcut(T.med_hh_income, 5, labels=["lowest fifth", "second", "middle", "fourth", "highest fifth"])
out = {"tracts": int(len(T))}


def pct(x):
    return round(float(x) * 100, 1)


def dist(s):
    s = s.dropna()
    return {"median": round(float(s.median()), 1), "p90": round(float(s.quantile(.9)), 1)}


def by_q(s):
    return {str(k): round(float(v), 1) for k, v in s.groupby(Q, observed=True).median().items()}


# ---------- ACS: answers the Census Bureau allocated (filled in) ----------
acs = {}
d, _ = b.table("B99192"); d = d.reindex(IDX)
tot, none_ = d.B99192_001E, d.B99192_002E
share_any = (tot - none_) / tot * 100
acs["household_income"] = {
    "what": "households with some or all of their income filled in by the Census Bureau",
    "national_pct": pct((tot - none_).sum() / tot.sum()),
    "all_income_filled_pct": pct(d.B99192_008E.sum() / tot.sum()),
    "tract": dist(share_any), "median_by_income_fifth": by_q(share_any)}
for t, name, what in [("B99231", "employment_status", "people 16+ whose employment status was filled in"),
                      ("B99221", "snap", "households whose SNAP receipt was filled in"),
                      ("B992701", "health_insurance", "people with one or more insurance answers filled in"),
                      ("B992518", "gross_rent", "renter units whose gross rent was filled in")]:
    d, _ = b.table(t); d = d.reindex(IDX)
    s = d[f"{t}_002E"] / d[f"{t}_001E"] * 100
    acs[name] = {"what": what, "national_pct": pct(d[f"{t}_002E"].sum() / d[f"{t}_001E"].sum()),
                 "tract": dist(s), "median_by_income_fifth": by_q(s)}
# history: employment status allocation, 2015-2019 vs 2020-2024 (all tracts in 50 states + DC, each period)
e = {}
for y in (2019, 2024):
    d, _ = b.table("B99231", y)
    d = d[d.index.str[:2].isin(__import__("common").STATES)]
    e[str(y)] = pct(d.B99231_002E.sum() / d.B99231_001E.sum())
acs["employment_status"]["national_pct_2015_2019"] = e["2019"]
acs["employment_status"]["national_pct_2020_2024_all_tracts"] = e["2024"]
out["acs_allocation"] = acs

# ---------- ACS: sampling error (90% margins of error) ----------
def prop_moe(num, mnum, den, mden):
    """Census Bureau formula for a proportion's MOE, falling back to the ratio formula when the root is negative."""
    p = num / den
    inner = mnum ** 2 - p ** 2 * mden ** 2
    alt = mnum ** 2 + p ** 2 * mden ** 2
    return np.sqrt(np.where(inner < 0, alt, inner)) / den * 100


def summ(m, est=None):
    m = pd.Series(m, index=IDX).replace([np.inf, -np.inf], np.nan)
    r = {"median_moe": round(float(m.median()), 1), "p90_moe": round(float(m.quantile(.9)), 1)}
    if est is not None:
        r["share_moe_over_half_estimate_pct"] = pct(((m > est / 2) & est.notna()).sum() / est.notna().sum())
    return r


moe = {}
d, _ = b.table("B19013"); d = d.reindex(IDX)
# negative MOEs are Census annotation codes (for example top-coded or too few cases), not margins: drop them
inc_moe = d.B19013_001M.where(d.B19013_001M >= 0)
rel = inc_moe / d.B19013_001E * 100
cv = inc_moe / 1.645 / d.B19013_001E * 100
moe["median_household_income"] = {"unit": "MOE as % of the estimate", **summ(rel),
                                  "median_by_income_fifth": by_q(rel),
                                  "tracts_with_moe": int(rel.notna().sum()),
                                  "cv_over_30_pct": pct((cv > 30).sum() / cv.notna().sum())}
d, lab = b.table("C17002"); d = d.reindex(IDX)
v = b.pick(lab, lambda p: p[-1] == "2.00 and over", 1)[0]
m = prop_moe(d[v], d[v[:-1] + "M"], d.C17002_001E, d.C17002_001M)
moe["pct_above_200fpl"] = {"unit": "percentage points", **summ(m), "median_by_income_fifth": by_q(pd.Series(m, index=IDX))}
d, _ = b.table("B22003"); d = d.reindex(IDX)
m = prop_moe(d.B22003_002E, d.B22003_002M, d.B22003_001E, d.B22003_001M)
moe["pct_snap"] = {"unit": "percentage points", **summ(m, T.pct_snap)}
d, _ = b.table("B23025"); d = d.reindex(IDX)
m = prop_moe(d.B23025_005E, d.B23025_005M, d.B23025_003E, d.B23025_003M)
moe["unemp_rate"] = {"unit": "percentage points", **summ(m, T.unemp_rate)}
d, lab = b.table("B27010"); d = d.reindex(IDX)
uv = b.pick(lab, lambda p: p[-1] == "No health insurance coverage", 4)
num, mnum = d[uv].sum(axis=1), np.sqrt((d[[x[:-1] + "M" for x in uv]] ** 2).sum(axis=1))
m = prop_moe(num, mnum, d.B27010_001E, d.B27010_001M)
moe["pct_uninsured"] = {"unit": "percentage points (multi-line numerator, MOEs combined as root sum of squares)",
                        **summ(m, T.pct_uninsured)}
out["acs_moe"] = moe

# ---------- PLACES: every tract value is a model estimate ----------
p = pd.read_parquet(RAW / "places" / "places_tract_2025.parquet")
p = p[p.data_value_type.str.startswith("Crude") & p.measureid.isin(b.PLACES_KEEP)].copy()
p["geoid"] = p.locationname.astype(str).str.zfill(11)
p = p[p.geoid.isin(IDX)]
p["ci_width"] = p.high_confidence_limit - p.low_confidence_limit
p["rel_width"] = p.ci_width / p.data_value * 100
pl = {"direct_measurement_pct": 0.0,
      "note": "PLACES publishes no direct tract measurements; every value is predicted by CDC's small-area model.",
      "measures": {}}
for mid, g in p.groupby("measureid"):
    name = b.PLACES_KEEP[mid]
    pl["measures"][name] = {"core": name in b.HEALTH_CORE, "tracts": int(g.geoid.nunique()),
                            "median_value": round(float(g.data_value.median()), 1),
                            "median_ci_width_pts": round(float(g.ci_width.median()), 1),
                            "p90_ci_width_pts": round(float(g.ci_width.quantile(.9)), 1),
                            "median_ci_width_pct_of_value": round(float(g.rel_width.median()), 1)}
out["places"] = pl

# ---------- County Health Rankings: counted deaths, blanked where under 10 ----------
c = pd.read_parquet(PROC / "counties.parquet")
chr_ = {"counties": int(len(c))}
for m in ["overdose_rate", "suicide_rate", "life_expectancy"]:
    miss = c[m].isna()
    chr_[m] = {"blank": int(miss.sum()), "blank_pct": pct(miss.mean()),
               "pop_in_blank_counties_pct": pct(c.loc[miss, "pop"].sum() / c["pop"].sum()),
               "median_pop_blank": int(c.loc[miss, "pop"].median()) if miss.any() else None,
               "median_pop_with_value": int(c.loc[~miss, "pop"].median())}
out["chr"] = chr_

(ROOT / "analysis" / "coverage.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
