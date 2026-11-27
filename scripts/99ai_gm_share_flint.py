"""GM's share of all jobs in Genesee County, 1997 (2026-11-26), for the comparison with Dawson County, Nebraska.

GM workers in Genesee County in 1997: 33,000 (Highsmith 2009 dissertation, p. 9: "GM's workforce in Genesee County
dipped to thirty-three thousand"). All jobs located in Genesee County in 1997: BLS Quarterly Census of Employment and
Wages, SIC-based 1997 annual averages by area, total covered employment, all ownerships (own_code 0, agglvl 26),
https://data.bls.gov/cew/data/files/1997/sic/csv/sic_1997_annual_by_area.zip (saved to data/raw/qcew/).
This matches the Lexington post's method (plant positions over QCEW jobs located in the county).
Output: analysis/spotlight/gm_share_flint.csv
"""
import sys, zipfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, RAW

z = zipfile.ZipFile(RAW / "qcew/sic_1997_annual_by_area.zip")
name = [n for n in z.namelist() if "26049 (Genesee County, Michigan)" in n][0]
d = pd.read_csv(z.open(name), dtype=str)
tot = d[(d.own_code == "0") & (d.agglvl_code == "26")]
assert len(tot) == 1
jobs = int(tot.annual_avg_emplvl.iloc[0]); gm = 33000
out = pd.DataFrame([dict(year=1997, gm_workers=gm, county_jobs_qcew=jobs, gm_share_pct=round(100 * gm / jobs, 2))])
out.to_csv(ROOT / "analysis/spotlight/gm_share_flint.csv", index=False); print(out.to_string())
