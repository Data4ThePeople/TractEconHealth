"""Locator map for North and East Flint (U013): the eight tracts, the city of Flint, freeways, the Flint River, City Hall
and the former Buick City site, with an inset of Michigan.

Inputs: 2020 tracts (cb_2020_us_tract_500k); Flint city boundary (cb_2020_26_place_500k); state outlines
(cb_2020_us_state_500k); TIGER/Line 2024 roads for Genesee County (interstates and U.S. highways, MTFCC S1100/S1200
with an I- or US prefix); TIGER/Line 2023 area water for Genesee County (Flint River). Points geocoded with the Census
Bureau geocoder: Flint City Hall, 1101 S. Saginaw St. (43.01073, -83.68591); Buick City site, 1051 E. Hamilton
Ave. (43.03544, -83.68590), one of the two addresses RACER Trust lists for the site (tract 980100, the plant site).
Output: posts/spotlight-north-flint/images/00b-locator.png; prints the share of each tract inside the city.
"""
import sys
from pathlib import Path
import geopandas as gpd, pandas as pd, matplotlib.pyplot as plt
from shapely.geometry import box
from pyproj import Transformer
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, GRID, BLUE, MAGENTA, SURFACE

use_house_style(); CRS = "EPSG:32617"
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U013"].tracts.split(";")
tr = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").query("GEOID in @T20").to_crs(CRS)
city = gpd.read_file(f"zip://{RAW / 'tiger' / 'place' / 'cb_2020_26_place_500k.zip'}").query("NAME == 'Flint'").to_crs(CRS)
st = gpd.read_file(f"zip://{RAW / 'tiger' / 'cb_2020_us_state_500k.zip'}").to_crs(CRS)
rd = gpd.read_file(RAW / "tiger" / "roads" / "tl_2024_26049_roads.shp")
rd = rd[rd.MTFCC.isin(["S1100", "S1200"]) & rd.FULLNAME.fillna("").str.match(r"^(I-|US Hwy)")].to_crs(CRS)
wa = gpd.read_file(f"zip://{RAW / 'tiger' / 'water' / 'tl_2023_26049_areawater.zip'}").to_crs(CRS)
river = wa[wa.FULLNAME.fillna("").str.contains("Flint Riv")]

cu = city.union_all()
print({g: round(float(geom.intersection(cu).area / geom.area), 3) for g, geom in zip(tr.GEOID, tr.geometry)})
hood = tr.union_all(); c = hood.centroid
frame = box(c.x - 7500, c.y - 6200, c.x + 7500, c.y + 5200)
tf = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
hall = tf.transform(-83.685913675249, 43.010728093818); buick = tf.transform(-83.685899176594, 43.035440246763)

fig = plt.figure(figsize=(10, 7.8)); ax = fig.add_axes([0.02, 0.07, 0.96, 0.75])
gpd.GeoSeries([frame], crs=CRS).plot(ax=ax, color=SURFACE, lw=0)
city.clip(frame).plot(ax=ax, color="#2a2e31", lw=0)
city.boundary.clip(frame).plot(ax=ax, color=MUTED, lw=1, linestyle="--")
river.clip(frame).plot(ax=ax, color=BLUE, lw=0)
rd.clip(frame).plot(ax=ax, color=INK_DIM, lw=1.2, alpha=0.85)
tr.plot(ax=ax, color=MAGENTA, alpha=0.5, lw=0); tr.dissolve().boundary.plot(ax=ax, color=MAGENTA, lw=2)
fx0, fy0, fx1, fy1 = frame.bounds; ax.set_xlim(fx0, fx1); ax.set_ylim(fy0, fy1); ax.set_axis_off()
ax.plot(*hall, marker="o", ms=7, color=INK, mec=SURFACE); ax.annotate("City Hall", hall, xytext=(-12, -18), ha="right", textcoords="offset points", color=INK, fontsize=10)
ax.plot(*buick, marker="s", ms=8, color=INK, mec=SURFACE)
ax.annotate("Former Buick City\nsite address", buick, xytext=(-120, 95), textcoords="offset points", color=INK, fontsize=10,
            arrowprops=dict(arrowstyle="-", color=INK_DIM, lw=1))
ax.annotate("North and East Flint", (c.x, c.y), xytext=(c.x + 3800, c.y + 4300), ha="center", color=INK, fontsize=11, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=INK_DIM, lw=1))
ax.annotate("Flint River", (c.x - 6200, c.y - 2100), color=BLUE, fontsize=10)
i475 = rd[rd.FULLNAME.str.startswith("I- 475") | rd.FULLNAME.str.startswith("I-475")]
print("I-475 segments:", len(i475))
ax.annotate("I-475", (c.x - 900, c.y + 3700), color=INK_DIM, fontsize=10, fontweight="bold")
ax.annotate("City of Flint\n(dashed line)", (fx0 + 2600, fy0 + 7700), color=MUTED, fontsize=9)
ins = fig.add_axes([0.80, 0.60, 0.17, 0.22]); mi = st[st.STUSPS == "MI"]
mi.plot(ax=ins, color="#2c3033", lw=0); mi.boundary.plot(ax=ins, color=MUTED, lw=0.6)
ins.plot([c.x], [c.y], marker="o", ms=7, color=MAGENTA, mec=SURFACE); ins.set_axis_off()
ins.annotate("Michigan", (0.40, 0.08), xycoords="axes fraction", color=INK_DIM, fontsize=9, ha="center")
titleblock(fig, "North and East Flint, around the old Buick plants",
           "The eight census tracts in this story (pink), on Flint's north and east sides. Gray lines are interstates and U.S.\n"
           "highways, including I-475. The square marks an address RACER Trust lists for the former Buick City site.")
credit(fig, "Source: Census Bureau 2020 tracts and places, TIGER/Line roads and water; Census Bureau geocoder.")
fig.savefig(ROOT / "posts/spotlight-north-flint/images/00b-locator.png"); plt.close(fig)
