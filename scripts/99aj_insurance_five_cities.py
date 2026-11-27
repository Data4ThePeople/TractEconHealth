"""Medicaid and no insurance, ages 19 to 64, in the five city neighborhoods and their states (2026-11-27).

For the Flint post's comparison of Medicaid expansion and non-expansion states. Same tables, cells and method as
scripts/99ac_insurance_northflint.py: ACS 2020-2024 5-year C27007 (Medicaid or other means-tested coverage, 19-64:
cells 007 + 017 over 006 + 016) and B27010 (no coverage, 19-64: 033 + 050 over 018 + 034), tract values summed;
margins of error by root sum of squares and the Census proportion formula.
Neighborhoods (final_sets.csv): West Dayton U047 (Ohio), West Baltimore U039 (Maryland), North Birmingham U034
(Alabama), El Segundo Barrio U028 (Texas), North and East Flint U013 (Michigan).
Expansion status (KFF, Status of State Medicaid Expansion Decisions): Ohio, Maryland and Michigan expanded in 2014;
Alabama and Texas have not expanded.
Output: analysis/spotlight/insurance_five_cities.csv
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd, requests
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file
ROOT = Path(__file__).resolve().parents[1]
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
S = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id")
HOODS = [("West Dayton", "U047", "Ohio", True), ("West Baltimore", "U039", "Maryland", True),
         ("North and East Flint", "U013", "Michigan", True), ("North Birmingham", "U034", "Alabama", False),
         ("El Segundo Barrio", "U028", "Texas", False)]
M = {"medicaid_19_64_pct": (["C27007_007", "C27007_017"], ["C27007_006", "C27007_016"]),
     "uninsured_19_64_pct": (["B27010_033", "B27010_050"], ["B27010_018", "B27010_034"])}
cells = sorted({x for n, d in M.values() for x in n + d})


def get(geo, within=None):
    p = {"get": ",".join(x + s for x in cells for s in "EM"), "for": geo, "key": KEY}
    if within: p["in"] = within
    r = requests.get("https://api.census.gov/data/2024/acs/acs5", params=p, timeout=120); r.raise_for_status(); j = r.json()
    d = pd.DataFrame(j[1:], columns=j[0])
    for x in cells:
        for s in "EM": d[x + s] = pd.to_numeric(d[x + s]).clip(lower=0)
    return d


def rate(d, num, den):
    n = d[[x + "E" for x in num]].sum().sum(); dd = d[[x + "E" for x in den]].sum().sum()
    mn = np.sqrt((d[[x + "M" for x in num]] ** 2).sum().sum()); md = np.sqrt((d[[x + "M" for x in den]] ** 2).sum().sum())
    p = n / dd; inner = mn ** 2 - p ** 2 * md ** 2
    moe = np.sqrt(inner if inner >= 0 else mn ** 2 + p ** 2 * md ** 2) / dd
    return round(n), round(dd), round(100 * p, 3), round(100 * moe, 2)


rows = []
for name, cid, state, exp in HOODS:
    T = S.loc[cid].tracts.split(";"); st = T[0][:2]
    counties = sorted({t[2:5] for t in T})
    t = pd.concat([get("tract:*", f"state:{st} county:{c}") for c in counties])
    t = t[(t.state + t.county + t.tract).isin(T)]
    assert len(t) == len(T), (name, len(t), len(T))
    sd = get(f"state:{st}")
    for area, d, kind in ((name, t, "neighborhood"), (state, sd, "state")):
        for m, (num, den) in M.items():
            n, dd, p, moe = rate(d, num, den)
            rows.append(dict(area=area, kind=kind, state=state, expansion=exp, measure=m, num=n, den=dd, pct=p, moe_pts=moe))
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/insurance_five_cities.csv", index=False)
print(out.pivot_table(index=["area", "expansion"], columns="measure", values="pct").round(1).to_string())
print(out[out.kind == "neighborhood"][["area", "measure", "pct", "moe_pts"]].to_string(index=False))

# chart: 07b-expansion.png
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE, YELLOW
use_house_style()
V = out[out.kind == "neighborhood"].set_index(["area", "measure"]).pct
labs = {"West Dayton": "West Dayton,\nOhio", "West Baltimore": "West Baltimore,\nMaryland", "North and East Flint": "North and East\nFlint, Michigan",
        "North Birmingham": "North Birmingham,\nAlabama", "El Segundo Barrio": "El Segundo Barrio,\nTexas"}
fig, ax = plt.subplots(figsize=(10, 6.2)); fig.subplots_adjust(left=0.08, right=0.97, top=0.72, bottom=0.17)
w = 0.36; xs = [0, 1, 2, 3.5, 4.5]
for j, (m, col, lab) in enumerate((("medicaid_19_64_pct", BLUE, "Medicaid"), ("uninsured_19_64_pct", YELLOW, "No health insurance"))):
    for x, (name, *_r) in zip(xs, HOODS):
        v = V[(name, m)]; xx = x + (j - 0.5) * w * 1.08
        ax.bar(xx, v, width=w, color=col, label=lab if name == "West Dayton" else None)
        ax.annotate(f"{v:.0f}%", (xx, v), xytext=(0, 5), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_xticks(xs); ax.set_xticklabels([labs[h[0]] for h in HOODS], color=INK, fontsize=9.5); ax.set_ylim(0, 82)
ax.axvline(2.75, color=INK_DIM, lw=0.8, ls="--")
ax.annotate("States that expanded Medicaid", (1, 76), ha="center", color=INK_DIM, fontsize=10.5)
ax.annotate("States that did not", (4, 76), ha="center", color=INK_DIM, fontsize=10.5)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
ax.legend(loc="upper left", bbox_to_anchor=(0, 0.93), frameon=False, labelcolor=INK, fontsize=10)
titleblock(fig, "A smaller share of adults was uninsured in the neighborhoods in expansion states",
           "Share of people ages 19 to 64 with Medicaid or other public coverage based on income, and with no\n"
           "health insurance, in the five neighborhoods in this series, 2020-2024. Margins of error run from about 2 to 8 points.")
credit(fig, "Source: Census Bureau, American Community Survey 2020-2024, tables C27007 and B27010; expansion status from KFF.")
fig.savefig(ROOT / "posts/spotlight-north-flint/images/07b-expansion.png"); plt.close(fig)
