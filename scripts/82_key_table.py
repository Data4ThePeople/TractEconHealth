"""Key measures panel for a spotlight post, drawn as a PNG in the house chart style.
Usage: python scripts/82_key_table.py U047 [more ids]   (or "all")
Left: 5 economic measures. Right: 5 health measures. Each row: the measure, the neighborhood value
(large), the U.S. value (dim), and a thin bar pair so the gap reads at a glance.
Output: posts/<slug>/images/00-key-measures.png
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, GRID, BLUE, SURFACE

import importlib.util
spec = importlib.util.spec_from_file_location("ch", Path(__file__).parent / "81_spotlight_charts.py")
CFG = None
src = (Path(__file__).parent / "81_spotlight_charts.py").read_text()
CFG = eval(src[src.index("CFG = {") + 6: src.index("\n}\n") + 2])  # reuse names and slugs without running the charts

LABEL = {"Median household income": "Median household income", "Poverty rate (%)": "People in poverty",
         "Unemployment rate (%)": "Unemployment rate", "Households on SNAP (%)": "Households on SNAP",
         "Homes vacant (%)": "Homes vacant", "Life expectancy (years)": "Life expectancy at birth",
         "Fair or poor health (%)": "Adults in fair or poor health", "Diabetes (%)": "Adults with diabetes",
         "High blood pressure (%)": "Adults with high blood pressure", "Frequent mental distress (%)": "Adults with frequent mental distress"}


def fmt(m, v):
    if m.startswith("Median"): return f"${round(v, -2):,.0f}"
    if m.startswith("Life"): return f"{v:.1f} yrs"
    return f"{v:.0f}%"


use_house_style()
K = pd.read_csv(ROOT / "analysis/spotlight/key_measures.csv")


def build(cid):
    C = CFG[cid]; name = C["name"]; k = K[K.cand_id == cid]
    fig = plt.figure(figsize=(11, 5.4))
    titleblock(fig, f"{name} by the numbers", f"{name} compared with the United States. Economy on the left, health on the right.")
    for col, (side, head) in enumerate([("economic", "Economy"), ("health", "Health")]):
        x0 = 0.03 + col * 0.495; w = 0.455
        fig.text(x0, 0.775, head, color=INK, fontsize=13.5, fontweight="bold", va="bottom")
        fig.text(x0 + w * 0.80, 0.775, name if len(name) < 18 else "Here", color=INK, fontsize=9.5, ha="right", va="bottom", fontweight="bold")
        fig.text(x0 + w, 0.775, "U.S.", color=INK_DIM, fontsize=9.5, ha="right", va="bottom", fontweight="bold")
        rows = k[k.side == side]
        for i, r in enumerate(rows.itertuples()):
            y = 0.70 - i * 0.118
            fig.add_artist(plt.Line2D([x0, x0 + w], [y + 0.058, y + 0.058], color=GRID, lw=0.8, transform=fig.transFigure))
            fig.text(x0, y + 0.012, LABEL[r.measure], color=INK, fontsize=11, va="center")
            fig.text(x0 + w * 0.80, y + 0.012, fmt(r.measure, r.value), color="#E4E5E7", fontsize=15, fontweight="bold", ha="right", va="center")
            fig.text(x0 + w, y + 0.012, fmt(r.measure, r.us_value), color=INK_DIM, fontsize=11.5, ha="right", va="center")
            # paired bars on a shared 0-max scale for this row
            mx = max(r.value, r.us_value); bx, bw = x0, w * 0.52
            for j, (v, c) in enumerate([(r.value, BLUE), (r.us_value, MUTED)]):
                fig.add_artist(plt.Rectangle((bx, y - 0.032 - j * 0.016), bw * v / mx, 0.010, color=c, transform=fig.transFigure, lw=0))
    le = k[k.measure == "Life expectancy (years)"].source.iloc[0]
    le_note = ("life expectancy 2010-2015 (USALEEP)" if le.startswith("USALEEP")
               else "life expectancy 2021-2023, county-wide (County Health Rankings)")
    pl = "CDC PLACES 2024" if "2024" in k[k.side == "health"].source.iloc[-1] else "CDC PLACES 2025"
    credit(fig, f"Sources: Census Bureau, American Community Survey 2020-2024; {pl} (model estimates for adults); {le_note}.\n"
                f"Blue bar: {name}. Gray bar: U.S.")
    out = ROOT / "posts" / C["slug"] / "images"; out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "00-key-measures.png"); plt.close(fig)
    print(cid, out / "00-key-measures.png")


for cid in (list(CFG) if sys.argv[1:] == ["all"] else sys.argv[1:]):
    build(cid)
