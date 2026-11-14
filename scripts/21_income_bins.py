"""Health measures by median household income, 20 equal-count groups -> analysis/income_binned.csv."""
import os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import PROC, ROOT

d = pd.read_parquet(PROC / "tracts.parquet")
d = d[d.med_hh_income.notna()]
q = pd.qcut(d.med_hh_income, 20, labels=False)
rows = []
for m in ["health_index", "obesity", "diabetes", "smoking", "mental_distress", "depression", "high_bp", "fair_poor_health"]:
    g = d.groupby(q)[m]
    t = pd.DataFrame({"group": range(20), "income_median": d.groupby(q).med_hh_income.median(), "n": g.size(),
                      "p10": g.quantile(.1), "p25": g.quantile(.25), "median": g.median(), "p75": g.quantile(.75),
                      "p90": g.quantile(.9)})
    t["measure"] = m
    rows.append(t)
out = pd.concat(rows)
out.to_csv(ROOT / "analysis" / "income_binned.csv", index=False)
print(out[out.group.isin([0, 4, 9, 14, 19])].round(1).to_string(index=False))
