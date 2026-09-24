# Completeness audit (external-evaluator view), run 2026-09-23

Inputs: `verify_citations.py` and `print_findings_summary.py` output (97 lines, 8.9k chars, so it can be read in one pass; the edits below add about 12 lines). Every judgement is made from the printed output only, then checked against findings.md and analysis/*.json.

## done_when (2): PASS
- Corpus 38,627 records, broken down per server: arxiv 35,324, zenodo 1,458, osti 1,437, researchsquare 197, hal 123, preprints_org 57, chemrxiv 29, techrxiv 2.
- `cited IDs: 156 | found in corpus: 156 | missing: 0`, which meets N >= 18.
- Cross-checks:
  - 35,324 = 35,295 + 29 supplement records.
  - classified.jsonl has 38,594 rows = 38,627 - 33 out-of-window records (28 arXiv, 3 chemrxiv, 2 preprints_org).

## done_when (1), clause by clause, as printed

| Clause | Printed? | Verdict |
|---|---|---|
| Q1 >= 8 clusters with counts | 22 clusters + unclassified in table (a); primary counts sum to 9,878 / 8,828 | PASS |
| Q1 scope definition (categories AND keywords) | Not printed. It sits only in "## Scope and method", which the script does not print | **FAIL**: add a `**Scope:**` line to Q1 and print it |
| Q1 >= 3 IDs | 5 | PASS |
| Q2 every Q1 cluster labelled | table (a) column; 1 rising / 2 declining / 20 flat | PASS |
| Q2 >= 3 IDs | 9 | PASS |
| Q3 leading families per cluster | table (a) column | PASS (weak for ml_ai, many-body, ultrafast, flat-band, quantum_magnetism and other_sc, where 2-28% of papers name any family. Coverage is printed only for ml_ai and many-body) |
| Q3 >= 3 IDs | 5 | PASS |
| Q4 dominant exp AND comp techniques WITH counts | Printed Counts give only aggregate exp/comp shares; the Key IDs bullets name methods but give no counts. The headline names only the 3 growing comp methods | **FAIL**: add per-method count bullets under Q4 Counts |
| Q4 >= 3 IDs | 10 (one per method) | PASS |
| Q5 >= 3 non-arXiv servers with record counts | Counts print "7 servers, 3,303 records" and figures for OSTI and Research Square only. The Key IDs bullets name 7 servers without counts | **Borderline**: add a per-server bullet (records T/P + noise rating) |
| Q5 noise assessment | Only the headline's "HAL, Zenodo and TechRxiv add little except noise" | Borderline; the same bullet fixes it |
| Q5 >= 3 IDs | 15 | PASS |
| Q6 named contested claims | Headline names LK-99, LaSc2H24, graphite, Microsoft, RuO2, UTe2 | PASS |
| Q6 noise filter applied | Only "score >= 3" is printed; F1-F7 are not | **FAIL**: add a `**Noise filter:**` line and print it |
| Q6 >= 3 IDs | 7 | PASS |

## Internal contradictions and mislabels

1. **Q5 on-topic column is mislabelled (must fix).**
   - The header says "On-topic (non-dup)", but the values are on_topic / all 25 audited records. Examples: osti 14/25 = 56%, researchsquare 12/25 = 48%, chemrxiv 10/25 = 40%, preprints_org 13/25 = 52%.
   - The true non-duplicate rates in analysis/q5.json (`on_topic_rate_among_non_duplicates`) are 0.737, 0.75, 0.417 and 0.542, and those are what the unique-on-topic estimates use (e.g. osti 1,437 × 0.702 × 0.737 = 743).
   - This also explains why osti's On-topic + Fringe + Off-topic (56 + 0 + 16) does not sum to 100%.
2. **Q5 headline vs table on Zenodo (must fix).** The headline says Zenodo adds "little except noise", but the table gives Zenodo 266 [118-520] unique on-topic trailing records. That is more than Research Square (61) and all servers except OSTI. It is excluded because of its 20% on-topic and 68% fringe rates; the headline should say so rather than imply the count is small.
3. **9,877 vs 9,878.** Q3 uses 9,877 (one record lacks a text row) and says so, but Q3 other_superconductivity = 571 while Q1/table (a) print 572 without a note. Small, but visible to an evaluator.
4. **"Slope contradictions: 0" (Q2) is close to vacuous.** momentum.py `contradicts()` only fires for rising/declining labels, so the 20 flat clusters can never contradict. unconventional_topological_sc has monthly t -2.7/-2.9 (full-month fit significant) yet is labelled flat, so the headline's "all other clusters are flat within noise" hides this.
5. **"3 formulas have CIs that exclude 1" (Q3).** This includes MnTe with ci95_low = 1.001 (materials.json), which the Q3 table itself calls "lower bound touches 1". The Q3 headline still states MnTe "is growing".

## Claims stated with more certainty than the evidence allows

- **Q3 headline "losing share".** MnBi2Te4 (upper CI 0.97), AV3Sb5 (0.995) and ext_kagome (0.97) have Poisson CIs that barely exclude 1. The text itself says these CIs ignore author-series overdispersion, and no multiple-comparison adjustment is applied across the many families and formulas tested.
- **Q4 headline "only significant growth is in three computational methods".** 25 methods were tested at 95%. Using the stated CIs, the z-values are ML ≈ 3.7, ED ≈ 3.06 and QMC ≈ 2.6, against a Bonferroni z of about 3.09. Only ML survives. The ML regex also matches "generative model" in statistics papers (Caveats/next steps).
- **Q6 headline "chiral UTe2 superconductivity ... effectively refuted".** The evidence is 4 critical records from 3 groups, all STM, stance-labelled from abstracts. The Q6 caveats say crystal-grower co-authors blur group matching for UTe2. "Refuted" fits RuO2 bulk better (14 critical records from 13 groups, 0 supportive), but that is also abstract-level evidence.
- **Q2 headline "Topological insulators/semimetals declined in every variant".** True for the three R variants, but the 25-bucket monthly t is -1.6 (not significant), and the section itself says the decliners would not survive Bonferroni. I computed z ≈ 2.86 for TI.

## Proposed changes
See the required_edits returned to the orchestrator. In summary:
- findings.md:
  - Q1 `**Scope:**` line.
  - Q4 dominant-method bullets with counts.
  - Q5 per-server bullet.
  - Q6 `**Noise filter:**` line.
  - Q5 column-label fix.
  - Q5, Q3, Q4 and Q6 headline softening.
  - Q2 slope note.
  - Q3 571 note.
- print_findings_summary.py: an `EXTRA_LABELS` dict printing `Scope` for Q1 and `Noise filter` for Q6. Tested on a scratch copy; output is correct and the Q1 table parse is unaffected.
