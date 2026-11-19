"""Tie-out for the 10 spotlight picks. Recomputes each figure by a second path and reports differences.

1. Key measures (ACS): poverty, unemployment and vacancy from key_measures.csv (fresh Census API pull) vs. the
   separate ACS 2020-2024 history pull (data/raw/acs/acs2024_tract_history.parquet).
2. Median household income: the interpolated neighborhood median must fall inside the range of its tracts'
   own published medians (tracts.parquet).
3. PLACES health: key_measures.csv vs. an adult-weighted average rebuilt from the screen's tract file
   (tracts.parquet, weighted by total population; Kentucky skipped, not in that file). Differences come from
   the weights only and should be small.
4. Life expectancy: key_measures.csv vs. USALEEP US_A.CSV read directly, mapped 2020 -> 2010 tracts.
5. Narrative numbers in SPOTLIGHTS.md (population change since 1970/1980/1990) vs. tables.md.
Writes analysis/spotlight/tieout_spotlight.csv and prints failures.
"""
import re, sys
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT, PROC

OUT = ROOT / "analysis" / "spotlight"
PICKS = ["U047", "U034", "U039", "U028", "U013", "M016", "R007", "R046", "R004", "M014"]
sets = pd.read_csv(OUT / "final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[PICKS]
km = pd.read_csv(OUT / "key_measures.csv").set_index(["cand_id", "measure"]).value
a24 = pd.read_parquet(RAW / "acs" / "acs2024_tract_history.parquet")
tr = pd.read_parquet(PROC / "tracts.parquet")
rows = []
def chk(cid, item, ours, other, tol):
    ok = abs(ours - other) <= tol if pd.notna(ours) and pd.notna(other) else False
    rows.append(dict(cand_id=cid, item=item, ours=round(ours, 2), check=round(other, 2), tol=tol, ok=ok))

for cid, r in sets.iterrows():
    t = r.tracts.split(";")
    s = a24.reindex(t).sum(min_count=1)
    chk(cid, "Poverty rate (%)", km[(cid, "Poverty rate (%)")], 100 * s.B17001_002E / s.B17001_001E, 0.05)
    chk(cid, "Unemployment rate (%)", km[(cid, "Unemployment rate (%)")], 100 * s.B23025_005E / s.B23025_003E, 0.05)
    chk(cid, "Homes vacant (%)", km[(cid, "Homes vacant (%)")], 100 * s.B25002_003E / s.B25002_001E, 0.05)
    x = tr.reindex(t).med_hh_income.dropna()
    if len(x):
        inside = x.min() - 1 <= km[(cid, "Median household income")] <= x.max() + 1
        rows.append(dict(cand_id=cid, item="Median income inside tract range", ours=round(km[(cid, "Median household income")]),
                         check=f"{x.min():,.0f}-{x.max():,.0f}", tol="", ok=inside))
    for col, lab in [("fair_poor_health", "Fair or poor health (%)"), ("diabetes", "Diabetes (%)"),
                     ("high_bp", "High blood pressure (%)"), ("mental_distress", "Frequent mental distress (%)")]:
        d = tr.reindex(t)[[col, "pop"]].dropna()
        if len(d):
            chk(cid, lab, km[(cid, lab)], float((d[col] * d["pop"]).sum() / d["pop"].sum()), 1.0)

# life expectancy straight from USALEEP
le = pd.read_csv(RAW / "usaleep" / "US_A.CSV", dtype={"Tract ID": str})
le = pd.Series(le["e(0)"].to_numpy(float), index=le["Tract ID"].str.zfill(11))
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
std = pd.read_csv(RAW / "nhgis" / "extract" / "nhgis0010_csv" / "nhgis0010_ts_geog2010_tract.csv", encoding="latin-1", usecols=["GISJOIN", "CL8AA2010"])
std.index = std.GISJOIN.str[1:3] + std.GISJOIN.str[4:7] + std.GISJOIN.str[8:14]
for cid, r in sets.iterrows():
    p = rel[rel.GEOID_TRACT_20.isin(r.tracts.split(";"))]
    sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
    s10 = sh.index[sh >= 0.5]; l = le.reindex(s10); w = std.CL8AA2010.reindex(s10); ok = l.notna() & w.notna()
    if ok.any() and w[ok].sum() / w.sum() >= 0.8 and cid != "R007":  # R007 uses the county figure by choice
        chk(cid, "Life expectancy (USALEEP direct)", km[(cid, "Life expectancy (years)")], float(np.average(l[ok], weights=w[ok])), 0.05)

# narrative population changes in SPOTLIGHTS.md
T = (OUT / "tables.md").read_text()
def pop(cid, yr):
    blk = re.search(rf"### {cid}\n\n(.*?)(?=\n### |\Z)", T, re.S).group(1)
    hdr = [c.strip() for c in blk.splitlines()[0].strip("|").split("|")]
    vals = [c.strip() for c in [l for l in blk.splitlines() if l.startswith("| People")][0].strip("|").split("|")]
    return float(vals[hdr.index(yr)].replace(",", ""))
CLAIMS = [("U047", "1970", 74), ("U034", "1980", 67), ("U039", "1970", 59), ("U028", "1970", 58), ("U013", "1990", 50)]
for cid, y, pct in CLAIMS:
    chk(cid, f"Population drop since {y} (%)", pct, 100 * (1 - pop(cid, "2020-2024") / pop(cid, y)), 0.5)

o = pd.DataFrame(rows)
o.to_csv(OUT / "tieout_spotlight.csv", index=False)
print(f"{o.ok.sum()} of {len(o)} checks pass")
print(o[~o.ok].to_string(index=False) if (~o.ok).any() else "no failures")
