"""Static charts for the post, house dark palette. Every number is read from data/processed at render time.
01: county median household income against life expectancy (County Health Rankings, counted deaths)."""
import os, sys
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import PROC, ROOT
from plot_style import BLUE, GRID, INK, INK_DIM, SURFACE, YELLOW, credit, titleblock, use_house_style

use_house_style()
OUT = ROOT / "posts" / "income-health-viz" / "images"
OUT.mkdir(parents=True, exist_ok=True)


def median_line(x, y, groups=20):
    """Same rule as the viz: 20 equal-count groups along x, median x and median y of each."""
    order = np.argsort(x, kind="stable")
    xs, ys = x[order], y[order]
    pts = []
    for b in range(groups):
        lo, hi = int(np.floor(b * len(xs) / groups)), int(np.floor((b + 1) * len(xs) / groups))
        pts.append((np.median(xs[lo:hi]), np.median(ys[lo:hi])))
    return np.array(pts)


def chart_life_expectancy():
    c = pd.read_parquet(PROC / "counties.parquet")
    c = c[c.med_hh_income.notna() & c.life_expectancy.notna()]
    x, y = c.med_hh_income.to_numpy(float), c.life_expectancy.to_numpy(float)
    rho = float(np.corrcoef(pd.Series(x).rank(), pd.Series(y).rank())[0, 1])
    line = median_line(x, y)

    fig, ax = plt.subplots(figsize=(10, 6.6))
    fig.subplots_adjust(top=0.80, bottom=0.17, left=0.08, right=0.95)
    ax.scatter(x / 1000, y, s=9, color=BLUE, alpha=0.45, linewidths=0)
    ax.plot(line[:, 0] / 1000, line[:, 1], color=YELLOW, lw=2.5, solid_capstyle="round")
    for (lx, ly), ha, dx in [(line[0], "right", -2), (line[-1], "left", 2)]:
        ax.text(lx / 1000 + dx, ly, f"{ly:.1f} years", color=INK, fontsize=10, ha=ha, va="center", fontweight="bold",
                path_effects=[pe.withStroke(linewidth=4, foreground=SURFACE)])
    # the highest value comes from very few deaths; label it with its published range rather than drop it
    raw = pd.read_csv(ROOT / "data" / "raw" / "chr" / "analytic_supplement_20260325.csv", dtype=str).set_index("fipscode")
    top = c.life_expectancy.idxmax()
    lo, hi = (float(raw.loc[top, k]) for k in ("v147_cilow", "v147_cihigh"))
    tname = c.loc[top, "name"].replace(", North Dakota", ", N.D.")
    ax.annotate(f"{tname}, {int(c.loc[top, 'pop']):,} people: {c.loc[top, 'life_expectancy']:.1f} years from very few\n"
                f"deaths. Its published range runs {lo:.0f} to {hi:.0f} years.",
                (c.loc[top, "med_hh_income"] / 1000, c.loc[top, "life_expectancy"]), xytext=(8, 0),
                textcoords="offset points", color=INK_DIM, fontsize=8.5, va="center")
    ax.set_xlim(20, np.ceil(x.max() / 10000) * 10 + 5)
    ax.set_ylim(50, 110)
    ax.xaxis.set_major_formatter(lambda v, _: f"${int(v)}k" if v else "$0")
    ax.set_xlabel("Median household income, 2020-2024", color=INK_DIM, fontsize=10)
    ax.set_ylabel("Life expectancy at birth (years)", color=INK_DIM, fontsize=10)
    ax.yaxis.grid(True); ax.xaxis.grid(True); ax.set_axisbelow(True)
    ax.tick_params(labelsize=9)
    titleblock(fig, "Life expectancy rises with county income",
               f"Each dot is one of {len(c):,} counties. Life expectancy is counted from death records, not modeled. "
               f"The yellow line joins the\nmiddle county in each of 20 equal-size income groups. "
               f"Rank correlation with income: {rho:.2f}.")
    credit(fig, "Life expectancy, 2021-2023: County Health Rankings & Roadmaps, March 2026 release, from NCHS mortality "
                "files. Income: U.S. Census Bureau,\nAmerican Community Survey 2020-2024. Counties under 500 people, mostly "
                "group quarters, or in Kentucky and Pennsylvania are left out.")
    fig.savefig(OUT / "01-county-life-expectancy.png")
    plt.close(fig)
    print("01", len(c), round(rho, 3), [round(v, 1) for v in line[[0, -1], 1]], [round(v) for v in line[[0, -1], 0]])


if __name__ == "__main__":
    chart_life_expectancy()
