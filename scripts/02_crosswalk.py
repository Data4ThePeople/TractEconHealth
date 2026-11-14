"""Group 2010 and 2020 census tracts into 'families' using the Census Bureau's 2020 tract relationship file.
Two tracts join the same family when their shared land is at least 2% of either tract's land (or, for
all-water tracts, of its water). Labor force change is then computed family by family, so a split or
merged tract compares the same territory in both periods. Slivers under 2% are ignored, which leaves a
small mismatch at family edges; each 2020 tract gets its family's change."""
import sys, os
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import RAW, PROC, STATES

THRESH = 0.02

def main():
    r = pd.read_csv(RAW / "xwalk" / "tab20_tract20_tract10_natl.txt", sep="|", dtype=str, encoding="utf-8-sig")
    for c in ["AREALAND_TRACT_20", "AREAWATER_TRACT_20", "AREALAND_TRACT_10", "AREAWATER_TRACT_10", "AREALAND_PART", "AREAWATER_PART"]:
        r[c] = r[c].astype(float)
    r = r[r.GEOID_TRACT_20.str[:2].isin(STATES) & r.GEOID_TRACT_10.notna()]
    def share(part, whole):
        return (part / whole).where(whole > 0, 0)
    land = (share(r.AREALAND_PART, r.AREALAND_TRACT_20) >= THRESH) | (share(r.AREALAND_PART, r.AREALAND_TRACT_10) >= THRESH)
    water_only = (r.AREALAND_TRACT_20 == 0) | (r.AREALAND_TRACT_10 == 0)
    water = water_only & ((share(r.AREAWATER_PART, r.AREAWATER_TRACT_20) >= THRESH) | (share(r.AREAWATER_PART, r.AREAWATER_TRACT_10) >= THRESH))
    e = r[land | water][["GEOID_TRACT_20", "GEOID_TRACT_10"]]

    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in zip("n20_" + e.GEOID_TRACT_20, "n10_" + e.GEOID_TRACT_10):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    # tracts with no qualifying edge still get their own family
    for g in r.GEOID_TRACT_20.unique(): find("n20_" + g)
    for g in r.GEOID_TRACT_10.unique(): find("n10_" + g)
    fam = pd.DataFrame({"node": list(parent)}); fam["family"] = fam.node.map(find)
    fam["vintage"] = fam.node.str[1:3]; fam["geoid"] = fam.node.str[4:]
    PROC.mkdir(parents=True, exist_ok=True)
    fam[["geoid", "vintage", "family"]].to_parquet(PROC / "tract_families.parquet", index=False)
    sizes = fam.groupby("family").vintage.value_counts().unstack(fill_value=0)
    one = ((sizes.get("20", 0) == 1) & (sizes.get("10", 0) == 1)).sum()
    print(f"{len(sizes):,} families; {one:,} are one 2010 tract to one 2020 tract; "
          f"largest family: {sizes.sum(axis=1).max()} tracts")

if __name__ == "__main__":
    main()
