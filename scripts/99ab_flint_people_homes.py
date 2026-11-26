"""North and East Flint (U013): people, children, race and homes, 1990-2020, here, in the rest of Flint and in Genesee County.

Questions:
- How many homes were lost (the draft's hedge that vacancy fell "mostly because empty houses were torn down")?
- Did people, and children in particular, leave faster in the 2010s (the decade of state emergency management and the
  water crisis) than in the 2000s? Either answer is reported; the counts cannot say why people left.
- Who stayed: Black and white residents, 1990-2020.

Inputs:
- NHGIS time series standardized to 2010 tracts (data/raw/nhgis/extract/nhgis0010_csv/nhgis0010_ts_geog2010_tract.csv):
  CL8AA total population, CM1AA White alone, CM1AB Black alone, CM9AA occupied and CM9AB vacant housing units,
  1990, 2000, 2010 and 2020. Areas use 2010 tracts.
- Children under 18: 2000 SF1 P014 (sex by single year of age, under 18 summed), crosswalked to 2010 tracts with
  NHGIS population weights; 2010 and 2020 redistricting files (total minus 18 and over), Census API.
Areas (all on 2010 tracts):
- here: 2010 tracts with half or more of their land inside the eight 2020 tracts (Census relationship file);
- rest of Flint: other 2010 tracts with half or more of their land inside the city of Flint (2020 place boundary);
- Genesee County: all tracts.
Output: analysis/spotlight/people_homes_northflint.csv
"""
import sys
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, requests
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW
sys.path.insert(0, str(Path.home() / ".claude/d4tp-process"))
from d4tp_env import read_env_file

KEY = read_env_file(Path.home() / ".claude/d4tp-process/.env")["CENSUS_API_KEY"]
ST, CO = "26", "049"
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U013"].tracts.split(";")

rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                  usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
rel = rel[rel.GEOID_TRACT_10.str.startswith(ST + CO)]


def s10_for(t20s):
    p = rel[rel.GEOID_TRACT_20.isin(t20s)]
    sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
    return set(sh.index[sh >= 0.5])


HERE = s10_for(T20)
tr = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").query("STATEFP == @ST and COUNTYFP == @CO").to_crs("ESRI:102003")
pl = gpd.read_file(f"zip://{RAW / 'tiger' / 'place' / 'cb_2020_26_place_500k.zip'}").query("NAME == 'Flint'").to_crs("ESRI:102003")
city = pl.union_all()
share = tr.geometry.intersection(city).area / tr.geometry.area
FLINT20 = set(tr.GEOID[share >= 0.5])
REST = s10_for(FLINT20 - set(T20)) - HERE
AREAS = {"North and East Flint": HERE, "Rest of Flint": REST}
print("2010 tracts here:", sorted(HERE)); print("rest of Flint 2010 tracts:", len(REST))

n = pd.read_csv(RAW / "nhgis/extract/nhgis0010_csv/nhgis0010_ts_geog2010_tract.csv", encoding="latin-1", dtype={"GISJOIN": str})
n = n[n.GISJOIN.str.startswith(f"G{ST}0{CO}0")]
n["geoid"] = ST + CO + n.GISJOIN.str[-6:]
rows = []
def put(area, year, measure, value): rows.append(dict(area=area, year=year, measure=measure, value=float(value)))
for y in (1990, 2000, 2010, 2020):
    for area, sel in list(AREAS.items()) + [("Genesee County", set(n.geoid))]:
        d = n[n.geoid.isin(sel)]
        put(area, y, "people", d[f"CL8AA{y}"].sum()); put(area, y, "white", d[f"CM1AA{y}"].sum()); put(area, y, "black", d[f"CM1AB{y}"].sum())
        put(area, y, "occupied_homes", d[f"CM9AA{y}"].sum()); put(area, y, "vacant_homes", d[f"CM9AB{y}"].sum())
        put(area, y, "homes", d[f"CM9AA{y}"].sum() + d[f"CM9AB{y}"].sum())


def api(path, vars_):
    r = requests.get(f"https://api.census.gov/data/{path}", params={"get": ",".join(vars_), "for": "tract:*", "in": f"state:{ST} county:{CO}", "key": KEY}, timeout=120)
    r.raise_for_status(); j = r.json(); d = pd.DataFrame(j[1:], columns=j[0])
    d["geoid"] = ST + CO + d.tract.where(d.tract.str.len() == 6, d.tract + "00")  # 2000 API drops a "00" suffix
    for v in vars_: d[v] = pd.to_numeric(d[v])
    return d


# children: 2000 SF1 P014 (male 003-020, female 024-041 are ages under 1 through 17), crosswalked to 2010 tracts
kids00 = [f"P014{k:03d}" for k in list(range(3, 21)) + list(range(24, 42))]
d0 = api("2000/dec/sf1", ["P001001"] + kids00); d0["kids"] = d0[kids00].sum(axis=1)
x = pd.read_csv(RAW.parent / "raw/nhgis/nhgis_tr2000_tr2010.csv" if (RAW.parent / "raw/nhgis/nhgis_tr2000_tr2010.csv").exists() else RAW / "nhgis/nhgis_tr2000_tr2010.csv",
                dtype={"tr2000ge": str, "tr2010ge": str})
x = x[x.tr2000ge.str.startswith(ST + CO)].merge(d0[["geoid", "kids", "P001001"]], left_on="tr2000ge", right_on="geoid")
x["kids_w"] = x.kids * x.wt_pop; x["pop_w"] = x.P001001 * x.wt_pop
k00 = x.groupby("tr2010ge")[["kids_w", "pop_w"]].sum()
d1 = api("2010/dec/pl", ["P001001", "P003001"]); d1["kids"] = d1.P001001 - d1.P003001; d1 = d1.set_index("geoid")
d2 = api("2020/dec/pl", ["P1_001N", "P3_001N"]); d2["kids"] = d2.P1_001N - d2.P3_001N
# 2020 counts on 2010 tracts: apportion 2020 tracts to 2010 tracts by land share of the 2020 tract
r2 = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig",
                 usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_20", "AREALAND_PART"])
r2 = r2[r2.GEOID_TRACT_20.str.startswith(ST + CO)]
for c in ["AREALAND_TRACT_20", "AREALAND_PART"]: r2[c] = r2[c].astype(float)
r2["w"] = r2.AREALAND_PART / r2.AREALAND_TRACT_20
r2 = r2.merge(d2[["geoid", "kids", "P1_001N"]], left_on="GEOID_TRACT_20", right_on="geoid")
k20 = (r2.assign(kids_w=r2.kids * r2.w)).groupby("GEOID_TRACT_10").kids_w.sum()
for area, sel in list(AREAS.items()) + [("Genesee County", set(d1.index))]:
    put(area, 2000, "children", k00.loc[k00.index.isin(sel), "kids_w"].sum())
    put(area, 2010, "children", d1.loc[d1.index.isin(sel), "kids"].sum())
    put(area, 2020, "children", k20[k20.index.isin(sel)].sum())
# 2020 children for the eight 2020 tracts directly (for the text), as a check on the land-share apportionment
put("North and East Flint (2020 tracts)", 2020, "children", d2[d2.geoid.isin(T20)].kids.sum())
put("North and East Flint (2020 tracts)", 2020, "people", d2[d2.geoid.isin(T20)].P1_001N.sum())

out = pd.DataFrame(rows)
w = out.pivot_table(index=["area", "measure"], columns="year", values="value")
for a in ["North and East Flint", "Rest of Flint", "Genesee County"]:
    for m in ["people", "children", "homes", "occupied_homes", "white", "black"]:
        v = w.loc[(a, m)]
        for y0, y1 in ((1990, 2000), (2000, 2010), (2010, 2020)):
            if pd.notna(v.get(y0)) and pd.notna(v.get(y1)) and v[y0] > 0:
                put(a, f"{y0}-{y1}", f"{m}_change_pct", 100 * (v[y1] / v[y0] - 1))
    for y in (1990, 2000, 2010, 2020):
        put(a, y, "black_pct", 100 * w.loc[(a, "black"), y] / w.loc[(a, "people"), y])
        put(a, y, "vacant_pct", 100 * w.loc[(a, "vacant_homes"), y] / w.loc[(a, "homes"), y])
        if pd.notna(w.loc[(a, "children")].get(y)): put(a, y, "children_pct", 100 * w.loc[(a, "children"), y] / w.loc[(a, "people"), y])
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/people_homes_northflint.csv", index=False)
print(out.pivot_table(index=["area", "measure"], columns="year", values="value").round(1).to_string())
