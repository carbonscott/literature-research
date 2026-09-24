# Editor log (iteration 3)

Edits to findings.md were applied by a single script with exact-match assertions. Originals were backed up in the session scratchpad. print_findings_summary.py gained EXTRA_LABELS (Q1 Scope, Q6 Noise filter).

## Conflicts between auditors and how the data settled them

- **Q3 Headline** (q3q4 must vs completeness should). I used the q3q4 text, which has the family totals, MnTe as marginal and the Bonferroni statement. From completeness I added "CIs only just exclude 1 (upper bounds 0.90-0.995), ignore author clustering". Checked against materials.json: MnTe ci95_low 1.001; the kitaev, av3sb5 and ext_kagome_more upper bounds are 0.902, 0.995 and 0.970.
- **Q4 Headline** (q3q4 must vs completeness should). Merged the two: the technique names with trailing counts come from q3q4, and the Bonferroni caveat comes from completeness. I recomputed z from methods.json CIs: ML 3.66, ED 3.08, QMC 2.58. The Bonferroni threshold for 25 tests is 3.09, so ED is "borderline", not "survives".
- **Q5 Headline/Counts** (q5 must vs completeness must). Merged them: 3-4% with the OSTI share from q5, and the Zenodo 266 [118-520] explanation from completeness. Checked against q5.json: OSTI trailing 305.3, RS 61.0, ChemRxiv 5.6, Preprints.org 12.8, so the sum is about 385. OSTI censoring-corrected is 590 x 0.570 x 0.737 = 248, which gives a total of about 327. For Counts I used the q5 per-server bullet (it has the noise ratings), not the completeness bullet (the two duplicate each other).
- **Q5 On-topic definition.** Both auditors proposed a replacement. I merged them and used the fractions from q5.json on_topic_rate_among_non_duplicates (0.7368, 0.75, 0.4167, 0.5417, 0, 0.2).
- **Q6 Headline** (q6-skeptic must vs completeness should). I took the skeptic's version. It shows that "13 groups" drops to about 10 once co-author links are merged, and that the 4 UTe2 critical studies form one author-linked network. The completeness text repeats the 13-group and 3-group counts that the skeptic disproves.
- **Q6 noise filter placement.** The skeptic put the F1-F7 summary in Counts; completeness asked for a separate **Noise filter:** line. I used the separate line, because the task contract asks for one. The old "Noise filter definition" block was merged into it, keeping the same-group definition, so the definition is not duplicated.

## Corrections to auditor numbers

- **q1-precision "13 of 22 clusters fell below 0.80" is not supported by notes/audit/q1_precision_reaudit.json.** Per-cluster scores are 10/10 x3, 9/10 x7, 8/10 x6, 7/10 x4, 6/10 x2. So 6 clusters are below 0.80 and 6 more are exactly at 0.80. findings.md now says "6 of 22 fell below 0.80 and 6 more sat exactly at 0.80". The pooled 181/220 = 0.823 (0.767-0.868) and ml_ai 19/25 were confirmed.
- **q3q4 Q1 cell for topological_insulators_semimetals** listed "tetradymite TIs 35" as the third family, but materials.json has TMDs 36 in that cluster. The cell now reads "Weyl/Dirac semimetals 86; graphene 45; TMDs 36; tetradymite TIs 35".
- **Q6 label count.** q6.json has 186 stance entries on 184 distinct IDs, which confirms the skeptic's figure.
- **Q2 LOMO.** recount_q1q2.json confirms that spin_liquid flips on 2025-05, 2025-10 and 2026-08 (CI high 1.007, 1.015, 1.005), and that cdw flips to rising on 2024-11 (CI low 1.000).
- **OSTI truncation.** native_harvest_log.json confirms it: 3 truncated terms, 15,925 of 20,971 fetched.
- **Coincidence check.** ext_kagome_more and the formula MnBi2Te4 both have 37 vs 52, R 0.636 (0.417-0.970) in materials.json. Both rows are stored independently, so I kept both. This is worth a sanity check by the materials owner.

## Structural changes

- The Q1 and Q2 tables now use the same human-readable cluster names, with the key in parentheses. The Q3 per-cluster table uses the same names, and its family keys were mapped to readable names (glossary inserted above the table).
- Added a Q1 **Scope:** line (categories, compact keyword list, both windows) and a Q6 **Noise filter:** line. Both are printed by print_findings_summary.py.

## Skipped or folded in

- q3q4 nice "Next-largest probes" bullet: folded into the completeness "Dominant experimental methods" Counts bullet (ultrafast, ARPES, neutron, STM, RIXS counts plus the thin-film synthesis note).
- completeness nice "ultrafast coverage 21%": already covered by the q3q4 cell "No dominant family (coverage 21%; ...)".
- q6-skeptic Counts noise-filter sentence: replaced by the dedicated **Noise filter:** line.
- Not done (outside the editor's write permission): the q6-skeptic issue asking to change status/stance labels in analysis/q6_claims.py. findings.md now says "disfavoured" / "strongly disfavoured (bulk)" for UTe2 chiral and bulk RuO2, while q6.json still says "refuted". I added a next-step bullet for this.
