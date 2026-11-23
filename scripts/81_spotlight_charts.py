"""Charts for the spotlight posts. Usage: python scripts/81_spotlight_charts.py U047 [more ids]   (or "all")

Urban picks (HOLC map exists):
  01-map.png              the neighborhood outline on the 1930s HOLC map, with today's freeways (TIGER S1100)
Rural picks:
  01-map.png              the neighborhood outline inside its county, with main roads (TIGER S1100, S1200) and the county seat
  01b-county-population.png  county population, 1900-2020 (Census counts: NBER cencounts 1900-1990; Census API 2000-2020)
All picks:
  02-population.png       people living in the tracts, oldest reliable year to 2020-2024 (history_final.csv)
  03-low-income-vacancy.png  share below 200% of the poverty line (below200.csv) and share of homes vacant, 1990 to 2020-2024,
                          with the U.S. share below 200% as a dashed reference
  04-overdose.png         county drug overdose death rate vs. the middle U.S. county, 2003-2021 (CDC NCHS model rates), or,
                          where overdoses are not part of the story (health4 in CFG), one health chart that is:
                          04-life-expectancy.png (county vs. state vs. U.S., CHR) or 04-<measure>.png (PLACES, neighborhood vs. county, state, U.S.)
Years whose old-tract fit is under 0.8 are left out, as in the tables. Output: posts/<slug>/images/
"""
import sys
import numpy as np, pandas as pd, geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, GRID, YELLOW, BLUE, MAGENTA, SURFACE

# county = main county (overdose, county history); od_fips = the code CDC's file uses (Oglala Lakota was Shannon, 46113)
CFG = {
    "U047": dict(health4="TREND", pov_line=True, slug="spotlight-west-dayton", name="West Dayton", county="39113", county_name="Montgomery County",
                 city="Dayton", state="OH", holc_year="1937", labels=[("Downtown", 39.7589, -84.1916)]),
    "U034": dict(health4="COPD", slug="spotlight-north-birmingham", name="North Birmingham", county="01073", county_name="Jefferson County",
                 city="Birmingham", state="AL", holc_year="1930s", labels=[("Downtown", 33.5186, -86.8104)]),
    "U039": dict(slug="spotlight-west-baltimore", name="West Baltimore", county="24510", county_name="Baltimore", extra_roads=["US Hwy 40"],
                 city="Baltimore", state="MD", holc_year="1937", labels=[("Downtown", 39.2904, -76.6122)]),
    "U028": dict(health4="DIABETES", slug="spotlight-el-segundo-barrio", name="El Segundo Barrio and Chamizal", county="48141", county_name="El Paso County",
                 city="El Paso", state="TX", holc_year="1936", labels=[("Downtown", 31.7587, -106.4869)]),
    "U013": dict(slug="spotlight-north-flint", name="North and East Flint", county="26049", county_name="Genesee County",
                 city="Flint", state="MI", holc_year="1937", labels=[("Downtown", 43.0125, -83.6875)]),
    "M016": dict(health4="LE", slug="spotlight-clarksdale", name="Clarksdale", county="28027", county_name="Coahoma County",
                 labels=[("Clarksdale", 34.2001, -90.5709)]),
    "R007": dict(slug="spotlight-mcdowell-county", name="McDowell County", county="54047", county_name="McDowell County",
                 labels=[("Welch", 37.4329, -81.5848)]),
    "R046": dict(health4="LE", slug="spotlight-pine-ridge", name="Pine Ridge", county="46102", od_fips="46113", county_name="Oglala Lakota County",
                 labels=[("Pine Ridge", 43.0255, -102.5563)]),
    "R004": dict(slug="spotlight-owsley-county", name="Owsley County", county="21189", county_name="Owsley County",
                 labels=[("Booneville", 37.4762, -83.6749)]),
    "M014": dict(health4="LE", slug="spotlight-clarksville-texas", name="Clarksville", county="48387", county_name="Red River County",
                 labels=[("Clarksville", 33.6107, -95.0527)]),
}
YX = {"1970": 1970, "1980": 1980, "1990": 1990, "2000": 2000, "2010": 2010, "2020-2024": 2022}
GC = {"A": "#5a9e6f", "B": "#4f8fc0", "C": "#c9a227", "D": "#c4554d"}
use_house_style()
sets = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id")
H = pd.read_csv(ROOT / "analysis/spotlight/history_final.csv", dtype={"year": str})
H = H[H.fit.isna() | (H.fit >= 0.8)]
G20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").set_index("GEOID")
OD = pd.read_parquet(RAW / "cdc" / "overdose_county_model.parquet")
OD["fips"] = OD.fips.astype(str).str.zfill(5); OD["year"] = OD.year.astype(int); OD["r"] = pd.to_numeric(OD.model_based_death_rate, errors="coerce")
MID = OD.groupby("year").r.median()
B200 = pd.read_csv(ROOT / "analysis/spotlight/below200.csv", dtype={"area": str})


def axes_style(ax):
    ax.grid(axis="y", color=GRID, linewidth=0.6); ax.tick_params(length=0)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)


def xlabels(ax, xs):
    ax.set_xticks(list(xs)); ax.set_xticklabels([("2020-24" if x == 2022 else str(int(x))) for x in xs])


def build(cid):
    C = CFG[cid]; rural = "city" not in C
    out = ROOT / "posts" / C["slug"] / "images"; out.mkdir(parents=True, exist_ok=True)
    tracts = sets.loc[cid, "tracts"].split(";"); n = len(tracts)
    h = H[H.cand_id == cid]
    outline = G20.loc[tracts].to_crs(4326).dissolve()
    minx, miny, maxx, maxy = outline.total_bounds
    info = {}

    # ---------- 01 map ----------
    roads = gpd.read_file(RAW / "tiger" / "roads" / f"tl_2024_{C['county']}_roads.shp").to_crs(4326)
    fig, ax = plt.subplots(figsize=(10, 8.6)); fig.subplots_adjust(left=0.03, right=0.97, top=0.84, bottom=0.08)
    if not rural:
        holc = gpd.read_file(RAW / "holc" / "mappinginequality.json", bbox=(minx - 0.1, miny - 0.08, maxx + 0.1, maxy + 0.08)).to_crs(4326)
        holc = holc[(holc.city == C["city"]) & (holc.state == C["state"])]
        for gr, col in GC.items():
            sub = holc[holc.grade == gr]
            if len(sub): sub.plot(ax=ax, color=col, alpha=0.55, edgecolor=SURFACE, linewidth=0.6)
        other = holc[~holc.grade.isin(list(GC))]
        if len(other): other.plot(ax=ax, color=MUTED, alpha=0.25, edgecolor=SURFACE, linewidth=0.6)
        roads[(roads.MTFCC == "S1100") | roads.FULLNAME.isin(C.get("extra_roads", []))].plot(ax=ax, color=INK_DIM, linewidth=1.6)
        lx = [lo for _, la, lo in C["labels"]] + [minx, maxx]; ly = [la for _, la, lo in C["labels"]] + [miny, maxy]
        p = 0.012; x0, x1, y0, y1 = min(lx) - p - 0.02, max(lx) + p + 0.02, min(ly) - p, max(ly) + p
        k = np.cos(np.radians((y0 + y1) / 2)); asp = (y1 - y0) / ((x1 - x0) * k)
        if asp < 0.62: d = (0.62 * (x1 - x0) * k - (y1 - y0)) / 2; y0, y1 = y0 - d, y1 + d
        if asp > 1.0: d = ((y1 - y0) / k - (x1 - x0)) / 2; x0, x1 = x0 - d, x1 + d
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
        fig.set_size_inches(10, 10 * 0.76 * (y1 - y0) / ((x1 - x0) * k) + 2.2)
        top_in, bot_in = 1.35, 1.25; H_ = fig.get_figheight(); fig.subplots_adjust(top=1 - top_in / H_, bottom=bot_in / H_)
        leg = [Patch(fc=GC[g], alpha=0.55, label=l) for g, l in
               [("A", "A, \"best\""), ("B", "B, \"still desirable\""), ("C", "C, \"declining\""), ("D", "D, \"hazardous\"")]]
        leg += [Line2D([], [], color=INK, lw=2.4, label=f"{C['name']} (this story)"), Line2D([], [], color=INK_DIM, lw=1.6, label="Freeways today")]
        title = f"{C['name']} on the {C['holc_year']} federal mortgage map"
        sub = f"Home Owners' Loan Corporation grades for {C['city']}, with the {n} census tracts in this story outlined\nand today's freeways drawn in gray."
        src = "Source: Mapping Inequality, University of Richmond Digital Scholarship Lab; U.S. Census Bureau TIGER/Line 2024 roads and 2020 tracts."
    else:
        counties = sorted({t[:5] for t in tracts})
        cty = G20[G20.index.str[:5].isin(counties)].to_crs(4326)
        cty = cty.assign(c=cty.index.str[:5]).dissolve(by="c")
        cty.plot(ax=ax, color="#22262A", edgecolor="none")
        cty.boundary.plot(ax=ax, color=YELLOW, linewidth=1.0, linestyle=(0, (4, 3)))
        for c in counties:
            if c != C["county"]:
                rr = gpd.read_file(RAW / "tiger" / "roads" / f"tl_2024_{c}_roads.shp").to_crs(4326) if (RAW / "tiger" / "roads" / f"tl_2024_{c}_roads.shp").exists() else None
                if rr is not None: roads = pd.concat([roads, rr])
        big = roads[roads.MTFCC.isin(["S1100", "S1200"])]
        big.plot(ax=ax, color=INK_DIM, linewidth=1.1)
        G20.loc[tracts].to_crs(4326).plot(ax=ax, color=BLUE, alpha=0.35, edgecolor="none")
        cx0, cy0, cx1, cy1 = cty.total_bounds; px, py = (cx1 - cx0) * 0.06, (cy1 - cy0) * 0.06
        ax.set_xlim(cx0 - px, cx1 + px); ax.set_ylim(cy0 - py, cy1 + py)
        leg = [Line2D([], [], color=INK, lw=2.4, label="The tracts in this story"),
               Line2D([], [], color=YELLOW, lw=1.0, ls=(0, (4, 3)), label="County line"), Line2D([], [], color=INK_DIM, lw=1.1, label="Main roads")]
        title = f"Where {C['name']} is" if C["name"] != C["county_name"] else (f"{C['name']}: the tracts in this story")
        names = C["county_name"] + (" and parts of Bennett and Jackson counties" if len(counties) > 1 else "")
        sub = f"The {n} census tracts in this story, shaded and outlined, in {names}."
        src = "Source: U.S. Census Bureau TIGER/Line 2024 roads and 2020 census tracts."
    outline.boundary.plot(ax=ax, color=INK, linewidth=2.4)
    for lab, la, lo in C["labels"]:
        ax.plot(lo, la, "o", color=INK, ms=4) if rural else None
        ax.annotate(lab, (lo, la), xytext=(0, 10) if rural else (0, 0), textcoords="offset points", color=INK, fontsize=10,
                    ha="center", va="bottom" if rural else "center",
                    bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec="none", alpha=0.8))
    ax.set_axis_off(); ax.set_aspect(1 / np.cos(np.radians((miny + maxy) / 2)))
    lk = dict(handles=leg, frameon=True, facecolor=SURFACE, edgecolor=GRID, labelcolor=INK, fontsize=9.5)
    if rural: fig.legend(loc="lower left", bbox_to_anchor=(0.03, 0.08), **lk)  # figure corner, clear of the county
    else: fig.legend(loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.045), **lk)  # one band under the map, off the grades
    titleblock(fig, title, sub); credit(fig, src)
    fig.savefig(out / "01-map.png"); plt.close(fig)

    # ---------- 01b county population (rural) ----------
    if rural:
        cc = pd.read_csv(RAW / "county_pop" / "cencounts.csv", dtype={"fips": str}, na_values=".")
        cfips = C.get("od_fips", C["county"])  # Shannon County code before 2015
        old = cc[cc.fips == cfips].iloc[0]
        s = {int(k[3:]): old[k] for k in cc.columns if k.startswith("pop") and pd.notna(old[k])}
        new = pd.read_csv(RAW / "county_pop" / "county_pop_2000_2020.csv", dtype={"fips": str})
        for y in (2000, 2010, 2020):
            v = new[(new.fips.isin([C["county"], cfips])) & (new.year == y)]["pop"]
            if len(v): s[y] = int(v.iloc[0])
        s = pd.Series(s).sort_index().astype(float)
        fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.16)
        ax.plot(s.index, s.values, color=BLUE, lw=2, marker="o", ms=7, mec=SURFACE, mew=2)
        pk = s.idxmax()
        for x in sorted({s.index[0], pk, s.index[-1]}):
            ax.annotate(f"{s[x]:,.0f}", (x, s[x]), xytext=(0, 11), textcoords="offset points", ha="center", color=INK, fontsize=10)
        ax.set_ylim(0, s.max() * 1.18); ax.set_xlim(s.index[0] - 4, 2024); ax.set_xticks([y for y in range(1900, 2021, 20) if y >= s.index[0]])
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}")); axes_style(ax)
        if pk not in (s.index[-1],):
            t = f"{C['county_name']} peaked at {s[pk]:,.0f} people in {pk}"
        else:
            t = f"{C['county_name']} has grown since {s.index[0]}"
        titleblock(fig, t, f"People counted in each census, {s.index[0]}-2020, for the whole county.")
        credit(fig, "Source: U.S. Census Bureau decennial census county counts (1900-1990 file via NBER; 2000-2020 Census API).")
        fig.savefig(out / "01b-county-population.png"); plt.close(fig)
        info["county_pop"] = s.round(0).astype(int).to_dict()

    # ---------- 02 population ----------
    pop = h[h.measure == "population"].assign(x=lambda d: d.year.map(YX)).dropna(subset=["x"]).sort_values("x")
    fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.16)
    ax.plot(pop.x, pop.value, color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    for x, v in zip(pop.x, pop.value):
        ax.annotate(f"{v:,.0f}", (x, v), xytext=(0, 11), textcoords="offset points", ha="center", color=INK, fontsize=10)
    ax.set_ylim(0, pop.value.max() * 1.18); ax.set_xlim(pop.x.min() - 4, 2026); xlabels(ax, pop.x)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}")); axes_style(ax)
    first, last, y0 = pop.value.iloc[0], pop.value.iloc[-1], int(pop.x.iloc[0])
    ch = 100 * (last / first - 1)
    t = (f"{C['name']} has {abs(ch):.0f}% fewer people than in {y0}" if ch <= -5 else
         f"{C['name']} has {ch:.0f}% more people than in {y0}" if ch >= 5 else f"{C['name']}'s population, {y0} to today")
    titleblock(fig, t, f"People living in the {n} census tracts, counted on today's tract lines.")
    credit(fig, f"Source: NHGIS (IPUMS) decennial census tract counts, {y0}-2010, matched to today's tracts; ACS 2020-2024 five-year estimates.")
    fig.savefig(out / "02-population.png"); plt.close(fig)
    info["pop"] = dict(zip(pop.year, pop.value.round(0))); info["pop_change"] = round(ch, 1)

    # ---------- 03 low income and vacancy ----------
    # Low income = below 200% of the poverty line (below200.csv: NHGIS C20 1990-2000, ACS C17002 after); U.S. as a dashed reference.
    LX = {"1970": 1970, "1980": 1980, "1990": 1990, "2000": 2000, "2008-2012": 2010, "2010": 2010, "2020-2024": 2022}
    PL = C.get("pov_line")  # also draw poverty (below 100% of the line), 1970 on, from history_final
    pv = h[h.measure == "poverty_rate"].assign(x=lambda d: d.year.map(LX)).dropna(subset=["x"]).sort_values("x") if PL else None
    lw = B200[B200.area == cid].assign(x=lambda d: d.year.map(LX)).sort_values("x")
    us = B200[B200.area == "US"].assign(x=lambda d: d.year.map(LX)).sort_values("x")
    vc_ = h[(h.measure == "vacancy_rate") & (h.year != "2008-2012")].assign(x=lambda d: d.year.map(LX)).dropna(subset=["x"]).sort_values("x")
    fig, ax = plt.subplots(figsize=(10, 6.0)); fig.subplots_adjust(left=0.08, right=0.8, top=0.72, bottom=0.15)
    ax.plot(lw.x, lw.value, color=MAGENTA, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    ax.plot(vc_.x, vc_.value, color=YELLOW, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
    if not PL: ax.plot(us.x, us.value, color=INK, lw=2, ls="--")  # West Dayton drops the U.S. line to declutter
    if PL:
        ax.plot(pv.x, pv.value, color=BLUE, lw=2, marker="o", ms=8, mec=SURFACE, mew=2)
        for x, v in zip(pv.x, pv.value):
            ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    usv = us.set_index("x").value if not PL else pd.Series(dtype=float)
    for x, v in zip(lw.x, lw.value):
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, 10), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    for x, v in zip(vc_.x, vc_.value):  # below the marker when the U.S. line is close above it
        dn = PL or (x in usv.index and 0 <= usv[x] - v < 7)
        ax.annotate(f"{v:.0f}%", (x, v), xytext=(0, -17 if dn else 10), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    top = max(100, 0) if lw.value.max() > 80 else max(lw.value.max(), 60) + 10
    ax.set_ylim(0, min(100, np.ceil(top / 10) * 10)); ax.set_xlim(1966 if PL else 1986, 2026)
    xt = ([1970, 1980] if PL else []) + [1990, 2000, 2010, 2022]
    ax.set_xticks(xt); ax.set_xticklabels([str(x) for x in xt[:-1]] + ["2020-24"])
    # end labels, pushed apart so they never overlap
    ends = sorted([(lw.value.iloc[-1], "Low income"), (vc_.value.iloc[-1], "Homes vacant"), ] + ([(us.value.iloc[-1], "U.S., low income")] if not PL else [(pv.value.iloc[-1], "Poverty")]))
    gapu = ax.get_ylim()[1] * 0.06; pos = []
    for v, l in ends:
        y = v if not pos or v - pos[-1] >= gapu else pos[-1] + gapu; pos.append(y)
        ax.annotate(l, (2022, v), xytext=(2026.5, y), textcoords="data", va="center", color=INK, fontsize=10.5, annotation_clip=False)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%")); axes_style(ax)
    ax.legend(handles=[Line2D([], [], color=MAGENTA, lw=2, marker="o", label="People below 200% of the poverty line"),
                       Line2D([], [], color=YELLOW, lw=2, marker="o", label="Homes vacant"),
                       ] + ([Line2D([], [], color=INK, lw=2, ls="--", label="U.S., below 200% of the poverty line")] if not PL else
                            [Line2D([], [], color=BLUE, lw=2, marker="o", label="People below the poverty line")]),
              loc="upper left", frameon=False, labelcolor=INK, fontsize=9.5, ncol=3, bbox_to_anchor=(0, 1.11))
    l0, l1 = lw.value.iloc[0], lw.value.iloc[-1]; v0, v1 = vc_.value.iloc[0], vc_.value.iloc[-1]
    t = ("More people with low incomes, more homes empty" if l1 - l0 >= 5 and v1 - v0 >= 3 else
         "Fewer people with low incomes than in 1990, but more homes empty" if l0 - l1 >= 5 and v1 - v0 >= 3 else
         "Most people here have low incomes, and more homes are empty" if v1 - v0 >= 3 else
         "Most people here have low incomes")
    if PL: t = "Poverty here more than doubled since 1970, and more homes are empty"
    sub = (f"Share of people below the poverty line (1970 on) and below 200% of it (1990 on), and share of homes vacant, {C['name']}.\nIncome for 2010 is from the 2008-2012 survey; vacancy is from the 2010 census." if PL else
           f"Share of people below 200% of the poverty line and share of homes vacant, {C['name']}, with the U.S. share\nbelow 200% for comparison. Income for 2010 is from the 2008-2012 survey; vacancy is from the 2010 census.")
    titleblock(fig, t, sub)
    credit(fig, "Source: NHGIS (IPUMS) decennial census, 1970-2010, fitted to today's tracts; ACS 2008-2012 and 2020-2024 five-year estimates." if PL else
           "Source: NHGIS (IPUMS) decennial census, 1990-2010; ACS 2008-2012 and 2020-2024 five-year estimates.")
    fig.savefig(out / "03-low-income-vacancy.png"); plt.close(fig)
    info.update(low_income=dict(zip(lw.year, lw.value.round(1))), vacancy=dict(zip(vc_.year, vc_.value.round(1))))

    if C.get("health4") == "TREND":
        health_trend(cid, C, out, info); print(cid, C["slug"], info); return
    if C.get("health4"):
        health_bars(C, tracts, out, info); print(cid, C["slug"], info); return

    # ---------- 04 overdose ----------
    here = OD[OD.fips == C.get("od_fips", C["county"])].sort_values("year").set_index("year").r
    fig, ax = plt.subplots(figsize=(10, 5.6)); fig.subplots_adjust(left=0.08, right=0.8, top=0.8, bottom=0.16)
    ax.plot(here.index, here.values, color=MAGENTA, lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5)
    ax.plot(MID.index, MID.values, color=INK, lw=2, ls="--")
    lab_here = C["county_name"] if not C["county_name"].endswith("Baltimore") else "Baltimore city"
    ends = [(here, lab_here), (MID, "Middle U.S. county")]
    gap = abs(here.iloc[-1] - MID.iloc[-1]) / max(here.max(), MID.max())
    for i, (d, lab) in enumerate(ends):
        off = 0 if gap > 0.12 else (14 if d.iloc[-1] >= ends[1 - i][0].iloc[-1] else -14)
        ax.annotate(f"{lab}\n{d.iloc[-1]:.0f} per 100,000", (d.index[-1], d.iloc[-1]), xytext=(10, off), textcoords="offset points", va="center", color=INK, fontsize=10)
    ax.annotate(f"{here.iloc[0]:.0f}", (here.index[0], here.iloc[0]), xytext=(0, 10 if here.iloc[0] >= MID.iloc[0] else -16), textcoords="offset points", ha="center", color=INK, fontsize=9.5)
    ax.set_ylim(0, max(here.max(), MID.max()) * 1.15); ax.set_xticks(range(2003, 2022, 3)); axes_style(ax)
    r = here.iloc[-1] / MID.iloc[-1]
    verb = ("rose far above the typical county" if r >= 1.5 else "rose above the typical county" if r >= 1.15 else
            "stayed below the typical county" if r <= 0.85 else "tracked the typical county")
    titleblock(fig, f"Overdose deaths in {lab_here} {verb}",
               f"Drug overdose deaths per 100,000 people, CDC model estimates, {lab_here} and the middle U.S. county,\n2003-2021. County-wide, not {C['name']} alone." if C["name"] != C["county_name"] else
               f"Drug overdose deaths per 100,000 people, CDC model estimates, {lab_here} and the middle U.S. county,\n2003-2021.")
    credit(fig, "Source: CDC National Center for Health Statistics, Drug Poisoning Mortality by County (model-based rates), data.cdc.gov.")
    fig.savefig(out / "04-overdose.png"); plt.close(fig)
    info["overdose"] = {int(k): round(v, 1) for k, v in here.items() if k in (2003, 2010, 2017, 2021)}
    info["overdose_mid_2021"] = round(MID.iloc[-1], 1)
    print(cid, C["slug"], info)


TREND_M = [("DIABETES", "Diabetes"), ("COPD", "COPD"), ("BPHIGH", "High blood pressure"), ("MHLTH", "Frequent mental distress")]


def health_trend(cid, C, out, info):
    """04 for picks with health4="TREND": four tract health measures over every CDC release (scripts/84_health_trend.py),
    the pick against the U.S. Survey years 2013/2014-2023; nothing at the tract level exists before that."""
    d = pd.read_csv(ROOT / f"analysis/spotlight/health_trend_{cid}.csv")
    # two releases can reuse a survey year (high blood pressure is asked every other year): keep the later release
    d = d.sort_values("release", key=lambda r: r.str[-4:]).drop_duplicates(["measure", "area", "year"], keep="last")
    fig, axs = plt.subplots(2, 2, figsize=(10, 7.4), sharex=True)
    fig.subplots_adjust(left=0.07, right=0.88, top=0.79, bottom=0.1, hspace=0.42, wspace=0.42)
    info["trend"] = {}
    for ax, (m, lab) in zip(axs.flat, TREND_M):
        here = d[(d.measure == m) & (d.area == cid)].sort_values("year"); us = d[(d.measure == m) & (d.area == "US")].sort_values("year")
        ax.plot(here.year, here.value, color=BLUE, lw=2, marker="o", ms=5, mec=SURFACE, mew=1.2)
        ax.plot(us.year, us.value, color=INK, lw=1.8, ls="--")
        for dd, nm in ((here, C["name"]), (us, "U.S.")):
            ax.annotate(f"{dd.value.iloc[-1]:.0f}%", (dd.year.iloc[-1], dd.value.iloc[-1]), xytext=(6, 0), textcoords="offset points", va="center", color=INK, fontsize=10, fontweight="bold" if nm != "U.S." else "normal")
            ax.annotate(f"{dd.value.iloc[0]:.0f}%", (dd.year.iloc[0], dd.value.iloc[0]), xytext=(-6, 0), textcoords="offset points", va="center", ha="right", color=INK_DIM, fontsize=9.5)
        ax.axvline(2017.5, color=GRID, lw=1.2)
        ax.set_title(lab, color=INK, fontsize=12, loc="left", fontweight="bold")
        ax.set_ylim(0, max(here.value.max(), us.value.max()) * 1.2); ax.set_xlim(2012.3, 2024.2)
        ax.set_xticks([2014, 2017, 2020, 2023]); axes_style(ax)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
        info["trend"][m] = {"here": [(int(here.year.iloc[0]), round(here.value.iloc[0], 1)), (int(here.year.iloc[-1]), round(here.value.iloc[-1], 1))],
                            "us": [(int(us.year.iloc[0]), round(us.value.iloc[0], 1)), (int(us.year.iloc[-1]), round(us.value.iloc[-1], 1))]}
    axs[0, 1].annotate(C["name"], (1.02, 0.86), xycoords="axes fraction", color=BLUE, fontsize=10, fontweight="bold")
    axs[0, 1].annotate("U.S., dashed", (1.02, 0.30), xycoords="axes fraction", color=INK, fontsize=10)
    titleblock(fig, f"{C['name']} has been far less healthy than the U.S. since tract estimates began",
               "Share of adults, CDC model estimates by survey year. The thin line marks CDC's switch from 500 Cities to PLACES.\n"
               "Compare the two lines within each year: CDC says these estimates do not support tracking a tract's change over time.")
    credit(fig, "Source: CDC 500 Cities (2016-2019 releases) and PLACES (2020-2025 releases), census tract estimates weighted by population.\n"
                "U.S.: 500 Cities national figure (BRFSS) through 2017; average of all tracts, weighted by population, from 2018.")
    fig.savefig(out / "04-health-trend.png"); plt.close(fig)


STATE = {"01": "Alabama", "48": "Texas", "28": "Mississippi", "46": "South Dakota", "54": "West Virginia", "21": "Kentucky"}
PNAME = {"COPD": ("COPD", "Adults who have ever been told they have COPD (chronic obstructive pulmonary disease)"),
         "DIABETES": ("diabetes", "Adults who have ever been told they have diabetes")}


def health_bars(C, tracts, out, info):
    """04 health chart chosen per story: county life expectancy (CHR) or one PLACES measure, vs. state and U.S."""
    st = C["county"][:2]
    if C["health4"] == "LE":
        chr_ = pd.read_csv(RAW / "chr" / "analytic_supplement_20260325.csv", dtype={"fipscode": str}, low_memory=False).set_index("fipscode")
        le = pd.to_numeric(chr_["v147_rawvalue"], errors="coerce")
        rows = [(C["county_name"], le[C["county"]]), (STATE[st], le[st + "000"]), ("United States", le["00000"])]
        fmt = lambda v: f"{v:.1f} years"; fn = "04-life-expectancy.png"
        title = f"Life expectancy in {C['county_name']} is {round(le['00000'], 1) - round(le[C['county']], 1):.1f} years below the U.S."
        sub = f"Life expectancy at birth, 2021-2023, {C['county_name']}, {STATE[st]} and the United States."
        src = "Source: County Health Rankings & Roadmaps, 2026 supplemental release (life expectancy, 2021-2023, from National Vital Statistics deaths)."
    else:
        m = C["health4"]
        pl = pd.read_parquet(RAW / "places" / "places_tract_2025.parquet", columns=["locationname", "measureid", "data_value", "totalpop18plus"])
        pl = pl[pl.measureid == m].copy(); pl["v"] = pd.to_numeric(pl.data_value, errors="coerce"); pl["w"] = pd.to_numeric(pl.totalpop18plus, errors="coerce")
        def wa(d): d = d.dropna(subset=["v", "w"]); return float((d.v * d.w).sum() / d.w.sum())
        rows = [(C["name"], wa(pl[pl.locationname.isin(tracts)])), (C["county_name"], wa(pl[pl.locationname.str[:5] == C["county"]])),
                (STATE[st], wa(pl[pl.locationname.str[:2] == st])), ("United States", wa(pl))]
        fmt = lambda v: f"{v:.0f}%"; fn = f"04-{PNAME[m][0].lower()}.png"
        title = f"{PNAME[m][0][0].upper() + PNAME[m][0][1:]} is far more common in {C['name']}"
        sub = f"{PNAME[m][1]}, CDC model estimates for 2023.\nEach area is the average of its census tracts, weighted by adult population."
        src = "Source: CDC PLACES 2025 census tract estimates (adult crude prevalence), weighted by adult population."
    fig, ax = plt.subplots(figsize=(10, 1.6 + 0.75 * len(rows) + 1.6)); H_ = fig.get_figheight()
    fig.subplots_adjust(left=0.24, right=0.88, top=1 - 1.45 / H_, bottom=0.75 / H_)
    ys = list(range(len(rows)))[::-1]
    for y, (lab, v) in zip(ys, rows):
        ax.barh(y, v, height=0.55, color=BLUE if y == ys[0] else MUTED)
        ax.annotate(fmt(v), (v, y), xytext=(8, 0), textcoords="offset points", va="center", color=INK, fontsize=11, fontweight="bold" if y == ys[0] else "normal")
    ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], color=INK, fontsize=11)
    ax.set_xticks([]); ax.tick_params(length=0)
    for sp in ("left", "bottom"): ax.spines[sp].set_visible(False)
    ax.set_xlim(0, max(v for _, v in rows) * 1.18)
    titleblock(fig, title, sub); credit(fig, src)
    fig.savefig(out / fn); plt.close(fig)
    info["health4"] = {lab: round(v, 1) for lab, v in rows}; info["health4_file"] = fn


ids = list(CFG) if sys.argv[1:] == ["all"] else sys.argv[1:]
for cid in ids:
    build(cid)
