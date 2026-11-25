"""Share of a spotlight's employed residents who work in manufacturing, 1960 to 2020-2024, with the county for comparison.
Census tract tables by industry of employed residents: 1960 NT50 (B9F, 14+; manufacturing = 003-011), 1970 NT117 (C09,
004-005), 1980 NT65 (DIA, 003-004), 1990 NP77 (E4P, 004-005), 2000 NP049C (GMH, 003 + 016), ACS C24050 (_004 / _001).
These count where residents work by industry, not where the plants are. Geography and fit rules as in scripts/99e_labor_spotlight.py.
Run: python scripts/99h_industry_spotlight.py U034   Output: analysis/spotlight/industry_<out>.csv
"""
import sys
from pathlib import Path
import pandas as pd, geopandas as gpd, requests
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from common import RAW, ROOT
from d4tp_env import read_env_file
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
NH = RAW / "nhgis"
AREAS = {"U034": dict(name="North Birmingham", st="01", co="073", nst="Alabama", nco="Jefferson", cmp="Jefferson County", out="northbirmingham")}
CID = sys.argv[1] if len(sys.argv) > 1 else "U034"; A = AREAS[CID]
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[CID].tracts.split(";")
OUTLINE = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]).set_index("GEOID").loc[T20].to_crs("ESRI:102003").unary_union

def overlay(shp, ids):
    s = gpd.read_file(shp, columns=["GISJOIN"]).set_index("GISJOIN")
    s = s.set_crs("ESRI:102003", allow_override=True) if s.crs is None else s.to_crs("ESRI:102003")
    s = s[s.index.isin(ids)]; hits = s[s.intersects(OUTLINE)]
    ch = hits[hits.intersection(OUTLINE).area / hits.area >= 0.5]; u = ch.unary_union
    return list(ch.index), round(u.intersection(OUTLINE).area / u.union(OUTLINE).area, 3)

def county(d):
    n = d.COUNTY.astype(str).str.strip().str.replace(" County", "", regex=False).str.lower()
    return d[(d.STATE == A["nst"]) & (n == A["nco"].lower())]

SPEC = {1960: ("B9F", range(1, 26), range(3, 12)), 1970: ("C09", range(1, 15), (4, 5)), 1980: ("DIA", range(1, 16), (3, 4)),
        1990: ("E4P", range(1, 18), (4, 5)), 2000: ("GMH", range(1, 27), (3, 16))}
SHP = {1960: next((NH / "extract_early").rglob("US_tract_1960_conflated.shp")),
       1970: NH / "extract" / "nhgis0010_shape" / "US_tract_1970_conflated.shp", 1980: NH / "extract" / "nhgis0010_shape" / "US_tract_1980_conflated.shp"}
cw = {1990: pd.read_csv(NH / "nhgis_tr1990_tr2010.csv", dtype={"tr1990gj": str, "tr2010ge": str}, usecols=["tr1990gj", "tr2010ge", "wt_pop"]),
      2000: pd.read_csv(NH / "nhgis_tr2000_tr2010.csv", dtype={"tr2000gj": str, "tr2010ge": str}, usecols=["tr2000gj", "tr2010ge", "wt_pop"])}
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig", usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
p = rel[rel.GEOID_TRACT_20.isin(T20)]; sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
S10 = list(sh.index[sh >= 0.5])
rows = []
for y, (code, allc, mfg) in SPEC.items():
    f = next((NH / "extract_industry").rglob(f"*_{y}_tract.csv"))
    d = pd.read_csv(f, encoding="latin-1", low_memory=False, skiprows=[1]).set_index("GISJOIN")
    cols_all = [f"{code}{k:03d}" for k in allc]; cols_m = [f"{code}{k:03d}" for k in mfg]
    if y in SHP:
        ids, fit = overlay(SHP[y], d.index); wb = d.reindex(ids)[cols_all].sum()
    else:
        c = cw[y][cw[y].tr2010ge.isin(S10)]; fit = None
        wb = d.reindex(c[f"tr{y}gj"])[cols_all].mul(c.wt_pop.to_numpy(), axis=0).sum()
    for area, s, fl in ((A["name"], wb, fit), (A["cmp"], county(d.reset_index())[cols_all].sum(), None)):
        rows.append(dict(year=str(y), area=area, employed=round(s[cols_all].sum()), mfg=round(s[cols_m].sum()), mfg_share=round(100 * s[cols_m].sum() / s[cols_all].sum(), 1), fit=fl))
for year, tracts, lab in ((2012, S10, "2008-2012"), (2024, T20, "2020-2024")):
    r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params={"get": "C24050_001E,C24050_004E", "for": "tract:*", "in": f"state:{A['st']} county:{A['co']}", "key": KEY}, timeout=120)
    r.raise_for_status(); j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d["geoid"] = A["st"] + A["co"] + d.tract
    for c in ("C24050_001E", "C24050_004E"): d[c] = pd.to_numeric(d[c])
    for area, dd in ((A["name"], d[d.geoid.isin(tracts)]), (A["cmp"], d)):
        rows.append(dict(year=lab, area=area, employed=int(dd.C24050_001E.sum()), mfg=int(dd.C24050_004E.sum()), mfg_share=round(100 * dd.C24050_004E.sum() / dd.C24050_001E.sum(), 1), fit=None))
out = pd.DataFrame(rows); out.to_csv(ROOT / f"analysis/spotlight/industry_{A['out']}.csv", index=False); print(out.to_string(index=False))
