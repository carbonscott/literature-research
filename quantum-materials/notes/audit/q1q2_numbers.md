# Audit lane q1q2-numbers

Script: `notes/audit/recount_q1q2.py` (independent; reads `analysis/classified.jsonl`,
`corpus/arxiv.jsonl`, `corpus/arxiv_harvest_log.json`, `findings.md`; does not import
momentum.py or count_clusters.py). Output: `notes/audit/recount_q1q2.json`.
Run: `/usr/bin/python3 notes/audit/recount_q1q2.py`.

## 1. Recount of the Q1 and Q2 tables

Population: arXiv, `in_scope == true`, window trailing/preceding.
scope_T = 9,878, scope_P = 8,828 (+11.89%). Category / keyword split 6,700 / 3,178 (T) and
6,061 / 2,767 (P). Every record's `window` agrees with its `date`, and every `month` equals `date[:7]`.

The script parsed 23 Q1 rows and 23 Q2 rows and compared them cell by cell:
- Q1: primary T, multi-label T, primary P, the trend label and R.
- Q2: T, P, R, CI low, CI high and label.
- Q2 robustness notes: the multi-label R and label, and the category-only R and label.

**Mismatches: 0** (tolerance 0.01 on R and CI).

Other Q1/Q2 numbers that check out:
- The residual clusters hold 2,224 trailing records (22.5%).
- Unclassified is 982/9,878 = 9.94% (trailing) and 856/8,828 = 9.70% (preceding).
- There are 22 clusters plus the unclassified bucket.
- Labels: 1 rising, 2 declining, 20 flat.
- 2025-10 shares: topological 4.5% (34/749), spin liquid 2.3% (17/749).

I did not verify: "down from about 17% in v1" (a v1 figure), and the monthly-slope t values
beyond the two clusters below. For those two, my own OLS gives t25 / t23 = -1.64 / -2.78
(topological) and -2.04 / -1.73 (spin liquid), which match the table.

## 2. The 2025-10 dip

### Harvest

- All 100 slices in `corpus/arxiv_harvest_log.json` are reconciled (totalResults = parsed = unique_ids), and `unreconciled_slices` is empty.
- In every calendar month, the per-category record counts from `matched_terms` in corpus/arxiv.jsonl exactly equal the slice totalResults.
- 2025-10 totals: str-el 393, supr-con 179, mes-hall 451, mtrl-sci 792, all within the range of the other months.
- The daily counts for 2025-10 follow the normal weekday/weekend pattern. No days are missing.

**Verdict: not a harvest artefact.**

### Baseline composition

| month | all arXiv | in scope | category | keyword | keyword, mtrl-sci only | keyword share |
|---|---|---|---|---|---|---|
| 2025-08 | 1300 | 678 | 465 | 213 | 70 | 0.314 |
| 2025-09 | 1487 | 848 | 591 | 257 | 93 | 0.303 |
| 2025-10 | 1464 | 749 | 510 | 239 | 90 | 0.319 |
| 2025-11 | 1394 | 741 | 503 | 238 | 77 | 0.321 |
| 2025-12 | 1682 | 906 | 641 | 265 | 107 | 0.292 |

- The keyword share over the 23 full months ranges from 0.292 to 0.346, so 2025-10 is typical.
- The dip persists in category-only scope. Topological share is 1.4% vs a pooled 3.3% (z = -2.44). Spin liquid is 3.3% vs 5.7% (z = -2.31).

**Verdict: not a baseline-composition effect.**

### Which clusters dip

2025-10 z-scores of the primary count against the pooled 23-full-month share:
- topological_insulators_semimetals: -3.07 (34 observed vs 56.2 expected)
- spin_liquid_frustrated: -2.72 (17 vs 32.1)
- Every other cluster has |z| < 1.6, except moire_twisted_2d, which is +2.27 (42 vs 29.8).
- The top-5-cluster share sum in 2025-10 is 0.406, within its monthly range of 0.377-0.447.

"Several cluster shares dip" is therefore an overstatement: exactly two clusters dip.

Across 529 cluster-month cells, 5 have |z| >= 3, against about 1.4 expected under a binomial model. Similar-sized outliers occur elsewhere:
- altermagnetism 2024-10: -3.47
- moire 2026-06: +3.45
- moire 2025-04: -3.08
- altermagnetism 2026-02: +3.06

The monthly counts are mildly overdispersed, and 2025-10 is one of several comparable outliers.

**Verdict: noise / overdispersion, not an artefact.**

### 2025-09 boundary bucket

The 20250901_20250930 slice spans the window boundary. Its 848 in-scope records split into 641 preceding (446 category, 195 keyword) and 207 trailing (145 category, 62 keyword). Window assignment follows the record date with no errors, and the bucket's shares are ordinary (topological z +0.05, spin liquid +0.62). No problem found.

### Consequence (material)

The dip is not an artefact, but the spin-liquid "declining" label depends on it.
- Dropping 2025-10 alone gives R 0.879 (CI 0.761-1.015), which is flat.
- Leave-one-month-out flips spin_liquid_frustrated to flat in 3 of 25 drops: 2025-05 (CI high 1.007), 2025-10 (1.015) and 2026-08 (1.005).
- topological_insulators_semimetals stays declining when 2025-10 is dropped: R 0.875, CI 0.783-0.977 (also declining in multi-label and category-only).
- Leave-one-month-out also flips cdw_nematic_excitonic to rising when 2024-11 is dropped (CI low 1.000). That is borderline.

## 3. Sensitivity: partial months

| variant | scope_T | scope_P | label changes |
|---|---|---|---|
| exclude 2026-09 (partial) | 9,235 | 8,828 | none |
| exclude 2024-09-24..30 | 9,878 | 8,663 | none |
| exclude both | 9,235 | 8,663 | none |

The closest calls:
- spin liquid excluding 2026-09: R 0.862, CI 0.746-0.996. Still declining, but barely.
- kagome excluding 2026-09: R 0.858, CI 0.729-1.011. Still flat.

## Required edits (summary)

1. Q2 caveat bullet "Unexplained October 2025 dip": replace it with the verdict above, and note that the spin-liquid label depends on single months.
2. The matching sentence in notes (Caveats and next steps: the "October 2025 dip" bullet and the "Investigate the 2025-10 dip" next step): resolve both.
3. The Q2 headline/Counts could note that the spin-liquid decline is fragile (flips to flat when any one of 3 of the 25 months is dropped).

The table numbers need no fixes.
