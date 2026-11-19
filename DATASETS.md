# Datasets

One section per dataset, written before any analysis and updated as the work turns up more. Items marked
**(check)** are confirmed from the downloaded data during the build and the result is written here.

## American Community Survey, 2020-2024 5-year estimates (U.S. Census Bureau)

**What it is.** Survey-based estimates for every census tract and county, pooled from responses collected January 2020
through December 2024. Each value describes the five-year period, not any single year.

**Where it comes from.** Census Data API, `https://api.census.gov/data/2024/acs/acs5`, one call per table and
state for `tract:*`. Free key (`CENSUS_API_KEY`). Script: `scripts/01_fetch_acs.py`. Tables: B01003 (total
population), B26001 (group quarters population), B19013 (median household income), C17002 (ratio of income to
poverty), B23001 (sex by age by employment status), B23025 (employment status), B25070 (gross rent as a share of
income), B25071 (median gross rent as a share of income), B25140 (housing costs as a share of income, by
tenure), B22003 (SNAP receipt), C27007 (Medicaid or means-tested coverage by sex and age), B27010 (health
insurance by age), B19057 (public assistance income), B19083 (Gini index), B19301 (per capita income).
Every estimate is saved with its margin of error, along with the table's variable labels. The same tables are
pulled for every county (`for=county:*`, one call per table) by `scripts/05_fetch_acs_county.py`. Allocation
tables for the coverage check (B99192, B99231, B992701, B99221, B992518) are pulled by
`scripts/04_fetch_allocation.py`.

**Version and vintage.** 2020-2024 5-year release, published January 29, 2026. The Bureau does not revise a published ACS release.

**Coverage.** 50 states and DC on 2020 census tract boundaries and 2024 county boundaries, where Connecticut's
nine planning regions replace its eight old counties. Puerto Rico is left out because PLACES does not
cover it. Every value is an estimate from a sample of about 1 in 8 households over five years. The Bureau
weights responses to match its own population estimates; values are not filled in for tracts with no sample.
A blank median means the sample was too small to compute it.

**Changes over time.** 2020 tracts differ from the 2010 tracts used in the 2015-2019 release (see the
relationship file below). In 2020 the pandemic cut in-person follow-up and response rates fell; the Bureau
used adjusted weights for 2020 and still includes 2020 in this five-year window. Income values are in 2024
dollars, adjusted by the Bureau using CPI-U-RS.

**Suppressed, censored or masked values.** Median household income is top-coded at $250,001 and bottom-coded
at $2,499; the API returns those bounds. Annotation codes in the margin of error fields (for example -555555555
for "controlled, no sampling error", -222222222 for "too few cases to compute", -666666666 for "cannot be
computed") are treated as missing for the estimate when they appear in the estimate field, and as a zero or
unknown margin otherwise. Top-coded incomes stay as published in every calculation; 541 analysis tracts sit at the $250,001 cap. The viz
and the hero do not draw those tracts when income is on the axis, since they would stack on one value, and say so;
they stay in the rank correlation and the median line.

**Missing data.** Tracts with zero population return zeros or null medians. These tracts are dropped by the
population filter (under 500 people).

**Revisions.** None. We pin the 2020-2024 release.

**Units and rounding.** Counts are whole numbers; medians in dollars; B25071 in percent to one decimal; the Bureau publishes 50.0% or more as 51.0 (4,881
analysis tracts) and 10.0% or less as 9.0 (271 tracts), and the viz shows those as the caps. Shares
we compute are rounded only for display.

**Known quirks.** Small tracts have large margins of error; a share computed from a few dozen households can
swing widely. Tracts dominated by group quarters (prisons, dormitories, nursing homes, military barracks)
describe institutions rather than neighborhoods, and household measures such as income and SNAP leave out
group quarters residents entirely. These are filtered out (group quarters 50% or more of total population).
The C27007 Medicaid table counts the civilian noninstitutionalized population, a different base from the
household tables.

**Uncertainty.** Margins of error are published at 90% confidence. Margins for sums use the Bureau's root of
summed squares; margins for shares use the Bureau's ratio formula. For median household income, the
coefficient of variation (margin of error divided by 1.645, over the estimate) passes 30% in 4.8% of the 77,167
analysis tracts with a published margin; see the source coverage check for the other measures.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, American Community Survey 2020-2024
5-year estimates.

## American Community Survey, 2015-2019 5-year estimates (U.S. Census Bureau)

**What it is.** The last five-year release before the 2020-2024 window, so the two periods do not overlap.
Used for one measure only: change in the size of the labor force.

**Where it comes from.** `https://api.census.gov/data/2019/acs/acs5`, table B23025, all tracts and all counties.
Same scripts.

**Version and vintage.** Published December 2020. Not revised.

**Coverage.** 2010 census tract boundaries; 2019 county boundaries. Collected 2015 through 2019, before the
pandemic. For counties, labor force change matches the same county code in both periods. It is blank for
Connecticut's planning regions and for Alaska's Chugach (02063) and Copper River (02066) census areas, whose codes
do not appear in the 2015-2019 county file.

**Changes over time.** Tract boundaries differ from 2020-2024; handled by the tract families below. Population
controls in 2015-2019 come from estimates built on the 2010 census; 2020-2024 controls come from the 2020
census, so a part of any change can reflect the new base rather than real change.

**Suppressed, censored or masked values.** None for B23025 counts.

**Missing data.** Zero-population tracts return zeros.

**Revisions.** None.

**Units and rounding.** Whole persons.

**Known quirks.** Labor force is people 16 and over who are working or looking for work, so the measure moves
with population growth as well as with participation.

**Uncertainty.** Each period's estimate has its own margin of error; the change between them is noisier than
either. Change is computed for tract families, not single tracts, which pools sample and reduces noise.

**License and attribution.** Public domain. U.S. Census Bureau.

## 2020 census tract relationship file (U.S. Census Bureau)

**What it is.** One row for every piece of land or water shared by a 2010 tract and a 2020 tract, with the
area of each tract and of the shared piece.

**Where it comes from.**
`https://www2.census.gov/geo/docs/maps-data/data/rel2020/tract/tab20_tract20_tract10_natl.txt`, pipe-separated.
Script: `scripts/02_crosswalk.py`.

**Version and vintage.** 2020 relationship files, published 2021. Fixed.

**Coverage.** All 2010 and 2020 tracts.

**Changes over time.** Not applicable.

**Suppressed, censored or masked values.** None.

**Missing data.** None.

**Revisions.** None.

**Units and rounding.** Square meters.

**Known quirks.** Boundary edits often create tiny slivers of overlap. We link a 2010 tract and a 2020 tract
only when their shared land is at least 2% of either tract's land, or, when either tract is all water, their
shared water is at least 2% of either tract's water, then group
linked tracts into families. Families are built for 50 states and DC. Of 68,562 families, 56,496 pair one 2010 tract with one 2020 tract. The
largest family chains 67 tracts together. Labor force change is computed for each family and given to each
2020 tract in it. Ignoring slivers under 2% leaves a small mismatch at family edges.

**Uncertainty.** None published. Area is used only to decide links, not to split counts.

**License and attribution.** Public domain. U.S. Census Bureau.

## PLACES: Local Data for Better Health, census tract data, 2025 release (CDC)

**What it is.** Model-based estimates of the share of adults in each tract with a given health condition,
behavior or social need. These are not survey results for the tract. CDC fits a statistical model to a
national survey and uses it to predict a value for every tract.

**Where it comes from.** data.cdc.gov dataset `cwsq-ngmh` (long format, one row per tract and measure), pulled
with the Socrata API in pages of 200,000 rows. Script: `scripts/03_fetch_places.py`. Method pages:
https://www.cdc.gov/places/methodology/index.html, https://www.cdc.gov/places/faqs/index.html,
https://www.cdc.gov/places/current-release-notes/index.html.

**Version and vintage.** 2025 release (dataset last updated December 2025). 35 measures use 2023 BRFSS survey
data; five use 2022 BRFSS because the survey asks them every other year (all teeth lost, dental visits,
mammograms, colorectal cancer screening, short sleep). The model also uses ACS 2019-2023 data and 2020 census
block population counts. Each annual release refits the model, and CDC says the estimates should not be used
to track change in a place over time.

**Coverage.** 50 states and DC. Tracts with fewer than 50 adults get no estimate. 40 measures in the release.
Seven health-related social needs measures (food insecurity, loneliness, lack of social and emotional
support, housing insecurity, utility shutoff threat, transportation barriers, SNAP receipt) come from an
optional BRFSS module that only 39 states and DC ran. **Kentucky and Pennsylvania have only 5 of the 40 measures** in this release (the five based on 2022 BRFSS: all teeth
lost, dental visits, mammograms, colorectal screening, short sleep), so both states have no health index and are
left out of the tract analysis. We do not fill them from the 2024 release, which rests on 2022 survey data and an
earlier model fit, because that would mix years in one comparison. The seven social-needs measures are also missing in Colorado, Florida, Oregon,
South Dakota, Tennessee, Texas, Vermont, Washington and Wyoming. The file holds 83,522 tracts and 40 measures;
83,508 of the tract IDs match 2020 ACS tracts, so the release uses 2020 tract boundaries. The other 14 do not
appear in the ACS tract list.

How the estimates are made, in plain words: CDC fits a model for each measure to individual BRFSS answers,
using each person's age, sex, race and ethnicity, and education, plus the share of adults in their county
below 150% of the poverty line, with state and county effects. It then applies the model to the 2020 census
count of people of each age, sex and race in every block and adds the blocks up to tracts. CDC's FAQ (https://www.cdc.gov/places/faqs/index.html,
December 11, 2025) adds: "In the prediction step of the modeling process, we do use census-tract poverty
estimates." The methodology page and the 2022 PLACES paper (Greenlund et al.) name only the county poverty input,
and none of these say which tract poverty table or vintage is used. So tract-to-tract differences within a county come
from differences in who lives there (age, sex, race, education) and in tract poverty, not from asking people
in that tract. **This matters for this project:** part of any link between a tract's economic measures and its
PLACES health estimates is built in by the model. We disclose this, and we check the main result against
county death rates, which are counted rather than modeled.

**Changes over time.** 2025: "feelings of social isolation" renamed "feelings of loneliness" with a new
definition (always, usually or sometimes lonely); cervical cancer screening dropped.

**Suppressed, censored or masked values.** No estimate for tracts under 50 adults; those tracts are simply absent
from the file (the footnote field is empty on every row). These tracts are also removed by our population filter.

**Missing data.** Blank values for small tracts and for states that did not run the optional module.

**Revisions.** Each release replaces the last. We pin the 2025 release.

**Units and rounding.** Crude prevalence, percent of adults 18 and over, one decimal. Tract estimates are not
age-adjusted (CDC does not publish age-adjusted tract values), so tracts with older residents show more
chronic disease partly because of age.

**Known quirks.** CDC asks users not to rank places with these estimates and not to use them to evaluate local
programs, because the model cannot see local effects. Depression is "ever told by a health professional,"
a lifetime measure that also depends on access to care.

**Uncertainty.** 95% intervals from 1,000 simulated runs are published with each value. CDC validated the
model at state, county and city level; it reports "strong/moderate" agreement and gives no tract-level
validation. A 2017 Boston study found neighborhood-level agreement was weak for current smoking and frequent
mental distress.

**License and attribution.** Public domain (U.S. government). Credit: CDC, PLACES: Local Data for Better
Health, 2025 release.

## PLACES: Local Data for Better Health, county data, 2025 release (CDC)

**What it is.** CDC's own county estimates from the same model and survey years as the tract release, for the
same measures. Used for the county view's health measures and health index. These are not averages of tract
values.

**Where it comes from.** Socrata dataset `swc5-untb` on data.cdc.gov, crude prevalence. Script:
`scripts/06_fetch_places_county.py`. Updated December 4, 2025.

**Coverage.** 3,144 counties in the file. As with tracts, Kentucky and Pennsylvania lack the measures based on 2023
survey data, so they drop out. Connecticut appears as its nine planning regions, which match the ACS 2024 county
codes.

**Everything else** (model, intervals, quirks, license) is as described for the tract release above.

## Group quarters and population filters

Applied in `scripts/10_build.py`, logged in `data/processed/filter_log.csv`: 84,401 tracts in 50 states and DC;
83,344 with 500 or more people; 82,562 after dropping tracts where group quarters are half or more of the
population; 77,919 with PLACES estimates for the measures based on 2023 survey data (Kentucky and Pennsylvania drop
here); 77,918 with both indexes. Of those,
77,708 have a published median household income, the headline economic measure.

Counties, same filters, in `scripts/11_build_county.py`, logged in `data/processed/county_filter_log.csv`: 3,144
counties; 3,136 with 500 or more people; 3,135 after the group quarters filter; 2,948 with PLACES estimates for the measures based on 2023 survey data and both indexes.

## County Health Rankings, supplemental data release, March 25, 2026 (University of Wisconsin Population Health Institute)

**What it is.** County measures compiled from federal sources. We use three that are counts of deaths, not
model estimates: drug overdose deaths (measure 138, 2021-2023), suicides (measure 161, 2019-2023) and life
expectancy (measure 147, 2021-2023). Shown in the county view and used for the county check, never placed on
tracts.

**Where it comes from.**
`https://www.countyhealthrankings.org/sites/default/files/media/document/analytic_supplement_20260325%5B1%5D.csv`
and its codebook PDF. No login. The data come from NCHS mortality files and Census
population estimates. We use this rather than CDC WONDER because the WONDER API does not return county-level
results.

**Version and vintage.** Supplemental release of March 25, 2026.

**Coverage.** All counties. Deaths are counted in the county where the person lived.

**Changes over time.** Each release shifts the pooled years forward.

**Suppressed, censored or masked values.** Counties with too few deaths have no value. The codebook does not state the cutoff
for these measures; in this file the smallest death count with a value is 10. Of the 2,948 counties in the county view, overdose deaths are blank for 1,080,
suicides for 675 and life expectancy for 78. These are mostly small counties, which tilts the overdose and
suicide checks toward larger counties.

**Missing data.** Blank for suppressed counties.

**Revisions.** Pinned to this release.

**Units and rounding.** Overdose deaths and suicides per 100,000 people. The codebook does not say whether
they are age-adjusted, so we tested it: every overdose rate equals deaths over population times 100,000 (a crude
rate), and suicide rates do not (median gap 0.7 per 100,000), which fits an age-adjusted rate. Crude overdose rates
partly reflect each county's age mix. Life expectancy in years.

**Known quirks.** Connecticut's counties were replaced by planning regions in 2022. The supplement says
Connecticut data may be reported by county or planning region depending on the measure. All 2,948 county codes in
the county view matched a row in the file.

**Uncertainty.** Confidence intervals published per county.

**License and attribution.** Free to use with credit: County Health Rankings & Roadmaps, University of
Wisconsin Population Health Institute, 2026.

## Source coverage check (scripts/40_coverage.py, analysis/coverage.json)

How much of what we use was measured directly, how much the publisher filled in or modeled, and how large the
publisher's own uncertainty is. Run on the 77,918 tracts in the analysis.

**PLACES: none of the tract values are direct measurements.** Every tract number is a prediction from CDC's
model, which takes BRFSS survey answers (about 400,000 adults a year, nationwide), fits how each health measure
varies with age, sex, race and ethnicity, education and county and tract poverty, and then applies that fit to
each tract's population counts. A tract's value says what the model expects for people like the ones who live
there, in that county, at that poverty level. It does not come from surveying that tract. The 95% intervals CDC
publishes are wide: the typical tract's obesity interval spans 9.8 points around a value of 34.1%, and across the
14 health index measures the median interval runs 19% to 36% of the value. Because tract poverty is a model input,
part of the link between tract income and tract health is built into the estimates. The county life expectancy
check (below) uses counted deaths and is the result to lean on for that reason. The viz cannot show measured and
modeled values apart, because no tract value is measured.

**ACS: a large share of income answers are filled in by the Census Bureau.** When a household skips a question
or gives an answer that fails edits, the Bureau fills it in from a similar household nearby (hot-deck
allocation). Shares of answers allocated, from the B99 tables:

| Item | Nationally | Typical tract | Lowest-income fifth of tracts | Highest-income fifth |
|---|---|---|---|---|
| Household income, some or all filled in (all but "no income allocated") | 37.8% | 37.4% | 41.3% | 33.9% |
| Household income, all of it filled in | 17.8% | | | |
| Employment status | 11.5% | 10.4% | 10.9% | 10.0% |
| Any health insurance item | 20.3% | 19.5% | 18.9% | 19.3% |
| Gross rent | 17.8% | 15.6% | 16.2% | 16.0% |
| SNAP receipt | 2.9% | 2.3% | 2.6% | 2.1% |

Income is filled in more often in lower-income tracts; the other items differ little by income. Employment status allocation rose from 9.0% in 2015-2019 to 11.5%
in 2020-2024, so the labor force change measure compares two periods with different shares of filled-in answers.

**ACS sampling error is large at the tract level.** The typical tract's median household income has a 90% margin
of error of 20.6% of the estimate (27.4% in the lowest-income fifth of tracts, 18.0% in the highest), among the
77,167 tracts with a published margin (top-coded and other annotated tracts have none). The share above 200%
of poverty has a typical margin of 8.7 points. For the unemployment rate, the margin is more than half the
estimate in 92.6% of tracts, for SNAP in 62.6% and for uninsured in 59.6%. Noisy measures show weaker links to
anything, which may be part of why unemployment relates only weakly to health here. Larger error at the low end also
adds some spread among low-income tracts that comes from measurement, not from health.

**County Health Rankings: counted deaths, blanked when too few.** Overdose deaths are blank for 1,080 of
2,948 counties (36.6%, holding 4.4% of the population in the county view), suicides for 675 (22.9%, 2.4% of
population) and life expectancy for 78 (2.6%, 1.2%). Blank counties are small: median population 8,160 for blank
overdose counties against 49,432 for those with a value.

## Method (how the measures and indexes are built)

Tracts in `scripts/10_build.py`, counties in `scripts/11_build_county.py`, tests in `scripts/20_analysis.py`.

**Headline economic measure: median household income.** Its link to the health index is as strong as any
economic measure's (0.82 for tracts, tied with income per person; highest of all at the county level), it holds up against counted life expectancy at the county level, and readers know what it means.
The economic index stays in the viz as a second view.

**Economic measures (ACS 2020-2024 unless noted).** Median household income (B19013). People at or above 200% of the
poverty line: C17002 "2.00 and over" over the C17002 total. Prime-age labor force participation: B23001 people
25-54 in the labor force (including armed forces) over all people 25-54, both sexes. Prime-age employment: the same
base, with civilian employed plus armed forces on top. Unemployment rate: B23025 unemployed over civilian labor
force. Labor force change: B23025 labor force for each tract family in 2020-2024 over the same family in
2015-2019, minus one, blank when the family had under 100 people in the 2015-2019 labor force. Housing cost
burden: B25140 "Over 30 Percent" for owners with a mortgage, owners without, and renters, over all occupied units
minus "Not Calculated." Median rent as share of income: B25071. SNAP: B22003 households receiving over all
households. Medicaid: C27007 people with Medicaid or means-tested coverage (all age and sex groups) over the total.
Uninsured: B27010 "No health insurance coverage" (all age groups) over the total. Public assistance: B19057
households with cash public assistance over all households. Gini (B19083) and income per person (B19301) are shown
but not in the index.

**Health measures (PLACES 2025, crude prevalence, % of adults).** Obesity, diabetes, high blood pressure, coronary
heart disease, COPD, any disability, frequent physical distress, fair or poor health, depression, frequent mental
distress, current smoking, binge drinking, no leisure-time physical activity, short sleep. Food insecurity,
loneliness and lack of social and emotional support are shown but not in the index.

**Indexes.** Each measure is turned into a national percentile rank across the 77,919 tracts that pass the filters and have
PLACES estimates (rank divided by the number of tracts with a value, tied values averaged, 0 to 100), flipped where lower is better so that higher always means better. The index is the plain average of a
tract's ranks, and a tract needs at least 75% of the measures (9 of 12 economic, 11 of 14 health). Each index is
then stretched so the lowest tract is 0 and the highest is 100. Housing cost burden, median rent share and labor force change stay in the
economic index even though each relates only weakly to health, because the index was defined before the analysis
and dropping measures after seeing their link to health would tune the result.

**Counties.** The same ACS definitions, applied to county tables. Health measures are PLACES county estimates.
Both indexes are rebuilt with percentile ranks taken across counties.

**Shape tests.** Run with median household income on the x-axis (and repeated for the economic index). Binned
medians: 50 equal-count groups along income, with the 10th, 25th, 50th, 75th
and 90th percentile of the health index in each. Broken-line fit: a continuous line with one bend, the bend tried
at 91 evenly spaced dollar values between the 5th and 95th percentile of income, keeping the one with the smallest squared error;
200 bootstrap resamples give a range for the bend. Also a straight line on the log of income, for comparison. Spread: interquartile range of the leftover distance from
that line on each side of the bend. The bend is refit in each state with 200 or more tracts, and its gain is measured against a straight line in
that state. Rank (Spearman) correlations nationally, by state, below and above the bend,
and within counties (each tract's values minus its county average). County check: ACS county median household income
(and the county economic index) against the PLACES county health index and against County Health Rankings life
expectancy, overdose deaths and suicides.

---

# Community spotlight series (follow-on posts)

The sources below are used to pick and document 10 neighborhood spotlights. The income-health-viz post does not use them.

## PLACES: Local Data for Better Health, census tract data, 2024 release (CDC), Kentucky and Pennsylvania only

- **What:** the same model-based tract estimates as the 2025 release. Pulled from data.cdc.gov dataset ai6z-tcin by `scripts/71_fetch_places2024_kypa.py`.
- **Vintage:** BRFSS 2022 for most measures (some 2021). The 2025 release has no health estimates for these two states.
- **Use:** screening only. Each 2024 measure is placed in the national 2025 distribution. The index formula is then applied, and the result is placed in the national index distribution.
- **Caveat:** a Kentucky or Pennsylvania tract is compared against other states' figures from a year later. That's close enough to screen with. Any number shown for those places names the 2024 release.
- **Coverage:** 4,627 tracts after the same population and group quarters filters.

## Rural-Urban Commuting Area codes, 2020 (USDA Economic Research Service)

- **What:** a code from 1 to 10 for each 2020 tract, based on population density, urbanization and daily commuting (2020 census and ACS 2016-2020).
- **Source:** `RUCA-codes-2020-tract.csv` from ers.usda.gov.
- **Use:** codes 1-3 are urban, 4-6 micropolitan (small cities), 7-10 rural. Micropolitan places are assigned to a week by their story and flagged.
- **Quirk:** 63 qualifying tracts have no code.
- **Revision:** ERS revised the product on December 9, 2025, for a 1990 formatting error. The 2020 codes we use were not affected.

## 2020 census tract boundaries, cartographic boundary file 1:500,000 (U.S. Census Bureau)

- **What:** `cb_2020_us_tract_500k`. Used only to find tracts that share a border.
- **Rule:** two tracts are neighbors if they share more than 50 meters of edge, in an equal-area projection (EPSG 5070). Corner touches don't count.
- **Caveat:** the generalized lines are fine for adjacency. They are not used to measure area.

## NHGIS tract time series and tract crosswalk, 1970-2020 (IPUMS NHGIS, University of Minnesota)

- **Source:** extract nhgis0010, pulled by `scripts/70_fetch_nhgis.py` with the IPUMS API.
- **Nominal tract series, 1970-2000 decennial:**
  - Tables: total population (AV0, also 2010 and 2020), race (B18), persons below poverty (CL6) and poverty universe (AX6), median household income (B79, from 1980), median family income (AB2, from 1980), labor force and employment status (B84), and households by income (BS7).
  - "Nominal" means each year is on its own tract lines, linked by tract code only. A code match does not prove the same area, so finalists get a map overlay.
- **Standardized to 2010 tracts, 1990-2020:** population (CL8), race (CM1), occupancy (CM9), tenure (CN1). NHGIS standardized tables at tract level start in 1990 and cover only these census short-form items. Income, poverty and jobs are available only on each year's own tract lines.
- **Tract maps:** 1970, 1980 and 1990 tracts on the 2008 TIGER/Line basis, and 2010 tracts.
- **1990-2010 tract crosswalk** (`nhgis_tr1990_tr2010`): weights built from census blocks, giving the share of each 1990 tract's population that falls in each 2010 tract. NHGIS has no 1970 or 1980 tract crosswalk.
- **Coverage gap:** in 1970 only metro areas had tracts. All counties were tracted by 1990. Most rural tracts therefore start in 1990, and rural history before that comes from county data.
- **Citation:** Manson, Schroeder, Van Riper, Knowles, Kugler, Roberts and Ruggles. IPUMS NHGIS. Free for research with citation.

## Spotlight screen (`scripts/72_screen.py`)

- **Qualifying tract:** bottom 20% nationally on median household income and on the health index (ranks among the 77,708 published tracts; Kentucky and Pennsylvania placed as described above).
- **Neighborhood:** qualifying tracts that share a border, grouped. Groups over 8 tracts are split by starting at the deepest tract and adding the deepest neighbors until there are 8.
- **Depth:** the population-weighted average of the income and health percentiles. Lower is deeper.
- **Boundary stability, 1990 to 2020:**
  - The neighborhood's 2020 tracts are matched to 2010 tracts (each 2010 tract with half or more of its land in the neighborhood). Those are matched to 1990 tracts by population weight.
  - Score: the smaller of (a) the share of the neighborhood's 1990 population that comes from 1990 tracts at least 80% inside it, and (b) the share of those tracts' population that is inside it. This is multiplied by the 2010-2020 land match.
  - The neighborhood passes at 0.80.
  - Population loss, demolition or turnover never disqualify a place. Only boundaries do.
  - When the neighborhood is one piece of a larger old tract, it can be compared on the old tract's outline instead. That's a judgment call, recorded per spotlight.
- **Candidate list:** the deepest neighborhoods of at least 1,500 people.
  - 60 urban, at most 3 per urban area.
  - 45 rural (at most 4 per state) and 15 micropolitan (at most 2 per state).
  - Plus the seed places Eric named, found by the nearest neighborhood to a point.
- **Output:** `analysis/spotlight/clusters.csv` (all 4,053 neighborhoods) and `candidates.csv` (131).

## U.S. Small-area Life Expectancy Estimates Project (USALEEP), 2010-2015 (NCHS, CDC)

- **What:** life expectancy at birth for most 2010 census tracts, from 2010-2015 death records and the 2010 census. File `US_A.CSV` from ftp.cdc.gov.
- **Use:** one life expectancy figure per spotlight, the average over the neighborhood's 2010 tracts weighted by 2010 population.
- **Limits:** tracts with too few deaths have no estimate, and the "fit" column gives the share of population covered. NCHS publishes a standard error per tract, and small tracts carry wide ranges. It is a single period, not a trend.

## ACS 5-year tract counts for history: 2008-2012 (2010 tracts) and 2020-2024 (2020 tracts)

- **Source:** Census API (`scripts/73_fetch_history_extras.py`).
- **Variables:** poverty (B17001), civilian labor force and unemployed (B23025), total and Black alone population (B02001), occupancy (B25002), tenure (B25003).
- **Missing values:** negative annotation codes are set to missing.

## Spotlight then-and-now tables (`scripts/74_history.py`, `analysis/spotlight/history_long.csv`)

Census counts from each era are added up onto the same neighborhood. Rates are computed from the summed counts.
- **1970 and 1980:** an old tract counts if half or more of its area is inside the neighborhood outline. "Fit" is the overlap of those tracts with the outline divided by their combined area. Years with fit under 0.8 are not shown in the spotlights.
- **1990 and 2000:** NHGIS crosswalks move each year's counts onto the neighborhood's 2010 tracts by population weight.
- **2010 and 2020 census:** counts standardized to 2010 tracts.
- **ACS:** 2008-2012 on 2010 tracts, and 2020-2024 on the neighborhood's own tracts.
- **Comparability:** census poverty and labor force questions moved from the long-form census (1970-2000) to the ACS, which is a sample with margins of error. Small neighborhoods carry wide ranges. Before 1980, "Black" means a single race; 2000 and later use Black alone.
