"""Chart for the West Dayton post: no vehicle, no reliable transportation and food insecurity, West Dayton vs. comparison.
Reads analysis/spotlight/transport_westdayton.csv (scripts/92_transport_westdayton.py).
Comparison: U.S. for households with no vehicle (ACS); all PLACES tracts in the 40 states with these measures for the two CDC measures.
Output: posts/spotlight-west-dayton/images/05a-transport.png
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
sys.path.insert(0, str(Path(__file__).parent))
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE, SURFACE

use_house_style()
ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "analysis/spotlight/transport_westdayton.csv")
g = lambda a, m: float(d[(d.area == a) & (d.measure == m)].value.iloc[0])
M = [("Households with\nno vehicle", g("West Dayton", "households_no_vehicle_pct"), g("United States", "households_no_vehicle_pct")),
     ("Adults without reliable\ntransportation in the past year", g("West Dayton", "LACKTRPT"), g("PLACES tracts (40 states)", "LACKTRPT")),
     ("Adults who were food\ninsecure in the past year", g("West Dayton", "FOODINSECU"), g("PLACES tracts (40 states)", "FOODINSECU"))]
fig, ax = plt.subplots(figsize=(10, 6.2)); fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.17)
x = np.arange(len(M)); w = 0.34
for i, (lab, here, cmp_) in enumerate(M):
    for dx, v, col in ((-w / 2 - 0.01, here, BLUE), (w / 2 + 0.01, cmp_, INK_DIM)):
        ax.bar(i + dx, v, w, color=col, edgecolor=SURFACE, linewidth=2)
        ax.annotate(f"{v:.0f}%", (i + dx, v), xytext=(0, 6), textcoords="offset points", ha="center", color=INK, fontsize=11)
ax.set_xticks(x); ax.set_xticklabels([m[0] for m in M], color=INK, fontsize=10.5)
ax.set_ylim(0, 60); ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
ax.legend(handles=[Patch(fc=BLUE, label="West Dayton (six tracts)"), Patch(fc=INK_DIM, label="Nationwide")],
          loc="upper left", frameon=False, labelcolor=INK, fontsize=10, ncol=2, bbox_to_anchor=(0, 1.1))
titleblock(fig, "Fewer cars, less reliable transportation and more food insecurity",
           "Share of households with no vehicle (2020-2024) and share of adults without reliable transportation or food\nat some point in the past year (2023), West Dayton and nationwide.")
credit(fig, "Sources: U.S. Census Bureau, American Community Survey 2020-2024 (vehicles; U.S.); CDC PLACES 2025 release, model estimates\n(transportation and food; nationwide here means tracts in the 40 states with these measures, weighted by population).")
fig.savefig(ROOT / "posts/spotlight-west-dayton/images/05a-transport.png"); plt.close(fig)
