"""Population inside a spotlight's 2020 tract outline, 1910 to 1960, from NHGIS tract counts and tract maps.

Same map-overlay rule as 1970 and 1980 in scripts/74_history.py: an old tract is in if half or more of its area falls
inside the outline (2020 tracts, cartographic file). Fit = area of the chosen old tracts that overlaps the outline /
area of their union with the outline. Years with fit under 0.8 are reported but should not be charted.
Inputs: data/raw/nhgis/extract_early (1910, 1930, 1950, 1960; scripts/97_fetch_nhgis_early.py) and
data/raw/nhgis/extract_1940 (scripts/86_fetch_nhgis_1940.py).
Run: python scripts/98_population_early.py U039
Output: analysis/spotlight/population_early_<cand_id>.csv (year, pop, fit, n_tracts)
"""
import sys
import geopandas as gpd, pandas as pd
sys.path.insert(0, __import__("pathlib").Path(__file__).parent.as_posix())
from common import RAW, ROOT

CID = sys.argv[1] if len(sys.argv) > 1 else "U039"
T = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc[CID].tracts.split(";")
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp")
outline = g20[g20.GEOID.isin(T)].to_crs(5070).unary_union
E = RAW / "nhgis" / "extract_early"; E40 = RAW / "nhgis" / "extract_1940"


def table(year):
    base = E40 if year == 1940 else E
    f = next(p for p in base.rglob(f"*_{year}_tract*.csv"))
    lab = pd.read_csv(f, encoding="latin-1", nrows=1)  # row 2 holds labels
    d = pd.read_csv(f, encoding="latin-1", low_memory=False, skiprows=[1])
    labels = lab.iloc[0].to_dict()
    col = next(c for c, l in labels.items() if isinstance(l, str) and ("Total" in l) and "Suppression" not in l and c not in ("GISJOIN",) and pd.api.types.is_numeric_dtype(d[c]))
    return d[["GISJOIN", col]].rename(columns={col: "pop"}), labels[col]


def shape(year):
    base = E40 if year == 1940 else E
    f = next(p for p in base.rglob(f"US_tract_{year}_conflated.shp"))
    return gpd.read_file(f).to_crs(5070)


rows = []
for y in (1910, 1930, 1940, 1950, 1960):
    t, lab = table(y); s = shape(y)
    s = s[s.GISJOIN.isin(t.GISJOIN)]
    hits = s[s.intersects(outline)]
    if not len(hits): rows.append(dict(year=y, pop=None, fit=None, n_tracts=0, label=lab)); continue
    share = hits.intersection(outline).area / hits.area
    ch = hits[share >= 0.5]
    u = ch.unary_union
    fit = u.intersection(outline).area / u.union(outline).area if len(ch) else 0
    pop = t.set_index("GISJOIN")["pop"].reindex(ch.GISJOIN).sum()
    rows.append(dict(year=y, pop=int(pop), fit=round(fit, 3), n_tracts=len(ch), label=lab))
out = pd.DataFrame(rows)
out.to_csv(ROOT / f"analysis/spotlight/population_early_{CID}.csv", index=False)
print(out.to_string(index=False))
