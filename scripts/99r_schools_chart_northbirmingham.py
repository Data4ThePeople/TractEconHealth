"""North Birmingham: each regular public school inside the four tracts, 1986-87 to 2023-24, as a bar from its first to its
last school year with students reported. Reads analysis/spotlight/schools_geocoded_northbirmingham.csv (scripts/99p).
Dupuy is shown as a regular school through 1999-2000; from 2000-01 it was listed as an alternative school.
Output: posts/spotlight-north-birmingham/images/02b-schools.png
"""
import sys
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE

use_house_style()
d = pd.read_csv(ROOT / "analysis/spotlight/schools_geocoded_northbirmingham.csv", dtype={"ncessch": str})
r = d[(d.kind == "regular") & (d.enrollment > 0)]
r = r[~((r.ncessch == "010039000118") & (r.year >= 2000))]  # Dupuy turns alternative
g = r.sort_values("year").groupby("ncessch").agg(first=("year", "min"), last=("year", "max"), e0=("enrollment", "first"), e1=("enrollment", "last"))
NAMES = {"010039000109": "Calloway Elementary", "010039000110": "Carver High (old building)", "010039000118": "Dupuy Elementary",
         "010039000120": "Eagan Elementary", "010039000139": "Hudson K-8", "010039000147": "Kingston K-8", "010039000150": "Lewis Elementary",
         "010039000158": "North Birmingham Elementary", "010039000177": "Riggins Elementary", "010039000183": "Shields Elementary",
         "010039001468": "Carver High (new building)", "010020402476": "i3 Academy (charter)"}
g["name"] = g.index.map(NAMES); last_year = int(d.year.max())
g["open"] = g["last"] == last_year
g = g.sort_values(["open", "last", "first"], ascending=[True, True, True])
fig, ax = plt.subplots(figsize=(10, 7.2)); fig.subplots_adjust(left=0.27, right=0.95, top=0.8, bottom=0.12)
sy = lambda y: f"{y}-{str(y + 1)[2:]}"
for i, (k, s) in enumerate(g.iterrows()):
    col = BLUE if s.open else INK_DIM
    ax.barh(i, s["last"] + 1 - s["first"], left=s["first"], height=0.6, color=col)
    lab = f"open, {s.e1:,.0f} students" if s.open else f"last year {sy(int(s['last']))}"
    ax.annotate(lab, (s["last"] + 1, i), xytext=(5, 0), textcoords="offset points", va="center", color=INK, fontsize=9.5,
                annotation_clip=False) if not s.open else ax.annotate(lab, (s["first"], i), xytext=(-5, 0), textcoords="offset points", va="center", ha="right", color=INK, fontsize=9.5) if s["first"] > 1995 else ax.annotate(lab, (s["last"] + 1, i), xytext=(-6, 0), textcoords="offset points", va="center", ha="right", color="white", fontsize=9.5)
ax.set_yticks(range(len(g))); ax.set_yticklabels(g.name, color=INK, fontsize=10.5)
ax.set_xlim(1986, last_year + 1); xt = [1990, 2000, 2010, 2020]; ax.set_xticks(xt); ax.set_xticklabels([sy(x) for x in xt])
ax.grid(axis="x", color=GRID, linewidth=0.6); ax.tick_params(length=0); ax.set_axisbelow(True)
for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
n86 = int((g["first"] == 1986).sum()); nnow = int(g.open.sum())
titleblock(fig, f"{n86} public schools here in 1986, {nnow} today",
           "Regular public schools inside North Birmingham's four census tracts, by school year, from the first to the last\n"
           "year each reported students. Gray bars are schools that closed or changed; blue bars are open in 2023-24.")
credit(fig, "Source: NCES Common Core of Data school directory, 1986-87 to 2023-24, via the Urban Institute; addresses placed with the Census geocoder.")
fig.savefig(ROOT / "posts/spotlight-north-birmingham/images/02b-schools.png"); plt.close(fig)
print(g.to_string())
