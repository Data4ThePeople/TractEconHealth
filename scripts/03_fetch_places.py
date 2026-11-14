"""CDC PLACES 2025 release, census tract data (long format, data.cdc.gov cwsq-ngmh).
Pulls every tract and measure with confidence limits and the footnote fields, in pages."""
import io, sys, time
from pathlib import Path
import pandas as pd, requests

OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "places"
URL = "https://data.cdc.gov/resource/cwsq-ngmh.csv"
COLS = ("year,stateabbr,countyfips,countyname,locationname,measureid,measure,category,data_value_type,"
        "data_value,low_confidence_limit,high_confidence_limit,data_value_footnote_symbol,totalpopulation,totalpop18plus")
PAGE = 200_000

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    parts, off = [], 0
    while True:
        cache = OUT / f"page_{off:08d}.csv"
        if not cache.exists():
            for i in range(8):
                try:
                    r = requests.get(URL, params={"$select": COLS, "$order": "locationname,measureid,data_value_type",
                                                  "$limit": PAGE, "$offset": off}, timeout=(30, 300))
                    if r.ok:
                        cache.write_text(r.text); break
                except requests.RequestException as e:
                    print("retry", off, e, flush=True)
                time.sleep(10 * (i + 1))
            else:
                raise RuntimeError(f"page {off} failed")
        df = pd.read_csv(cache, dtype={"locationname": str, "countyfips": str})
        print(off, len(df), flush=True)
        parts.append(df)
        if len(df) < PAGE: break
        off += PAGE
    a = pd.concat(parts, ignore_index=True)
    if a.duplicated(["locationname", "measureid", "data_value_type"]).any():
        raise ValueError("duplicate tract-measure rows")
    a.to_parquet(OUT / "places_tract_2025.parquet", index=False)
    print(len(a), "rows;", a.locationname.nunique(), "tracts;", a.measureid.nunique(), "measures")

if __name__ == "__main__":
    main()
