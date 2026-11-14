# Datasets

One section per dataset, written before any analysis and updated as the work turns up more. Items marked
**(check)** are confirmed from the downloaded data during the build and the result is written here.

## American Community Survey, 2020-2024 5-year estimates (U.S. Census Bureau)

**What it is.** Survey-based estimates for every census tract, pooled from responses collected January 2020
through December 2024. Each value describes the five-year period, not any single year.

**Where it comes from.** Census Data API, `https://api.census.gov/data/2024/acs/acs5`, one call per table and
state for `tract:*`. Free key (`CENSUS_API_KEY`). Script: `scripts/01_fetch_acs.py`. Tables: B01003 (total
population), B26001 (group quarters population), B19013 (median household income), C17002 (ratio of income to
poverty), B23001 (sex by age by employment status), B23025 (employment status), B25070 (gross rent as a share of
income), B25071 (median gross rent as a share of income), B25140 (housing costs as a share of income, by
tenure), B22003 (SNAP receipt), C27007 (Medicaid or means-tested coverage by sex and age), B27010 (health
insurance by age), B19057 (public assistance income), B19083 (Gini index), B19301 (per capita income).
Every estimate is saved with its margin of error, along with the table's variable labels.

**Version and vintage.** 2020-2024 5-year release (release date **(check)**). The Bureau does not revise a published ACS release.

**Coverage.** 50 states and DC on 2020 census tract boundaries. Puerto Rico is left out because PLACES does not
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
unknown margin otherwise. Top-coded incomes stay as published and are noted where they affect a chart.

**Missing data.** Tracts with zero population return zeros or null medians. These tracts are dropped by the
population filter (under 500 people).

**Revisions.** None. We pin the 2020-2024 release.

**Units and rounding.** Counts are whole numbers; medians in dollars; B25071 in percent to one decimal. Shares
we compute are rounded only for display.

**Known quirks.** Small tracts have large margins of error; a share computed from a few dozen households can
swing widely. Tracts dominated by group quarters (prisons, dormitories, nursing homes, military barracks)
describe institutions rather than neighborhoods, and household measures such as income and SNAP leave out
group quarters residents entirely. These are filtered out (group quarters 50% or more of total population).
The C27007 Medicaid table counts the civilian noninstitutionalized population, a different base from the
household tables.

**Uncertainty.** Margins of error are published at 90% confidence. Margins for sums use the Bureau's root of
summed squares; margins for shares use the Bureau's ratio formula. We flag tracts where a key measure's
coefficient of variation passes 30% and report how many there are **(check)**.

**License and attribution.** Public domain. Credit: U.S. Census Bureau, American Community Survey 2020-2024
5-year estimates.

## American Community Survey, 2015-2019 5-year estimates (U.S. Census Bureau)

**What it is.** The last five-year release before the 2020-2024 window, so the two periods do not overlap.
Used for one measure only: change in the size of the labor force.

**Where it comes from.** `https://api.census.gov/data/2019/acs/acs5`, table B23025, all tracts. Same script.

**Version and vintage.** Published December 2020. Not revised.

**Coverage.** 2010 census tract boundaries. Collected 2015 through 2019, before the pandemic.

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
only when their shared land is at least 2% of either tract's land (water for all-water tracts), then group
linked tracts into families. Of 68,562 families, 56,496 are a single tract that kept the same boundaries. The
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
optional BRFSS module that only 39 states and DC ran. CDC says Kentucky and Pennsylvania have no estimates for
measures based on 2023 BRFSS. Which states are missing each measure is counted from the data **(check)**.
Tract geography is not stated on the method page; the census block counts are from 2020, and we confirm the
tract IDs match 2020 tracts **(check)**.

How the estimates are made, in plain words: CDC fits a model for each measure to individual BRFSS answers,
using each person's age, sex, race and ethnicity, and education, plus the share of adults in their county
below 150% of the poverty line, with state and county effects. It then applies the model to the 2020 census
count of people of each age, sex and race in every block and adds the blocks up to tracts. CDC's FAQ adds that
tract poverty estimates are used at that prediction step. So tract-to-tract differences within a county come
from differences in who lives there (age, sex, race, education) and in tract poverty, not from asking people
in that tract. **This matters for this project:** part of any link between a tract's economic measures and its
PLACES health estimates is built in by the model. We disclose this, and we check the main result against
county death rates, which are counted rather than modeled.

**Changes over time.** 2025: "feelings of social isolation" renamed "feelings of loneliness" with a new
definition (always, usually or sometimes lonely); cervical cancer screening dropped. Before 2024, tracts with
under 50 total people were dropped; now it is under 50 adults.

**Suppressed, censored or masked values.** No estimate for tracts under 50 adults; footnote fields mark these
**(check codes)**. These tracts are also removed by our population filter.

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

## County Health Rankings, supplemental data release, March 25, 2026 (University of Wisconsin Population Health Institute)

**What it is.** County measures compiled from federal sources. We use three that are counts of deaths, not
model estimates: drug overdose deaths (measure 138, 2021-2023), suicides (measure 161, 2019-2023) and life
expectancy (measure 147, 2021-2023). Used only for the county-level check, never placed on tracts.

**Where it comes from.**
`https://www.countyhealthrankings.org/sites/default/files/media/document/analytic_supplement_20260325%5B1%5D.csv`
and its codebook PDF. No login. The data come from the NCHS multiple cause of death files and Census
population estimates. We use this rather than CDC WONDER because the WONDER API does not return county-level
results.

**Version and vintage.** Supplemental release of March 25, 2026, which updated these measures with one more
year of deaths than the 2025 annual release.

**Coverage.** All counties. Deaths are counted in the county where the person lived.

**Changes over time.** Each release shifts the pooled years forward.

**Suppressed, censored or masked values.** Counties with fewer than 10 deaths in the pooled period have no
value. Overdose deaths are suppressed in many small rural counties **(check count)**, which tilts the check
toward larger counties.

**Missing data.** Blank for suppressed counties.

**Revisions.** Pinned to this release.

**Units and rounding.** Overdose deaths and suicides per 100,000 people (age-adjusted for overdose, per the
codebook **(check)**); life expectancy in years.

**Known quirks.** Connecticut's counties were replaced by planning regions in 2022 data; we check how the file
handles them **(check)**.

**Uncertainty.** Confidence intervals published per county.

**License and attribution.** Free to use with credit: County Health Rankings & Roadmaps, University of
Wisconsin Population Health Institute, 2026.
