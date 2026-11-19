---
title: "Income and Health, Neighborhood by Neighborhood: An Interactive Chart"
subtitle: A free, interactive chart of income and other economic measures against physical and mental health for about 78,000 U.S. census tracts and about 2,900 counties.
slug: income-health-viz
date: 2026-11-20
time: 07:30:00-05:00
section: Visualization
hero: images/income-health-viz-hero-1680x1080.png
hero_alt:
meta_title:
description:
keywords:
schema_type: dataset
drop_cap: false
heading_spacer: 20px
caption_spacer: 20px
dividers: false
---

# Income and Health, Neighborhood by Neighborhood: An Interactive Chart

<iframe src="https://data4thepeople.github.io/TractEconHealth/dist/index.html?v=20261120a" width="100%" height="1150" loading="lazy" style="border:0" title="Income and physical and mental health, by census tract and county: interactive chart"></iframe>

::: spacer 40px

::: blurb
**[Open the full visualization](https://data4thepeople.github.io/TractEconHealth/dist/)** **for the title and the full notes.**
:::

::: spacer

## Purpose

::: spacer 5px

[Eric drafts the purpose section here.]

::: blurb Read this first
The health numbers are CDC model estimates, not surveys of each neighborhood. CDC builds them partly from each area's age, sex, race, education and poverty, so part of the link between a place's income and its health estimate is built into the estimate itself. Counts of deaths at the county level, which are not modeled, are the check on that. The chart shows which places have both conditions. It does not show that one causes the other.
:::

::: spacer

## Using the visualization

::: spacer 5px

**1. Pick census tracts or counties.** The Show menu at the top switches between about 78,000 census tracts and about 2,900 counties. A census tract is a neighborhood of about 4,000 people.

**2. Pick an economic measure.** The list on the left holds 15: median household income (the default), an economic index, income per person, the share of people at or above 200% of the poverty line, work, housing cost, public assistance and health insurance measures, and income inequality.

**3. Pick a health measure.** The list on the right holds 18 from CDC: a health index, physical health conditions such as obesity, diabetes and high blood pressure, mental health measures, behaviors such as smoking and short sleep, and three social needs such as food insecurity. In the county view, three more are counted from death records: life expectancy, drug overdose deaths and suicides.

**4. Pick an area.** The Area menu shows one state in blue against the rest of the country in gray. The rank correlation under the chart updates for that state.

**5. Hover over or tap a dot.** A box shows the tract or county, its state, and both values.

To share a view, add it to the page address. `#county` opens the county view, and `&x=` and `&y=` pick the measures. For example, `#county&y=life_expectancy` opens counties against life expectancy.

### How to read it

- **Each dot is one place.** Income runs across the bottom; the health measure runs up the side.
- **The orange line follows the middle of the cloud.** It splits the places into 20 equal-size groups along the economic measure and joins each group's median values.
- **The rank correlation under the chart** runs from -1 to 1. Near 1, places that rank higher on the economic measure also rank higher on the health measure. Near 0, there is no pattern. It uses ranks, so a few extreme places do not swing it.
- **The health index runs from 0 to 100, and higher is better.** It averages each place's national rank on 14 health measures. The economic index works the same way for 12 economic measures.
- **Some values are capped by the Census Bureau.** Median household income is shown as "$250,000 or more" for the highest-income tracts, and median rent share as "50.0% or more" or "10.0% or less" at its limits.

### What it shows right now

Across 77,708 census tracts with a published median household income, the rank correlation between income and the health index is 0.82. For the 12-measure economic index it is 0.71.

Health improves fastest at the low end of income, and it keeps improving at the top. Below about $110,000, the health index rises 0.66 points for each $1,000 of income. Above that, it rises 0.18 points, about 27% of the lower rate. The middle tract's diabetes rate falls from 20.2% in the lowest-income group of tracts (median income about $31,000) to 14.2% in a group with median income about $56,000, and to 8.6% in the highest-income group (about $197,000).

The same pattern holds in each state with enough tracts to test. Rank correlations run from 0.55 in North Dakota to 0.86 in New Jersey.

At the county level, income tracks life expectancy, which comes from death records rather than a model, at a rank correlation of 0.73. Drug overdose deaths (-0.25) and suicides (-0.31) follow county income much more loosely.

## What this page is

::: spacer 5px

Every chart we publish should be something you can check, question and rebuild yourself. This page gives a short summary of how we built this one. The full documentation, with every source, definition and check, is in the public repository: [DATASETS.md](https://github.com/Data4ThePeople/TractEconHealth/blob/main/DATASETS.md).

## The data sources

::: spacer 5px

**American Community Survey, 2020-2024 five-year estimates, U.S. Census Bureau.** Every economic measure, for census tracts and counties. Labor force change also uses the 2015-2019 estimates.

**PLACES: Local Data for Better Health, 2025 release, CDC.** Every physical and mental health measure, for census tracts and counties. Most are based on CDC's 2023 Behavioral Risk Factor Surveillance System survey.

**County Health Rankings & Roadmaps, March 2026 release, University of Wisconsin Population Health Institute.** Life expectancy (2021-2023), drug overdose deaths (2021-2023) and suicides (2019-2023), built from death records.

**2020 census tract relationship file, U.S. Census Bureau.** Used to match 2010 and 2020 tract boundaries for labor force change.

## How we built it, in short

::: spacer 5px

- **We use each publisher's numbers as published.** Nothing is filled in. When a source has no number, the place is left out of that chart.
- **Some places are left out.** Places with fewer than 500 people, or where half or more of residents live in group quarters such as prisons, dormitories or nursing homes, are left out. So are Kentucky and Pennsylvania (see below).
- **The two indexes.** Each measure is turned into a national rank from 0 to 100, flipped where lower is better so that higher always means better. The index is the average of a place's ranks. The economic index uses 12 measures and the health index uses 14. Each index was set before we looked at the results, and we did not drop measures after seeing how they related to health.
- **Counties are not averages of tracts.** County values come straight from the county releases of each source.
- **We check the numbers.** A script rebuilds every measure from the source files with separate code and compares the results with the chart. A separate check, written from scratch without our code, pulled the data again and compared its results with the chart. Both matched every value in the chart.

## Honest notes and limitations

::: spacer 5px

These are the main limits. The full list is in [DATASETS.md](https://github.com/Data4ThePeople/TractEconHealth/blob/main/DATASETS.md) and under "Show notes and disclaimers" at the bottom of the chart.

- **No tract health number is a direct measurement.** Each one is a CDC model estimate, and the ranges around them are wide: the typical tract's obesity estimate has a 95% range about 10 points wide. CDC asks users not to rank places with these estimates.
- **Part of the income link is built into the health estimates.** CDC's model uses county and tract poverty as inputs, so part of the link between income and the health estimates comes from the model itself. The county death measures do not depend on that model.
- **Kentucky and Pennsylvania are not shown.** The 2025 PLACES release has no estimates for these two states for the measures based on 2023 survey data.
- **Income numbers are estimates too.** The typical tract's median household income has a margin of error of about 21% of the estimate, and more in lower-income tracts. The Census Bureau filled in some or all of the income answer for 37.8% of households.
- **Death counts are blank for many small counties.** Counties with too few deaths have no value: more than 1 in 3 counties for overdose deaths and nearly 1 in 4 for suicides. Overdose rates are not adjusted for age.
- **Health estimates are not adjusted for age.** Tracts with older residents show more chronic disease partly because of age.
- **Food insecurity, loneliness and lack of emotional support** are available for 39 states and DC only, and are not in the health index.

## Reproduce it yourself

::: spacer 5px

The code, the data sources and the full method are at [github.com/Data4ThePeople/TractEconHealth](https://github.com/Data4ThePeople/TractEconHealth). Every step is in the scripts, in order. If you get a different number from us, tell us, and we will look.

::: divider

## Common questions

::: spacer 5px

### Is income linked to health in the United States?

In this data, closely. Across 77,708 census tracts, the rank correlation between median household income and a health index built from 14 CDC measures is 0.82. Part of that link is built into CDC's estimates, which use poverty as an input. At the county level, income also tracks life expectancy from death records, at 0.73.

### Does health keep improving at higher incomes?

Yes, in this data, though more slowly. Above about $110,000 in median household income, the health index rises about 27% as fast for each added dollar as it does below that level. It still rises in each of the 45 states with enough tracts to test.

### What is a census tract?

A small area the Census Bureau draws to hold about 4,000 people. Tracts are often used as a stand-in for neighborhoods.

### Where does the health data come from?

From CDC's PLACES project, 2025 release. CDC uses a national health survey and each area's population makeup to estimate how common each condition is in every tract and county. The numbers are estimates, not counts.

### Why are Kentucky and Pennsylvania missing?

CDC's 2025 PLACES release has no estimates for either state for the measures based on its 2023 survey, which covers 13 of the 14 measures in the health index.

### Can I see my county?

Yes. Switch Show to Counties, pick your state in the Area menu, and hover over the dots. In the tract view, each tract's box names its county.

### Does higher income cause better health?

This chart does not test that. It shows which places have both higher incomes and better health estimates. Many other things, such as age, access to care and the CDC model itself, sit behind the pattern.

### Is the chart free to use?

Yes. It is free to use and needs no sign-in.
