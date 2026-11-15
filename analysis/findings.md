# Findings, first pass (November 14, 2026)

Every number here comes from `analysis/results.json`, `analysis/binned.csv`, `analysis/income_binned.csv`,
`analysis/by_state.csv` and `analysis/corr_matrix.csv`. Not yet tied out.

## The theory

Health tracks economic health closely at the low end, up to a point, and above that point the relationship turns
into scatter.

## What the data show

**1. The link is strong across the whole range.** Across 77,918 tracts, the rank correlation between the economic
index and the health index is 0.71.

**2. Health improves fastest at the low end.** By median household income (20 equal groups of about 3,900 tracts):

| Income group (median) | Obesity | Diabetes | Smoking | Frequent mental distress |
|---|---|---|---|---|
| $30,867 | 45.8% | 20.2% | 22.7% | 21.8% |
| $56,417 | 38.2% | 14.2% | 16.5% | 18.5% |
| $75,973 | 34.6% | 12.1% | 13.6% | 17.0% |
| $102,174 | 30.7% | 10.5% | 10.9% | 15.6% |
| $197,000 | 23.6% | 8.6% | 6.8% | 12.5% |

Going from about $31,000 to about $56,000 cuts the middle tract's diabetes rate by 6 points. Going from about
$102,000 to about $197,000 cuts it by 2 points. Each added dollar goes with less improvement as income rises.

**3. But health keeps improving all the way up, and the spread does not widen.** This is where the data part from
the theory. The middle tract's health keeps getting better through the top income group. The gap between the
10th and 90th percentile tract is widest at the lowest incomes and narrows or holds steady above that (obesity:
18.4 points in the lowest group, 11.3 in the highest). On the economic index, the spread of the health index is
widest in the middle of the range and narrower at both ends.

**4. A one-bend line barely beats a straight line.** The best bend is at 78 on the economic index, but resampling
puts it anywhere from 32 to 81, and the bend adds almost nothing (share of variation explained: 50.2% for a
straight line, 50.3% with the bend). Above 78, the rank correlation drops to 0.19, but those are only the top 8% of
tracts, where the health index is also bunched near its ceiling.

**5. Every state shows the same pattern.** Rank correlations run from 0.59 (North Dakota) to 0.87 (DC). In the 46
states with enough tracts to fit a bend, it adds under 1 point of explained variation in half of them, and at most
6.2 points (Hawaii, then DC and Arkansas at 4.9).

**6. Which economic measures go with health.** Rank correlation with the health index: income per person 0.82,
median household income 0.82, share above 200% of poverty 0.80, Medicaid share -0.69, SNAP share -0.68, uninsured
-0.48, prime-age participation 0.50. Weak: unemployment -0.26, public assistance -0.21, housing cost burden -0.11,
median rent share -0.10, labor force change 0.10.

## Why the PLACES model matters here

CDC builds tract health estimates from each tract's age, sex, race and ethnicity, education, and county and tract
poverty. Two signs that this shapes the result:

- The link is **stronger within counties** (rank correlation 0.79 after removing each county's average) than
  overall (0.71). Within a county, the model's tract differences come only from those demographic and poverty
  inputs, so a tight link there is partly built in.
- The economic measures most tied to poverty (income, share above 200% of poverty, SNAP, Medicaid) are the ones
  most tied to the health estimates. Measures the model does not use (housing cost burden, labor force change) show
  little link.

## County check with counted deaths (not modeled)

County Health Rankings, March 2026 supplement, against the population-weighted county economic index:

- Life expectancy (2,871 counties): rank correlation 0.72, about as strong as the tract result. The steeper slope
  is again at the low end (0.25 years per index point below the bend, 0.17 above).
- Overdose deaths (1,868 counties with data; 1,081 blank because of fewer than 10 deaths): -0.33.
- Suicides (2,273 counties; 676 blank): -0.23.

The life expectancy result says the overall link is not only a product of the PLACES model. Overdose and suicide
deaths follow county economics much more loosely.

## Decisions (November 15, 2026, accepted by Eric)

1. Kentucky and Pennsylvania stay out, and the post says so. No fill from the 2024 PLACES release.
2. Housing cost burden, median rent share and labor force change stay in the economic index.
3. Framing: "steepest at the bottom, still rising at the top."
