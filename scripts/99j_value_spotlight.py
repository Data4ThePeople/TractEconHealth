"""Median value of owner-occupied homes in a spotlight and its county, 1980 to 2020-2024, in 2024 dollars.
Medians cannot be added across tracts, so each area's median is estimated from the summed value distribution by linear
interpolation within the bracket holding the middle home (the Census Bureau's method for combined areas).
Tables: 1980 STF1 NT38 (owner-occupied noncondominium units), 1990 STF1 NH23 (specified owner-occupied units),
2000 SF3 NH074B (specified owner-occupied units), ACS B25075 (owner-occupied units) for 2008-2012 and 2020-2024.
"Specified" units leave out homes on 10+ acres and homes with a business or medical office, so the series is close but not identical.
Values are owners' own estimates. Dollars adjusted with the CPI-U annual average (BLS): 1980 82.4, 1990 130.7, 2000 172.2,
2012 229.594, 2024 313.689. Geography and fit rules as in scripts/99e_labor_spotlight.py.
Run: python scripts/99j_value_spotlight.py U034   Output: analysis/spotlight/value_<out>.csv
"""
import sys, re
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, requests
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from common import RAW, ROOT
from d4tp_env import read_env_file
KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
NH = RAW / "nhgis"
AREAS = {"U034": dict(name="North Birmingham", st="01", co="073", nst="Alabama", nco="Jefferson", cmp="Jefferson County", out="northbirmingham")}
CID = sys.argv[1] if len(sys.argv) > 1 else "U034"; A = AREAS[CID]
CPI = {"1980": 82.4, "1990": 130.7, "2000": 172.2, "2008-2012": 229.594, "2020-2024": 313.689}
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[CID].tracts.split(";")
OUTLINE = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]).set_index("GEOID").loc[T20].to_crs("ESRI:102003").unary_union

def overlay(shp, ids):
    s = gpd.read_file(shp, columns=["GISJOIN"]).set_index("GISJOIN")
    s = s.set_crs("ESRI:102003", allow_override=True) if s.crs is None else s.to_crs("ESRI:102003")
    s = s[s.index.isin(ids)]; hits = s[s.intersects(OUTLINE)]
    ch = hits[hits.intersection(OUTLINE).area / hits.area >= 0.5]; u = ch.unary_union
    return list(ch.index), round(u.intersection(OUTLINE).area / u.union(OUTLINE).area, 3)

def bounds(label):
    """Bracket edges from a label like 'Less than $10,000', '$10,000 to $14,999', '$500,000 or more'."""
    n = [float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", label)]
    if "Less than" in label or "less than" in label: return 0.0, n[0]
    if "or more" in label: return n[0], None
    return n[0], n[1] + 1

def median(counts, edges):
    c = np.array(counts, float); tot = c.sum(); half = tot / 2; cum = 0.0
    for k, (lo, hi) in zip(c, edges):
        if cum + k >= half:
            if hi is None: return lo  # middle home is in the open top bracket: report its floor
            return lo + (half - cum) / k * (hi - lo)
        cum += k
    return np.nan

rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig", usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
p = rel[rel.GEOID_TRACT_20.isin(T20)]; sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
S10 = list(sh.index[sh >= 0.5])
cw = {y: pd.read_csv(NH / f"nhgis_tr{y}_tr2010.csv", dtype={f"tr{y}gj": str, "tr2010ge": str}, usecols=[f"tr{y}gj", "tr2010ge", "wt_ownhu"]) for y in (1990, 2000)}  # owner-occupied unit weights
rows = []
for y in (1980, 1990, 2000):
    f = next((NH / "extract_value").rglob(f"*_{y}_tract.csv"))
    lab = pd.read_csv(f, encoding="latin-1", nrows=1).iloc[0].to_dict()
    d = pd.read_csv(f, encoding="latin-1", low_memory=False, skiprows=[1]).set_index("GISJOIN")
    vc = [c for c, l in lab.items() if isinstance(l, str) and "$" in l and len(c) == 6 and c[-3:].isdigit()]
    edges = [bounds(lab[c]) for c in vc]
    if y == 1980:
        ids, fit = overlay(NH / "extract" / "nhgis0010_shape" / "US_tract_1980_conflated.shp", d.index); wb = d.reindex(ids)[vc].sum()
    else:
        c = cw[y]; c = c[c.tr2010ge.isin(S10)]; w = "wt_ownhu"; fit = None
        wb = d.reindex(c[f"tr{y}gj"])[vc].mul(c[w].to_numpy(), axis=0).sum()
    n = d.reset_index(); n = n[(n.STATE == A["nst"]) & (n.COUNTY.astype(str).str.replace(" County", "", regex=False).str.strip().str.lower() == A["nco"].lower())][vc].sum()
    for area, s, fl in ((A["name"], wb, fit), (A["cmp"], n, None)):
        m = median(s.values, edges); rows.append(dict(year=str(y), area=area, homes=round(s.sum()), median_nominal=round(m), fit=fl))
for year, tracts, lb in ((2012, S10, "2008-2012"), (2024, T20, "2020-2024")):
    meta = requests.get(f"https://api.census.gov/data/{year}/acs/acs5/groups/B25075.json", timeout=60).json()["variables"]
    vc = sorted([k for k in meta if k.endswith("E") and k != "B25075_001E" and "$" in meta[k]["label"]])
    r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params={"get": ",".join(vc), "for": "tract:*", "in": f"state:{A['st']} county:{A['co']}", "key": KEY}, timeout=120)
    r.raise_for_status(); j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d["geoid"] = A["st"] + A["co"] + d.tract
    for c in vc: d[c] = pd.to_numeric(d[c])
    edges = [bounds(meta[k]["label"].split("!!")[-1]) for k in vc]
    for area, dd in ((A["name"], d[d.geoid.isin(tracts)]), (A["cmp"], d)):
        s = dd[vc].sum(); rows.append(dict(year=lb, area=area, homes=int(s.sum()), median_nominal=round(median(s.values, edges)), fit=None))
out = pd.DataFrame(rows)
out["median_2024usd"] = (out.median_nominal * 313.689 / out.year.map(CPI)).round(-2)
out.to_csv(ROOT / f"analysis/spotlight/value_{A['out']}.csv", index=False); print(out.to_string(index=False))
