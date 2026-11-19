# Independent check of the spotlight numbers

Written by the independent tie-out agent, saved here by the main session because the agent could not write report files. Comparison with our numbers is in `TIEOUT.md`.

Code: `check.py` in this folder. Results: `results.csv` (331 rows, 301 with a value). The code was written from DATASETS.md and the tract lists in `final_sets.csv` only. None of the other analyst's outputs or scripts were opened.

## Sources as used
- ACS 2020-2024 5-year: pulled fresh from the Census API, by county and for the U.S.
- ACS 2008-2012 5-year (B17001, 2010 tracts): pulled fresh from the Census API.
- PLACES 2025 (cwsq-ngmh), and 2024 (ai6z-tcin) for Kentucky: pulled fresh. GHLTH, DIABETES, BPHIGH and MHLTH, crude prevalence, weighted by totalpop18plus.
- USALEEP US_A.CSV: pulled fresh from ftp.cdc.gov.
- On-disk files: the NHGIS nominal and 2010-standardized tables, the 1970 and 1980 shapes, the 1990 and 2000 crosswalks, the 2020-2010 relationship file, cb_2020 tracts and the CHR supplement.

## Where DATASETS.md was unclear, and what I did
1. The neighborhood's 2010 tracts are not defined for the final sets. I used the screen's rule: each 2010 tract with half or more of its land inside the pick's 2020 tracts. This adds 24510180100 and 24510180200 to U039. M014 gets one 2010 tract (48387950500, later split in two).
2. The 2010-2020 land match is not defined beyond its name. I used shared land divided by the larger of the two sets' land.
3. "Fit" is defined only for 1970 and 1980. For 1990 and 2000 I used the screen's stability score. For 2010 and the 2020 census I used the land match. For ACS 2020-2024 the fit is 1.
4. The outline layer for the overlay is not named. I used the dissolved cb_2020 1:500k tracts in EPSG 5070.
5. The overlay fit as written measures how much of the old tracts lies inside the outline, not how much of the outline they cover. I followed the text and put the outline coverage in each note. U034 in 1970 has a fit of 0.93, but its tracts cover only 71% of the outline.
6. For 1990 and 2000 percent Black, I crosswalked the nominal counts. The NHGIS standardized counts come out nearly the same.
7. The poverty table is not named for the key measures. I used B17001.
8. For 2010, population and percent Black are from the 2010 census and poverty is from ACS 2008-2012.
9. For the median, I interpolated in a straight line within the B19001 bin. On the U.S. this gives $81,202, against the published B19013 figure of $80,734. No pick's median falls in the open top bin.
10. "Main county" is not defined. I used the county with the most 2020-2024 residents of the pick.
11. Group quarters residents were not removed.

## What I could not compute
- 1970 and 1980 for M014, M016, R004, R007 and R046. These areas had no tracts then.
- USALEEP for R046: only 2 of 5 2010 tracts have an estimate, covering 21% of residents. The key value is the CHR county figure (58.4).
- Margins of error.

## Data problems noticed
- Shannon County (46113) was renamed Oglala Lakota (46102). Filtering crosswalks by 2020 county codes drops the Pine Ridge tracts. (Our build matched the agent's corrected values, so it did not fall into this.)
- Fits: none under 0.8 under the agent's definition.
- Group quarters are 0.2% to 4.4% of residents across the picks; tract 24510160300 in U039 is at 12%.
- M014: ACS poverty falls from 23.1% (2008-2012) to 14.8% (2020-2024) while SNAP stays near 29%. With about 4,000 people, the margin of error is likely wide.
- USALEEP has no estimate for 1 of U013's 8 2010 tracts (88% covered) or for 3 of R046's 5.
- The PLACES U.S. value covers 78,815 tracts, with no Kentucky or Pennsylvania.
- data/raw/nhgis/ holds nhgis_tr1970_tr2010.zip and nhgis_tr1980_tr2010.zip. (Main session: these are 9-byte failed downloads reading "Not Found".)

## How to rerun
`.venv/bin/python analysis/spotlight/independent/check.py [cache_dir]`
