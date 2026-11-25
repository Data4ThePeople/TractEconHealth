"""Chart for the North Birmingham post: jobs located inside the four tracts, and how many of them were held by people who
live in the four tracts, 2002-2022. Reads analysis/spotlight/lodes_od_northbirmingham.csv (scripts/99g_lodes_od_spotlight.py).
Output: posts/spotlight-north-birmingham/images/02d-jobs-here.png
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, GRID, BLUE, INK_DIM, SURFACE
use_house_style()
d = pd.read_csv(ROOT / "analysis/spotlight/lodes_od_northbirmingham.csv")
fig, ax = plt.subplots(figsize=(10, 6.0)); fig.subplots_adjust(left=0.09, right=0.97, top=0.72, bottom=0.14)
x = np.arange(len(d)); w = 0.38
ax.bar(x - w / 2 - 0.01, d.jobs_in_tracts, w, color=INK_DIM, edgecolor=SURFACE, linewidth=2)
ax.bar(x + w / 2 + 0.01, d.held_by_residents, w, color=BLUE, edgecolor=SURFACE, linewidth=2)
for i, r in d.iterrows():
    ax.annotate(f"{int(r.jobs_in_tracts):,}", (i - w / 2 - 0.01, r.jobs_in_tracts), xytext=(0, 5), textcoords="offset points", ha="center", color=INK, fontsize=10)
    ax.annotate(f"{int(r.held_by_residents):,}\n({r.pct_held_by_residents:.1f}%)",
                (i + w / 2 + 0.01, r.held_by_residents), xytext=(0, 5), textcoords="offset points", ha="center", color=INK, fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(d.year.astype(str)); ax.set_ylim(0, 12000)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
ax.legend(handles=[Patch(color=INK_DIM, label="Jobs located in the four tracts"), Patch(color=BLUE, label="Of those, jobs held by people who live in the four tracts")],
          loc="upper left", frameon=False, labelcolor=INK, fontsize=9.5, ncol=2, bbox_to_anchor=(0, 1.11))
titleblock(fig, "Few of the jobs here went to people who live here",
           "Jobs located inside North Birmingham's four census tracts, and how many were held by people living in them.\n"
           "Counts are jobs, not people, and include only workers who live in Alabama.")
credit(fig, "Source: Census Bureau, LEHD Origin-Destination Employment Statistics (LODES 8), all jobs.")
fig.savefig(ROOT / "posts/spotlight-north-birmingham/images/02d-jobs-here.png"); plt.close(fig)
