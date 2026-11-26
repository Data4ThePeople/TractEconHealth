"""El Segundo Barrio river map: the 1955 USGS topographic map (before the 1963 Chamizal settlement moved the Rio Grande),
with today's six census tracts and today's river channel drawn on top.

Base: USGS Historical Topographic Map Collection, 1:24,000, 1955 (public domain, U.S. government work), two sheets
joined at their shared edge, latitude 31 deg 45 min:
  El Paso, Tex.  .../HistoricalTopo/GeoTIFF/TX/TX_El%20Paso_107857_1955_24000_geo.tif -> data/raw/usgs/TX_El_Paso_1955_24000_geo.tif
  Ysleta NW, Tex.-Chih.  .../HistoricalTopo/GeoTIFF/TX/TX_Ysleta%20NW_117323_1955_24000_geo.tif -> data/raw/usgs/TX_Ysleta_NW_117323_1955.tif
  (prefix https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps). Both are warped to UTM zone 13N for display.
Overlays: 2020 tract boundaries (cartographic file); today's U.S.-Mexico border, from the Texas outline in the Census Bureau's
2020 cartographic state file (cb_2020_us_state_500k), which follows the river's current channel here.
The El Paso sheet's west edge is longitude 106 deg 30 min; the westernmost tip of the tracts lies beyond it and is cut off.
Output: posts/spotlight-el-segundo-barrio/images/01b-river-1955.png
"""
import sys
from pathlib import Path
import geopandas as gpd, numpy as np, rasterio, matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW
from plot_style import use_house_style, titleblock, credit, INK, BLUE, MAGENTA

use_house_style()
T20 = __import__("pandas").read_csv(ROOT / "analysis/spotlight/final_sets.csv", dtype={"tracts": str}).set_index("cand_id").loc["U028"].tracts.split(";")
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from pyproj import Transformer
CRS = "EPSG:32613"
tr = gpd.read_file(RAW / "tiger" / "cb_2020_us_tract_500k.shp").query("GEOID in @T20").to_crs(CRS)
tx = gpd.read_file(f"zip://{RAW / 'tiger' / 'cb_2020_us_state_500k.zip'}").query("STUSPS == 'TX'").to_crs(CRS)
x0, y0, x1, y1 = tr.total_bounds; pad = 700
x0, y0, x1, y1 = 357960, y0 - 500, x1 + pad, y1 + 350  # west edge = the 1955 sheet's neatline
res = 2.5; W, Hh = int((x1 - x0) / res), int((y1 - y0) / res); dst_t = from_origin(x0, y1, res, res)
cols, rows = np.meshgrid(np.arange(W) + 0.5, np.arange(Hh) + 0.5)
_, lat = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform(x0 + cols * res, y1 - rows * res)
img = np.full((Hh, W, 3), 255, np.uint8)
for f, keep in (("TX_Ysleta_NW_117323_1955.tif", lat < 31.75), ("TX_El_Paso_1955_24000_geo.tif", lat >= 31.75)):
    with rasterio.open(RAW / "usgs" / f) as src:
        for b in range(3):
            band = np.zeros((Hh, W), np.uint8)
            reproject(src.read(b + 1), band, src_transform=src.transform, src_crs=src.crs, dst_transform=dst_t, dst_crs=CRS, resampling=Resampling.bilinear)
            img[..., b] = np.where(keep, band, img[..., b])
fig, ax = plt.subplots(figsize=(10, 7.6)); fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.07)
ax.imshow(img, extent=(x0, x1, y0, y1), alpha=0.9)
tr.dissolve().boundary.plot(ax=ax, color=MAGENTA, lw=2.4)
tx.boundary.plot(ax=ax, color=BLUE, lw=2.2, ls="--", zorder=5)
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_axis_off()
titleblock(fig, "Where the Rio Grande ran before 1963",
           "A 1955 federal map. Pink outlines today's six tracts; dashed blue is today's border, in the river's new channel.\n"
           "U.S. land between the 1955 river and the blue line went to Mexico. Cordova Island, at center, was already Mexican;\n"
           "its northern part went to the U.S.")
credit(fig, "Base map: U.S. Geological Survey, El Paso, Tex., 1:24,000, 1955 (public domain). Overlays: Census Bureau 2020 tracts and state boundary.")
fig.savefig(ROOT / "posts/spotlight-el-segundo-barrio/images/01b-river-1955.png", dpi=150); plt.close(fig)
print("saved")
