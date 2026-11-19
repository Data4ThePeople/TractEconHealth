"""Key measures table for a spotlight post, as inline-styled HTML for a `::: html` slice.
Usage: python scripts/82_key_table.py U047 "West Dayton"  -> prints the HTML (also saved to analysis/spotlight/key_tables/<id>.html)
Left: 5 economic measures. Right: 5 health measures. Each row shows the neighborhood and the U.S.
The two halves sit side by side on a wide screen and stack on a phone (flex-wrap).
"""
import sys
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT

cid, name = sys.argv[1], sys.argv[2]
k = pd.read_csv(ROOT / "analysis/spotlight/key_measures.csv")
k = k[k.cand_id == cid]
LABEL = {"Median household income": "Median household income", "Poverty rate (%)": "People in poverty",
         "Unemployment rate (%)": "Unemployment rate", "Households on SNAP (%)": "Households on SNAP",
         "Homes vacant (%)": "Homes vacant", "Life expectancy (years)": "Life expectancy",
         "Fair or poor health (%)": "Adults in fair or poor health", "Diabetes (%)": "Adults with diabetes",
         "High blood pressure (%)": "Adults with high blood pressure", "Frequent mental distress (%)": "Adults with frequent mental distress"}

def fmt(m, v):
    if m.startswith("Median"): return f"${round(v, -2):,.0f}"
    if m.startswith("Life"): return f"{v:.1f} years"
    return f"{v:.0f}%"

BG, INK, DIM, LINE, HEAD = "#181A1B", "#BBBDC0", "#8A9098", "#2A2D2F", "#E4E5E7"
def half(side, title):
    rows = "".join(
        f'<tr><td style="padding:7px 8px 7px 0;border-top:1px solid {LINE};color:{INK}">{LABEL[r.measure]}</td>'
        f'<td style="padding:7px 8px;border-top:1px solid {LINE};text-align:right;color:{HEAD};font-weight:600;white-space:nowrap">{fmt(r.measure, r.value)}</td>'
        f'<td style="padding:7px 0 7px 8px;border-top:1px solid {LINE};text-align:right;color:{DIM};white-space:nowrap">{fmt(r.measure, r.us_value)}</td></tr>'
        for r in k[k.side == side].itertuples())
    return (f'<div style="flex:1 1 300px;min-width:280px">'
            f'<table style="width:100%;border-collapse:collapse;font-size:15px;line-height:1.35">'
            f'<thead><tr><th style="text-align:left;padding:0 8px 8px 0;color:{HEAD};font-size:16px">{title}</th>'
            f'<th style="text-align:right;padding:0 8px 8px;color:{HEAD};font-size:13px;font-weight:600">{name}</th>'
            f'<th style="text-align:right;padding:0 0 8px 8px;color:{DIM};font-size:13px;font-weight:600">U.S.</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div>')

le_src = k[k.measure == "Life expectancy (years)"].source.iloc[0]
le_note = "life expectancy 2010-2015 (USALEEP)" if le_src.startswith("USALEEP") else "life expectancy 2021-2023 for the county (County Health Rankings)"
html = (f'<div style="background:{BG};color:{INK};font-family:Helvetica Neue,Helvetica,Arial,sans-serif;padding:18px 20px;border-radius:6px">'
        f'<div style="display:flex;flex-wrap:wrap;gap:20px 36px">{half("economic", "Economy")}{half("health", "Health")}</div>'
        f'<p style="margin:14px 0 0;font-size:12px;color:{DIM};line-height:1.45">Sources: Census Bureau, American Community Survey 2020-2024; '
        f'CDC PLACES {"2024" if "2024" in k[k.side == "health"].source.iloc[-1] else "2025"} (model estimates for adults); {le_note}. '
        f'Built by Data 4 The People.</p></div>')
out = ROOT / "analysis/spotlight/key_tables"; out.mkdir(exist_ok=True)
(out / f"{cid}.html").write_text(html)
print(html)
