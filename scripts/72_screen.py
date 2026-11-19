"""Community spotlight screen: find neighborhoods (clusters of adjacent tracts) at the low end of income and the poor
end of health, split urban and rural, and test whether their boundaries are stable enough to compare over time.

Inputs
  data/processed/tracts.parquet            the published tract set (ACS 2020-2024, PLACES 2025, health index)
  data/raw/places/places_tract_2024_kypa   PLACES 2024 for Kentucky and Pennsylvania (no 2025 health estimates)
  data/raw/acs/...                         via 10_build.build_acs() for Kentucky and Pennsylvania economics
  data/raw/ruca/RUCA-codes-2020-tract.csv  USDA ERS 2020 rural-urban commuting area codes
  data/raw/tiger/cb_2020_us_tract_500k     2020 tract boundaries (adjacency)
  data/raw/xwalk/tab20_tract20_tract10     2020-2010 tract relationship file (land area)
  data/raw/nhgis/nhgis_tr1990_tr2010.csv   NHGIS 1990-2010 tract crosswalk (population weights)
  data/raw/nhgis/extract/nhgis0010_csv     NHGIS nominal tract series (1990 population for the crosswalk weights)

Rules
  qualifying tract: bottom 20% nationally on median household income AND on the health index.
    Kentucky and Pennsylvania: each 2024 health measure is placed in the national 2025 distribution, the same index
    formula is applied, and the result is placed in the national index distribution.
  urban: RUCA 1-3; rural: RUCA 7-10; micropolitan (4-6) kept as its own group.
  neighborhood: tracts that share a border (more than 50 m of common edge). Groups over 8 tracts are split by
    growing from the deepest tract to 8 tracts at a time, deepest neighbors first.
  stability (1990 to 2020): 2020 tracts -> 2010 tracts (each 2010 tract with half or more of its land in the
    neighborhood) -> 1990 tracts by population weight. Score = the smaller of (a) the share of the neighborhood's
    1990 population that comes from 1990 tracts mostly (80%+) inside it and (b) the share of those old tracts'
    population that falls inside it, times the 2010-2020 land match. Pass at 0.80.

Output: analysis/spotlight/clusters.csv (all), analysis/spotlight/candidates.csv (selected), screen_log.txt
"""
import sys, glob, zipfile, io
import numpy as np, pandas as pd, geopandas as gpd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from common import RAW, PROC, ROOT
import importlib
b = importlib.import_module("10_build")

OUT = ROOT / "analysis" / "spotlight"; OUT.mkdir(parents=True, exist_ok=True)
Q = 0.20
log = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

# ---------- health and income percentiles, national set + KY/PA ----------
t = pd.read_parquet(PROC / "tracts.parquet")
t = t[t.med_hh_income.notna() & t.health_index.notna()].copy()
raw_nat, _ = b.index(t, b.HEALTH_CORE, [-1] * len(b.HEALTH_CORE))
t["health_raw"] = raw_nat

def place(vals, ref):
    """percentile (0-1] of each value within the reference distribution, ties averaged (as rank(pct=True))"""
    ref = np.sort(ref[np.isfinite(ref)])
    lo = np.searchsorted(ref, vals, "left"); hi = np.searchsorted(ref, vals, "right")
    return np.where(np.isfinite(vals), (lo + hi + 1) / 2 / len(ref), np.nan)

p24 = pd.read_parquet(RAW / "places" / "places_tract_2024_kypa.parquet")
p24 = p24[p24.data_value_type.str.startswith("Crude") & p24.measureid.isin(b.PLACES_KEEP)]
w = p24.pivot(index="locationname", columns="measureid", values="data_value").rename(columns=b.PLACES_KEEP)
w.index = w.index.astype(str).str.zfill(11)
acs = b.lf_change(b.build_acs())
k = acs[acs.index.str[:2].isin(["21", "42"])].join(w[b.HEALTH_CORE], how="inner")
k = k[(k["pop"] >= 500) & ((k.gq_pop / k["pop"]) < 0.5) & k.obesity.notna() & k.med_hh_income.notna()].copy()
r = pd.DataFrame({c: 100 - place(k[c].to_numpy(float), t[c].to_numpy(float)) * 100 for c in b.HEALTH_CORE}, index=k.index)
k["health_raw"] = r.mean(axis=1).where(r.notna().sum(axis=1) >= np.ceil(0.75 * len(b.HEALTH_CORE)))
k = k[k.health_raw.notna()]
k["stateabbr"] = np.where(k.index.str[:2] == "21", "KY", "PA")
k["health_source"] = "PLACES 2024"
t["health_source"] = "PLACES 2025"
say(f"KY/PA tracts added from PLACES 2024: {len(k):,} (KY {int((k.stateabbr=='KY').sum()):,}, PA {int((k.stateabbr=='PA').sum()):,})")

cols = ["pop", "med_hh_income", "health_raw", "stateabbr", "health_source", "pct_above_200fpl", "prime_epop",
        "unemp_rate", "pct_snap", "pct_medicaid"] + b.HEALTH_CORE
a = pd.concat([t[cols + ["countyname", "health_index"]], k[cols]])
a["inc_pct"] = place(a.med_hh_income.to_numpy(float), t.med_hh_income.to_numpy(float))
a["hlth_pct"] = place(a.health_raw.to_numpy(float), t.health_raw.to_numpy(float))  # low = poor health
a["depth"] = (a.inc_pct + a.hlth_pct) / 2
a["qual"] = (a.inc_pct <= Q) & (a.hlth_pct <= Q)
say(f"tracts screened: {len(a):,}; qualifying (bottom {Q:.0%} on both): {int(a.qual.sum()):,}")

# ---------- RUCA ----------
ru = pd.read_csv(RAW / "ruca" / "RUCA-codes-2020-tract.csv", dtype={"TractFIPS20": str}, encoding="latin-1")
ru = ru.set_index(ru.TractFIPS20.str.zfill(11))
a = a.join(ru[["PrimaryRUCA", "UrbanAreaName20", "PrimaryDestinationName", "CountyName20", "StateName20"]], how="left")
a["kind"] = np.select([a.PrimaryRUCA.between(1, 3), a.PrimaryRUCA.between(4, 6), a.PrimaryRUCA.between(7, 10)],
                      ["urban", "micro", "rural"], "unknown")
say("qualifying by kind:", a[a.qual].kind.value_counts().to_dict())

# ---------- adjacency among qualifying tracts ----------
g = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]).set_index("GEOID")
q = g.loc[g.index.intersection(a.index[a.qual])].to_crs(5070)
q["geoid"] = q.index
pairs = gpd.sjoin(q[["geoid", "geometry"]], q[["geoid", "geometry"]], predicate="intersects", lsuffix="l", rsuffix="r")
pairs = pairs[pairs.geoid_l < pairs.geoid_r]
gl = q.geometry.reindex(pairs.geoid_l).to_numpy(); gr = q.geometry.reindex(pairs.geoid_r).to_numpy()
shared = np.array([x.boundary.intersection(y.boundary).length for x, y in zip(gl, gr)])
edges = pairs[shared > 50][["geoid_l", "geoid_r"]].to_numpy()
nb = {i: set() for i in q.index}
for x, y in edges: nb[x].add(y); nb[y].add(x)
cent = q.geometry.centroid.to_crs(4326)

# connected components, then split big ones
depth = a.depth
seen, comps = set(), []
for s in q.index:
    if s in seen: continue
    stack, comp = [s], []
    seen.add(s)
    while stack:
        u = stack.pop(); comp.append(u)
        for v in nb[u]:
            if v not in seen: seen.add(v); stack.append(v)
    comps.append(comp)
MAXN = 8
clusters = []
for comp in comps:
    left = set(comp)
    while left:
        if len(left) <= MAXN and len(left) == len(comp):
            clusters.append(sorted(left)); break
        seed = min(left, key=lambda i: depth[i]); grp = {seed}
        while len(grp) < MAXN:
            front = {v for u in grp for v in nb[u] if v in left and v not in grp}
            if not front: break
            grp.add(min(front, key=lambda i: depth[i]))
        clusters.append(sorted(grp)); left -= grp
say(f"neighborhoods (clusters of adjacent qualifying tracts, max {MAXN}): {len(clusters):,} from {len(comps):,} connected groups")

# ---------- stability ----------
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_20", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_20", "AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
rel20 = {k2: d for k2, d in rel.groupby("GEOID_TRACT_20")}
cw = pd.read_csv(RAW / "nhgis" / "nhgis_tr1990_tr2010.csv", dtype={"tr1990ge": str, "tr2010ge": str},
                 usecols=["tr1990ge", "tr2010ge", "wt_pop"])
cw = cw[cw.wt_pop > 0]
nom = RAW / "nhgis" / "extract" / "nhgis0010_csv" / "nhgis0010_ts_nominal_tract.csv"
d = pd.read_csv(nom, usecols=["GJOIN1990", "AV0AA1990"], dtype={"GJOIN1990": str}, encoding="latin-1")
d = d[d.GJOIN1990.notna() & d.AV0AA1990.notna()]
pop90 = pd.Series(d.AV0AA1990.astype(float).to_numpy(), index=d.GJOIN1990).groupby(level=0).sum()
cwj = pd.read_csv(RAW / "nhgis" / "nhgis_tr1990_tr2010.csv", dtype=str, usecols=["tr1990gj", "tr1990ge"]).drop_duplicates()
gj_of = dict(zip(cwj.tr1990ge, cwj.tr1990gj))
by10 = {k2: d for k2, d in cw.groupby("tr2010ge")}
by90 = {k2: d for k2, d in cw.groupby("tr1990ge")}
say("1990 population for crosswalk weights:", "loaded" if pop90 is not None else "NOT AVAILABLE (stability uses equal weights)")

def stability(tr20):
    parts = pd.concat([rel20[x] for x in tr20 if x in rel20])
    land20 = parts.drop_duplicates("GEOID_TRACT_20").AREALAND_TRACT_20.sum()
    in10 = parts.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / parts.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
    s10 = set(in10.index[in10 >= 0.5])
    if not s10: return np.nan, np.nan, ""
    s10_land = parts[parts.GEOID_TRACT_10.isin(s10)].drop_duplicates("GEOID_TRACT_10").AREALAND_TRACT_10.sum()
    inter = parts[parts.GEOID_TRACT_10.isin(s10)].AREALAND_PART.sum()
    f20 = inter / max(land20, s10_land) if max(land20, s10_land) > 0 else np.nan
    rows = pd.concat([by10[x] for x in s10 if x in by10]) if any(x in by10 for x in s10) else None
    if rows is None: return f20, np.nan, ""
    olds = rows.tr1990ge.unique()
    inS = {o: by90[o][by90[o].tr2010ge.isin(s10)].wt_pop.sum() for o in olds}
    w90 = {o: (pop90.get(gj_of.get(o), np.nan) if pop90 is not None else 1.0) for o in olds}
    w90 = {o: (v if np.isfinite(v) else 0.0) for o, v in w90.items()}
    tot_in = sum(w90[o] * inS[o] for o in olds)
    core = [o for o in olds if inS[o] >= 0.8]
    if tot_in <= 0: return f20, np.nan, ""
    a_ = sum(w90[o] * inS[o] for o in core) / tot_in
    b_ = (sum(w90[o] * inS[o] for o in core) / sum(w90[o] for o in core)) if core and sum(w90[o] for o in core) > 0 else 0
    return f20, min(a_, b_) * f20, ";".join(sorted(core))

rows = []
for n, tr in enumerate(clusters):
    s = a.loc[tr]
    pw = s["pop"]
    c = cent.loc[tr]
    f20, stab, core90 = stability(tr)
    kinds = s.kind.value_counts()
    rows.append(dict(
        cid=n, n_tracts=len(tr), tracts=";".join(tr), pop=int(pw.sum()),
        state=s.stateabbr.mode()[0], county=s.CountyName20.mode()[0] if s.CountyName20.notna().any() else "",
        urban_area=s.UrbanAreaName20.dropna().mode()[0] if s.UrbanAreaName20.notna().any() else "",
        destination=s.PrimaryDestinationName.dropna().mode()[0] if s.PrimaryDestinationName.notna().any() else "",
        kind=kinds.index[0], ruca=",".join(str(int(x)) for x in sorted(s.PrimaryRUCA.dropna().unique())),
        lat=round(float(np.average([p.y for p in c], weights=pw)), 4), lon=round(float(np.average([p.x for p in c], weights=pw)), 4),
        med_hh_income_wavg=round(float(np.average(s.med_hh_income, weights=pw))),
        inc_pct=round(float(np.average(s.inc_pct, weights=pw)) * 100, 1),
        hlth_pct=round(float(np.average(s.hlth_pct, weights=pw)) * 100, 1),
        depth=round(float(np.average(s.depth, weights=pw)) * 100, 1),
        obesity=round(float(np.average(s.obesity, weights=pw)), 1), diabetes=round(float(np.average(s.diabetes, weights=pw)), 1),
        copd=round(float(np.average(s.copd, weights=pw)), 1), smoking=round(float(np.average(s.smoking, weights=pw)), 1),
        pct_snap=round(float(np.average(s.pct_snap.fillna(s.pct_snap.mean()), weights=pw)), 1),
        prime_epop=round(float(np.average(s.prime_epop.fillna(s.prime_epop.mean()), weights=pw)), 1),
        health_source=",".join(sorted(s.health_source.unique())),
        match_2010_2020=round(f20, 3) if np.isfinite(f20) else np.nan,
        stability_1990=round(stab, 3) if np.isfinite(stab) else np.nan, core_1990_tracts=core90))
cl = pd.DataFrame(rows)
cl["stable"] = cl.stability_1990 >= 0.8
cl["stability_note"] = np.select(
    [cl.match_2010_2020.isna(), cl.stable, (cl.stability_1990 < 0.3) & (cl.n_tracts <= 2), cl.stability_1990 < 0.8],
    ["piece of a larger 2010 tract: compare on the old tract's outline, or skip",
     "stable: old tracts line up with the neighborhood",
     "piece of a larger 1990 tract: compare on the old tract's outline, or skip",
     "boundaries shifted since 1990: judgment call"], "")
# earliest census year in which every core 1990 tract has a population count under the same tract code
# (NHGIS nominal series; a code match is a first check only, finalists get a map overlay)
nm = pd.read_csv(nom, usecols=["GJOIN1990", "AV0AA1970", "AV0AA1980"], dtype={"GJOIN1990": str}, encoding="latin-1").dropna(subset=["GJOIN1990"])
nm = nm.groupby("GJOIN1990").sum(min_count=1)
def oldest(core):
    gj = [gj_of.get(o) for o in core.split(";") if o]
    if not gj: return ""
    sub = nm.reindex(gj)
    if sub.AV0AA1970.notna().all() and (sub.AV0AA1970 > 0).all(): return "1970"
    if sub.AV0AA1980.notna().all() and (sub.AV0AA1980 > 0).all(): return "1980"
    return "1990"
cl["oldest_tract_year"] = cl.core_1990_tracts.fillna("").map(oldest)
cl.to_csv(OUT / "clusters.csv", index=False)
say("oldest tract year (all clusters):", cl.oldest_tract_year.value_counts().to_dict())
say("clusters by kind:", cl.kind.value_counts().to_dict(), "| stable share:", round(cl.stable.mean(), 3))

# ---------- seeds ----------
SEEDS = {  # name: (lat, lon)
    "West Dayton, OH": (39.7520, -84.2400), "Roxbury, Boston": (42.3150, -71.0880), "Mattapan, Boston": (42.2770, -71.0920),
    "Dorchester, Boston": (42.3000, -71.0680), "Englewood, Chicago": (41.7790, -87.6450), "Woodlawn, Chicago": (41.7800, -87.5960),
    "Garfield Park, Chicago": (41.8810, -87.7290), "Compton, CA": (33.8958, -118.2201), "Watts, Los Angeles": (33.9420, -118.2420),
    "Clarksdale, MS (Delta)": (34.2001, -90.5709), "Sunflower County, MS (Delta)": (33.45, -90.65), "Belzoni, MS (Delta)": (33.18, -90.49),
    "Welch, McDowell County, WV (coal)": (37.4330, -81.5840), "Pine Ridge, SD": (43.0250, -102.5560), "Harlan County, KY (coal)": (36.8434, -83.3219),
}
def nearest(lat, lon, pool):
    d = (pool.lat - lat) ** 2 + ((pool.lon - lon) * np.cos(np.radians(lat))) ** 2
    return pool.index[d.argmin()], float(np.sqrt(d.min()) * 111)
seed_rows = {}
for nm, (la, lo) in SEEDS.items():
    i, km = nearest(la, lo, cl)
    seed_rows[i] = seed_rows.get(i, []) + [f"{nm} ({km:.1f} km)"]
    say(f"seed {nm}: cluster {cl.loc[i,'cid']} {km:.1f} km away, {cl.loc[i,'n_tracts']} tracts, depth {cl.loc[i,'depth']}, stability {cl.loc[i,'stability_1990']}")

# ---------- selection ----------
cl["seed"] = cl.index.map(lambda i: " | ".join(seed_rows.get(i, [])))
def pick(kind, n, cap_key, cap):
    pool = cl[(cl.kind == kind) & (cl["pop"] >= 1500)].sort_values("depth")
    out, cnt = [], {}
    for i, r_ in pool.iterrows():
        key = r_[cap_key] or r_.state
        if cnt.get(key, 0) >= cap: continue
        out.append(i); cnt[key] = cnt.get(key, 0) + 1
        if len(out) >= n: break
    return out
urb = pick("urban", 60, "urban_area", 3)
rur = pick("rural", 45, "state", 4) + pick("micro", 15, "state", 2)
sel = list(dict.fromkeys(urb + rur + list(seed_rows)))
cand = cl.loc[sel].copy()
cand["selected_as"] = np.where(cand.index.isin(seed_rows) & ~cand.index.isin(urb + rur), "seed", "screen")
cand = cand.sort_values(["kind", "depth"])
cand.insert(0, "cand_id", cand.kind.map({"urban": "U", "micro": "M", "rural": "R"}).fillna("X") + (cand.groupby("kind").cumcount() + 1).map("{:03d}".format))
cand.to_csv(OUT / "candidates.csv", index=False)
say("candidates:", len(cand), cand.kind.value_counts().to_dict(), "| stable:", int(cand.stable.sum()))
(OUT / "screen_log.txt").write_text("\n".join(log) + "\n")
