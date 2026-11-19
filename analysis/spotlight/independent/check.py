"""Independent recomputation of the spotlight key measures and then-and-now tables.

Written from the method in DATASETS.md only. Pulls ACS, PLACES and USALEEP fresh;
uses the untouched NHGIS, crosswalk, TIGER and CHR downloads already on disk.

Usage: .venv/bin/python analysis/spotlight/independent/check.py [cache_dir]
"""
import os
import sys
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CACHE = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "_cache"
CACHE.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, os.path.expanduser("~/.claude/d4tp-process"))
from d4tp_env import read_env_file  # noqa: E402

KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]

PICKS = "U047 U034 U039 U028 U013 M016 R007 R046 R004 M014".split()
fs = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype=str, usecols=["cand_id", "tracts"])
fs = fs[fs.cand_id.isin(PICKS)].drop_duplicates("cand_id")
SETS = {r.cand_id: [t.strip().zfill(11) for t in r.tracts.split(";") if t.strip()] for r in fs.itertuples()}
assert set(SETS) == set(PICKS)

rows = []


def add(cid, measure, year, value, fit=np.nan, note=""):
    rows.append(dict(cand_id=cid, measure=measure, year=year, value=value, fit=fit, note=note))


def cached_json(name, url, params):
    f = CACHE / name
    if f.exists():
        return json.loads(f.read_text())
    for attempt in range(4):
        r = requests.get(url, params=params, timeout=180)
        if r.status_code == 200:
            break
        time.sleep(3)
    r.raise_for_status()
    data = r.json()
    f.write_text(json.dumps(data))
    return data


def census(year, vars_, geo_for, geo_in=None, tag=""):
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    p = {"get": ",".join(vars_), "for": geo_for, "key": KEY}
    if geo_in:
        p["in"] = geo_in
    name = f"acs{year}_{tag}_{geo_for.replace(':', '').replace('*', 'all')}_{(geo_in or '').replace(' ', '_').replace(':', '')}.json"
    d = cached_json(name, url, p)
    df = pd.DataFrame(d[1:], columns=d[0])
    for v in vars_:
        df[v] = pd.to_numeric(df[v], errors="coerce")
        df.loc[df[v] < 0, v] = np.nan  # annotation codes
    return df


# ---------------------------------------------------------------- ACS 2020-2024
B19001 = [f"B19001_{i:03d}E" for i in range(1, 18)]
BIN_LO = [0, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000, 60000, 75000,
          100000, 125000, 150000, 200000]
BIN_HI = BIN_LO[1:] + [np.inf]
OTHER = ["B17001_001E", "B17001_002E", "B23025_003E", "B23025_005E", "B22003_001E", "B22003_002E",
         "B25002_001E", "B25002_003E", "B02001_001E", "B02001_003E", "B01003_001E", "B26001_001E"]

counties = sorted({t[:5] for s in SETS.values() for t in s})
acs = []
for c in counties:
    a = census(2024, B19001, "tract:*", f"state:{c[:2]} county:{c[2:]}", "b19001")
    b = census(2024, OTHER, "tract:*", f"state:{c[:2]} county:{c[2:]}", "other")
    m = a.merge(b, on=["state", "county", "tract"])
    acs.append(m)
acs = pd.concat(acs)
acs["geoid"] = acs.state + acs.county + acs.tract
acs = acs.set_index("geoid")

us_a = census(2024, B19001 + ["B19013_001E"], "us:1", None, "b19001us").iloc[0]
us_b = census(2024, OTHER, "us:1", None, "otherus").iloc[0]


def interp_median(counts):
    counts = np.asarray(counts, float)
    tot = counts.sum()
    half = tot / 2
    cum = 0.0
    for c, lo, hi in zip(counts, BIN_LO, BIN_HI):
        if cum + c >= half and c > 0:
            if np.isinf(hi):
                return np.nan  # median in open top bin
            return lo + (half - cum) / c * (hi - lo)
        cum += c
    return np.nan


def ratio(n, d):
    return n / d * 100 if d else np.nan


for cid, tracts in SETS.items():
    sub = acs.reindex(tracts)
    miss = [t for t in tracts if t not in acs.index]
    note = f"missing from ACS: {miss}" if miss else ""
    s = sub.sum(numeric_only=True)
    add(cid, "median_household_income", "2020-2024", round(interp_median(s[B19001[1:]].values)), note=note or "B19001 linear interpolation")
    add(cid, "poverty_rate", "2020-2024", ratio(s["B17001_002E"], s["B17001_001E"]), note=note)
    add(cid, "unemployment_rate", "2020-2024", ratio(s["B23025_005E"], s["B23025_003E"]), note=note)
    add(cid, "snap_households", "2020-2024", ratio(s["B22003_002E"], s["B22003_001E"]), note=note)
    add(cid, "homes_vacant", "2020-2024", ratio(s["B25002_003E"], s["B25002_001E"]), note=note)
    gq = sub["B26001_001E"] / sub["B01003_001E"]
    hi_gq = gq[gq >= 0.10]
    add(cid, "group_quarters_share", "2020-2024", ratio(s["B26001_001E"], s["B01003_001E"]),
        note=("tracts with GQ>=10%: " + ", ".join(f"{k} {v:.0%}" for k, v in hi_gq.items())) if len(hi_gq) else "")

add("US", "median_household_income", "2020-2024", us_a["B19013_001E"], note="B19013 published")
add("US", "median_household_income_interp", "2020-2024", round(interp_median(us_a[B19001[1:]].values)), note="B19001 interpolation, for comparison only")
add("US", "poverty_rate", "2020-2024", ratio(us_b["B17001_002E"], us_b["B17001_001E"]))
add("US", "unemployment_rate", "2020-2024", ratio(us_b["B23025_005E"], us_b["B23025_003E"]))
add("US", "snap_households", "2020-2024", ratio(us_b["B22003_002E"], us_b["B22003_001E"]))
add("US", "homes_vacant", "2020-2024", ratio(us_b["B25002_003E"], us_b["B25002_001E"]))

# ---------------------------------------------------------------- 2020 -> 2010 tracts
rel = pd.read_csv(ROOT / "data/raw/xwalk/tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
for c in ["AREALAND_TRACT_20", "AREALAND_TRACT_10", "AREALAND_PART"]:
    rel[c] = rel[c].astype(float)
rel = rel[rel.GEOID_TRACT_20.str[:5].isin(counties) | rel.GEOID_TRACT_10.str[:5].isin(counties)]

SETS10, LANDMATCH = {}, {}
for cid, tracts in SETS.items():
    r = rel[rel.GEOID_TRACT_20.isin(tracts)]
    inside = r.groupby("GEOID_TRACT_10").agg(part=("AREALAND_PART", "sum"), land10=("AREALAND_TRACT_10", "first"))
    inside["share"] = inside.part / inside.land10
    t10 = sorted(inside[inside.share >= 0.5].index)
    SETS10[cid] = t10
    land20 = rel[rel.GEOID_TRACT_20.isin(tracts)].drop_duplicates("GEOID_TRACT_20").AREALAND_TRACT_20.sum()
    land10 = rel[rel.GEOID_TRACT_10.isin(t10)].drop_duplicates("GEOID_TRACT_10").AREALAND_TRACT_10.sum()
    overlap = r[r.GEOID_TRACT_10.isin(t10)].AREALAND_PART.sum()
    LANDMATCH[cid] = overlap / max(land20, land10)
# 2010 county codes can differ from 2020 ones (Shannon County SD, 46113, became Oglala Lakota, 46102, in 2015)
counties10 = sorted({t[:5] for s in SETS10.values() for t in s})


def gj2010(g):  # 11-digit GEOID -> NHGIS GISJOIN
    return "G" + g[:2] + "0" + g[2:5] + "0" + g[5:]


# ---------------------------------------------------------------- NHGIS
nom = pd.read_csv(ROOT / "data/raw/nhgis/extract/nhgis0010_csv/nhgis0010_ts_nominal_tract.csv",
                  dtype=str, encoding="latin-1")
numcols = [c for c in nom.columns if c[:3] in ("AV0", "B18", "AX6", "CL6")]
for c in numcols:
    nom[c] = pd.to_numeric(nom[c], errors="coerce")
std = pd.read_csv(ROOT / "data/raw/nhgis/extract/nhgis0010_csv/nhgis0010_ts_geog2010_tract.csv",
                  dtype=str, encoding="latin-1")
for c in std.columns:
    if c[:3] in ("CL8", "CM1"):
        std[c] = pd.to_numeric(std[c], errors="coerce")
std = std.set_index("GISJOIN")


def nominal_year(y):
    d = nom[nom[f"GJOIN{y}"].notna()].copy()
    d = d.set_index(f"GJOIN{y}")
    return pd.DataFrame({"pop": d[f"AV0AA{y}"], "black": d[f"B18AB{y}"],
                         "pov": d[f"CL6AA{y}"], "povu": d[f"AX6AA{y}"]})


def add_hist(cid, y, pop, pov, povu, black, fit, note):
    add(cid, "population", y, pop, fit, note)
    add(cid, "poverty_rate", y, ratio(pov, povu), fit, note)
    add(cid, "pct_black", y, ratio(black, pop), fit, note)


for y, fname, gjcol in [(1990, "nhgis_tr1990_tr2010.csv", "tr1990gj"), (2000, "nhgis_tr2000_tr2010.csv", "tr2000gj")]:
    xw = pd.read_csv(ROOT / f"data/raw/nhgis/{fname}", dtype=str)
    xw["wt_pop"] = xw.wt_pop.astype(float)
    xw = xw[xw.tr2010ge.str[:5].isin(counties10)]
    data = nominal_year(y)
    for cid, t10 in SETS10.items():
        x = xw[xw.tr2010ge.isin(t10)]
        insh = x.groupby(gjcol).wt_pop.sum()
        d = data.reindex(insh.index)
        nmiss = d["pop"].isna().sum()
        pop = (d["pop"] * insh).sum()
        pov = (d["pov"] * insh).sum()
        povu = (d["povu"] * insh).sum()
        blk = (d["black"] * insh).sum()
        # stability score, as for the screen
        core = insh[insh >= 0.8].index
        a = (d.loc[core, "pop"] * insh[core]).sum() / pop if pop else np.nan
        b = (d.loc[core, "pop"] * insh[core]).sum() / d.loc[core, "pop"].sum() if d.loc[core, "pop"].sum() else np.nan
        fit = min(a, b) * LANDMATCH[cid]
        # standardized cross-check
        g = [gj2010(t) for t in t10]
        sp = std.reindex(g)[f"CL8AA{y}"].sum()
        sb = std.reindex(g)[f"CM1AB{y}"].sum()
        note = (f"crosswalk wt_pop; {len(insh)} source tracts; standardized check pop {sp:,.0f}, "
                f"pct Black {ratio(sb, sp):.1f}" + (f"; {nmiss} source tracts without data" if nmiss else ""))
        add_hist(cid, y, pop, pov, povu, blk, fit, note)

# 2010: census standardized counts (= 2010 tracts), poverty from ACS 2008-2012 on 2010 tracts
for cid, t10 in SETS10.items():
    g = [gj2010(t) for t in t10]
    s = std.reindex(g)
    pop, blk = s.CL8AA2010.sum(), s.CM1AB2010.sum()
    pv = []
    for c in sorted({t[:5] for t in t10}):
        pv.append(census(2012, ["B17001_001E", "B17001_002E"], "tract:*", f"state:{c[:2]} county:{c[2:]}", "pov"))
    pv = pd.concat(pv)
    pv.index = pv.state + pv.county + pv.tract
    pv = pv.reindex(t10)
    note = f"2010 census on {len(t10)} 2010 tracts; poverty ACS 2008-2012; fit = 2010-2020 land match"
    if pv.B17001_001E.isna().any():
        note += f"; {pv.B17001_001E.isna().sum()} tracts missing ACS 2012"
    add_hist(cid, 2010, pop, pv.B17001_002E.sum(), pv.B17001_001E.sum(), blk, LANDMATCH[cid], note)
    add(cid, "population", "2020 census", s.CL8AA2020.sum(), LANDMATCH[cid], "2020 census standardized to 2010 tracts")
    add(cid, "pct_black", "2020 census", ratio(s.CM1AB2020.sum(), s.CL8AA2020.sum()), LANDMATCH[cid],
        "2020 census standardized to 2010 tracts")

# ACS 2020-2024 on own tracts
for cid, tracts in SETS.items():
    s = acs.reindex(tracts).sum(numeric_only=True)
    add_hist(cid, "2020-2024", s["B02001_001E"], s["B17001_002E"], s["B17001_001E"], s["B02001_003E"], 1.0,
             "ACS on own 2020 tracts; B02001, B17001")

# 1970 and 1980: map overlay
cb = gpd.read_file(ROOT / "data/raw/tiger/cb_2020_us_tract_500k.shp")
cb = cb[cb.GEOID.str[:5].isin(counties)].to_crs(5070)
for y in (1970, 1980):
    shp = gpd.read_file(ROOT / f"data/raw/nhgis/extract/nhgis0010_shape/US_tract_{y}_conflated.shp")
    shp = shp[shp.NHGISST.isin({c[:2] + "0" for c in counties})].to_crs(5070)
    data = nominal_year(y)
    for cid, tracts in SETS.items():
        outline = cb[cb.GEOID.isin(tracts)].union_all()
        cand = shp[shp.intersects(outline)].copy()
        if cand.empty:
            add_hist(cid, y, np.nan, np.nan, np.nan, np.nan, np.nan, f"no {y} tracts here (area not tracted)")
            continue
        cand["a"] = cand.area
        cand["ov"] = cand.intersection(outline).area
        sel = cand[cand.ov / cand.a >= 0.5]
        if sel.empty:
            add_hist(cid, y, np.nan, np.nan, np.nan, np.nan, np.nan,
                     f"no {y} tract has half its area inside (best {(cand.ov / cand.a).max():.2f})")
            continue
        fit = sel.ov.sum() / sel.a.sum()
        cover = sel.ov.sum() / outline.area
        d = data.reindex(sel.GISJOIN)
        nmiss = d["pop"].isna().sum()
        note = (f"{len(sel)} tracts {sorted(sel.GISJOIN)}; they cover {cover:.0%} of outline"
                + (f"; {nmiss} without data" if nmiss else "")
                + ("; FIT UNDER 0.8" if fit < 0.8 else ""))
        add_hist(cid, y, d["pop"].sum(min_count=1), d["pov"].sum(min_count=1), d["povu"].sum(min_count=1),
                 d["black"].sum(min_count=1), fit, note)

# flag fits under 0.8 in all years
# ---------------------------------------------------------------- USALEEP + CHR
ule_f = CACHE / "US_A.CSV"
if not ule_f.exists():
    r = requests.get("https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NVSS/USALEEP/CSV/US_A.CSV", timeout=300)
    r.raise_for_status()
    ule_f.write_bytes(r.content)
ule = pd.read_csv(ule_f, dtype={"Tract ID": str})
ule["geoid"] = ule["Tract ID"].str.zfill(11)
ule = ule.set_index("geoid")["e(0)"]

chr_ = pd.read_csv(ROOT / "data/raw/chr/analytic_supplement_20260325.csv", dtype=str, low_memory=False)
chr_ = chr_.set_index("fipscode")
chr_le = pd.to_numeric(chr_["v147_rawvalue"], errors="coerce")
us_le = chr_le.get("00000")
add("US", "life_expectancy_chr", "2021-2023", us_le, note="CHR v147 fipscode 00000")

for cid, tracts in SETS.items():
    pop = acs.reindex(tracts)["B01003_001E"]
    main = pop.groupby(pop.index.str[:5]).sum().idxmax()
    add(cid, "life_expectancy_chr_main_county", "2021-2023", chr_le.get(main), note=f"county {main}")
    t10 = SETS10[cid]
    p10 = std.reindex([gj2010(t) for t in t10]).CL8AA2010.values
    e = ule.reindex(t10).values
    cov = p10[~np.isnan(e)].sum() / p10.sum() if p10.sum() else 0
    usal = np.nansum(e * p10) / p10[~np.isnan(e)].sum() if cov > 0 else np.nan
    add(cid, "life_expectancy_usaleep", "2010-2015", usal, cov,
        f"{(~np.isnan(e)).sum()} of {len(t10)} 2010 tracts with estimate")
    if cov >= 0.8:
        add(cid, "life_expectancy", "key", usal, cov, "USALEEP (coverage >= 80%)")
    else:
        add(cid, "life_expectancy", "key", chr_le.get(main), cov, f"CHR county {main} (USALEEP coverage {cov:.0%})")

# ---------------------------------------------------------------- PLACES
MEAS = ["GHLTH", "DIABETES", "BPHIGH", "MHLTH"]


def places(dataset, where, tag):
    out, off = [], 0
    while True:
        d = cached_json(f"places_{tag}_{off}.json", f"https://data.cdc.gov/resource/{dataset}.json",
                        {"$select": "locationid,stateabbr,measureid,data_value,totalpop18plus,datavaluetypeid",
                         "$where": where, "$limit": 50000, "$offset": off, "$order": "locationid,measureid"})
        out += d
        if len(d) < 50000:
            break
        off += 50000
    df = pd.DataFrame(out)
    df["data_value"] = pd.to_numeric(df.data_value, errors="coerce")
    df["totalpop18plus"] = pd.to_numeric(df.totalpop18plus.astype(str).str.replace(",", ""), errors="coerce")
    return df[df.datavaluetypeid == "CrdPrv"]


mlist = ",".join(f"'{m}'" for m in MEAS)
p25 = places("cwsq-ngmh", f"measureid in({mlist})", "2025")
p24 = places("ai6z-tcin", f"measureid in({mlist}) AND stateabbr='KY'", "2024ky")


def wavg(df):
    df = df.dropna(subset=["data_value", "totalpop18plus"])
    return (df.data_value * df.totalpop18plus).sum() / df.totalpop18plus.sum()


for m in MEAS:
    add("US", f"places_{m}", "2025", wavg(p25[p25.measureid == m]), note=f"{p25[p25.measureid == m].locationid.nunique()} tracts")

for cid, tracts in SETS.items():
    src, rel_ = (p24, "2024") if tracts[0][:2] == "21" else (p25, "2025")
    for m in MEAS:
        d = src[(src.measureid == m) & src.locationid.isin(tracts)]
        miss = sorted(set(tracts) - set(d.locationid))
        add(cid, f"places_{m}", rel_, wavg(d), note=f"PLACES {rel_}" + (f"; missing tracts {miss}" if miss else ""))

res = pd.DataFrame(rows)
res["fit"] = res.fit.astype(float)
flag = res.measure.isin(["population", "poverty_rate", "pct_black"]) & (res.fit < 0.8)
res.loc[flag & ~res.note.str.contains("FIT UNDER"), "note"] += "; FIT UNDER 0.8"
# history 2020-2024 poverty duplicates the key-measure row; keep the history copy (it carries a fit)
res = res.sort_values("fit", na_position="last").drop_duplicates(["cand_id", "measure", "year"]).sort_index()
res["value"] = pd.to_numeric(res.value, errors="coerce").round(3)
res["fit"] = res.fit.round(3)
res.to_csv(OUT / "results.csv", index=False)
for k, v in SETS10.items():
    print(k, "2010 tracts:", ";".join(v), "land match", round(LANDMATCH[k], 3))
print(len(res), "rows;", res.value.notna().sum(), "values")
