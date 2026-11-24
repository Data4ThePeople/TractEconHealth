"""Work in West Baltimore's nine tracts, 1940 to 2020-2024: labor force participation and the share of adults with a job.

Measures (each for West Baltimore and for Baltimore city as a whole):
  lfp        people in the labor force (working or looking for work) / all people of working age
  epop       people with a job / all people of working age
  epop_male  the same for men
  prime_lfp, prime_epop   the same for ages 25 to 54 (1990 on; earlier tract tables have no age detail)
Working age is 14 and over in 1940-1960 and 16 and over from 1970 on (the census definitions changed), so the two
periods do not line up exactly. "With a job" counts civilians employed plus armed forces from 1970 on; in 1940 it
counts people at work and leaves out people on public emergency (relief) work, who are shown separately.

Geography, same rules as the other then-and-now numbers:
  1940, 1950, 1960, 1970, 1980  old tracts chosen by map overlay (half or more of a tract's area inside the 2020 outline)
  1990, 2000                    NHGIS block-based crosswalks to 2010 tracts (population weights), summed over the
                                neighborhood's 2010 tracts
  2008-2012                     ACS on the neighborhood's 2010 tracts; 2020-2024 ACS on its 2020 tracts
Baltimore city: all tracts in the city each year (1990-2000 nominal tracts).
Inputs: NHGIS extracts (extract, extract_1940b, extract_labor_early, extract_labor_age), Census API (ACS B23025, B23001).
Output: analysis/spotlight/labor_westbaltimore.csv
"""
import sys, re
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, requests
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from common import RAW, ROOT
from d4tp_env import read_env_file
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
NH = RAW / "nhgis"
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U039"].tracts.split(";")
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]).set_index("GEOID")
OUTLINE = g20.loc[T20].to_crs("ESRI:102003").unary_union
rows = []


def add(year, area, m, num, den, fit=None, note=""):
    if den and den > 0: rows.append(dict(year=year, area=area, measure=m, value=round(100 * num / den, 1), num=round(num), den=round(den), fit=fit, note=note))


def overlay(shp, ids):
    s = gpd.read_file(shp, columns=["GISJOIN"]).set_index("GISJOIN")
    s = s.set_crs("ESRI:102003", allow_override=True) if s.crs is None else s.to_crs("ESRI:102003")
    s = s[s.index.isin(ids)]
    hits = s[s.intersects(OUTLINE)]
    share = hits.intersection(OUTLINE).area / hits.area
    ch = hits[share >= 0.5]; u = ch.unary_union
    return list(ch.index), round(u.intersection(OUTLINE).area / u.union(OUTLINE).area, 3)


def read_nhgis(f):
    lab = pd.read_csv(f, encoding="latin-1", nrows=1).iloc[0].to_dict()
    d = pd.read_csv(f, encoding="latin-1", low_memory=False, skiprows=[1])
    return d, lab


def city(d):
    c = [c for c in ("COUNTY",) if c in d.columns][0]
    return d[(d.STATE == "Maryland") & (d[c].astype(str).str.strip().isin(["Baltimore City", "Baltimore city"]))]


def cols(lab, *must, exclude=()):
    return [c for c, l in lab.items() if isinstance(l, str) and all(m in l for m in must) and not any(x in l for x in exclude)]


# ---------- 1940, 1950, 1960 (persons 14+), explicit NHGIS codes ----------
# 1940 NT22 (BUX): 001/009 employed, 002/010 public emergency work, 003/011 seeking work, 004-008/012-016 not in labor force (M/F)
# 1950 NT23 (B0N): 001/003 labor force, 002/004 not in labor force; NT25 (B0P): 001/003 civilian employed, 002/004 unemployed
# 1960 NT39 (B82): 001/005 employed civilians, 002/006 unemployed, 003/007 armed forces, 004/008 not in labor force
def early(y, d):
    g = lambda c: d[c].sum()
    if y == 1940:
        m = dict(emp=g("BUX001"), lf=g("BUX001") + g("BUX002") + g("BUX003"), pop=sum(g(f"BUX{k:03d}") for k in range(1, 9)))
        f = dict(emp=g("BUX009"), lf=g("BUX009") + g("BUX010") + g("BUX011"), pop=sum(g(f"BUX{k:03d}") for k in range(9, 17)))
        relief = g("BUX002") + g("BUX010")
    elif y == 1950:
        m = dict(lf=g("B0N001"), pop=g("B0N001") + g("B0N002")); m["emp"] = m["lf"] - g("B0P002")   # armed forces counted as with a job
        f = dict(lf=g("B0N003"), pop=g("B0N003") + g("B0N004")); f["emp"] = f["lf"] - g("B0P004"); relief = None
    else:
        m = dict(emp=g("B82001") + g("B82003"), lf=g("B82001") + g("B82002") + g("B82003")); m["pop"] = m["lf"] + g("B82004")
        f = dict(emp=g("B82005") + g("B82007"), lf=g("B82005") + g("B82006") + g("B82007")); f["pop"] = f["lf"] + g("B82008"); relief = None
    return m, f, relief

f40 = next((NH / "extract_1940b").rglob("*_1940_tract.csv"))
src = {1940: (f40, next((NH / "extract_1940").rglob("US_tract_1940_conflated.shp")))}
for y in (1950, 1960):
    src[y] = (next((NH / "extract_labor_early").rglob(f"*_{y}_tract.csv")), next((NH / "extract_early").rglob(f"US_tract_{y}_conflated.shp")))
for y, (fcsv, fshp) in src.items():
    d, lab = read_nhgis(fcsv)
    ids, fit = overlay(fshp, d.GISJOIN)
    for area, dd, fl in (("West Baltimore", d[d.GISJOIN.isin(ids)], fit), ("Baltimore city", city(d), None)):
        m, f, relief = early(y, dd)
        note = "14+" + ("; with a job excludes public emergency work" if y == 1940 else "")
        add(y, area, "lfp", m["lf"] + f["lf"], m["pop"] + f["pop"], fl, "14+")
        add(y, area, "epop", m["emp"] + f["emp"], m["pop"] + f["pop"], fl, note)
        add(y, area, "epop_male", m["emp"], m["pop"], fl, note)
        if relief is not None: add(y, area, "relief_work", relief, m["pop"] + f["pop"], fl, "14+; public emergency work")

# ---------- 1970-2000 (persons 16+), NHGIS time series nominal tracts ----------
nom = pd.read_csv(NH / "extract" / "nhgis0010_csv" / "nhgis0010_ts_nominal_tract.csv", encoding="latin-1", low_memory=False,
                  dtype={f"GJOIN{y}": str for y in (1970, 1980, 1990, 2000)})
nom = nom[(nom.STATEFP.astype(str).str.zfill(2) == "24")]
def nomsum(y, d):
    g = lambda k: d[f"B84A{k}{y}"].sum()
    return g("A"), g("B") + g("D"), g("A") + g("F")  # labor force, employed (armed + civilian employed), 16+ population
cw = {1990: pd.read_csv(NH / "nhgis_tr1990_tr2010.csv", dtype={"tr1990gj": str, "tr2010ge": str}, usecols=["tr1990gj", "tr2010ge", "wt_pop"]),
      2000: pd.read_csv(NH / "nhgis_tr2000_tr2010.csv", dtype={"tr2000gj": str, "tr2010ge": str}, usecols=["tr2000gj", "tr2010ge", "wt_pop"])}
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig", usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
p = rel[rel.GEOID_TRACT_20.isin(T20)]
sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
S10 = list(sh.index[sh >= 0.5])
for y in (1970, 1980, 1990, 2000):
    d = nom.dropna(subset=[f"GJOIN{y}"]).groupby(f"GJOIN{y}")[[c for c in nom.columns if c.startswith("B84A") and c.endswith(str(y))]].sum(min_count=1)
    cd = nom[nom.COUNTYFP.astype(str).str.zfill(3) == "510"].dropna(subset=[f"GJOIN{y}"]).groupby(f"GJOIN{y}")[[c for c in nom.columns if c.startswith("B84A") and c.endswith(str(y))]].sum(min_count=1)
    if y in (1970, 1980):
        ids, fit = overlay(NH / "extract" / "nhgis0010_shape" / f"US_tract_{y}_conflated.shp", d.index); wb = d.reindex(ids)
    else:
        c = cw[y][cw[y].tr2010ge.isin(S10)]; gj = f"tr{y}gj"; fit = None
        wb = d.reindex(c[gj]).mul(c.wt_pop.to_numpy(), axis=0)
    for area, dd, fl in (("West Baltimore", wb, fit), ("Baltimore city", cd, None)):
        lf, emp, pop = nomsum(y, dd); add(y, area, "lfp", lf, pop, fl, "16+"); add(y, area, "epop", emp, pop, fl, "16+")

# ---------- ACS 2008-2012 and 2020-2024 (16+), and prime age from B23001 ----------
def acs(year, get):
    r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params={"get": ",".join(get), "for": "tract:*", "in": "state:24 county:510", "key": KEY}, timeout=120)
    r.raise_for_status(); j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d["geoid"] = "24510" + d.tract
    for c in get: d[c] = pd.to_numeric(d[c])
    return d.set_index("geoid")
B25 = ["B23025_001E", "B23025_002E", "B23025_004E", "B23025_006E"]
# B23001: male 003-071, female 089-157. Prime age groups 25-29, 30-34, 35-44, 45-54. Each group block: total, in LF, armed, civilian, employed, unemployed, NILF
PR = {"M": [24, 31, 38, 45], "F": [110, 117, 124, 131]}  # first cell (group total) of each prime-age group
def b23(i): return f"B23001_{i:03d}E"
B23 = [b23(s + k) for g in PR.values() for s in g for k in (0, 1, 2, 4)]  # total, in LF, armed forces, civilian employed
for year, tracts, lab in ((2012, S10, "2008-2012"), (2024, T20, "2020-2024")):
    d = acs(year, B25 + B23)
    for area, dd in (("West Baltimore", d.loc[d.index.isin(tracts)]), ("Baltimore city", d)):
        s = dd.sum()
        add(lab, area, "lfp", s.B23025_002E, s.B23025_001E, None, "16+"); add(lab, area, "epop", s.B23025_004E + s.B23025_006E, s.B23025_001E, None, "16+")
        tot = sum(s[b23(x)] for g in PR.values() for x in g); lfx = sum(s[b23(x + 1)] for g in PR.values() for x in g)
        empx = sum(s[b23(x + 2)] + s[b23(x + 4)] for g in PR.values() for x in g)
        add(lab, area, "prime_lfp", lfx, tot, None, "25-54"); add(lab, area, "prime_epop", empx, tot, None, "25-54")
        mt = sum(s[b23(x)] for x in PR["M"]); me = sum(s[b23(x + 2)] + s[b23(x + 4)] for x in PR["M"])
        add(lab, area, "prime_epop_male", me, mt, None, "men 25-54")

# ---------- 2000 prime age (NHGIS SF3 PCT35: GYA labor force status, GYC employment status, by sex and age) ----------
# Prime-age groups: 25-29, 30-34, 35-44, 45-54 = GYA 007-014 (male), 033-040 (female); GYC same positions.
# 1990 has no 25-54 split at tract level (NP66 is 16-64 only), so prime age starts in 2000.
# GYC counts civilians, so armed forces in the labor force are counted as in the labor force but not as employed (very few here).
d, lab = read_nhgis(next((NH / "extract_labor_age").rglob("*_2000_tract.csv")))
lfc = [f"GYA{k:03d}" for k in list(range(7, 15, 2)) + list(range(33, 41, 2))]
nlc = [f"GYA{k:03d}" for k in list(range(8, 15, 2)) + list(range(34, 41, 2))]
emc = [f"GYC{k:03d}" for k in list(range(7, 15, 2)) + list(range(33, 41, 2))]
mlf = [f"GYA{k:03d}" for k in range(7, 15, 2)]; mnl = [f"GYA{k:03d}" for k in range(8, 15, 2)]; mem = [f"GYC{k:03d}" for k in range(7, 15, 2)]
c = cw[2000][cw[2000].tr2010ge.isin(S10)]
D = d.set_index("GISJOIN")
wb = D.reindex(c.tr2000gj)[lfc + nlc + emc].mul(c.wt_pop.to_numpy(), axis=0).sum()
for area, s_ in (("West Baltimore", wb), ("Baltimore city", city(d)[lfc + nlc + emc].sum())):
    tot = s_[lfc].sum() + s_[nlc].sum()
    add(2000, area, "prime_lfp", s_[lfc].sum(), tot, None, "25-54"); add(2000, area, "prime_epop", s_[emc].sum(), tot, None, "25-54")
    add(2000, area, "prime_epop_male", s_[mem].sum(), s_[mlf].sum() + s_[mnl].sum(), None, "men 25-54")

out = pd.DataFrame(rows)
out.to_csv(ROOT / "analysis/spotlight/labor_westbaltimore.csv", index=False)
print(out.pivot_table(index=["measure", "area"], columns="year", values="value", aggfunc="first").to_string())
