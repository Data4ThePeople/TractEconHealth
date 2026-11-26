"""Locator map for El Segundo Barrio: the six tracts, the city of El Paso, the U.S.-Mexico border along the Rio Grande,
and Ciudad Juarez across it, with an inset of Texas. Also measures how far the tracts are from the border.

Inputs: 2020 tracts (cb_2020_us_tract_500k); state outlines (cb_2020_us_state_500k: the outer edge of Texas and New Mexico
together is the international border); downtown marker at San Jacinto Plaza (31.7587, -106.4869); TIGER/Line 2024 roads, El Paso County
(interstates and U.S. highways, MTFCC S1100 and S1200 with an I- or US prefix).
Distances in UTM zone 13N meters: the farthest point of the six tracts from the border, and the tract centroids.
Output: posts/spotlight-el-segundo-barrio/images/00b-locator.png; prints distances.
"""
import sys
from pathlib import Path
import geopandas as gpd, pandas as pd, matplotlib.pyplot as plt
from shapely.geometry import box
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW
from plot_style import use_house_style, titleblock, credit, INK, INK_DIM, MUTED, GRID, BLUE, MAGENTA, SURFACE

use_house_style(); CRS = "EPSG:32613"; MI = 1609.344
T20 = pd.read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U028"].tracts.split(";")
tr = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").query("GEOID in @T20").to_crs(CRS)
st = gpd.read_file(f"zip://{RAW / 'tiger' / 'cb_2020_us_state_500k.zip'}").to_crs(CRS)
us = st[st.STUSPS.isin(["TX", "NM"])].union_all()
rd = gpd.read_file(f"zip://{RAW / 'tiger' / 'roads' / 'tl_2024_48141_roads.zip'}")
rd = rd[rd.MTFCC.isin(["S1100", "S1200"]) & rd.FULLNAME.fillna("").str.match(r"^(I-|US Hwy)")].to_crs(CRS)

hood = tr.union_all(); c = hood.centroid
frame = box(c.x - 9000, c.y - 6500, c.x + 9000, c.y + 6500)
border = us.boundary.intersection(frame.buffer(20000))  # outer edge of Texas + New Mexico = the international border here
far = max(border.distance(gpd.GeoSeries([p for g in [hood] for p in [g]]).iloc[0].exterior.interpolate(i / 400, normalized=True)) for i in range(401))
cent = tr.centroid.distance(border)
print(f"farthest point of the tracts from the border: {far:.0f} m = {far / MI:.2f} mi; tract centroids: {[round(v / MI, 2) for v in cent]}")

fig = plt.figure(figsize=(10, 7.6)); fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.07)
ax = fig.add_axes([0.02, 0.07, 0.96, 0.75])
mex = frame.difference(us)
gpd.GeoSeries([mex], crs=CRS).plot(ax=ax, color="#2f3337", lw=0)
gpd.GeoSeries([frame.intersection(us)], crs=CRS).plot(ax=ax, color=SURFACE, lw=0)
rd.clip(frame).plot(ax=ax, color=INK_DIM, lw=1.1, alpha=0.8)
tr.plot(ax=ax, color=MAGENTA, alpha=0.55, lw=0); tr.dissolve().boundary.plot(ax=ax, color=MAGENTA, lw=2)
gpd.GeoSeries([border], crs=CRS).plot(ax=ax, color=BLUE, lw=2.4)
fx0, fy0, fx1, fy1 = frame.bounds; ax.set_xlim(fx0, fx1); ax.set_ylim(fy0, fy1); ax.set_axis_off()
lab = lambda x, y, s, **k: ax.annotate(s, (x, y), ha="center", va="center", color=k.pop("color", INK), fontsize=k.pop("fs", 10.5), **k)
lab(c.x - 500, c.y - 4200, "Ciudad Juárez, Mexico", fs=13, color=INK_DIM)
lab(c.x - 1500, c.y + 4600, "El Paso, Texas", fs=13, color=INK_DIM)
lab(c.x - 7600, c.y + 3400, "New\nMexico", fs=10, color=MUTED)
ax.annotate("El Segundo Barrio\nand Chamizal", (c.x + 1500, c.y + 200), xytext=(c.x + 4800, c.y + 3600), ha="center", va="center", color=INK, fontsize=11, fontweight="bold", arrowprops=dict(arrowstyle="-", color=INK_DIM, lw=1))
from pyproj import Transformer
dx, dy = Transformer.from_crs("EPSG:4326", CRS, always_xy=True).transform(-106.4869, 31.7587)  # San Jacinto Plaza, downtown
ax.plot([dx], [dy], marker="o", ms=6, color=INK, mec=SURFACE); ax.annotate("Downtown", (dx, dy), xytext=(10, 12), textcoords="offset points", ha="left", color=INK, fontsize=10)
lab(c.x + 3600, c.y - 3300, "Rio Grande and\nU.S.-Mexico border", color=BLUE, fs=10)
# inset: Texas
ins = fig.add_axes([0.80, 0.62, 0.17, 0.2]); tx = st[st.STUSPS == "TX"]
tx.plot(ax=ins, color="#2c3033", lw=0); tx.boundary.plot(ax=ins, color=MUTED, lw=0.6)
ins.plot([c.x], [c.y], marker="o", ms=7, color=MAGENTA, mec=SURFACE); ins.set_axis_off()
ins.annotate("Texas", (0.55, 0.45), xycoords="axes fraction", color=INK_DIM, fontsize=9, ha="center")
titleblock(fig, "The neighborhood sits on the border",
           f"El Segundo Barrio and Chamizal (pink), just south of downtown El Paso. No part of the six tracts is more than\n"
           f"{far / MI:.1f} miles from the Rio Grande, which is the border with Ciudad Juárez. Gray lines are interstates and U.S. highways.")
credit(fig, "Source: Census Bureau 2020 tracts and state boundaries, TIGER/Line 2024 roads.")
fig.savefig(ROOT / "posts/spotlight-el-segundo-barrio/images/00b-locator.png"); plt.close(fig)
