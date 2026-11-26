"""El Segundo Barrio (U028), 1960 to 2000: homes, people per home, crowding, plumbing, foreign born, residence five years
earlier, recent arrivals. El Paso County for comparison. Recent years come from scripts/99u_elsegundo_recent.py.

Inputs: data/raw/nhgis/extract_housing (scripts/99t_fetch_nhgis_housing_nativity.py); 1960 population from
analysis/spotlight/population_early_U028.csv (scripts/98_population_early.py).
Geography (same rules as scripts/99h_industry_spotlight.py): 1960, 1970, 1980 = old tracts with half or more of their area
inside the 2020 outline; 1990, 2000 = NHGIS crosswalks to the 2010 tracts S10 (household weights for housing counts,
population weights for people).
Definitions:
  people per occupied home = people in households / occupied homes; 1960 uses all people (group quarters not in the extract)
  crowded = more than 1.00 person per room, share of occupied homes
  lacking plumbing: 1960 homes lacking or sharing hot water, a private toilet, a bath or running water (sound or deteriorating;
    dilapidated homes are not split by plumbing and are left out of the count but kept in the total), all homes;
    1970 occupied homes lacking one or more facilities; 1980 year-round homes lacking complete plumbing for exclusive use;
    1990 all homes, 2000 occupied homes, lacking complete plumbing. Definitions tighten over time; read the trend, not exact steps.
  same house 5 years earlier: share of people 5 and over living in the same home five years before the census
  recent arrivals: share of foreign-born people who came to the U.S. in the previous ten years (1990, 2000)
Output: analysis/spotlight/housing_nativity_elsegundo.csv
"""
import sys
from pathlib import Path
import geopandas as gpd, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW
NH = RAW / "nhgis"; X = NH / "extract_housing"
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U028"].tracts.split(";")
OUTLINE = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp", columns=["GEOID"]).set_index("GEOID").loc[T20].to_crs("ESRI:102003").union_all()
SHP = {1960: next((NH / "extract_early").rglob("US_tract_1960_conflated.shp")),
       1970: NH / "extract" / "nhgis0010_shape" / "US_tract_1970_conflated.shp", 1980: NH / "extract" / "nhgis0010_shape" / "US_tract_1980_conflated.shp"}
rel = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig", usecols=["GEOID_TRACT_20", "GEOID_TRACT_10", "AREALAND_TRACT_10", "AREALAND_PART"])
for c in ["AREALAND_TRACT_10", "AREALAND_PART"]: rel[c] = rel[c].astype(float)
p = rel[rel.GEOID_TRACT_20.isin(T20)]; sh = p.groupby("GEOID_TRACT_10").AREALAND_PART.sum() / p.groupby("GEOID_TRACT_10").AREALAND_TRACT_10.first()
S10 = list(sh.index[sh >= 0.5])
CW = {y: pd.read_csv(NH / f"nhgis_tr{y}_tr2010.csv", dtype={f"tr{y}gj": str, "tr2010ge": str}, usecols=[f"tr{y}gj", "tr2010ge", "wt_pop", "wt_hu"]) for y in (1990, 2000)}


def overlay(shp, ids):
    s = gpd.read_file(shp, columns=["GISJOIN"]).set_index("GISJOIN")
    s = s.set_crs("ESRI:102003", allow_override=True) if s.crs is None else s.to_crs("ESRI:102003")
    s = s[s.index.isin(ids)]; hits = s[s.intersects(OUTLINE)]
    ch = hits[hits.intersection(OUTLINE).area / hits.area >= 0.5]; u = ch.union_all()
    return list(ch.index), round(u.intersection(OUTLINE).area / u.union(OUTLINE).area, 3)


def load(pattern):
    f = next(X.rglob(pattern)); d = pd.read_csv(f, encoding="latin-1", low_memory=False, skiprows=[1] if "ts_" not in f.name else [1])
    return d


ts = load("*ts_nominal_tract.csv")
ts = ts[ts.STATEFP.astype(str).str.zfill(2) == "48"]
DS = {1960: load("*ds92_1960_tract.csv"), 1970: load("*ds97_1970_tract.csv").merge(load("*ds99_1970_tract.csv")[["GISJOIN"] + [f"C15{k:03d}" for k in range(1, 11)]], on="GISJOIN", how="outer"),
      1980: load("*ds104_1980_tract.csv").merge(load("*ds107_1980_tract.csv")[["GISJOIN"] + [f"DG7{k:03d}" for k in range(1, 9)]], on="GISJOIN", how="outer"),
      1990: load("*ds120_1990_tract.csv").merge(load("*ds123_1990_tract.csv").drop(columns=[c for c in load("*ds120_1990_tract.csv").columns if c != "GISJOIN"], errors="ignore"), on="GISJOIN", how="outer"),
      2000: load("*ds151_2000_tract.csv")}
for y in (1970, 1980, 1990, 2000):
    t = ts[ts.YEAR.astype(str) == str(y)].set_index("GISJOIN")[["AU9AA", "AU9AB", "AT5AA", "AT5AB", "A41AA", "A43AA"]]
    DS[y] = DS[y].set_index("GISJOIN").join(t, how="left").reset_index()
r = lambda a, b: list(f"{a}{k:03d}" for k in b)
# per year: housing columns (weighted by households/homes) and person columns (weighted by population)
SPEC = {
    1960: dict(hu=["CA5001"], occ=r("CAS", range(1, 9)), crowd=["B76004"], crowd_den=r("B76", range(1, 5)), lack=["B9V002", "B9V003", "B9V005", "B9V006"], lack_den=r("B9V", range(1, 8)),
               fb=["B8J001"], same=["B8U001"], same_den=r("B8U", range(1, 8))),
    1970: dict(hu=["A41AA"], occ=["A43AA"], crowd=r("CV7", (4, 5, 6)), crowd_den=r("CV7", range(1, 7)), lack=["CYQ002", "CYQ003"], lack_den=r("CYQ", range(1, 4)),
               fb=["AT5AB"], nat=["AT5AA"], gq=["AU9AA", "AU9AB"], same=["C15001"], same_den=r("C15", range(1, 11))),
    1980: dict(hu=["A41AA"], occ=["A43AA"], crowd=["C8G002", "C8G003"], crowd_den=r("C8G", range(1, 4)), lack=["C8R002"], lack_den=["C8R001", "C8R002"],
               fb=["AT5AB"], nat=["AT5AA"], gq=["AU9AA", "AU9AB"], same=["DG7001"], same_den=r("DG7", range(1, 9))),
    1990: dict(hu=["A41AA"], occ=["A43AA"], crowd=r("ESP", (3, 4, 5)), crowd_den=r("ESP", range(1, 6)), lack=["EZL002"], lack_den=["EZL001", "EZL002"],
               fb=["AT5AB"], nat=["AT5AA"], gq=["AU9AA", "AU9AB"], same=["E3O001"], same_den=r("E3O", range(1, 11)), recent=r("E3F", range(1, 5)), recent_den=r("E3F", range(1, 11))),
    2000: dict(hu=["A41AA"], occ=["A43AA"], crowd=["GA3002", "GA3004"], crowd_den=r("GA3", range(1, 5)), lack=["GA3003", "GA3004"], lack_den=r("GA3", range(1, 5)),
               fb=["AT5AB"], nat=["AT5AA"], gq=["AU9AA", "AU9AB"], same=["GJG001"], same_den=["GJG001", "GJG002"], recent=["GJE001"], recent_den=r("GJE", range(1, 4))),
}
HOUSING = {"hu", "occ", "crowd", "crowd_den", "lack", "lack_den"}
pop1960 = pd.read_csv(ROOT / "analysis/spotlight/population_early_U028.csv").set_index("year").loc[1960, "pop"]
rows = []
for y, sp in SPEC.items():
    d = DS[y].set_index("GISJOIN")
    cols = sorted({c for v in sp.values() for c in v})
    d[cols] = d[cols].apply(pd.to_numeric, errors="coerce")
    if y in SHP:
        ids, fit = overlay(SHP[y], d.index); here = {k: d.reindex(ids)[v].sum().sum() for k, v in sp.items()}
    else:
        c = CW[y][CW[y].tr2010ge.isin(S10)]; fit = None; here = {}
        for k, v in sp.items():
            wt = c.wt_hu if k in HOUSING else c.wt_pop
            here[k] = d.reindex(c[f"tr{y}gj"])[v].sum(axis=1).mul(wt.to_numpy()).sum()
    cty = d.reset_index(); cty = cty[(cty.STATE == "Texas") & (cty.COUNTY.astype(str).str.replace(" County", "", regex=False).str.strip() == "El Paso")] if "STATE" in cty else cty
    county = {k: cty[v].sum().sum() for k, v in sp.items()}
    for area, h in (("El Segundo Barrio", here), ("El Paso County", county)):
        pop = (h["fb"] + h["nat"]) if "nat" in h else (pop1960 if area == "El Segundo Barrio" else None)
        hhpop = pop - h["gq"] if "gq" in h else pop
        row = dict(year=str(y), area=area, fit=fit if area == "El Segundo Barrio" else None, population=round(pop) if pop else None,
                   housing_units=round(h["hu"]), occupied_units=round(h["occ"]), people_per_occupied_home=round(hhpop / h["occ"], 2) if hhpop else None,
                   crowded_pct=round(100 * h["crowd"] / h["crowd_den"], 1), lacking_plumbing_pct=round(100 * h["lack"] / h["lack_den"], 1),
                   foreign_born_pct=round(100 * h["fb"] / pop, 1) if pop else None, same_house_5yr_pct=round(100 * h["same"] / h["same_den"], 1),
                   recent_arrivals_pct=round(100 * h["recent"] / h["recent_den"], 1) if "recent" in h else None)
        rows.append(row)
out = pd.DataFrame(rows); out.to_csv(ROOT / "analysis/spotlight/housing_nativity_elsegundo.csv", index=False)
pd.set_option("display.width", 250); print(out.to_string(index=False))
