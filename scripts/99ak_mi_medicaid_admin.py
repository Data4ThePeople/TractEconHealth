"""Michigan Medicaid administration measures for the Flint post (2026-11-27).

1. The 2023-2024 renewals ("unwinding") in Michigan: CMS Medicaid and CHIP renewal data (October 2026 release,
   data/raw/cms/renewal-dataset-october-2026-release.csv, from https://download.medicaid.gov/data/), renewals due
   June 2023 through May 2024, "Updated" rows where present, else "Original": disenrolled at renewal (total),
   disenrolled for procedural reasons, determined ineligible.
2. Timeliness: CMS Medicaid and CHIP Performance Indicator data (October 2026 release,
   data/raw/cms/pi-dataset-october-2026-release.csv): share of Medicaid and CHIP determinations processed in more than
   45 days, by month, Michigan and Ohio, January 2023 through the latest month; "Updated" rows where present.
Output: analysis/spotlight/mi_medicaid_admin.csv
"""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "data/raw/cms"


def best(d):  # prefer Updated over Original for each state and month
    d = d.assign(_o=(d["Original or Updated"] != "U").astype(int)) if "Original or Updated" in d else d.assign(_o=(d["Preliminary or Updated"] != "U").astype(int))
    return d.sort_values("_o").drop_duplicates(["State Abbreviation", "Reporting Period"])


rows = []
r = best(pd.read_csv(RAW / "renewal-dataset-october-2026-release.csv", low_memory=False))
mi = r[(r["State Abbreviation"] == "MI") & r["Reporting Period"].between(202306, 202405)]
num = lambda c: pd.to_numeric(mi[c].astype(str).str.replace(",", ""), errors="coerce").sum()
due, dis, proc, inel = (num(c) for c in ("Beneficiaries with a Renewal Due", "Beneficiaries Disenrolled at Renewal (Total)",
                                          "Beneficiaries Disenrolled for Procedural Reasons at Renewal", "Beneficiaries Determined Ineligible at Renewal"))
rows += [dict(area="Michigan", measure=m, value=v) for m, v in (("unwinding_months", len(mi)), ("renewals_due", due), ("disenrolled", dis),
         ("procedural", proc), ("ineligible", inel), ("procedural_pct_of_disenrolled", round(100 * proc / dis, 2)))]

p = best(pd.read_csv(RAW / "pi-dataset-october-2026-release.csv", low_memory=False))
cols = ["Total Medicaid and CHIP Determinations Processed in Less than 24 Hours", "Total Medicaid and CHIP Determinations Processed Between 24 Hours and 7 Days",
        "Total Medicaid and CHIP Determinations Processed Between 8 Days and 30 Days", "Total Medicaid and CHIP Determinations Processed between 31 days and 45 days",
        "Total Medicaid and CHIP Determinations Processed in More than 45 Days"]
cols = [c for c in cols if c in p.columns]
for st in ("MI", "OH"):
    d = p[(p["State Abbreviation"] == st) & (p["Reporting Period"] >= 202301)].copy()
    for c in cols: d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", ""), errors="coerce")
    d = d.dropna(subset=cols)
    d["over45_pct"] = 100 * d[cols[-1]] / d[cols].sum(axis=1)
    for _, x in d.iterrows(): rows.append(dict(area=st, measure=f"over45_pct_{x['Reporting Period']}", value=round(x.over45_pct, 2)))
    s = d.over45_pct
    rows += [dict(area=st, measure=m, value=v) for m, v in (("over45_months", len(s)), ("over45_min", round(s.min(), 2)), ("over45_median", round(s.median(), 2)),
             ("over45_p10", round(s.quantile(.1), 2)), ("over45_p90", round(s.quantile(.9), 2)), ("over45_max", round(s.max(), 2)),
             ("over45_first", d["Reporting Period"].min()), ("over45_last", d["Reporting Period"].max()))]
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/mi_medicaid_admin.csv", index=False)
print(out[~out.measure.str.match(r"over45_pct_\d")].to_string())
