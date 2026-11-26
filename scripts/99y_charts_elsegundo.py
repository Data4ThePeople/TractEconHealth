"""El Segundo Barrio story-first charts (2026-11-26).

02-people-homes.png   three stacked panels, 1960 to 2020: people, homes, people per occupied home (no second y-axis)
03b-crowding.png      share of occupied homes with more than one person per room, 1960 to 2020-2024, vs. El Paso County
03c-poverty-birthplace.png  poverty rate of U.S.-born residents and immigrants, 2020-2024, here and in the county
04b-diabetes-age.png  CDC diabetes estimate vs. the rate expected from the neighborhood's age mix at Texas rates
Inputs: analysis/spotlight/history_final.csv (population 1970-2020), population_early_U028.csv (1960),
housing_nativity_elsegundo.csv (99x), recent_elsegundo.csv (99u), diabetes_age_elsegundo.csv (99v).
"""
import sys
from pathlib import Path
import pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, GRID, BLUE, MAGENTA, YELLOW, SURFACE, MUTED

use_house_style(); OUT = ROOT / "posts/spotlight-el-segundo-barrio/images"; A = ROOT / "analysis/spotlight"
H = pd.read_csv(A / "housing_nativity_elsegundo.csv", dtype={"year": str}); R = pd.read_csv(A / "recent_elsegundo.csv", dtype={"period": str})
ES, CO = "El Segundo Barrio", "El Paso County"
hist = pd.read_csv(A / "history_final.csv", dtype={"year": str}); hist = hist[(hist.cand_id == "U028") & (hist.measure == "population")].set_index("year").value
pop = {1960: float(pd.read_csv(A / "population_early_U028.csv").set_index("year").loc[1960, "pop"])} | {y: float(hist[str(y)]) for y in (1970, 1980, 1990, 2000, 2010, 2020)}
h = H[H.area == ES].set_index("year"); r = R[R.area == ES]
rv = lambda per, m: float(r[(r.period == per) & (r.measure == m)].num.iloc[0])
homes = {int(y): float(h.loc[y, "housing_units"]) for y in h.index} | {2010: rv("2010", "housing_units"), 2020: rv("2020", "housing_units")}
pph = {int(y): float(h.loc[y, "people_per_occupied_home"]) for y in h.index} | {y: rv(str(y), "household_pop") / rv(str(y), "occupied_units") for y in (2010, 2020)}


def style(a):
    a.grid(axis="y", color=GRID, linewidth=0.6); a.tick_params(length=0)
    for sp in ("left", "bottom"): a.spines[sp].set_color(GRID)


# 02: people, homes, people per home
fig, axs = plt.subplots(3, 1, figsize=(10, 9.6), sharex=True, gridspec_kw=dict(hspace=0.42))
fig.subplots_adjust(left=0.1, right=0.95, top=0.83, bottom=0.08)
for a, data, col, ttl, fmt, top in ((axs[0], pop, BLUE, "People living in the six tracts", lambda v: f"{v:,.0f}", 62000),
                                     (axs[1], homes, MAGENTA, "Homes (housing units)", lambda v: f"{v:,.0f}", 16500),
                                     (axs[2], pph, YELLOW, "People per occupied home", lambda v: f"{v:.1f}", 5.6)):
    xs, ys = list(data), list(data.values())
    for x0, x1 in ((1964, 1967), (1973, 1974)): a.axvspan(x0, x1 + 0.6, color=GRID, alpha=0.9, lw=0)
    a.plot(xs, ys, color=col, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(xs, ys): a.annotate(fmt(v), (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=10)
    a.set_ylim(0, top); a.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _, f=fmt: f(v))); a.set_title(ttl, loc="left", color=INK, fontsize=11); style(a)
axs[0].annotate("Chamizal\nclearance", (1965.8, 62000 * 0.97), ha="center", va="top", color=INK_DIM, fontsize=8.5)
axs[0].annotate("Tenement\ndrive", (1974.6, 62000 * 0.97), ha="left", va="top", color=INK_DIM, fontsize=8.5)
axs[2].set_xlim(1955, 2025); axs[2].set_xticks([1960, 1970, 1980, 1990, 2000, 2010, 2020])
ch_h = 100 * (1 - homes[2020] / homes[1960])
titleblock(fig, f"{ch_h:.0f}% fewer homes than in 1960, and fewer people in each",
           "People, homes and people per occupied home inside today's six tract lines, census years 1960 to 2020. Shaded: the\n"
           "Chamizal clearance (1964-1967) and the Tenement Eradication Program (1973-1974). 1960 counts all people per home.")
credit(fig, "Source: NHGIS (IPUMS) decennial census tract counts, 1960-2000, fitted to today's tracts; Census Bureau 2010 and 2020 censuses.")
fig.savefig(OUT / "02-people-homes.png"); plt.close(fig)

# 03b: crowding
cr = {ES: {}, CO: {}}
for area in cr:
    hh = H[H.area == area].set_index("year"); rr = R[(R.area == area) & (R.measure == "crowded_pct")].set_index("period")
    cr[area] = {int(y): float(hh.loc[y, "crowded_pct"]) for y in hh.index} | {2010: float(rr.loc["2008-2012", "value"]), 2022: float(rr.loc["2020-2024", "value"])}
fig, ax = plt.subplots(figsize=(10, 6)); fig.subplots_adjust(left=0.08, right=0.84, top=0.76, bottom=0.13)
for area, col, ls in ((CO, INK_DIM, "--"), (ES, BLUE, "-")):
    xs, ys = list(cr[area]), list(cr[area].values())
    ax.plot(xs, ys, color=col, lw=2, ls=ls, marker="o", ms=7 if area == CO else 8, mec=SURFACE, mew=2)
    for x, v in zip(xs, ys): ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 10 if area == ES else -16), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    ax.annotate("El Segundo Barrio\nand Chamizal" if area == ES else area, (2022, ys[-1]), xytext=(2024.5, ys[-1] + (3 if area == ES else -2)), textcoords="data", va="center", color=INK, fontsize=10, annotation_clip=False)
ax.set_ylim(0, 65); ax.set_xlim(1955, 2024); ax.set_xticks([1960, 1970, 1980, 1990, 2000, 2010, 2022]); ax.set_xticklabels(["1960", "1970", "1980", "1990", "2000", "2010", "2020-24"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); style(ax)
titleblock(fig, "Crowding fell, but homes here are still more crowded than the county's",
           "Share of occupied homes with more than one person per room. The 2010 point is from the 2008-2012 survey;\n"
           "2020-24 is the 2020-2024 survey.")
credit(fig, "Source: NHGIS (IPUMS) decennial census tract counts, 1960-2000, fitted to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates.")
fig.savefig(OUT / "03b-crowding.png"); plt.close(fig)

# 03c: poverty by birthplace
pv = R[(R.period == "2020-2024") & R.measure.isin(["poverty_us_born_pct", "poverty_foreign_born_pct"])].set_index(["area", "measure"]).value
fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.14)
grp = [(ES, "El Segundo Barrio and Chamizal"), (CO, "El Paso County")]; w = 0.36
for i, (area, lab) in enumerate(grp):
    for j, (m, col, nm) in enumerate((("poverty_us_born_pct", BLUE, "Born in the U.S."), ("poverty_foreign_born_pct", YELLOW, "Born outside the U.S."))):
        v = pv[(area, m)]; x = i + (j - 0.5) * w * 1.08
        ax.bar(x, v, width=w, color=col, label=nm if i == 0 else None)
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 6), textcoords="offset points", ha="center", color=INK, fontsize=11)
ax.set_xticks([0, 1]); ax.set_xticklabels([g[1] for g in grp], color=INK, fontsize=11); ax.set_ylim(0, 75)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); style(ax)
ax.legend(loc="upper right", frameon=False, labelcolor=INK, fontsize=10)
titleblock(fig, "People born in the U.S. here are as likely to be poor as immigrants",
           "Share of people below the poverty line, by place of birth, 2020-2024. In the six tracts, the margins of error\n"
           "are about 10 points (U.S.-born) and 14 points (born outside the U.S.).")
credit(fig, "Source: Census Bureau, American Community Survey 2020-2024 five-year estimates, table B17025, summed across the six tracts.")
fig.savefig(OUT / "03c-poverty-birthplace.png"); plt.close(fig)

# 04b: diabetes vs. age alone
D = pd.read_csv(A / "diabetes_age_elsegundo.csv").set_index("area")
bars = [("CDC estimate,\nEl Segundo Barrio\nand Chamizal", D.loc[ES, "places_observed"], BLUE),
        ("Expected here from\nage alone, at Texas\nrates for each age", D.loc[ES, "expected_at_texas_rates"], INK_DIM),
        ("CDC estimate,\nEl Paso County", D.loc[CO, "places_observed"], MUTED)]
fig, ax = plt.subplots(figsize=(10, 5.8)); fig.subplots_adjust(left=0.08, right=0.97, top=0.74, bottom=0.2)
for i, (lab, v, col) in enumerate(bars):
    ax.bar(i, v, width=0.55, color=col); ax.annotate(f"{v:.0f}%", (i, v), xytext=(0, 6), textcoords="offset points", ha="center", color=INK, fontsize=12)
ax.set_xticks(range(3)); ax.set_xticklabels([b[0] for b in bars], color=INK, fontsize=10); ax.set_ylim(0, 40)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); style(ax)
titleblock(fig, "An older population explains only a small part of the diabetes rate",
           f"Share of adults ever told they have diabetes. {D.loc[ES, 'share_65plus']:.0f}% of adults here are 65 or older, compared with "
           f"{D.loc[CO, 'share_65plus']:.0f}% in the county.\nThe middle bar applies Texas's 2023 rate for each age group to the neighborhood's adults.")
credit(fig, "Source: CDC PLACES 2025 (2023 model estimates, weighted by adult population); CDC BRFSS 2023, Texas, by age group;\n"
            "Census Bureau, American Community Survey 2020-2024 (adults by age).")
fig.savefig(OUT / "04b-diabetes-age.png"); plt.close(fig)
print("homes", homes); print("people per home", {k: round(v, 2) for k, v in pph.items()}); print("crowding", cr); print(pv)
