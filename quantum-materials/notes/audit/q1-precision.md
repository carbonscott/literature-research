# Audit lane q1-precision: independent cluster-label re-audit and exemplar check

Auditor lane, 2026-09-23. Verdicts: notes/audit/q1_precision_reaudit.json (220 items, one per record, with title, all_clusters, correct, note).

## Method
- Population: analysis/classified.jsonl, server=arxiv, window=trailing, in_scope=true, grouped by primary_cluster.
- Excluded the 330 ids already judged in analysis/precision_audit_v2.json.
- Ids sorted; one `random.Random(2026)` instance; `rng.sample(ids, 10)` per cluster in the cluster order of precision_audit_v2.json.
- Title + abstract read from corpus/arxiv.jsonl. Strict rule: correct only if the paper's MAIN subject is the cluster topic. Methods papers count as correct when the cluster physics is the stated application. Residual clusters are judged against their own broad label. This is the v2 rule applied more strictly: "topic is only motivation / one example" counts as wrong.
- One annotator (this auditor). Wilson 95% intervals.

## Results (primary labels, n = 10 per cluster)

| Cluster | Re-audit | Wilson 95% | v2 (n=15) | Combined /25 |
|---|---|---|---|---|
| nickelate_sc | 8/10 | 0.49-0.94 | 14/15 | 22 |
| cuprate_sc | 7/10 | 0.40-0.89 | 13/15 | 20 |
| iron_based_sc | 10/10 | 0.72-1.00 | 14/15 | 24 |
| hydride_high_pressure_sc | 9/10 | 0.60-0.98 | 15/15 | 24 |
| kagome | 9/10 | 0.60-0.98 | 15/15 | 24 |
| altermagnetism | 10/10 | 0.72-1.00 | 15/15 | 25 |
| fractional_qah_chern | 8/10 | 0.49-0.94 | 15/15 | 23 |
| rhombohedral_multilayer_graphene | **6/10** | 0.31-0.83 | 15/15 | 21 |
| moire_twisted_2d | 9/10 | 0.60-0.98 | 14/15 | 23 |
| unconventional_topological_sc | 7/10 | 0.40-0.89 | 14/15 | 21 |
| spin_liquid_frustrated | 8/10 | 0.49-0.94 | 14/15 | 22 |
| heavy_fermion_kondo_qcp | **6/10** | 0.31-0.83 | 15/15 | 21 |
| vdw_magnets_topological_magnetism | 8/10 | 0.49-0.94 | 14/15 | 22 |
| cdw_nematic_excitonic | 8/10 | 0.49-0.94 | 15/15 | 23 |
| topological_insulators_semimetals | 8/10 | 0.49-0.94 | 13/15 | 21 |
| flat_band_quantum_geometry | 9/10 | 0.60-0.98 | 15/15 | 24 |
| mott_hubbard_strange_metal | 9/10 | 0.60-0.98 | 12/15 | 21 |
| ultrafast_floquet_noneq | 7/10 | 0.40-0.89 | 14/15 | 21 |
| ml_ai | 7/10 | 0.40-0.89 | 12/15 | **19 (0.76)** |
| quantum_magnetism_ferroic_order | 9/10 | 0.60-0.98 | 15/15 | 24 |
| quantum_many_body_theory | 9/10 | 0.60-0.98 | 15/15 | 24 |
| other_superconductivity | 10/10 | 0.72-1.00 | 13/15 | 23 |

- **Pooled re-audit: 181/220 = 0.82 (Wilson 95% 0.77-0.87).** v2: 311/330 = 0.94 (0.91-0.96). The intervals do not overlap; a two-proportion z-test gives z = 4.5. Combined: 492/550 = 0.89 (0.87-0.92).
- If the 3 items I marked "borderline" wrong are counted correct: 184/220 = 0.84 (0.78-0.88). The gap to v2 is still clear.
- Weighted by trailing primary population: 0.85.
- 13 of 22 clusters are below 0.80 on the fresh sample. With n = 10 this is weak evidence per cluster, but it contradicts the findings.md claim that "every cluster is at or above 0.80". On the combined 25, ml_ai is 19/25 = 0.76 (0.57-0.89).
- Two clusters are below 0.70: rhombohedral_multilayer_graphene and heavy_fermion_kondo_qcp (6/10 each).
  - Rhombohedral: 4 of the 4 errors are superconductivity papers where graphene is only the platform or the motivation: arXiv:2511.04480, arXiv:2608.01313, arXiv:2605.21618, arXiv:2607.28927 (the last is a shift-current selection rule).
  - Heavy fermion: 4 of the 4 errors have no heavy-fermion or Kondo content: arXiv:2601.00085 (ruthenate magnetism), arXiv:2604.28187 and arXiv:2602.05607 (superconductivity theory), arXiv:2607.28283 (magnetic Weyl semimetal DyB4).

## Error patterns (39 errors)
1. **Topic as motivation or example only (about 20).** Examples: arXiv:2603.09665, arXiv:2511.13831, arXiv:2605.24158, arXiv:2608.02753.
2. **Cross-cluster confusion, mostly superconductivity (about 10).** Examples: arXiv:2602.15106 (SC labelled FQAH), arXiv:2607.18686 (AFM labelled topological SC), arXiv:2604.21635 (SC labelled TI).
3. **Out of quantum-materials scope (about 8).** Examples: hep-th CFT arXiv:2605.24978; lattice Schwinger model arXiv:2606.27481; cold atoms arXiv:2606.02489; organic excitons arXiv:2511.23001; colloidal kagome arXiv:2511.06630; biography arXiv:2510.20865; quantum-information complexity arXiv:2510.08448.
4. **ml_ai without ML (2).** arXiv:2604.25199 and arXiv:2601.01617.

## Exemplar check (Q1 table "Example IDs" and Q1 **Key IDs:**)
All 44 table IDs and all 5 Key IDs pass every check:
- present in corpus/arxiv.jsonl;
- window = trailing and in_scope = true;
- primary_cluster equals the row's cluster;
- title clearly on-topic. Borderline ones were checked by abstract: arXiv:2602.23316 (Ce3TiBi5 Kondo-lattice neutron study, fine); arXiv:2606.02794 (NQS scaling laws, fine for ml_ai).

No replacement is needed. All 44 IDs come from the v2 audit sample and were judged correct there. So they are hand-picked positives and say nothing about precision.

## Implications
- The "0.94 / all clusters >= 0.80" statement is optimistic. An independent strict re-audit gives about 0.82 pooled.
- Cluster counts are best read as upper bounds on "papers mainly about X", by about 10-20% for most clusters. Up to about 40% for rhombohedral graphene and heavy fermions (95% upper bound 0.83 precision).
- The Q2 altermagnetism "rising" result is unaffected: 25/25 across both audits.
- No other Q2 labels change. Both sub-0.70 clusters are "flat".
