# Tie-out

Claude's tie-out, November 15, 2026. `scripts/50_tieout.py` rebuilds every measure from the raw downloads with its
own code (no imports from the build scripts), recomputes each published number, decodes the data packed into
`dist/index.html`, and writes `analysis/tieout.json`. The independent tie-out by a fresh agent is reported
separately below once it is back.

Result codes: **match** (same value at the precision shown), **fixed** (was wrong, corrected in this pass),
**supported / partly supported / not supported / could not check** for words.

## Built data

| Check | Result |
|---|---|
| Tract measures rebuilt from raw ACS, PLACES and the relationship file vs. `tracts.parquet` (32 columns incl. both indexes) | match, all differences under 0.000001, same blanks |
| Same 77,918 tract IDs | match |
| County measures, both indexes and CHR values vs. `counties.parquet` | match |
| Viz data decoded from `dist/index.html` vs. the processed files | match, every value within half a storage step, no blank mismatches; 15 economic and 18 health measures (21 in the county view) |
| Rank correlation the page computes for its default views, from the decoded data | tracts 0.82 (77,708); counties 0.82, life expectancy 0.73, overdose -0.25, suicides -0.31 |

My first pass differed on three things. Each traced to my own code, not the build, and each pointed to a vague
line in `DATASETS.md`, now reworded: tract families are built for 50 states and DC only, the water-linking rule
for all-water tracts, and percentile ranks are taken after Kentucky and Pennsylvania drop out.

## Numbers in the findings, README and viz notes

| Claim | Published | Recomputed | Result |
|---|---|---|---|
| Tracts / counties shown | 77,918 / 2,948 | 77,918 / 2,948 | match |
| Tracts with income | 77,708 | 77,708 | match |
| Tract filter steps | 84,401; 83,344; 82,562; 77,919; 77,918 | same | match (step label fixed, see words) |
| County filter steps | 3,144; 3,136; 3,135; 2,948 | same | match |
| Rank correlation, income vs. health index | 0.82 | 0.816 | match |
| Same, economic index | 0.71 | 0.705 | match |
| Bend, share explained: bent line / straight line / log line | 67.1% / 60.3% / 65.2% | 67.1% / 60.3% / 65.2% (finer grid) | match |
| Bend location | about $110,000, range $109,000-$112,000 | $109,800 on a 901-point grid | match |
| Slope below / above, per $1,000 | 0.66 / 0.18, about 27% | 0.66 / 0.18, 27% | match |
| Rank correlation below / above the bend | 0.71 / 0.57 | 0.71 / 0.56 | match (0.565 rounds either way by bend choice) |
| Spread around the line, below / above | 18.6 / 12.5 | 18.6 / 12.6 | match |
| Income table (5 groups x 4 measures, group medians) | as in findings | identical | match |
| Diabetes drop, $31k to $56k / $102k to $197k | 6 / 2 points | 6.0 / 1.9 | match |
| Health index 10th-90th spread by income group | 26 / about 40 at $79,000 / 13 | 28 / about 40 at $72,000 / 17 | **fixed**: the old numbers came from the 50-group file while the sentence and the obesity numbers use the 20 groups |
| Obesity 10th-90th spread, lowest / highest group | 18.4 / 11.3 | 18.4 / 11.3 | match |
| State range | 0.55 ND to 0.86 NJ | 0.55 ND, 0.86 NJ | match |
| States with a bend fit; rising above the bend | 45; 45 | 45; 45 | match |
| Median slope above as share of below | 29% | 29% | match |
| Median gain from the bend; top and bottom states | 3.9; CT 11.9, CO 10.0, NJ 9.8; ND 0.4, MS 0.6, AR 0.7 | same | match |
| Finding 6 correlations (12 values) | as in findings | identical at 2 decimals | match |
| Within-county rank correlation, income / index | 0.74 / 0.79 | 0.742 / 0.786 | match |
| County table (8 values) | 0.82, 0.70, 0.73, 0.70, -0.25, -0.33, -0.31, -0.16 | 0.817, 0.704, 0.733, 0.698, -0.250, -0.327, -0.310, -0.156 | match |
| CHR blanks: overdose / suicide / life expectancy | 1,080 / 675 / 78 | same | match |
| Blank share and population share | 36.6%, 4.4%; 22.9%, 2.4%; 2.6%, 1.2% | same | match |
| Median population, blank vs. with value (overdose) | 8,160 / 49,431 | 8,160 / 49,432 | match |
| Viz note "more than 1 in 3" / "nearly 1 in 4" counties blank | | 36.6% / 22.9% | match |
| Viz note "a neighborhood of about 4,000 people" | | mean 4,036, median 3,817 | match |
| Overdose rates are crude; suicide gap | crude; 0.7 | max gap 0.00000000000003; 0.73 | match |
| Income allocated, national / typical / lowest / highest fifth | 37.8 / 37.4 / 41.3 / 33.9 | same | match |
| All income allocated | 17.8 | 17.8 | match |
| Employment, insurance, rent, SNAP allocation rows | as in DATASETS | identical | match |
| Employment allocation 2015-2019 / 2020-2024 | 9.0 / 11.5 | 9.0 / 11.5 | match |
| Income margin of error, typical / lowest / highest fifth | 20.5 / 27.4 / 17.6 | 20.6 / 27.4 / 18.0 | **fixed**: the coverage script counted Census annotation codes (negative numbers, used for top-coded incomes and too-few-cases tracts) as margins, which pulled the median down. Script corrected; 77,167 tracts have a real margin |
| Share above 200% of poverty, typical margin | 8.7 points | 8.7 | match |
| Margin over half the estimate: unemployment / SNAP / uninsured | 92.6 / 62.6 / 59.6 | same | match |
| Obesity interval width, value; relative width range | 9.8, 34.1; 19%-36% | same | match |
| PLACES file: tracts, matches, measures | 83,522; 83,508; 40 | same | match |
| Kentucky and Pennsylvania measures | 5, listed | same 5 | match |
| States missing social-needs measures | 9 listed | same 9 | match |
| Food insecurity coverage, "39 states and DC" | | 40 places | match |
| Tract families; one-to-one; largest | 68,562; 56,496; 67 | same | match (wording fixed, see words) |
| Counties with blank labor force change | CT planning regions, AK 02063 and 02066 | same 11 counties | match |
| All 2,948 county codes found in CHR | | yes | match |
| README: 15 economic and 18 health measures | | 15 and 18 in the page | match |

## Words

| Text | Where | Source | Result |
|---|---|---|---|
| "Every U.S. census tract and county plotted" | page description | filters drop tracts and counties; KY and PA out | **not supported, fixed** to "U.S. census tracts and counties plotted" |
| Economic index is "the twelve measures from median household income through cash public assistance" | viz notes | list also holds income per person, which is not in the index | **not supported, fixed**: now names the two measures left out; income per person now says "not in the index" |
| "two Alaska areas that did not exist in 2015-2019" | viz notes | they were split from Valdez-Cordova (02261) in 2019; the 2015-2019 file has 02261 | **partly supported, fixed** to "whose county codes are not in the 2015-2019 data" |
| "Households paying 30%+ of income for housing" | measure label | B25140 counts "Over 30 Percent" | **partly supported, fixed** to "over 30%" |
| "People above 200% of poverty line" | measure label, findings | C17002 "2.00 and over" | **partly supported, fixed** to "at or above" |
| "77,919 with PLACES estimates (Kentucky and Pennsylvania drop here)" | DATASETS | KY and PA do have 5 PLACES measures | **partly supported, fixed** to "estimates for the measures based on 2023 survey data" |
| "56,496 are a single tract that kept the same boundaries" | DATASETS | 56,496 pair one 2010 tract with one 2020 tract; 56,321 also keep the same tract code | **partly supported, fixed** |
| ACS release date "(check)" | DATASETS | Census Bureau: public release January 29, 2026 | **filled in** |
| "We flag tracts where ... coefficient of variation passes 30% ... (check)" | DATASETS | never run | **fixed**: run for income (4.8% of tracts) |
| Fourteen index measures "from obesity through short sleep" | viz notes | list order | supported |
| Food insecurity etc. only for 39 states and DC | viz notes, labels | PLACES file | supported |
| PLACES uses county and tract poverty | viz notes, findings, DATASETS | CDC FAQ, Dec 11, 2025, quoted in DATASETS | supported |
| Counted deaths "built from death certificates", "not modeled" | viz notes | CHR codebook: NCHS mortality files | supported |
| Year ranges on death measures (2021-2023, 2019-2023) | measure notes | CHR codebook as recorded in DATASETS | supported (not re-read in this pass) |
| "Kentucky and Pennsylvania are not shown" because no 2023-survey measures | viz notes | PLACES file | supported |
| "Short sleep (under 7 hours)", "Depression (ever diagnosed)" | labels | PLACES measure definitions | supported |
| Orange line "is the middle (median) [tract] at each step" | legend | page code: running median | supported |
| Chetty et al. find the link steepest at low incomes and continuing up | findings | `analysis/literature.md` notes | **partly supported, fixed**: "steepest at low incomes" holds per dollar, not per income percentile; reworded to "larger gains per dollar at lower incomes" |
| Kong and Zhang 2020 say the link is partly built in | findings | literature notes | supported as noted; not re-read in this pass |
| "steepest at the bottom, still rising at the top" | framing | findings 3-5 | supported |
| "Correlation is not cause" | viz notes | | supported |

## Not checked by Claude

- The page in a browser (hover text, state filter, county switch, link options). The decoded data and the
  page's rank correlation were checked in Python.
- The literature papers themselves, beyond the notes in `analysis/literature.md`.

## Independent tie-out (fresh agent, November 15, 2026)

The agent saw only `DATASETS.md`, `dist/index.html` and `README.md`, downloaded every source again, and rebuilt
with its own code. Its working notes stay outside the repo.

**Matched:**
- Every embedded value and blank in both views (33 tract and 36 county columns, within half a storage step).
- Both GEOID sets, every filter count and the family counts.
- Every number in the source coverage check.
- Every findings statistic it recomputed: correlations, bend fit, income groups, states, within-county results
  and the county table.
- The PLACES method claims, checked against CDC's pages.
- The County Health Rankings years.

**Differences found, and what was done:**

| Item | Result |
|---|---|
| Tract tooltip showed "DoÃ±a Ana, NM" (PLACES name read with the wrong text encoding) | **fixed** in the viz build |
| Rent share 51.0 and 9.0 are Census stand-ins for "50.0% or more" and "10.0% or less" (4,881 and 271 tracts) | **fixed**: tooltip shows the cap; viz notes and DATASETS say so |
| 541 tracts at the $250,001 income cap not noted on the page | **fixed**: tooltip shows "$250,000 or more"; notes say so |
| "Strongest link of any economic measure": income per person is 0.818 vs. 0.816 at tract level | **partly supported, fixed**: DATASETS now says tied at tract level, highest at county level; findings give both values |
| Median line took the upper middle value for even groups; legend said "middle tract" | **fixed**: true median, legend reworded |
| 49,431 should round to 49,432 | **fixed** |
| "Moved from December 2025" not on the Census page | **removed** |
| "Fewer than 10 deaths" cutoff not in the codebook (data fit it: smallest count shown is 10) | **partly supported, reworded** |
| "One more year of deaths than the 2025 release" | **not supported, removed** |
| "NCHS multiple cause of death files" (codebook: "NCHS - Mortality Files") | **reworded** |
| "Before 2024, under 50 total people" | **could not check, removed** |
| "Part of why unemployment relates weakly" | **reworded** to "may be part of why" |
| "Mostly small rural counties" (small checked, rural not) | **reworded** to "small" (DATASETS and viz notes) |
| Social-needs measure notes said "39 states" | **fixed** to "39 states and DC" |
| "Counted deaths ... not modeled" (life expectancy is a life-table figure; suicides age-adjusted) | **reworded** in viz notes |
| Gini index grouped under "Assistance and coverage" | **moved** to Income |
| Method lines open to more than one reading: rank base, percentile formula, bend grid, state bend refit, "some or all filled in" | **clarified** in DATASETS |

**The agent could not check:**
- ACS background claims ("about 1 in 8 households," 2020 weighting, CPI-U-RS, the 2015-2019 release date).
- The relationship file date and the CDC WONDER API limit.
- The README's rebuild steps (it was not shown the scripts).
- The page in a real browser. It ran the page's correlation and median-line code in Python instead, and those
  worked as described.

## Numbers added in the post (step 2a)

| Claim | Where | Recomputed | Result |
|---|---|---|---|
| 2,869 counties with income and life expectancy; rank correlation 0.73 | chart 01, post | 2,869; 0.733 (`scripts/31_charts.py`, same as `county_results.json`) | match |
| Middle county, lowest and highest of 20 income groups: 70.7 and 80.8 years, at about $41,000 and $113,000 | box, post, chart 01, alt text | 70.7, 80.8; $41,278, $112,816 | match |
| Life expectancy steeper at the low end, still rising at the top | post | county bend fit: 0.21 years per $1,000 below about $75,000, 0.07 above | match |
| Oliver County, N.D.: 1,839 people, 107.9 years, published range 79 to 137 | chart 01 label, alt text | CHR v147 107.92, 78.97 to 136.87; ACS population 1,839 | match |
| Typical tract obesity 34%, coronary heart disease about 6% | index section | medians 34.1, 6.2 | match |
| Every tract has all 14 health measures | index section | minimum health_n 14 | match |
| Dwyer-Lindgren 2017: 60% (socioeconomic and race group), 41% (log income alone), 2009 | box | JAMA full text, abstract and Tables 1-2 | supported |
| Chetty 2016: life expectancy rises with income at every level; tax records matched to death records | box | `analysis/literature.md` quote: "no dividing line above or below which higher income was not associated with higher life expectancy" | supported |


## Numbers added in the post (step 2e)

| Claim | Where | Recomputed | Result |
|---|---|---|---|
| Five lowest life expectancy counties, all South Dakota: Buffalo 52.9, Dewey 57.3, Oglala Lakota 58.4, Corson 58.5, Todd 58.5 | Common questions | CHR v147 for the 2,948 chart counties: 52.94, 57.30, 58.37, 58.51, 58.55 | match |
| Buffalo County range 48.8 to 57.1 | Common questions | v147_cilow 48.79, v147_cihigh 57.09 | match |
| Obesity 45.8% and 23.6%, diabetes 20.2% and 8.6%, lowest and highest of 20 income groups (about $31,000 and $197,000) | Common questions | 45.8, 23.6; 20.2, 8.6; $30,867, $197,000 | match |
| Fentanyl post is "An Interactive Map" by county | link text | its POST.md title | supported |
| County life expectancy bend about $75,000; above it rises about 36% as fast | chart 01 label, post, email | county_results.json: k $75,228, slope ratio 0.364 | match |
| No county tops about $182,000; 2,841 tracts do | post | county max $181,765; tracts above it 2,841 | match |
