"""Food map for the West Dayton post: where people can buy groceries today, and where fast food is.

Stores: USDA SNAP retailer locator, live feed (FNS ArcGIS FeatureServer snap_retailer_location_data), pulled for a box
around West Dayton. USDA store types: Super Store and Supermarket are drawn as full grocery stores; Gem City Market
Cooperative (USDA "Grocery Store" in the live feed, "Large Grocery Store" in the historical file) is drawn on its own.
Other USDA "Grocery Store" entries are drawn as smaller grocery stores.
Closed stores: USDA SNAP retailer historical file 2005-2025: Supermarket, Super Store and Large Grocery Store
records within West Dayton or a half mile of it whose authorization ended, and with no later record at the same address.
Fast food: OpenStreetMap amenity=fast_food (Overpass API). OpenStreetMap is volunteer-mapped and may miss places.
Output: posts/spotlight-west-dayton/images/05-food-map.png, analysis/spotlight/food_westdayton.csv
"""
import json, sys, zipfile
import geopandas as gpd, numpy as np, pandas as pd, requests
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import RAW, ROOT
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, GRID, BLUE, MAGENTA, YELLOW, SURFACE

use_house_style()
BOX = (-84.30, 39.70, -84.15, 39.81)
sets = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id")
T = sets.loc["U047"].tracts.split(";")
g20 = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp")
wd = g20[g20.GEOID.isin(T)].dissolve().to_crs(5070)
W = wd.geometry.iloc[0]

# live SNAP stores
live_f = RAW / "snap" / "snap_live_westdayton.json"
if not live_f.exists():
    u = "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/snap_retailer_location_data/FeatureServer/0/query"
    r = requests.get(u, params={"where": "1=1", "geometry": ",".join(map(str, BOX)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "outSR": 4326, "f": "json", "resultRecordCount": 2000}, timeout=120)
    r.raise_for_status(); live_f.write_text(r.text)
L = pd.DataFrame([f["attributes"] for f in json.loads(live_f.read_text())["features"]])
L = gpd.GeoDataFrame(L, geometry=gpd.points_from_xy(L.Longitude, L.Latitude), crs=4326).to_crs(5070)
L["mi"] = L.distance(W) / 1609.34
L["kind"] = np.select([L.Store_Name.str.contains("Gem City", case=False), L.Store_Type.isin(["Super Store", "Supermarket"]) | L.Store_Name.str.contains("Gettysburg Grocery", case=False),
                       L.Store_Type.eq("Grocery Store"), L.Store_Type.eq("Convenience Store") | L.Store_Name.str.contains("Dollar", case=False)],
                      ["Gem City Market", "Full grocery store", "Smaller grocery store", "Convenience or dollar store"], "other")

# closed full grocery stores, historical file
z = zipfile.ZipFile(RAW / "snap" / "snap-retailer-locator-data2005-2025.zip")
Hh = pd.read_csv(z.open(z.namelist()[0]), low_memory=False)
Hh = Hh[(Hh.State == "OH") & Hh.County.str.upper().str.contains("MONTGOMERY", na=False)]
norm = lambda a: a.str.upper().str.replace(r"[.,]", "", regex=True).str.replace(r"\.0\b", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
Hh["addr"] = norm(Hh["Street Number"].astype(str).str.replace(r"\.0$", "", regex=True) + " " + Hh["Street Name"])
Hh["end"] = pd.to_datetime(Hh["End Date"], errors="coerce", format="mixed")
last = Hh.sort_values("Authorization Date").groupby("addr").tail(1)   # latest record at each address
Hg = gpd.GeoDataFrame(last, geometry=gpd.points_from_xy(last.Longitude, last.Latitude), crs=4326).to_crs(5070)
Hg["mi"] = Hg.distance(W) / 1609.34
big = Hh[Hh["Store Type"].isin(["Supermarket", "Super Store", "Large Grocery Store"])].addr.unique()
closed = Hg[Hg.addr.isin(big) & Hg.end.notna() & (Hg.mi <= 0.5)]
# still open per the live feed at the same street address? then not closed
live_addr = set(norm(L.Store_Street_Address))
# a store still listed today at the same street number with the same name is not a closing (e.g. More For Less, now a convenience store)
live_key = set(norm(L.Store_Street_Address).str.split().str[0] + "|" + L.Store_Name.str.upper().str.split().str[0])
ckey = closed.addr.str.split().str[0] + "|" + closed["Store Name"].str.upper().str.split().str[0]
closed = closed[~closed.addr.isin(live_addr) & ~ckey.isin(live_key)]

# fast food, OpenStreetMap
ff = json.loads((RAW / "osm" / "fastfood_westdayton.json").read_text())["elements"]
F = pd.DataFrame([{"name": e["tags"].get("name"), "kind": e["tags"].get("amenity") or e["tags"].get("shop"),
                   "lat": e.get("lat", e.get("center", {}).get("lat")), "lon": e.get("lon", e.get("center", {}).get("lon"))} for e in ff])
F = gpd.GeoDataFrame(F, geometry=gpd.points_from_xy(F.lon, F.lat), crs=4326).to_crs(5070)
F["mi"] = F.distance(W) / 1609.34
F["inside"] = F.within(W)

# tallies
L["inside"] = L.within(W)
tab = []
for k in ("Full grocery store", "Gem City Market", "Smaller grocery store", "Convenience or dollar store"):
    for lab, m in (("inside", L.inside), ("within 1 mile", (L.mi > 0) & (L.mi <= 1))):
        tab.append(dict(kind=k, where=lab, n=int(((L.kind == k) & m).sum()), names="; ".join(L[(L.kind == k) & m].Store_Name.str.strip())))
for lab, m in (("inside", F.inside & (F.kind == "fast_food")), ("within 1 mile", (F.mi > 0) & (F.mi <= 1) & (F.kind == "fast_food"))):
    tab.append(dict(kind="Fast food (OpenStreetMap)", where=lab, n=int(m.sum()), names="; ".join(F[m].name.fillna("unnamed"))))
for lab, m in (("inside", closed.within(W)), ("within half a mile", ~closed.within(W))):
    tab.append(dict(kind="Closed full grocery (USDA)", where=lab, n=int(m.sum()),
                    names="; ".join(f"{a.strip()} ({b}, closed {c:%Y})" for a, b, c in zip(closed[m]["Store Name"], closed[m].addr, closed[m].end))))
tab = pd.DataFrame(tab); tab.to_csv(ROOT / "analysis/spotlight/food_westdayton.csv", index=False)
pd.set_option("display.max_colwidth", 200); print(tab.to_string(index=False))

# ---- map ----
G4 = 4326
outline = wd.to_crs(G4); minx, miny, maxx, maxy = outline.total_bounds
p = 0.018; x0, x1, y0, y1 = minx - p, maxx + p, miny - p, maxy + p
k = np.cos(np.radians((y0 + y1) / 2))
fig, ax = plt.subplots(figsize=(10, 10 * 0.8 * (y1 - y0) / ((x1 - x0) * k) + 2.3))
H_ = fig.get_figheight(); fig.subplots_adjust(left=0.03, right=0.97, top=1 - 1.4 / H_, bottom=1.3 / H_)
roads = gpd.read_file(RAW / "tiger" / "roads" / "tl_2024_39113_roads.shp", bbox=(x0, y0, x1, y1)).to_crs(G4)
roads[roads.MTFCC.isin(["S1100", "S1200"])].plot(ax=ax, color=GRID, linewidth=1.2)
outline.plot(ax=ax, color=BLUE, alpha=0.10, edgecolor="none"); outline.boundary.plot(ax=ax, color=INK, linewidth=2.2)
Lm0 = L.to_crs(G4); Lm0[Lm0.kind == "Convenience or dollar store"].plot(ax=ax, color=INK_DIM, markersize=12, alpha=0.8, zorder=3)
Fm = F[F.kind == "fast_food"].to_crs(G4); Fm.plot(ax=ax, color=MAGENTA, markersize=22, alpha=0.85, edgecolor=SURFACE, linewidth=0.5, zorder=4)
cg = closed.to_crs(G4); cg.plot(ax=ax, marker="x", color=INK_DIM, markersize=60, linewidth=1.8, zorder=5)
Lm = L.to_crs(G4)
Lm[Lm.kind == "Smaller grocery store"].plot(ax=ax, marker="s", color=YELLOW, markersize=26, alpha=0.7, edgecolor=SURFACE, linewidth=0.5, zorder=5)
Lm[Lm.kind == "Full grocery store"].plot(ax=ax, marker="s", color=YELLOW, markersize=110, edgecolor=INK, linewidth=1.2, zorder=6)
gc = Lm[Lm.kind == "Gem City Market"]; gc.plot(ax=ax, marker="*", color="#7fd18b", markersize=420, edgecolor=SURFACE, linewidth=0.8, zorder=7)
for r in gc.itertuples():
    ax.annotate("Gem City Market", (r.geometry.x, r.geometry.y), xytext=(10, 6), textcoords="offset points", color=INK, fontsize=10.5, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.85), zorder=8)
for r in Lm[(Lm.kind == "Full grocery store")].itertuples():
    if x0 <= r.geometry.x <= x1 and y0 <= r.geometry.y <= y1:
        nm = r.Store_Name.split(" 30")[0].split(" 8")[0].split("  ")[0].title().replace("Kroger 836", "Kroger").strip()
        left = "Gettysburg Grocery" in r.Store_Name
        ax.annotate(nm.replace("Homefull Gettysburg Grocery", "GG's (Homefull, 2025)"), (r.geometry.x, r.geometry.y), xytext=(-8, -12) if left else (8, -12), ha="right" if left else "left", textcoords="offset points", color=INK, fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.8), zorder=8)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / k); ax.set_axis_off()
leg = [Line2D([], [], marker="*", color="none", markerfacecolor="#7fd18b", markersize=16, label="Gem City Market (co-op grocery, 2021)"),
       Line2D([], [], marker="s", color="none", markerfacecolor=YELLOW, markeredgecolor=INK, markersize=10, label="Full grocery store (USDA supermarket or superstore)"),
       Line2D([], [], marker="s", color="none", markerfacecolor=YELLOW, alpha=0.7, markersize=6, label="Smaller grocery store"),
       Line2D([], [], marker="x", color=INK_DIM, markersize=8, lw=0, label="Full grocery store that closed since 2005"),
       Line2D([], [], marker="o", color="none", markerfacecolor=MAGENTA, markersize=7, label="Fast food"),
       Line2D([], [], marker="o", color="none", markerfacecolor=INK_DIM, markersize=5, label="Convenience or dollar store (accepts SNAP)"),
       Line2D([], [], color=INK, lw=2.2, label="West Dayton (six tracts)")]
fig.legend(handles=leg, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.04), frameon=True, facecolor=SURFACE, edgecolor=GRID, labelcolor=INK, fontsize=9.5)
ff_in = int(tab.query("kind == 'Fast food (OpenStreetMap)' and where == 'inside'").n.iloc[0])
full_in = int(tab.query("kind == 'Full grocery store' and where == 'inside'").n.iloc[0])
cv_in = int(tab.query("kind == 'Convenience or dollar store' and where == 'inside'").n.iloc[0])
titleblock(fig, f"Inside West Dayton's six tracts: no full grocery store, and {cv_in} convenience and dollar stores",
           "Stores in and around West Dayton that accept SNAP today. The nearest full grocery store, a Save A Lot, sits just across\nGettysburg Avenue on the tracts' edge. X marks full grocery stores that closed since 2005.")
credit(fig, "Sources: USDA SNAP retailer locator (stores today; closed stores from the 2005-2025 historical file); fast food from OpenStreetMap, which may miss places;\nU.S. Census Bureau TIGER/Line 2024 roads and 2020 tracts.")
fig.savefig(ROOT / "posts/spotlight-west-dayton/images/05-food-map.png"); plt.close(fig)
