# Q2 Momentum: which clusters gain or lose share?

Script: `analysis/momentum.py` (reads `analysis/classified.jsonl`, taxonomy v2; writes `analysis/momentum.json`).
Population: arXiv records that are in scope. Trailing window 2025-09-24..2026-09-23 (scope_T = 9,878),
preceding window 2024-09-24..2025-09-23 (scope_P = 8,828). In-scope arXiv output grew by 11.9%, so a
cluster needs raw growth well above +12% before its **share** goes up.

## Method

* T, P = cluster counts. Base variant = PRIMARY cluster (each record counted once; records with no
  cluster form the `unclassified` row). share_T = T/scope_T, share_P = P/scope_P, R = share_T/share_P,
  raw growth = T/P - 1.
* 95% CI for R: exp(log R +/- 1.96 sqrt(1/T + 1/P + 1/scope_T + 1/scope_P)) (Poisson approximation).
  T is part of scope_T, so this CI is a little wider than a binomial CI.
* **LABEL RULE: rising if R >= 1.10 and CI lower bound > 1.0; declining if R <= 0.90 and CI upper bound < 1.0; otherwise flat.**
* Robustness: (a) least-squares slope of the monthly primary share vs month index, with
  t = slope / SE (residual variance, n-2 df); (b) labels re-computed with multi-label counts and with
  category-only scope (records whose arXiv categories include cond-mat.str-el or cond-mat.supr-con;
  scope_T = 6,700, scope_P = 6,061); (c) partial months (below).

## Results (base = primary counts, full scope; sorted by R)

| cluster | T | P | growth | R | 95% CI | label | R multi (label) | R cat-only primary (label) | slope sign | t (25 mo) | t (23 full mo) | label flips? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| altermagnetism | 660 | 414 | +59% | 1.42 | 1.26-1.62 | **rising** | 1.44 (rising) | 1.65 (rising) | + | 7.18 | 6.06 |  |
| rhombohedral_multilayer_graphene | 81 | 63 | +29% | 1.15 | 0.83-1.60 | flat | 1.09 (flat) | 1.16 (flat) | + | 1.50 | 1.64 |  |
| cdw_nematic_excitonic | 390 | 310 | +26% | 1.12 | 0.97-1.31 | flat | 1.01 (flat) | 1.11 (flat) | + | 0.96 | 0.95 |  |
| ml_ai | 115 | 93 | +24% | 1.11 | 0.84-1.45 | flat | 1.26 (rising) | 1.12 (flat) | + | 1.40 | 1.83 | yes |
| flat_band_quantum_geometry | 297 | 243 | +22% | 1.09 | 0.92-1.30 | flat | 1.07 (flat) | 1.01 (flat) | + | 2.03 | 2.03 |  |
| moire_twisted_2d | 405 | 335 | +21% | 1.08 | 0.93-1.25 | flat | 1.04 (flat) | 0.92 (flat) | + | 1.52 | 1.29 |  |
| quantum_many_body_theory | 1181 | 988 | +20% | 1.07 | 0.98-1.17 | flat | 1.07 (flat) | 1.09 (flat) | + | 1.00 | 1.55 |  |
| mott_hubbard_strange_metal | 533 | 454 | +17% | 1.05 | 0.92-1.19 | flat | 1.00 (flat) | 1.03 (flat) | - | -0.58 | -0.58 |  |
| cuprate_sc | 223 | 192 | +16% | 1.04 | 0.85-1.26 | flat | 1.01 (flat) | 1.05 (flat) | - | -0.83 | 0.13 |  |
| unclassified | 982 | 856 | +15% | 1.03 | 0.93-1.13 | flat | 1.03 (flat) | 1.03 (flat) | + | 0.13 | 0.40 |  |
| other_superconductivity | 572 | 506 | +13% | 1.01 | 0.89-1.14 | flat | 1.01 (flat) | 1.03 (flat) | - | -1.02 | -0.67 |  |
| hydride_high_pressure_sc | 57 | 52 | +10% | 0.98 | 0.67-1.43 | flat | 0.94 (flat) | 0.92 (flat) | - | -1.83 | -0.84 |  |
| heavy_fermion_kondo_qcp | 162 | 151 | +7% | 0.96 | 0.77-1.20 | flat | 0.94 (flat) | 0.98 (flat) | - | -0.35 | -1.05 |  |
| quantum_magnetism_ferroic_order | 471 | 440 | +7% | 0.96 | 0.84-1.09 | flat | 0.96 (flat) | 0.97 (flat) | - | -0.90 | -0.35 |  |
| nickelate_sc | 222 | 211 | +5% | 0.94 | 0.78-1.14 | flat | 0.94 (flat) | 0.95 (flat) | - | -0.03 | -0.52 |  |
| vdw_magnets_topological_magnetism | 820 | 784 | +5% | 0.93 | 0.84-1.04 | flat | 0.95 (flat) | 0.96 (flat) | - | -1.27 | -1.35 |  |
| ultrafast_floquet_noneq | 136 | 131 | +4% | 0.93 | 0.73-1.18 | flat | 1.03 (flat) | 0.81 (flat) | - | -1.10 | -0.41 |  |
| unconventional_topological_sc | 717 | 693 | +3% | 0.92 | 0.83-1.03 | flat | 0.98 (flat) | 0.91 (flat) | - | -2.72 | -2.88 |  |
| fractional_qah_chern | 364 | 363 | +0% | 0.90 | 0.77-1.04 | flat | 0.91 (flat) | 0.92 (flat) | - | -0.42 | -0.60 |  |
| iron_based_sc | 117 | 117 | +0% | 0.89 | 0.69-1.16 | flat | 0.91 (flat) | 0.89 (flat) | + | 0.19 | -0.51 |  |
| kagome | 308 | 313 | -2% | 0.88 | 0.75-1.03 | flat | 0.89 (flat) | 0.88 (flat) | - | -1.96 | -2.30 |  |
| topological_insulators_semimetals | 678 | 712 | -5% | 0.85 | 0.76-0.95 | **declining** | 0.86 (declining) | 0.77 (declining) | - | -1.64 | -2.78 |  |
| spin_liquid_frustrated | 387 | 407 | -5% | 0.85 | 0.74-0.98 | **declining** | 0.86 (declining) | 0.88 (flat) | - | -2.04 | -1.73 | yes |

(The multi-label category-only variant gives the same labels as the multi-label full-scope column:
altermagnetism rising, ml_ai rising, topological declining, spin liquid flat. All four variants are in `momentum.json`.)

## Reading

* **Altermagnetism is the only robust riser.** R = 1.42 (CI 1.26-1.62). It stays rising in all four
  variants and is stronger in category-only scope (R = 1.65). The monthly share climbs from about 3% to about 7%,
  t = 7.2. In the audit, 15/15 sampled records were correct (`analysis/precision_audit_v2.json`).
  Caveat: some of the growth may be relabelling. Work on collinear antiferromagnets and "p-wave magnets"
  now uses the altermagnet word, which the cluster keys on. This is a vocabulary signal as much as a
  new-research signal.
* **Two marginal decliners.** `topological_insulators_semimetals` (R = 0.85, CI upper bound 0.95) is declining in all
  four variants, and more strongly in category-only scope (0.77). The monthly slope is negative
  (t = -1.6 with all 25 months, -2.8 with only the 23 full months). `spin_liquid_frustrated` (R = 0.85, CI upper bound 0.98)
  is declining in full scope but **flips to flat** in category-only scope (R = 0.88, CI upper bound 1.02). Its decline is
  partly a decline of keyword-scoped (non-str-el/supr-con) frustrated-magnet papers. Treat it as weak.
* **Label flips across variants:** `ml_ai` (flat with primary counts -> rising with multi-label counts, R = 1.26,
  CI 1.03-1.55). ML *applied to* other clusters grows faster than ML as a primary topic. Primary ML-cluster
  precision is only 0.80. `spin_liquid_frustrated` (declining -> flat in category-only scope). No other cluster flips.
* **Slope vs label contradictions: none.** Every rising/declining label has a monthly slope of the same sign,
  in both the 25-bucket fit and the 23-full-month fit.
* **Flat labels with a notable trend.** These look like trends, but the window test does not confirm them:
  - `unconventional_topological_sc`: R = 0.92, CI 0.83-1.03, t = -2.7 / -2.9. This is the best candidate to become a decliner.
  - `kagome`: R = 0.88, CI 0.75-1.03, t = -2.0 / -2.3. It misses "declining" only because of the CI.
  - `flat_band_quantum_geometry`: R = 1.09, t = +2.0.
  - `rhombohedral_multilayer_graphene` (+29% raw) and `cdw_nematic_excitonic` (+26%) have point estimates above 1.10,
    but their CIs include 1.

  Several fashionable topics (moire, FQAH/Chern, nickelates) are flat in share. Their raw growth is about as fast as
  the field (+0% to +21% against +12%).

## Caveats

* **Partial months.** Month buckets are calendar months, so there are 25 of them, not 24. 2024-09 holds only
  09-24..30 (165 in-scope records). 2026-09 ends on **2026-09-22** in the data (643 records), one day short of
  the window end 2026-09-23. So the trailing window covers 364 days vs 365. Raw growth is biased low by about 0.3%.
  Shares and R are unaffected to first order. The noisy partial buckets are why slopes are given both with and
  without them. Monthly in-scope totals range from 615 to 906. There is also an unexplained dip in several cluster
  shares in 2025-10 (e.g. topological 4.5%, spin liquid 2.3%). It may be a harvest or listing artefact, and it adds noise to the slopes.
* **Multiple comparisons.** 23 rows at 95% means about one spurious label is expected by chance. Only altermagnetism
  would survive a Bonferroni-style correction (its CI lower bound is 1.26). The two decliners would not.
* The monthly-slope t-statistic assumes independent, equal-variance residuals. It ignores Poisson noise that
  differs from month to month, and autocorrelation. Read |t| > 2 as suggestive, not as a test.
* Primary counts depend on the cluster order (most specific first). A shift of records into an earlier, more specific cluster
  (e.g. altermagnet vs generic magnetism) lowers the later cluster's share. The multi-label variant reduces this problem.
  The residual clusters (magnetism, many-body theory, other SC) have multi-label = primary by construction.
* This is preprint output on arXiv, classified by regex. It measures what people post and what words they use,
  not scientific importance. Precision per cluster is 0.80-1.00 on 15-item samples.

## Exemplars (trailing window, primary cluster, title matches the cluster's core pattern)

Titles were chosen to contain the title bigrams most over-represented in the direction of the change. All IDs are in `corpus/arxiv.jsonl`.

**altermagnetism (rising)**
* arXiv:2511.06865 - Physical properties and first-principles calculations of an altermagnet candidate Cs1-δV2Te2O
* arXiv:2602.05745 - Anomalous thermoelectric and thermal Hall effects in irradiated altermagnets
* arXiv:2602.08790 - d-wave Surface Altermagnetism in Centrosymmetric Collinear Antiferromagnets

**topological_insulators_semimetals (declining)** (these are still-active examples of the sub-topics losing share: transport, Dirac cones, nodal-line semimetals)
* arXiv:2511.14454 - Observation of the surface hybridization gap in the electrical transport properties of the ultrathin topological insulator ...
* arXiv:2604.25758 - Linear response from tilted Dirac cones under strain-induced pseudomagnetic fields
* arXiv:2604.26480 - Large magnetoresistance and weak-antilocalization in the nodal-line semimetal VP2

**spin_liquid_frustrated (declining, full scope only)**
* arXiv:2603.14682 - Giant anomalous Hall conductivity in frustrated magnet EuCo2Al9
* arXiv:2601.03138 - Phase diagram and macroscopic ground state degeneracy of frustrated spin-1/2 anisotropic Heisenberg model on ...
* arXiv:2604.24744 - Dynamical preparation of U(1) quantum spin liquids in an analogue quantum simulator
