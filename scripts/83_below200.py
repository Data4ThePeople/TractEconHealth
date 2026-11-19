"""Share of people below 200% of the federal poverty level, for the 10 spotlight picks and the U.S.

Low income is often defined as below 200% of the poverty line. Poverty alone (below 100%) misses the
working families just above it.

  1990, 2000   NHGIS time series C20, "Persons by Ratio of Income to Poverty Level [9]", nominal tracts and nation.
               Below 200% = AA..AH (under .50 through 1.85-1.99); universe = AA..AI. Moved onto the pick's 2010
               tracts with the NHGIS 1990/2000 -> 2010 crosswalks (population weights), as in 74_history.py.
  2008-2012    ACS C17002 (ratio of income to poverty level), 2010 tracts. Below 200% = _002.._007; universe _001.
  2020-2024    ACS C17002, 2020 tracts.
  1970, 1980   not available at the tract level in NHGIS time series (C19 has only under .75 and under 1.25).
County, state and U.S. values for 2020-2024 come from the same ACS table, for the post's text.
Output: analysis/spotlight/below200.csv (cand_id or area, year, value, universe)
"""
import sys, time, zipfile, io
import pandas as pd, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from common import RAW, ROOT
from d4tp_env import read_env_file

ENV = read_env_file(Path.home() / ".claude/d4tp-process/.env")
OUT = ROOT / "analysis" / "spotlight"
PICKS = ["U047", "U034", "U039", "U028", "U013", "M016", "R007", "R046", "R004", "M014"]
sets = pd.read_csv(OUT / "final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[PICKS]
D = RAW / "nhgis" / "extract_c20"; D.mkdir(parents=True, exist_ok=True)

# ---- NHGIS C20, 1990 and 2000 ----
if not list(D.rglob("*.csv")):
    H = {"Authorization": ENV["IPUMS_API_KEY"], "Content-Type": "application/json"}
    body = {"timeSeriesTables": {"C20": {"years": ["1990", "2000"], "geogLevels": ["tract", "nation"]}},
            "timeSeriesTableLayout": "time_by_column_layout", "dataFormat": "csv_no_header",
            "description": "D4TP spotlight: ratio of income to poverty level"}
    r = requests.post("https://api.ipums.org/extracts?collection=nhgis&version=2", headers=H, json=body, timeout=120)
    if r.status_code >= 300: sys.exit(f"{r.status_code} {r.text[:1500]}")
    n = r.json()["number"]; print("extract", n)
    while True:
        s = requests.get(f"https://api.ipums.org/extracts/{n}?collection=nhgis&version=2", headers=H, timeout=120).json()
        if s["status"] == "completed": break
        if s["status"] in ("failed", "canceled"): sys.exit(str(s)[:1500])
        time.sleep(20)
    z = requests.get(s["downloadLinks"]["tableData"]["url"], headers=H, timeout=600); z.raise_for_status()
    zipfile.ZipFile(io.BytesIO(z.content)).extractall(D)
files = sorted(D.rglob("*.csv"))
tr = next(f for f in files if "tract" in f.name); nat = next(f for f in files if "nation" in f.name)
LOW = ["AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH"]; ALL = LOW + ["AI"]
def c20(df, y):
    return pd.DataFrame({"low": df[[f"C20{c}{y}" for c in LOW]].sum(axis=1, min_count=1),
                         "uni": df[[f"C20{c}{y}" for c in ALL]].sum(axis=1, min_count=1)})
t = pd.read_csv(tr, encoding="latin-1", low_memory=False)
gj = {y: c for y in (1990, 2000) for c in t.columns if c in (f"GJOIN{y}", "GISJOIN")}
N = {y: c20(t, y).set_index(t[gj[y]]).groupby(level=0).sum(min_count=1) for y in (1990, 2000)}
nt = pd.read_csv(nat, encoding="latin-1")

cw = {1990: pd.read_csv(RAW / "nhgis" / "nhgis_tr1990_tr2010.csv", dtype={"tr1990gj": str, "tr2010ge": str}, usecols=["tr1990gj", "tr2010ge", "wt_pop"]),
      2000: pd.read_csv(RAW / "nhgis" / "nhgis_tr2000_tr2010.csv", dtype={"tr2000gj": str, "tr2010ge": str}, usecols=["tr2000gj", "tr2010ge", "wt_pop"])}
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
def s10_of(tr20):
    p = rel[rel.GEOID_TRACT_20.isin(tr20)]
    share = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
    return list(share.index[share >= 0.5])

# ---- ACS C17002 ----
KEY = ENV["CENSUS_API_KEY"]; V = [f"C17002_{i:03d}E" for i in range(1, 9)]
def acs(year, geo_for, geo_in=None):
    p = {"get": ",".join(V), "for": geo_for, "key": KEY}
    if geo_in: p["in"] = geo_in
    r = requests.get(f"https://api.census.gov/data/{year}/acs/acs5", params=p, timeout=120); r.raise_for_status()
    j = r.json(); d = pd.DataFrame(j[1:], columns=j[0]); d[V] = d[V].apply(pd.to_numeric, errors="coerce"); return d
def low(d): return d[V[1:7]].sum(axis=1), d["C17002_001E"]

rows = []
all20 = {g for x in sets.tracts for g in x.split(";")}
cty = sorted({(g[:2], g[2:5]) for g in all20} | {(g[:2], g[2:5]) for x in sets.tracts for g in s10_of(x.split(";"))})
A = {}
for yr in (2012, 2024):
    gone = {2012: {"46102"}, 2024: {"46113"}}[yr]  # Shannon County (46113) became Oglala Lakota (46102) in 2015
    d = pd.concat([acs(yr, "tract:*", f"state:{s} county:{c}") for s, c in cty if s + c not in gone]); d.index = d.state + d.county + d.tract
    A[yr] = d
for cid, r in sets.iterrows():
    tr20 = r.tracts.split(";"); s10 = s10_of(tr20)
    for y in (1990, 2000):
        c = cw[y][cw[y].tr2010ge.isin(s10)]; g = "tr1990gj" if y == 1990 else "tr2000gj"
        v = N[y].reindex(c[g]).mul(c.wt_pop.to_numpy(), axis=0).sum(min_count=1)
        rows.append(dict(area=cid, year=str(y), value=100 * v.low / v.uni, universe=round(v.uni)))
    for yr, ids, lab in ((2012, s10, "2008-2012"), (2024, tr20, "2020-2024")):
        d = A[yr].reindex(ids); lo, un = low(d)
        rows.append(dict(area=cid, year=lab, value=100 * lo.sum() / un.sum(), universe=round(un.sum())))
for y in (1990, 2000):
    v = c20(nt, y).sum()
    rows.append(dict(area="US", year=str(y), value=100 * v.low / v.uni, universe=round(v.uni)))
for yr, lab in ((2012, "2008-2012"), (2024, "2020-2024")):
    d = acs(yr, "us:1"); lo, un = low(d)
    rows.append(dict(area="US", year=lab, value=100 * lo.sum() / un.sum(), universe=round(un.sum())))
# county and state, 2020-2024 (main county of each pick)
MAIN = {"U047": "39113", "U034": "01073", "U039": "24510", "U028": "48141", "U013": "26049", "M016": "28027",
        "R007": "54047", "R046": "46102", "R004": "21189", "M014": "48387"}
cd = acs(2024, "county:*"); cd.index = cd.state + cd.county
sd = acs(2024, "state:*"); sd.index = sd.state
for cid, f in MAIN.items():
    for area, d in ((f, cd.loc[[f]]), (f[:2], sd.loc[[f[:2]]])):
        lo, un = low(d); rows.append(dict(area=area, year="2020-2024", value=100 * lo.sum() / un.sum(), universe=round(un.sum())))
o = pd.DataFrame(rows).drop_duplicates(["area", "year"]); o["value"] = o.value.round(2)
o.to_csv(OUT / "below200.csv", index=False)
print(o[o.area.isin(PICKS + ["US"])].pivot(index="area", columns="year", values="value").round(1).loc[PICKS + ["US"]].to_string())
