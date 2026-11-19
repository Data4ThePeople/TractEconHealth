"""Then-and-now tables for SPOTLIGHTS.md, from analysis/spotlight/history_final.csv (scripts/74_history.py run on
final_sets.csv). Years whose old-tract fit is under 0.8 are left out. Writes analysis/spotlight/tables.md."""
import sys
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT

OUT = ROOT / "analysis" / "spotlight"
h = pd.read_csv(OUT / "history_final.csv", dtype={"year": str})
h = h[h.fit.isna() | (h.fit >= 0.8)].drop_duplicates(["cand_id", "measure", "year"])
YEARS = ["1970", "1980", "1990", "2000", "2010", "2020-2024"]
MEAS = [("population", "People", "{:,.0f}"), ("pct_black", "Black (%)", "{:.0f}"), ("poverty_rate", "In poverty (%)", "{:.0f}"),
        ("unemployment_rate", "Unemployed (%)", "{:.0f}"), ("vacancy_rate", "Homes vacant (%)", "{:.0f}"),
        ("owner_share", "Owner-occupied (%)", "{:.0f}")]
out = []
for cid, g in h.groupby("cand_id"):
    v = {(r.measure, r.year): r.value for r in g.itertuples()}
    ys = [y for y in YEARS if any((m, y) in v for m, _, _ in MEAS)]
    t = [f"### {cid}", "", "| Measure | " + " | ".join(ys) + " |", "|---|" + "---:|" * len(ys)]
    for m, lab, fmt in MEAS:
        t.append(f"| {lab} | " + " | ".join(fmt.format(v[(m, y)]) if (m, y) in v else "" for y in ys) + " |")
    le = g[g.measure == "life_expectancy"]
    if len(le):
        t += ["", f"Life expectancy, 2010-2015 (USALEEP): {le.value.iloc[0]:.1f} years (U.S. 78.7)."]
    out += t + [""]
(OUT / "tables.md").write_text("\n".join(out))
print("tables for", h.cand_id.nunique())
