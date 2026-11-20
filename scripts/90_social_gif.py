"""Social GIF for income-health-viz: screenshots of the built chart (dist/index.html), one per view,
stepping through health measures against median household income, then counties against life expectancy.
Each frame is the real page in dark mode; nothing is interpolated.
Usage: python scripts/90_social_gif.py
Output: posts/income-health-viz/social/income-health-measures.gif
"""
import subprocess, tempfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
VIEWS = ["x=med_hh_income&y=health_index", "x=med_hh_income&y=obesity", "x=med_hh_income&y=diabetes",
         "x=med_hh_income&y=high_bp", "x=med_hh_income&y=depression", "x=med_hh_income&y=smoking",
         "county&x=med_hh_income&y=life_expectancy"]
HOLD_MS, LAST_MS = 1600, 5000
W, H, CROP_H = 1100, 860, 728   # crop drops the notes toggle and credit line

out = ROOT / "posts/income-health-viz/social"; out.mkdir(parents=True, exist_ok=True)
frames = []
with tempfile.TemporaryDirectory() as td:
    for i, v in enumerate(VIEWS):
        png = Path(td) / f"{i}.png"
        subprocess.run([CHROME, "--headless=new", "--force-dark-mode", "--hide-scrollbars", "--disable-gpu",
                        "--virtual-time-budget=5000", f"--window-size={W},{H}", f"--screenshot={png}",
                        f"file://{ROOT}/dist/index.html#{v}"], check=True, capture_output=True)
        im = Image.open(png).convert("RGB").crop((0, 0, W, CROP_H))
        frames.append(im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
gif = out / "income-health-measures.gif"
frames[0].save(gif, save_all=True, append_images=frames[1:], loop=0, optimize=True,
               duration=[HOLD_MS] * (len(frames) - 1) + [LAST_MS])
print(gif, f"{gif.stat().st_size / 1e6:.1f} MB", len(frames), "frames")
