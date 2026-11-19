"""Then-and-now table for each spotlight candidate, 1970 to 2020-2024.

For a neighborhood (a set of 2020 tracts) it adds up census counts from each era onto the same area:
  1970, 1980   NHGIS nominal tract counts. Old tracts are chosen by map overlay: a 1970 or 1980 tract is in if half or
               more of its area falls inside the neighborhood outline (2020 tracts, cartographic file). Fit = area of
               the chosen old tracts that overlaps the outline / area of their union with the outline.
  1990, 2000   NHGIS nominal counts moved onto the neighborhood's 2010 tracts with the NHGIS block-based crosswalks
               (population weights). Fit (1990) = the screen's stability score.
  2010, 2020   NHGIS counts standardized to 2010 tracts (population, race, occupancy, tenure), summed over the
               neighborhood's 2010 tracts.
  2008-2012    ACS 5-year on 2010 tracts, summed over the neighborhood's 2010 tracts.
  2020-2024    ACS 5-year on 2020 tracts, summed over the neighborhood's own tracts.
  Life expectancy: USALEEP 2010-2015, average of the 2010 tracts weighted by 2010 population.
Rates are computed from summed counts (poverty = below poverty / poverty universe; unemployment = unemployed /
civilian labor force; vacancy = vacant / all housing units; owners = owner-occupied / occupied units).

Input:  analysis/spotlight/candidates.csv (or --file with a cand_id,tracts[,stability_1990] CSV)
Output: analysis/spotlight/history_long.csv (or --out <path>) (cand_id, year, measure, value, fit, source)
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
warnings.filterwarnings("ignore")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import RAW, ROOT

OUT = ROOT / "analysis" / "spotlight"
NH = RAW / "nhgis" / "extract"
args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
cand = pd.read_csv(args.get("--file", OUT / "candidates.csv"), dtype={"tracts": str})
OUTFILE = Path(args.get("--out", OUT / "history_long.csv"))

# ---------- inputs ----------
nom = pd.read_csv(NH / "nhgis0010_csv" / "nhgis0010_ts_nominal_tract.csv", encoding="latin-1", dtype={f"GJOIN{y}": str for y in (1970, 1980, 1990, 2000, 2010, 2020)})
std = pd.read_csv(NH / "nhgis0010_csv" / "nhgis0010_ts_geog2010_tract.csv", encoding="latin-1", dtype={"GISJOIN": str})
std["geoid10"] = std.GISJOIN.str[1:3] + std.GISJOIN.str[4:7] + std.GISJOIN.str[8:14]
std = std.set_index("geoid10")
def nomyear(y):
    cols = {"pop": f"AV0AA{y}", "black": f"B18AB{y}", "pov": f"CL6AA{y}", "povu": f"AX6AA{y}", "clf": f"B84AC{y}", "unemp": f"B84AE{y}"}
    d = nom[[f"GJOIN{y}"] + [c for c in cols.values() if c in nom.columns]].dropna(subset=[f"GJOIN{y}"])
    d = d.rename(columns={v: k for k, v in cols.items()}).groupby(f"GJOIN{y}").sum(min_count=1)
    return d
N = {y: nomyear(y) for y in (1970, 1980, 1990, 2000)}
cw90 = pd.read_csv(RAW / "nhgis" / "nhgis_tr1990_tr2010.csv", dtype={"tr1990gj": str, "tr2010ge": str}, usecols=["tr1990gj", "tr2010ge", "wt_pop"])
cw00 = pd.read_csv(RAW / "nhgis" / "nhgis_tr2000_tr2010.csv", dtype={"tr2000gj": str, "tr2010ge": str}, usecols=["tr2000gj", "tr2010ge", "wt_pop"])
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
a12 = pd.read_parquet(RAW / "acs" / "acs2012_tract_history.parquet")
a24 = pd.read_parquet(RAW / "acs" / "acs2024_tract_history.parquet")
le = pd.read_csv(RAW / "usaleep" / "US_A.CSV", dtype={"Tract ID": str})
le = pd.Series(le["e(0)"].to_numpy(float), index=le["Tract ID"].str.zfill(11))
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]).set_index("GEOID").to_crs("ESRI:102003")
old = {y: gpd.read_file(NH / "nhgis0010_shape" / f"US_tract_{y}_conflated.shp", columns=["GISJOIN"]).set_index("GISJOIN") for y in (1970, 1980)}
for y in old: old[y] = old[y].set_crs("ESRI:102003", allow_override=True)
cand_meta = pd.read_csv(OUT / "candidates.csv", dtype={"tracts": str}).set_index("cand_id")

def s10_of(tr20):
    p = rel[rel.GEOID_TRACT_20.isin(tr20)]
    share = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
    return list(share.index[share >= 0.5])

def rates(d):
    o = {}
    o["population"] = d.get("pop")
    if pd.notna(d.get("black")) and d.get("pop"): o["pct_black"] = 100 * d["black"] / d["pop"]
    if d.get("povu"): o["poverty_rate"] = 100 * d["pov"] / d["povu"]
    if d.get("clf"): o["unemployment_rate"] = 100 * d["unemp"] / d["clf"]
    if d.get("hu"): o["vacancy_rate"] = 100 * d["vac"] / d["hu"]
    if d.get("occ"): o["owner_share"] = 100 * d["own"] / d["occ"]
    return o

rows = []
def add(cid, year, d, fit, src):
    for k, v in rates(d).items():
        if v is not None and pd.notna(v):
            rows.append(dict(cand_id=cid, year=year, measure=k, value=round(float(v), 2), fit=None if fit is None else round(float(fit), 3), source=src))

for r in cand.itertuples():
    tr20 = r.tracts.split(";"); s10 = s10_of(tr20)
    outline = g20.loc[g20.index.intersection(tr20)].unary_union
    for y in (1970, 1980):
        o = old[y]; hits = o[o.intersects(outline)]
        if len(hits):
            share = hits.intersection(outline).area / hits.area
            chosen = hits[share >= 0.5]
            if len(chosen):
                u = chosen.unary_union
                fit = u.intersection(outline).area / u.union(outline).area
                d = N[y].reindex(chosen.index).sum(min_count=1).to_dict()
                if d.get("pop"): add(r.cand_id, str(y), d, fit, f"NHGIS nominal tracts {y}, map overlay")
    for y, cw, gj in ((1990, cw90, "tr1990gj"), (2000, cw00, "tr2000gj")):
        c = cw[cw.tr2010ge.isin(s10)]
        if len(c):
            v = N[y].reindex(c[gj]).mul(c.wt_pop.to_numpy(), axis=0).sum(min_count=1).to_dict()
            fit = (getattr(r, "stability_1990", None) if "stability_1990" in cand.columns
                   else cand_meta.loc[r.cand_id, "stability_1990"] if r.cand_id in cand_meta.index else None) if y == 1990 else None
            add(r.cand_id, str(y), v, fit, f"NHGIS nominal tracts {y}, NHGIS crosswalk to 2010 tracts")
    sd = std.reindex(s10)
    for y in (1990, 2000, 2010, 2020):
        d = {"pop": sd.get(f"CL8AA{y}", pd.Series(dtype=float)).sum(min_count=1),
             "black": sd.get(f"CM1AB{y}", pd.Series(dtype=float)).sum(min_count=1),
             "occ": sd.get(f"CM9AA{y}", pd.Series(dtype=float)).sum(min_count=1),
             "vac": sd.get(f"CM9AB{y}", pd.Series(dtype=float)).sum(min_count=1),
             "own": sd.get(f"CN1AA{y}", pd.Series(dtype=float)).sum(min_count=1)}
        d["hu"] = (d["occ"] or 0) + (d["vac"] or 0)
        if y in (1990, 2000):  # population and race for these years come from the nominal rows above; keep housing only
            d = {k: d[k] for k in ("occ", "vac", "own", "hu")}
        add(r.cand_id, f"{y}", d, None, f"NHGIS standardized to 2010 tracts, {y}")
    for yr, tab, ids, src in (("2008-2012", a12, s10, "ACS 2008-2012 5-year, 2010 tracts"), ("2020-2024", a24, tr20, "ACS 2020-2024 5-year, 2020 tracts")):
        t = tab.reindex(ids).sum(min_count=1)
        d = {"pov": t.B17001_002E, "povu": t.B17001_001E, "clf": t.B23025_003E, "unemp": t.B23025_005E,
             "hu": t.B25002_001E, "vac": t.B25002_003E, "occ": t.B25003_001E, "own": t.B25003_002E}
        if yr == "2020-2024": d.update({"pop": t.B02001_001E, "black": t.B02001_003E})
        add(r.cand_id, yr, d, None, src)
    w = std.reindex(s10)["CL8AA2010"]; l = le.reindex(s10)
    ok = l.notna() & w.notna()
    if ok.any():
        rows.append(dict(cand_id=r.cand_id, year="2010-2015", measure="life_expectancy", value=round(float(np.average(l[ok], weights=w[ok])), 1),
                         fit=round(float(w[ok].sum() / w.sum()), 3), source="USALEEP 2010-2015 (share of 2010 population with an estimate in fit)"))

h = pd.DataFrame(rows)
order = {"1970": 0, "1980": 1, "1990": 2, "2000": 3, "2008-2012": 4, "2010": 5, "2010-2015": 6, "2020": 7, "2020-2024": 8}
h["o"] = h.year.map(order); h = h.sort_values(["cand_id", "measure", "o"]).drop(columns="o")
h.to_csv(OUTFILE, index=False)
print(len(h), "rows for", h.cand_id.nunique(), "candidates")
