# Quantum-materials preprint landscape — run date 2026-09-23

## Scope and method

- **Windows.** Trailing = 2025-09-24..2026-09-23; preceding = 2024-09-24..2025-09-23. The data runs 2024-09-24..2026-09-22, so the trailing window covers 364 days, not 365. This biases raw growth low by about 0.3%. Shares and share ratios are essentially unaffected.
- **arXiv harvest.** cond-mat.str-el, cond-mat.supr-con, cond-mat.mes-hall and cond-mat.mtrl-sci, over 2024-09-24..2026-09-23 (corpus/arxiv_harvest_log.json). corpus/arxiv.jsonl has 35,295 records. The Q6 lane appended 29 records to corpus/arxiv_supplement.jsonl; 28 of them fall outside both windows. In-window arXiv records: 18,717 trailing and 16,579 preceding.
- **Other servers harvested** (corpus records; in-window trailing / preceding):

  | Server | Records | Trailing | Preceding |
  |---|---|---|---|
  | osti | 1,437 | 590 | 847 |
  | zenodo | 1,458 | 1,336 | 122 |
  | researchsquare | 197 | 109 | 88 |
  | hal | 123 | 95 | 28 |
  | preprints_org | 57 | 25 | 30 |
  | chemrxiv | 29 | 14 | 12 |
  | techrxiv | 2 | 1 | 1 |

- **Keyword scope rule (taxonomy v2, verbatim).** "Quantum-materials scope rule (taxonomy v2; the v1 rule plus one extra context veto). An arXiv record is IN SCOPE if its categories include cond-mat.str-el or cond-mat.supr-con, OR its normalized title+abstract matches any QM keyword group. Records from other servers are in scope only via the keyword groups. Keyword groups: topological phases (topological insulator/semimetal/superconductor/order/magnon/..., higher-order topology); moire & twisted layers (moire, twisted bilayer, magic angle, twist angle); correlated electrons (strongly correlated, Hubbard model, t-J, Hund's metal; NOT 'Hubbard U' DFT+U corrections); superconductivity; spin liquids/spinons; frustrated magnetism (Kitaev, spin ice, pyrochlore magnets, quantum magnets); altermagnets; kagome; Weyl/Dirac/nodal-line semimetals; heavy fermion/Kondo; charge/spin/pair density waves and charge order; quantum (anomalous/fractional) Hall and Chern insulators; Majorana/parafermions; flat bands; excitonic insulators/interlayer excitons; van der Waals/2D magnets (CrI3, CrSBr, Fe3GeTe2, ...); multiferroics/magnetoelectrics; Mott (not Mott-Schottky/Mott-Gurney); quantum criticality; electronic nematicity; strange metals/Planckian/non-Fermi liquids; skyrmions/hopfions/merons; Berry curvature/quantum geometry; quantum spin Hall; Wigner crystals; Luttinger liquids/anyons/fractionalization; and named classes (cuprate, nickelate, iron pnictide/chalcogenide, iridate, ruthenate). Context vetoes drop a keyword when it only appears in an engineering/soft-matter sense: superconductivity in superconducting magnets/cables/qubits/resonators/SRF/SNSPDs, nematic in liquid crystals/active nematics, moire in moire-fringe metrology, and photonic flat bands; and (new in v2) 'topological' in classical-wave contexts (topological photonics/acoustics/mechanics, metamaterials, phononic crystals, topolectric circuits, topological lasers, topological data analysis/optimization)."
- **In scope.** Trailing: 9,878 arXiv records (6,700 by category, 3,178 by keyword only). Preceding: 8,828 (6,061 by category, 2,767 by keyword only). The v2 classical-wave veto removed 27 trailing and 40 preceding records compared with v1 (9,905 / 8,868).
- **Taxonomy v2** (analysis/taxonomy.py, frozen; cached in analysis/classified.jsonl, which holds 38,594 records):
  - 22 clusters. Three of them are residual fallbacks (quantum_magnetism_ferroic_order, quantum_many_body_theory, other_superconductivity). A record gets at most one residual cluster, and only if nothing else matched.
  - A cluster needs a title hit, or at least two hits in title + abstract.
  - "Primary" is the first matching cluster in a fixed order; "multi-label" counts every matching cluster.
- **Audited precision** (analysis/precision_audit_v2.json; 15 primary labels per cluster, random.Random(42)): 311/330 = 0.94 overall, and every cluster is at or above 0.80 in that sample. An independent re-audit on a fresh sample (notes/audit/q1_precision_reaudit.json: 10 primary labels per cluster, random.Random(2026), v2 IDs excluded, strict 'main subject' rule) gave 181/220 = 0.82 (Wilson 95% 0.77-0.87). On that sample 6 of 22 clusters fell below 0.80 and 6 more sat exactly at 0.80; rhombohedral_multilayer_graphene and heavy_fermion_kondo_qcp fell below 0.70 (6/10 each). Pooled over both audits: 492/550 = 0.89.
  - 1.00: hydride_high_pressure_sc, kagome, altermagnetism, fractional_qah_chern, rhombohedral_multilayer_graphene, heavy_fermion_kondo_qcp, cdw_nematic_excitonic, flat_band_quantum_geometry, and the three residual clusters.
  - 0.93: nickelate_sc, iron_based_sc, moire_twisted_2d, unconventional_topological_sc, spin_liquid_frustrated, vdw_magnets_topological_magnetism, ultrafast_floquet_noneq.
  - 0.87: cuprate_sc, topological_insulators_semimetals, other_superconductivity.
  - 0.80: mott_hubbard_strange_metal, ml_ai.
  - With n = 15, each figure carries roughly ±15-20 points of uncertainty (±20-30 for the n = 10 re-audit). Only primary labels were audited. The two audits used different annotators and the re-audit rule was stricter: a paper where the cluster topic is only motivation or one example counts as wrong. Read cluster counts as upper bounds on 'papers mainly about X'.
- **Momentum label rule (verbatim):** "rising if R >= 1.10 and CI lower bound > 1.0; declining if R <= 0.90 and CI upper bound < 1.0; otherwise flat."
  - R = (T/scope_T) / (P/scope_P), the ratio of a cluster's share of in-scope records between windows.
  - 95% CI = exp(log R ± 1.96·sqrt(1/T + 1/P + 1/scope_T + 1/scope_P)), a Poisson approximation.
  - The base variant uses primary counts and full scope. The robustness variants use multi-label counts and category-only scope.
- **Noise filter** (analysis/q6.json): the Q6 score sums seven features, F1 to F7. A claim is noisy if the score is 3 or more, and gets a "watch" flag if it is not noisy but has F1 = 2 (full definition under Q6).
- **Caveats: preprints are noisy signals.**
  - Counts measure how often papers use a term, not how much physics is being done.
  - One annotator did every audit, with no second rater.
  - Growth of a new term (such as "altermagnet") partly reflects papers adopting the vocabulary.
  - The arXiv harvest covers only 4 cond-mat categories.
  - Treat every number below as an estimate with the stated interval, not as a precise count.

## Q1 Landscape

**Headline:** In-scope quantum-materials output on arXiv grew about 12% year on year and is spread across 22 clusters. The largest are many-body theory, 2D/vdW magnetism and spintronics, unconventional/topological superconductivity, topological insulators/semimetals and altermagnetism; altermagnetism is the only cluster whose share clearly rose.

**Counts:** In-scope arXiv records: 9,878 trailing and 8,828 preceding (+11.9%). There are 22 clusters, 3 of them residual. The unclassified share of in-scope records is 9.94% trailing (982/9,878) and 9.70% preceding (856/8,828), down from about 17% in v1.

**Scope:** arXiv categories cond-mat.str-el, cond-mat.supr-con, cond-mat.mes-hall and cond-mat.mtrl-sci; windows trailing 2025-09-24..2026-09-23 and preceding 2024-09-24..2025-09-23. A record is in scope if it is listed in cond-mat.str-el or cond-mat.supr-con, or if its title+abstract matches a QM keyword group (records from other servers qualify only through keywords). Keyword groups: topological phases; moire/twisted bilayer/magic angle; strongly correlated/Hubbard/t-J/Hund's metal; superconductivity; spin liquids/spinons; frustrated magnetism/Kitaev/spin ice; altermagnets; kagome; Weyl/Dirac/nodal-line; heavy fermion/Kondo; charge/spin/pair density waves; quantum (anomalous/fractional) Hall/Chern; Majorana; flat bands; excitonic insulators; vdW/2D magnets; multiferroics; Mott; quantum criticality; nematicity; strange metals/non-Fermi liquids; skyrmions; Berry curvature/quantum geometry; quantum spin Hall; Wigner crystals; Luttinger liquids/anyons; and the named classes cuprate, nickelate, iron pnictide/chalcogenide, iridate and ruthenate. Context vetoes drop engineering, soft-matter and classical-wave senses. The verbatim rule is under Scope and method.

Counts are primary cluster labels for in-scope arXiv records. Multi-label counts for the broad clusters (topological insulators, Mott, vdW/spintronics, flat bands, CDW/excitons) include secondary topics, so trends use primary counts. Families come from analysis/materials.json (trailing window, primary cluster, v2 families plus the extended lexicon).

| Cluster | Trailing 12 mo (primary) | Trailing (multi-label) | Preceding 12 mo (primary) | Q2 trend | Q3 leading material families | Example IDs |
|---|---|---|---|---|---|---|
| Nickelate superconductivity (nickelate_sc) | 222 | 222 | 211 | flat (R 0.94) | RP bilayer/trilayer nickelates 168; infinite-layer nickelates 56 (La3Ni2O7 103, La4Ni3O10 30) | arXiv:2512.05956, arXiv:2601.17663 |
| Cuprate superconductivity (cuprate_sc) | 223 | 240 | 192 | flat (R 1.04) | Cuprates 223, every record (YBa2Cu3O7 35, Bi2Sr2CaCu2O8 26) | arXiv:2601.01643, arXiv:2512.13588 |
| Iron-based superconductivity (iron_based_sc) | 117 | 123 | 117 | flat (R 0.89) | Iron pnictides/chalcogenides 111 (FeSe 41, FeTe 19) | arXiv:2601.02707, arXiv:2601.18247 |
| Hydride / high-pressure superconductivity (hydride_high_pressure_sc) | 57 | 61 | 52 | flat (R 0.98) | Superhydrides 34 of 57 (LaH10 11, H3S 9) | arXiv:2510.25902, arXiv:2608.18865 |
| Kagome materials (kagome) | 308 | 310 | 313 | flat (R 0.88) | AV3Sb5 kagome metals 63 and other kagome metals 63 (tie); further kagome compounds 23 (CsV3Sb5 39, CsCr3Sb5 10) | arXiv:2510.10958, arXiv:2511.09402 |
| Altermagnetism (altermagnetism) | 660 | 678 | 414 | rising (R 1.42) | Altermagnet candidates 203 (MnTe 60, CrSb 50, RuO2 33); coverage 44% | arXiv:2603.21455, arXiv:2510.13781 |
| Fractional QAH / Chern insulators (fractional_qah_chern) | 364 | 379 | 363 | flat (R 0.90) | Graphene 75; TMDs 52 (MoTe2 32, GaAs 16); coverage 40% | arXiv:2511.22326, arXiv:2602.14184 |
| Rhombohedral multilayer graphene (rhombohedral_multilayer_graphene) | 81 | 102 | 63 | flat (R 1.15) | Graphene 81, every record; TMDs 8 (WSe2 4) | arXiv:2603.13498, arXiv:2511.17423 |
| Moire / twisted 2D materials (moire_twisted_2d) | 405 | 489 | 335 | flat (R 1.08) | Graphene 187; TMDs 149; hBN 42 (WSe2 65, MoTe2 29) | arXiv:2601.16851, arXiv:2606.31028 |
| Unconventional / topological superconductivity (unconventional_topological_sc) | 717 | 945 | 693 | flat (R 0.92) | Semiconductor nanowires/2DEGs 64 (40 by the word 'nanowire'/'quantum well' only); UTe2 & f-electron compounds 54 (UTe2 40, NbSe2 18, InAs 14); coverage 36% | arXiv:2604.25169, arXiv:2512.03908 |
| Spin liquids / frustrated magnetism (spin_liquid_frustrated) | 387 | 484 | 407 | declining (R 0.85) | Pyrochlore/triangular rare-earth magnets 64 (39 by the word 'pyrochlore' only); Kitaev materials 39 (RuCl3 21); coverage 34% | arXiv:2601.20766, arXiv:2606.08558 |
| Heavy fermions / Kondo / quantum criticality (heavy_fermion_kondo_qcp) | 162 | 274 | 151 | flat (R 0.96) | Heavy-fermion f-electron compounds 26; further heavy-fermion compounds 8 (CeCoIn5 6, CeRh6Ge4 4, SmB6 4); coverage 31% | arXiv:2602.23316, arXiv:2512.11965 |
| 2D/vdW magnets, topological magnetism, spintronics (vdw_magnets_topological_magnetism) | 820 | 1168 | 784 | flat (R 0.93) | vdW magnets 234; TMDs 38; tetradymites/MnBi2Te4 35 (CrSBr 57, MnBi2Te4 26); coverage 55% | arXiv:2607.28828, arXiv:2512.24091 |
| Density waves / nematicity / excitonic insulators (cdw_nematic_excitonic) | 390 | 744 | 310 | flat (R 1.12) | TMDs 132; excitonic-insulator/CDW compounds 49 (TaS2 31, WSe2 21) | arXiv:2511.21914, arXiv:2601.13890 |
| Topological insulators / semimetals (topological_insulators_semimetals) | 678 | 1149 | 712 | declining (R 0.85) | Weyl/Dirac semimetals 86; graphene 45; TMDs 36; tetradymite TIs 35 (WTe2 18, Bi2Se3 12); coverage 33% | arXiv:2602.11932, arXiv:2511.17412 |
| Flat bands / quantum geometry (flat_band_quantum_geometry) | 297 | 852 | 243 | flat (R 1.09) | No dominant family (coverage 23%; graphene 26, TMDs 18) | arXiv:2511.23218, arXiv:2510.19515 |
| Mott-Hubbard physics / strange metals (mott_hubbard_strange_metal) | 533 | 976 | 454 | flat (R 1.05) | Iridates & 3d Mott oxides 76; SrTiO3/KTaO3 oxides & interfaces 44 (SrTiO3 28, VO2 21); coverage 32% | arXiv:2602.22705, arXiv:2512.02154 |
| Ultrafast / Floquet / nonequilibrium (ultrafast_floquet_noneq) | 136 | 433 | 131 | flat (R 0.93) | No dominant family (coverage 21%; graphene 8, TMDs 6) | arXiv:2603.18182, arXiv:2603.28724 |
| Machine learning / AI (ml_ai) | 115 | 229 | 93 | flat (R 1.11) | No dominant family (coverage 14%; four families tied at 3) | arXiv:2512.10847, arXiv:2606.02794 |
| Quantum magnetism / ferroic order, residual (quantum_magnetism_ferroic_order) | 471 | 471 | 440 | flat (R 0.96) | No dominant family (coverage 25%; ferroelectrics/multiferroics 17, graphene 16, altermagnet candidates 15; SrRuO3 7, RuO2 5) | arXiv:2511.07579, arXiv:2606.26243 |
| Quantum many-body theory, residual (quantum_many_body_theory) | 1181 | 1181 | 988 | flat (R 1.07) | No material focus (coverage 2%) | arXiv:2609.06751, arXiv:2602.22322 |
| Other superconductivity, residual (other_superconductivity) | 572 | 572 | 506 | flat (R 1.01) | Conventional/device superconductors 59 (NbN 17, MgB2 10, NbTiN 9); semiconductor-nanowire hybrids 33 (23 by the word only); coverage 28% | arXiv:2602.24028, arXiv:2609.13882 |
| Unclassified, in scope (unclassified) | 982 | - | 856 | flat (R 1.03) | - | - |

Notes:
- **Residual clusters are large but loosely defined.** The three residual clusters hold 2,224 of the 9,878 trailing records (22.5%). They are catch-all categories, not coherent research fronts.
- **Two clusters have low label precision on a fresh audit.** rhombohedral_multilayer_graphene (81) and heavy_fermion_kondo_qcp (162) each scored 6/10 on an independent re-audit (Wilson 95% 0.31-0.83), against 15/15 in v2.
  - Rhombohedral graphene: the misfiled records are superconductivity or superconducting-diode papers where graphene is only the platform or the motivation (e.g. arXiv:2511.04480, arXiv:2608.01313).
  - Heavy fermions: the misfiled records have no Kondo content (e.g. arXiv:2601.00085, arXiv:2602.05607).
  - These two counts may overstate the topic by up to about 40%. Both clusters are 'flat' in Q2, so no trend label depends on them.
- **Remaining unclassified records** are mostly quant-ph, hep-th and physics.* papers. They are in scope only because they are cross-listed to cond-mat.str-el or cond-mat.supr-con.
- **Non-arXiv servers have much higher unclassified shares** (trailing): zenodo 25.0%, hal 32.2%, osti 10.9%, researchsquare 2.9%.

**Key IDs:** arXiv:2603.21455, arXiv:2512.05956, arXiv:2609.06751, arXiv:2511.22326, arXiv:2607.28828

Example IDs were taken from records judged correct in the v2 precision audit, so they illustrate each cluster but say nothing about its precision.

## Q2 Momentum

**Headline:** Altermagnetism is the only cluster with robust momentum: its share of in-scope output rose by about 40%. Topological insulators/semimetals declined in every variant, and spin liquid/frustrated magnetism declined weakly: its label turns flat if any one of three single months is dropped. All other clusters are flat within noise.

**Counts:**
- In-scope growth: 9,878 vs 8,828 (+11.9%), so a cluster's share rises only if it grows faster than that.
- Labels: 1 rising, 2 declining, 20 flat (22 clusters plus the unclassified bucket).
- Label flips: 2 (ml_ai, spin_liquid_frustrated).
- Slope contradictions: 0 (checked with both the 25-bucket and the 23-full-month fits). The check only tests rising/declining labels, so flat clusters cannot contradict it. unconventional_topological_sc is flat by R but has a significant monthly downward drift (t -2.7/-2.9).

Base variant: primary counts, full scope. Robustness notes give the multi-label and category-only-scope R with their labels, and the monthly share-slope t-statistic over 25 calendar buckets / 23 full months (analysis/momentum.json).

| Cluster | T | P | Share ratio R | 95% CI | Label | Robustness note |
|---|---|---|---|---|---|---|
| Altermagnetism (altermagnetism) | 660 | 414 | 1.42 | 1.26-1.62 | rising | multi-label R 1.44 (rising); category-only R 1.65 (rising); monthly t 7.2/6.1 |
| Rhombohedral multilayer graphene (rhombohedral_multilayer_graphene) | 81 | 63 | 1.15 | 0.83-1.60 | flat | multi-label R 1.09 (flat); category-only R 1.16 (flat); monthly t 1.5/1.6 |
| Density waves / nematicity / excitonic insulators (cdw_nematic_excitonic) | 390 | 310 | 1.12 | 0.97-1.31 | flat | multi-label R 1.01 (flat); category-only R 1.11 (flat); monthly t 1.0/1.0 |
| Machine learning / AI (ml_ai) | 115 | 93 | 1.11 | 0.84-1.45 | flat | FLIP: multi-label R 1.26 (rising, CI 1.03-1.55); category-only R 1.12 (flat); monthly t 1.4/1.8 |
| Flat bands / quantum geometry (flat_band_quantum_geometry) | 297 | 243 | 1.09 | 0.92-1.30 | flat | multi-label R 1.07 (flat); category-only R 1.01 (flat); monthly t 2.0/2.0 |
| Moire / twisted 2D materials (moire_twisted_2d) | 405 | 335 | 1.08 | 0.93-1.25 | flat | multi-label R 1.04 (flat); category-only R 0.92 (flat); monthly t 1.5/1.3 |
| Quantum many-body theory, residual (quantum_many_body_theory) | 1181 | 988 | 1.07 | 0.98-1.17 | flat | multi-label R 1.07 (flat); category-only R 1.09 (flat); monthly t 1.0/1.6 |
| Mott-Hubbard physics / strange metals (mott_hubbard_strange_metal) | 533 | 454 | 1.05 | 0.92-1.19 | flat | multi-label R 1.00 (flat); category-only R 1.03 (flat); monthly t -0.6/-0.6 |
| Cuprate superconductivity (cuprate_sc) | 223 | 192 | 1.04 | 0.85-1.26 | flat | multi-label R 1.01 (flat); category-only R 1.05 (flat); monthly t -0.8/0.1 |
| Unclassified, in scope (unclassified) | 982 | 856 | 1.03 | 0.93-1.13 | flat | multi-label R 1.03 (flat); category-only R 1.03 (flat); monthly t 0.1/0.4 |
| Other superconductivity, residual (other_superconductivity) | 572 | 506 | 1.01 | 0.89-1.14 | flat | multi-label R 1.01 (flat); category-only R 1.03 (flat); monthly t -1.0/-0.7 |
| Hydride / high-pressure superconductivity (hydride_high_pressure_sc) | 57 | 52 | 0.98 | 0.67-1.43 | flat | multi-label R 0.94 (flat); category-only R 0.92 (flat); monthly t -1.8/-0.8 |
| Heavy fermions / Kondo / quantum criticality (heavy_fermion_kondo_qcp) | 162 | 151 | 0.96 | 0.77-1.20 | flat | multi-label R 0.94 (flat); category-only R 0.98 (flat); monthly t -0.3/-1.1 |
| Quantum magnetism / ferroic order, residual (quantum_magnetism_ferroic_order) | 471 | 440 | 0.96 | 0.84-1.09 | flat | multi-label R 0.96 (flat); category-only R 0.97 (flat); monthly t -0.9/-0.4 |
| Nickelate superconductivity (nickelate_sc) | 222 | 211 | 0.94 | 0.78-1.14 | flat | multi-label R 0.94 (flat); category-only R 0.95 (flat); monthly t -0.0/-0.5 |
| 2D/vdW magnets, topological magnetism, spintronics (vdw_magnets_topological_magnetism) | 820 | 784 | 0.93 | 0.84-1.04 | flat | multi-label R 0.95 (flat); category-only R 0.96 (flat); monthly t -1.3/-1.4 |
| Ultrafast / Floquet / nonequilibrium (ultrafast_floquet_noneq) | 136 | 131 | 0.93 | 0.73-1.18 | flat | multi-label R 1.03 (flat); category-only R 0.81 (flat); monthly t -1.1/-0.4 |
| Unconventional / topological superconductivity (unconventional_topological_sc) | 717 | 693 | 0.92 | 0.83-1.03 | flat | multi-label R 0.98 (flat); category-only R 0.91 (flat); monthly t -2.7/-2.9 (downward drift, not significant by R) |
| Fractional QAH / Chern insulators (fractional_qah_chern) | 364 | 363 | 0.90 | 0.77-1.04 | flat | multi-label R 0.91 (flat); category-only R 0.92 (flat); monthly t -0.4/-0.6 |
| Iron-based superconductivity (iron_based_sc) | 117 | 117 | 0.89 | 0.69-1.16 | flat | multi-label R 0.91 (flat); category-only R 0.89 (flat); monthly t 0.2/-0.5 |
| Kagome materials (kagome) | 308 | 313 | 0.88 | 0.75-1.03 | flat | multi-label R 0.89 (flat); category-only R 0.88 (flat); monthly t -2.0/-2.3 (borderline decline) |
| Topological insulators / semimetals (topological_insulators_semimetals) | 678 | 712 | 0.85 | 0.76-0.95 | declining | multi-label R 0.86 (declining); category-only R 0.77 (declining); monthly t -1.6/-2.8 |
| Spin liquids / frustrated magnetism (spin_liquid_frustrated) | 387 | 407 | 0.85 | 0.74-0.98 | declining | FLIP: multi-label R 0.86 (declining); category-only R 0.88 (flat, CI 0.76-1.02); monthly t -2.0/-1.7 |

Label rule (verbatim): rising if R >= 1.10 and CI lower bound > 1.0; declining if R <= 0.90 and CI upper bound < 1.0; otherwise flat.

Interpretation and caveats:
- **Multiple comparisons.** With 23 rows tested at 95%, about one spurious label is expected by chance. Only altermagnetism would survive a Bonferroni-style correction, so the two decliners are marginal.
- **Altermagnetism may be partly vocabulary.** The cluster matches on the word "altermagnet", so part of its rise may be papers adopting the new term rather than new research.
- **October 2025 dip is noise, but the spin-liquid label depends on it.** Only two clusters dip in 2025-10: topological (34 records vs 56 expected, z -3.1) and spin liquid (17 vs 32, z -2.7). It is not a harvest artefact: every harvest slice reconciles, and 2025-10 category totals are typical. It is not a baseline effect either: the keyword-only share is 0.319, against a monthly range of 0.29-0.35, and the dip persists in category-only scope. Similar single-month outliers occur elsewhere (5 of 529 cluster-months have |z| >= 3). Dropping 2025-10 leaves topological declining (R 0.875, CI 0.78-0.98) but turns spin liquid flat (R 0.88, CI 0.76-1.02). Spin liquid also turns flat when 2025-05 or 2026-08 is dropped instead, so treat its decline as fragile (notes/audit/q1q2_numbers.md).
- **CI width.** The Poisson CI treats T and scope_T as independent even though T is a subset of scope_T, so it is slightly wider than a binomial CI.

**Key IDs:**
- Rising (altermagnetism): arXiv:2511.06865, arXiv:2602.05745, arXiv:2602.08790
- Declining (topological_insulators_semimetals): arXiv:2511.14454, arXiv:2604.25758, arXiv:2604.26480
- Declining, full scope only (spin_liquid_frustrated): arXiv:2603.14682, arXiv:2601.03138, arXiv:2604.24744

## Q3 Materials

**Headline:** Altermagnet candidates are the one robust materials story: the family grew from 128 to 254 records (R 1.77, 95% CI 1.43-2.20), led by CrSb (R 2.32, 1.39-3.90). MnTe is marginal (R 1.49, 1.00-2.22) and RuO2 is flat. Kitaev materials (R 0.63), AV3Sb5 kagome metals (R 0.72), further kagome compounds such as RTi3Bi4, LaRu3Si2 and FeSn (R 0.64), and the compound MnBi2Te4 (R 0.64) appear to be losing share, but their CIs only just exclude 1 (upper bounds 0.90-0.995) and ignore author clustering; La3Ni2O7 is borderline (R 0.78, 0.60-1.01). Only the altermagnet family survives a multiple-comparison correction.

**Counts:**
- Population: in-scope arXiv records, 9,877 trailing (one record lacks a text row in the corpus) and 8,828 preceding.
- Families: v2 families plus 11 extended families.
- Family coverage varies widely by cluster: 0.99-1.00 for the nickelate, cuprate and rhombohedral clusters, but 0.02 for many-body theory.
- Share trends (support T+P >= 30; 34 families and 25 formulas ranked): 1 family (altermagnet candidates) and 3 formulas (CrSb, YBa2Cu3O7, MnTe; MnTe only barely, lower bound 1.001) grew with CIs above 1. 3 families (Kitaev materials, AV3Sb5 kagome metals, further kagome compounds) and 1 formula (MnBi2Te4) declined with CIs below 1.

Per-cluster leading families (trailing window, primary cluster; analysis/materials.json):

Family names used in these tables and in Q1: RP nickelates = bilayer/trilayer Ruddlesden-Popper nickelates (La3Ni2O7, La4Ni3O10); infinite-layer nickelates = square-planar RNiO2; graphene = any graphene or graphite (the regex matches the word 'graphene', so it is not limited to multilayers); TMDs = transition-metal dichalcogenides; semiconductor nanowires/2DEGs = InAs, InSb, GaAs, HgTe, GaN, ZnO plus the words 'nanowire' and 'quantum well'; ferroelectrics/multiferroics = BiFeO3, In2Se3, Cr2O3 ... plus the word 'multiferroic'; pyrochlore/triangular rare-earth magnets = Yb2Ti2O7, NaYbSe2, herbertsmithite ... plus the word 'pyrochlore'; iridates & 3d Mott oxides = Sr2IrO4, VO2, V2O3, RNiO3, manganites (also matches 1T-TaS2); conventional/device superconductors = NbN, NbTiN, MgB2, Nb3Sn, K3C60; further kagome compounds = RTi3Bi4, LaRu3Si2, FeSn, Nb3Cl8, RNb6Sn6, RFe6Ge6. The full key-to-name map is in notes/audit/q3q4.md.

| Cluster | N (T, primary) | Share naming a family (v2 -> +ext) | Leading families (n) | Top formulas (n) | Exemplar |
|---|---|---|---|---|---|
| Nickelate superconductivity (nickelate_sc) | 222 | 0.99 -> 0.99 | RP bilayer/trilayer nickelates 168; infinite-layer nickelates 56; cuprates 44 | La3Ni2O7 103, La4Ni3O10 30, SrLaAlO4 11 | arXiv:2509.20727 |
| Cuprate superconductivity (cuprate_sc) | 223 | 1.00 -> 1.00 | cuprates 223; spin-chain/ladder compounds 6; iron pnictides/chalcogenides 6 | YBa2Cu3O7 35, Bi2Sr2CaCu2O8 26, La2-xSrxCuO4 11 | arXiv:2509.19675 |
| Iron-based superconductivity (iron_based_sc) | 117 | 0.95 -> 0.95 | iron pnictides/chalcogenides 111; SrTiO3/KTaO3 oxides & interfaces 8; semiconductor nanowires/2DEGs 3 | FeSe 41, FeTe 19, SrTiO3 7 | arXiv:2509.23591 |
| Hydride / high-pressure superconductivity (hydride_high_pressure_sc) | 57 | 0.68 -> 0.68 | superhydrides 34; graphene 4; conventional/device superconductors 2 | LaH10 11, H3S 9, LaSc2H24 5 | arXiv:2510.10720 |
| Kagome materials (kagome) | 308 | 0.46 -> 0.53 | other kagome metals 63; AV3Sb5 kagome metals 63; further kagome compounds 23 | CsV3Sb5 39, CsCr3Sb5 10, Co3Sn2S2 10 | arXiv:2510.01053 |
| Altermagnetism (altermagnetism) | 660 | 0.38 -> 0.44 | altermagnet candidates 203; ferroelectrics/multiferroics 34 (23 by the word 'multiferroic' only); vdW magnets 13 | MnTe 60, CrSb 50, RuO2 33 | arXiv:2509.19932 |
| Fractional QAH / Chern insulators (fractional_qah_chern) | 364 | 0.40 -> 0.40 | graphene 75; TMDs 52; Weyl/Dirac list 35 (33 of these are MoTe2, double-counted with TMDs) | MoTe2 32, GaAs 16, WSe2 12 | arXiv:2511.12231 |
| Rhombohedral multilayer graphene (rhombohedral_multilayer_graphene) | 81 | 1.00 -> 1.00 | graphene 81; TMDs 8; hBN 4 | WSe2 4 (all other formulas 1) | arXiv:2511.16578 |
| Moire / twisted 2D materials (moire_twisted_2d) | 405 | 0.81 -> 0.82 | graphene 187; TMDs 149; hBN 42 | WSe2 65, MoTe2 29, WS2 25 | arXiv:2510.02444 |
| Unconventional / topological superconductivity (unconventional_topological_sc) | 717 | 0.34 -> 0.36 | semiconductor nanowires/2DEGs 64 (40 by the word 'nanowire'/'quantum well' only); UTe2 & f-electron compounds 54; TMDs 46 | UTe2 40, NbSe2 18, InAs 14 | arXiv:2604.24858 |
| Spin liquids / frustrated magnetism (spin_liquid_frustrated) | 387 | 0.30 -> 0.34 | pyrochlore/triangular rare-earth magnets 64; Kitaev materials 39; iridates & 3d Mott oxides 8 | RuCl3 21, Na3Co2SbO6 4, Na2Co2TeO6 4 | arXiv:2509.20199 |
| Heavy fermions / Kondo / quantum criticality (heavy_fermion_kondo_qcp) | 162 | 0.26 -> 0.31 | UTe2 & f-electron compounds 26; further heavy-fermion compounds 8; semiconductor nanowires/2DEGs 5 | CeCoIn5 6, CeRh6Ge4 4, SmB6 4 | arXiv:2509.19684 |
| 2D/vdW magnets, topological magnetism, spintronics (vdw_magnets_topological_magnetism) | 820 | 0.43 -> 0.55 | vdW magnets 234; ferroelectrics/multiferroics 90 (59 by the word 'multiferroic' only); TMDs 38 | CrSBr 57, MnBi2Te4 26, CrI3 22 | arXiv:2509.22303 |
| Density waves / nematicity / excitonic insulators (cdw_nematic_excitonic) | 390 | 0.52 -> 0.55 | TMDs 132; excitonic-insulator/CDW compounds 49; iridates & 3d Mott oxides 22 | TaS2 31, WSe2 21, MoSe2 20 | arXiv:2510.00556 |
| Topological insulators / semimetals (topological_insulators_semimetals) | 678 | 0.31 -> 0.33 | Weyl/Dirac semimetals 86; graphene 45; TMDs 36 | WTe2 18, Bi2Se3 12, Bi2Te3 9 | arXiv:2510.06618 |
| Flat bands / quantum geometry (flat_band_quantum_geometry) | 297 | 0.21 -> 0.23 | graphene 26; TMDs 18; SrTiO3/KTaO3 oxides & interfaces 5 | MoS2 5, CuMnAs 2, NbOCl2 2 | arXiv:2601.08586 |
| Mott-Hubbard physics / strange metals (mott_hubbard_strange_metal) | 533 | 0.30 -> 0.32 | iridates & 3d Mott oxides 76; SrTiO3/KTaO3 oxides & interfaces 44; cuprates 22 | SrTiO3 28, VO2 21, KTaO3 14 | arXiv:2509.20337 |
| Ultrafast / Floquet / nonequilibrium (ultrafast_floquet_noneq) | 136 | 0.15 -> 0.21 | graphene 8; TMDs 6; conventional/device superconductors 6 | K3C60 3, GeS 2, SnS 2 | arXiv:2603.28724 |
| Machine learning / AI (ml_ai) | 115 | 0.12 -> 0.14 | No dominant family: 4-way tie at 3 (cuprates, semiconductor quantum wells/nanowires, iridates/Mott oxides, graphene) | WS2 1, WSe2 1, Co2TiSn 1 | arXiv:2512.10909 (semiconductor quantum wells; no family leads) |
| Quantum magnetism / ferroic order, residual (quantum_magnetism_ferroic_order) | 471 | 0.18 -> 0.25 | ferroelectrics/multiferroics 17; graphene 16; altermagnet candidates 15 | SrRuO3 7, RuO2 5, SrTiO3 5 | arXiv:2604.05220 |
| Quantum many-body theory, residual (quantum_many_body_theory) | 1181 | 0.02 -> 0.02 | graphene 9; semiconductor nanowires/2DEGs 8; cuprates 3 | Fe4S4 4, GaAs 3, FP64 2 (FP64 is an extractor false positive) | arXiv:2512.20559 |
| Other superconductivity, residual (other_superconductivity) | 571 (572 in Q1; the one record without a text row) | 0.18 -> 0.28 | conventional/device superconductors 59; semiconductor nanowires/2DEGs 33; TMDs 24 | NbN 17, MgB2 10, NbTiN 9 | arXiv:2509.19697 |

Fastest-growing formulas (T+P >= 30, ranked by CI lower bound; R is the share ratio against the in-scope baseline):

| Rank | Formula | T vs P | R (95% CI) | Note | Exemplar |
|---|---|---|---|---|---|
| 1 | CrSb | 52 vs 20 | 2.32 (1.39-3.90) | altermagnet | arXiv:2509.21303 |
| 2 | YBa2Cu3O7 | 38 vs 18 | 1.89 (1.08-3.31) | concentrated in a few author series (5 records share one author and 4 share another); weak evidence | arXiv:2509.26095 |
| 3 | MnTe | 65 vs 39 | 1.49 (1.00-2.22) | altermagnet; lower bound touches 1 | arXiv:2509.20120 |
| 4 | WSe2 | 131 vs 91 | 1.29 (0.98-1.68) | CI includes 1 | arXiv:2510.11088 |
| 5 | MoSe2 | 51 vs 33 | 1.38 (0.89-2.14) | CI includes 1 | arXiv:2510.19596 |

Family-level trends:
- **Growing:** altermagnet candidates, 254 vs 128, R 1.77 (1.43-2.20). This is the only family whose CI excludes 1.
- **Declining:**
  - Kitaev materials: 49 vs 70, R 0.63 (0.43-0.90)
  - MnBi2Te4 (formula, 37 vs 52): R 0.64 (0.42-0.97). The wider tetradymite family (Bi2Se3, Bi2Te3, MnBi2Te4) is not significant: R 0.77 (0.58-1.01).
  - AV3Sb5 kagome metals: 64 vs 80, R 0.72 (0.51-0.995)
  - Further kagome compounds (RTi3Bi4, LaRu3Si2, FeSn ...): 37 vs 52, R 0.64 (0.42-0.97). The broader 'other kagome metals' family is flat: R 0.81 (0.63-1.04).
- **Borderline:** La3Ni2O7, 105 vs 121, R 0.78 (0.60-1.01).
- **Flat:**
  - RuO2: R 1.11 (0.74-1.68)
  - CrSBr: R 1.07
  - bilayer/trilayer nickelates: R 0.96
  - graphene: R 0.98
  - TMDs: R 1.10 (0.97-1.24)

Caveats:
- **Families overlap.** MoTe2/WTe2 belong to both TMDs and Weyl/Dirac semimetals, and MnBi2Te4 to both tetradymites and vdW magnets, so family counts are not additive.
- **Generic words inflate some families.** Some families match framing words rather than compounds. In the trailing window, the word alone gives:
  - "multiferroic": 23 of 34 ferroelectric/multiferroic hits in altermagnetism and 59 of 90 in vdW magnets.
  - "nanowire"/"quantum well": 40 of 64 semiconductor hits in unconventional/topological SC and 23 of 33 in other superconductivity.
  - "pyrochlore": 39 of 64 hits in spin liquids.
  - "cuprate": 41 of 44 cuprate hits in nickelate papers, mostly comparisons.
  - Double counts: the iridate/Mott-oxide family in the CDW cluster is 1T-TaS2 in 21 of 22 records, and the Weyl/Dirac family in FQAH/moire is MoTe2 in 33 of 35 and 29 of 31 records.
- **Multiple comparisons.** 59 families and formulas were ranked, so about 3 CIs would exclude 1 by chance. Only the altermagnet-candidate family survives a Bonferroni-style correction (z 5.2 against about 3.3 needed; CrSb is 3.2).
- **Extractor gaps.** The formula extractor misses formulas inside parentheses (e.g. SrCu2(BO3)2) and alloy notation.
- **Overdispersion.** The Poisson CI ignores author-series clustering.

**Key IDs:** arXiv:2509.21303, arXiv:2509.20120, arXiv:2509.19932, arXiv:2509.26095, arXiv:2510.01053

## Q4 Methods

**Headline:** The dominant experimental techniques (trailing-window in-scope arXiv papers) are magnetotransport/Hall/resistivity (1,098; 11.1%), optical/IR/THz/Raman (510), specific heat/magnetization (508) and diffraction/electron microscopy (485), plus thin-film growth (578, a synthesis tag). The dominant computational techniques are DFT/first-principles (1,490; 15.1%), tight-binding/continuum models (850), Hartree-Fock/mean-field (636) and DMRG/tensor networks (476). The mix is stable: 22 of 25 methods are flat. Machine learning (R 1.37, 1.16-1.62), exact diagonalization (R 1.36, 1.12-1.66) and quantum Monte Carlo (R 1.28, 1.06-1.54) have CIs above 1, but with 25 methods tested only machine learning clearly survives a Bonferroni correction (ED is borderline). The share of papers with a computational tag rose slightly (R 1.07, 1.01-1.13) while experimental papers were flat (R 0.97, 0.92-1.03).

**Counts:**
- In-scope arXiv: 9,878 trailing vs 8,828 preceding.
- 25 methods: 15 experimental, 10 computational. 7 of them were refined after a precision audit (382 hand-judged items).
- Papers with at least one experimental tag: 3,299 (33.4%) vs 3,036 (34.4%), R 0.97 (0.92-1.03).
- Papers with at least one computational tag: 3,732 (37.8%) vs 3,133 (35.5%), R 1.07 (1.01-1.13).
- Computational-only papers: 27.9% vs 26.2%, R 1.07 (1.00-1.14).
- Papers with no method tag: 38.7%.
- Dominant experimental methods (trailing papers): magnetotransport/Hall 1,098; thin-film growth 578 (synthesis, not a measurement); optical/IR/THz/Raman 510; specific heat/magnetization 508; X-ray/electron diffraction and microscopy 485; ultrafast 311; ARPES 310; neutron 271; STM/STS 258; RIXS 164.
- Dominant computational methods (trailing papers): DFT 1,490; tight-binding/Wannier/continuum 850; Hartree-Fock/mean field/BdG 636; DMRG/tensor networks 476; phonons/e-ph 360; machine learning 354; QMC 277; exact diagonalization 256.

Method table (refined lexicon; analysis/methods.json). The trend column says "grew" when the 95% CI excludes 1.

| Method | Kind | Trailing | Preceding | Share of in-scope (T) | R | 95% CI | Trend |
|---|---|---|---|---|---|---|---|
| DFT / first-principles | comp | 1490 | 1242 | 15.1% | 1.07 | 0.99-1.16 | flat |
| Magnetotransport / Hall / resistivity | exp | 1098 | 1051 | 11.1% | 0.93 | 0.85-1.02 | flat |
| Tight-binding / Wannier / continuum & effective models | comp | 850 | 763 | 8.6% | 1.00 | 0.90-1.10 | flat |
| Hartree-Fock / mean field / RPA / BdG | comp | 636 | 533 | 6.4% | 1.07 | 0.95-1.20 | flat |
| Thin-film growth (MBE, PLD, CVD, sputtering) | exp | 578 | 490 | 5.9% | 1.05 | 0.93-1.19 | flat |
| Optical / infrared / THz / Raman / magneto-optics | exp | 510 | 423 | 5.2% | 1.08 | 0.94-1.23 | flat |
| Specific heat / magnetization / thermodynamics | exp | 508 | 493 | 5.1% | 0.92 | 0.81-1.05 | flat |
| X-ray / electron diffraction & electron microscopy | exp | 485 | 407 | 4.9% | 1.06 | 0.93-1.22 | flat |
| DMRG / tensor networks | comp | 476 | 377 | 4.8% | 1.13 | 0.98-1.30 | flat |
| Phonons / electron-phonon / Eliashberg | comp | 360 | 310 | 3.6% | 1.04 | 0.89-1.21 | flat |
| Machine learning / neural networks | comp | 354 | 231 | 3.6% | 1.37 | 1.16-1.62 | grew |
| Ultrafast pump-probe / time-resolved | exp | 311 | 278 | 3.1% | 1.00 | 0.85-1.18 | flat |
| ARPES / photoemission | exp | 310 | 263 | 3.1% | 1.05 | 0.89-1.25 | flat |
| Quantum Monte Carlo | comp | 277 | 194 | 2.8% | 1.28 | 1.06-1.54 | grew |
| Neutron scattering | exp | 271 | 241 | 2.7% | 1.00 | 0.84-1.20 | flat |
| STM / STS / QPI | exp | 258 | 215 | 2.6% | 1.07 | 0.89-1.29 | flat |
| Exact diagonalization | comp | 256 | 168 | 2.6% | 1.36 | 1.12-1.66 | grew |
| High pressure / diamond anvil cell | exp | 186 | 160 | 1.9% | 1.04 | 0.84-1.29 | flat |
| DMFT / DFT+DMFT / cluster DMFT | comp | 182 | 157 | 1.8% | 1.04 | 0.83-1.28 | flat |
| RIXS / resonant & soft x-ray spectroscopy | exp | 164 | 145 | 1.7% | 1.01 | 0.81-1.27 | flat |
| GW / BSE / hybrid functionals / quantum chemistry (beyond DFT) | comp | 151 | 125 | 1.5% | 1.08 | 0.85-1.37 | flat |
| NMR / NQR | exp | 97 | 91 | 1.0% | 0.95 | 0.71-1.27 | flat |
| Quantum oscillations | exp | 80 | 72 | 0.8% | 0.99 | 0.72-1.37 | flat |
| muSR | exp | 73 | 85 | 0.7% | 0.77 | 0.56-1.05 | flat |
| NV-center / quantum sensing / scanning SQUID magnetometry | exp | 48 | 36 | 0.5% | 1.19 | 0.77-1.84 | flat |

Experimental vs computational split:

| | Trailing | Preceding | R (95% CI) |
|---|---|---|---|
| >= 1 experimental tag | 3,299 (33.4%) | 3,036 (34.4%) | 0.97 (0.92-1.03) |
| >= 1 computational tag | 3,732 (37.8%) | 3,133 (35.5%) | 1.07 (1.01-1.13) |
| both kinds | 972 | 824 | - |
| computational, no experimental tag | 27.9% | 26.2% | 1.07 (1.00-1.14) |
| no experimental tag (upper bound on theory-only) | 66.6% | 65.6% | - |
| no method tag at all | 38.7% | 39.5% | - |

The direction does not depend on the refinement: the unrefined v2 lexicon gives R 0.99 for experimental and 1.06 for computational.

Co-occurrences (trailing):
- 46% of DMFT papers also use DFT (lift 3.06).
- 35% of ARPES papers also use DFT (lift 2.35, down from 2.81).
- 27% of ML papers also use DFT (lift 1.76).
- Transport papers carry a computational tag less often than average: 22% (245/1,098) against 38% of all in-scope papers (lift 0.59).

Caveats:
- **Precision.** Seven methods were refined from precision as low as 0.2-0.4. After refinement the pooled precision is 0.74-0.95, but this is optimistic because the rules were tuned on some of the audit items. Fresh checks gave 0.80 for quantum oscillations and 0.70 for high pressure.
- **Recall.** Refinement cuts recall, so the refined transport and optical counts are undercounts. Transport dropped from 1,875 to 1,098 records and 1 of 6 audited dropped items was a real use (about 12% undercount). Optical dropped from 841 to 510 and 2 of 6 were real (about 22%). These are rough estimates from n = 6.
- **Growth claims.** Machine learning's v2 precision is 0.70 (n = 10, not refined); exact diagonalization's is 0.80 and QMC's 0.90. With 25 methods tested (Bonferroni z about 3.09), ML survives (z 3.7), ED is borderline (z 3.08) and QMC does not (z 2.6).
- **Single annotator.** One annotator made every judgment, with no inter-rater check.

**Key IDs:**
- Machine learning, fastest growing: arXiv:2602.15178
- Exact diagonalization: arXiv:2605.27524
- DMRG/tensor networks: arXiv:2512.06768
- DFT: arXiv:2602.07897
- Transport: arXiv:2604.26480
- Optical/Raman: arXiv:2511.15452
- Thin-film growth: arXiv:2605.22932
- Thermodynamics: arXiv:2606.10300
- Tight-binding: arXiv:2607.20624
- Mean field: arXiv:2510.04132

## Q5 Beyond arXiv

**Headline:** Beyond arXiv, only OSTI (a lagging, journal-dated layer) and Research Square add a meaningful number of unique on-topic records. Together, the non-arXiv servers other than Zenodo add only about 3-4% on top of arXiv in the trailing window, and about 80% of that is OSTI journal accepted manuscripts rather than preprints (the preprint servers add under 1%). Zenodo's point estimate is larger (about 266 unique on-topic trailing records, 95% range 118-520), but only 20% of audited Zenodo records are on-topic and 68% are fringe, so it is excluded as noise. HAL mostly duplicates arXiv (78%), and TechRxiv has 2 fringe records.

**Counts:**
- 7 non-arXiv servers, 3,303 corpus records (3,298 in window). Audit: 152 records hand-judged (random.Random(11), up to 25 per server).
- Records T / P and noise rating: OSTI 590 / 847 (low; journal-dated accepted manuscripts), Research Square 109 / 88 (low), Zenodo 1,336 / 122 (high; 68% fringe), HAL 95 / 28 (medium; 78% arXiv duplicates), Preprints.org 25 / 30 (high), ChemRxiv 14 / 12 (medium), TechRxiv 1 / 1 (high).
- Unique on-topic records, trailing window, all non-arXiv servers except Zenodo: about 330-390 (327 [225-403] with OSTI censoring-corrected; 385 [265-472] with the pooled dup share), against 9,878 arXiv in-scope records (3-4%). OSTI accounts for about 80% of it; Research Square + ChemRxiv + Preprints.org add about 80 (0.8%).
- OSTI: at most about 600 unique on-topic records over both windows (censoring-corrected 603 [419-722]). Research Square: 110 [74-132]. Both are upper bounds: arXiv dedup covered only 4 cond-mat categories from 2024-09-24.

Per-server table (analysis/q5.json, notes/q5_beyond_arxiv.md):
- **Yield** = kept phrase-filter hits / records fetched, from the harvest logs.
- **arXiv dup** = the record declares an arXiv ID, or its title matches a corpus title exactly or with token-set Jaccard >= 0.8. This is a lower bound, because the arXiv corpus covers only 4 cond-mat categories.
- **On-topic**, **Fringe** and **Off-topic** are shares of all audited records, duplicates included; the rest are arXiv duplicates or datasets/reports. The unique-on-topic estimate instead uses the on-topic rate among non-duplicates (analysis/q5.json `on_topic_rate_among_non_duplicates`): OSTI 74% (14/19), Research Square 75% (12/16), ChemRxiv 42% (10/24), Preprints.org 54% (13/24), HAL 0% (0/7), Zenodo 20% (5/25), TechRxiv 0/2.
- **Unique on-topic** = records × (1 − dup share) × on-topic rate, with a Wilson 95% range.

| Server | Records T / P | Yield (kept/fetched) | arXiv-duplicate share | On-topic (all audited) | Fringe | Off-topic | Unique on-topic T+P [95%] (T only) | Noise rating | Unique contribution |
|---|---|---|---|---|---|---|---|---|---|
| osti | 590 / 847 | 0.13 | 29.8% (43% for records dated 2026) | 56% | 0% | 16% | 744 [517-890]; censoring-corrected 603 [419-722] (T 305 [212-365] with the pooled dup share; 248 [172-296] censoring-corrected) | low | DOE-lab journal accepted manuscripts (1,150), 55 reports, 19 datasets. Journal-dated: arXiv comes first in 87% of matches, with a median lead of 127 days. |
| researchsquare | 109 / 88 | 0.026 | 25.4% | 48% | 8% | 8% | 110 [74-132] (T 61 [41-73]) | low | Springer Nature "In Review" submissions. The trailing count is likely overstated by roughly 10-35% because recent records have not reached arXiv yet (the dup share is 20% for trailing records, 32% for preceding, and 44-46% for 2025Q1-Q2). |
| chemrxiv | 14 / 12 | 0.009 | 3.8% | 40% | 4% | 52% | 10 [6-15] (T 6 [3-8]) | medium | A few chemistry-side materials papers. Many phrase collisions ("flat band potential", molecular "moire"). |
| preprints_org | 25 / 30 | 0.012 | 5.5% | 52% | 24% | 20% | 28 [18-38] (T 13 [8-17]) | high | Occasional early postings, one 221 days before its arXiv version. Needs manual screening. |
| hal | 95 / 28 | 0.57 | 78.0% | 0% (0/7 non-dup) | 4% | 20% | 0 [0-10] (T 0 [0-7]) | medium | Essentially none. The 95 vs 28 split is an artefact of HAL retyping preprints once they are published. |
| zenodo | 1,336 / 122 | 0.77 | 0.5% | 20% | 68% | 12% | 290 [129-567] (T 266 [118-520]) | high | Mostly fringe; one uploader accounts for 152 records. Its 11× growth tracks a 7.3× surge in uploads across all of Zenodo. |
| techrxiv | 1 / 1 | 0.002 | 0% | 0/2 | 2/2 | 0 | 0 [0-1] | high | None (n = 2). |

Recommendations:
- osti: treat as a secondary, lagging layer of published output. Dedupe it and keep it out of preprint trend counts.
- researchsquare: include after dedup, reported separately.
- chemrxiv and preprints_org: use only screened qualitative examples.
- hal: drop for counting.
- zenodo and techrxiv: exclude.

Caveats:
- One reviewer audited 25 records per server, so each rate carries about ±15-20 points of uncertainty.
- The OSTI harvest was truncated on 3 terms (superconductivity, nickelate, strongly correlated): 15,925 of 20,971 API hits were fetched, so OSTI record counts are lower bounds. All 'unique' figures are upper bounds, because arXiv dedup used only 4 cond-mat categories from 2024-09-24. The Wilson ranges cover only the on-topic sampling, not dup-share uncertainty.
- Declared arXiv IDs can be false positives: doi:10.20944/preprints202510.2304.v1 declares the ID of the paper it re-analyses, not its own arXiv version.

**Key IDs:**
- osti: osti:3818104 (on-topic, PRL accepted manuscript, no arXiv match in corpus), osti:3384904 (on-topic, PRB AM), osti:2560506 (on-topic, PRX; early-dated, arXiv version may predate the harvest), osti:2537889 (DOE technical report)
- researchsquare: doi:10.21203/rs.3.rs-4705720/v1, doi:10.21203/rs.3.rs-7287112/v1
- chemrxiv: doi:10.26434/chemrxiv.15002414/v1, doi:10.26434/chemrxiv-2025-95t55
- preprints_org: doi:10.20944/preprints202509.2167.v1, doi:10.20944/preprints202512.0291.v1
- hal: hal:hal-05482717 (duplicate of arXiv:2601.19473), hal:hal-04983943 (fringe)
- zenodo: doi:10.5281/zenodo.21765888 (on-topic by audit; independent author, not peer reviewed), doi:10.5281/zenodo.21357073 (fringe)
- techrxiv: doi:10.36227/techrxiv.176369865.59370636/v1 (fringe)

## Q6 Noise

**Headline:** Of 18 scored claims, 8 are flagged noisy (score >= 3). The strongest noise signals are the room-temperature superconductivity claims (LK-99, LaSc2H24, graphite) and Microsoft's Majorana parity readout. Bulk RuO2 altermagnetism is strongly disfavoured: 11 in-window bulk-crystal experiments from about 10 groups find no order, and the debate has moved to strained films. Chiral zero-field UTe2 superconductivity is disfavoured but not independently refuted: the 4 critical in-window studies are STM from one author-linked network, and the direct Kerr TRSB null is pre-window. All stances are abstract-level labels.

**Counts:**
- 18 claims scored: 8 noisy, 1 watch (Hg-1223).
- 184 abstracts stance-labelled (186 labels; 176 abstracts in window). The labelled sets are a small part of each topic neighbourhood (e.g. 18 of 104 RuO2 hits), so all counts are floors.
- Title sweep of corpus/arxiv.jsonl, trailing vs preceding:
  - Comment/Reply: 22 vs 22
  - "Absence of / No evidence": 20 vs 30
  - "Revisiting": 26 vs 35
  - Withdrawn: 8 vs 3; none of the withdrawals touches a Q6 claim.

**Noise filter:** Each claim's score is the sum of seven features (analysis/noise_filter.py, analysis/q6.json); 'same group' means sharing at least one author (first initial + surname):
- F1 +2: no supportive experiment in the corpus from outside the original group.
- F2 +1 per in-window Comment/Reply/Response or null-result record, max +2.
- F3 +3: an original or supportive record is withdrawn or retracted.
- F4 +1: weak-evidence wording in the original abstract (onset-only, filamentary, small-fraction, single-sample, 'signs of possible').
- F5: +1 if the original has no DOI, journal-ref or 'accepted' note after 12 months; -1 if it is linked to a peer-reviewed venue.
- F6 +1: all positive follow-ups come from the original group.
- F7 +1: critical records outnumber supportive ones in the window.
- A claim is noisy if its score is 3 or more, and 'watch' if it is not noisy but F1 = 2 (catches young single-group claims such as Hg-1223).

Named contested or unreplicated claims. Supportive and critical counts are in-window records, with the number of distinct groups in brackets. Source: analysis/q6.json.

| Claim | Status | Supportive (groups) | Critical (groups) | Noise score | IDs |
|---|---|---|---|---|---|
| LK-99 Cu-lead apatite room-temperature SC | refuted | 1 (1), theory only | 3 (3), experiments | 6 (noisy) | original arXiv:2307.12008 (pre-window, 2023); critical arXiv:2603.23377, doi:10.21203/rs.3.rs-10086532/v1, osti:2586715 |
| Microsoft topological gap protocol / Majorana parity readout | contested | 3 (1, all Microsoft) | 5 (3), no experiments (2 Legg Comments + 3 theory) | 5 (noisy) | critical arXiv:2502.19560, arXiv:2503.08944; supportive arXiv:2504.13240, arXiv:2507.08795, arXiv:2606.03884 |
| LaSc2H24 room-temperature SC (298 K) | unreplicated (one failed independent synthesis) | 1 (1, same-group theory) | 1 (1; 7 attempts did not form the phase; the critic's own calculation gives Tc > 300 K) | 5 (noisy) | original arXiv:2510.01273 (also doi:10.21203/rs.3.rs-7755852/v1); supportive arXiv:2601.01398; critical arXiv:2605.29985 |
| Graphite ambient room-temperature SC | unreplicated | 2 (2), theory only | 0 direct (arXiv:2604.14395 is the Gulian group retracting its own related graphene-heptane result) | 5 (noisy; 4 without 2604.14395) | originals arXiv:2410.18020, arXiv:2510.03256, arXiv:2609.15712; related self-retraction arXiv:2604.14395 |
| RuO2 as a bulk room-temperature altermagnet | strongly disfavoured (bulk) | 0 | 14 (13 by author matching, about 10 after merging co-author links), 11 experiments, 9 of 14 in the preceding window | 4 (noisy) | critical arXiv:2410.05850, arXiv:2503.20621, arXiv:2511.00399 (NQR); original is theory arXiv:1901.00445 (pre-window, 2019) |
| UTe2 chiral zero-field SC | disfavoured | 0 | 4 (3), all STM from one author-linked network (Davis on 3; 2 include original-group co-author Paglione) | 4 (noisy) | critical arXiv:2501.16636, arXiv:2503.17450, arXiv:2602.02490; bulk thermal conductivity arXiv:2603.11278 also excludes non-unitary pairing (unlabelled); Kerr TRSB null arXiv:2305.00589 is pre-window (2023) |
| UTe2 pair-density wave | contested | 1 (1) | 2 (2) | 3 (noisy) | originals arXiv:2209.10859, arXiv:2207.09491 (pre-window, 2022); supportive arXiv:2603.08688; critical arXiv:2504.12505 |
| tMoTe2 fractional quantum spin Hall | unreplicated | 0 | 1 (1), same group (Mak/Shan) refining the state | 3 (noisy; 1 = watch without the same-group record) | original arXiv:2402.03294 (pre-window, 2024); same-group refinement arXiv:2501.02525 |
| Hg-1223 pressure-quench 151 K SC | unreplicated | 0 | 0 | 1 (WATCH) | original arXiv:2603.12437; same-group precursor arXiv:2502.01881 |
| AV3Sb5 time-reversal breaking / loop currents | contested | 10 (9) | 5 (5) | 1 | supportive arXiv:2605.05101; critical arXiv:2510.26010, arXiv:2608.13579 (Comment), reply arXiv:2608.24927 |
| La3Ni2O7 bulk SC under pressure | partially_replicated | 10 (6) | 4 (3) | 1 | supportive arXiv:2501.14584; critical arXiv:2510.02429 (filamentary NV maps); volume-fraction critiques arXiv:2602.19282 (La4Ni3O10), arXiv:2602.23240 (accepts bulk SC) |
| RuO2 thin-film altermagnetism | contested | 15 (11) | 11 (9) | 1 | supportive arXiv:2412.18220; critical arXiv:2601.06791 |
| Nickelate films, ambient-pressure SC | partially_replicated | 12 (9) | 1 (1) | 1 | original arXiv:2412.16622; critical arXiv:2604.07807 |
| Hydride flux trapping / Meissner evidence | contested | 3 (3) | 3 (3) | 1 | original arXiv:2206.14108 (pre-window, 2022); critical proposal arXiv:2104.03925 (pre-window, 2021, Hirsch-Marsiglio) |
| Ta2NiSe5 excitonic insulator | contested | 5 (5) | 4 (4) | 1 | supportive arXiv:2504.10837; critical arXiv:2508.12363 |
| RuCl3 half-quantized thermal Hall | contested | 4 (2) | 1 (1) | 0 | supportive arXiv:2505.05417; critical arXiv:2510.06443 |
| Rhombohedral-graphene chiral SC | partially_replicated | 5 (3) | 0 | -1 | original arXiv:2408.15233 (pre-window, 2024-08) |
| Rhombohedral-graphene FQAH | partially_replicated | 3 (2) | 0 | -1 | original arXiv:2309.17436 (pre-window, 2023) |

Caveats:
- **Stance labels** come from one reader of titles and abstracts, not full texts. "Supportive" sometimes means only "consistent with".
- **Group matching is crude.** Matching by first initial + surname can merge people with common names, and crystal-grower co-authors can link critics to the original group (UTe2, AV3Sb5).
- **Coverage.** The corpus covers only 4 cond-mat categories, so some replication attempts may be missing.

**Key IDs:** arXiv:2307.12008 (pre-window LK-99 original), arXiv:2510.01273, arXiv:2605.29985, arXiv:2510.03256, arXiv:2410.05850, arXiv:2501.16636, arXiv:2502.19560, arXiv:2603.12437

## Caveats and next steps

Caveats:
- **Preprint counts measure vocabulary as much as research.** New terms such as "altermagnet" grow partly by adoption. The trends are shifts in share, each with a CI, and only altermagnetism survives a multiple-comparison correction.
- **Single-annotator audits.** Each audit (15 per cluster, 10 per method, 25 per server, and 186 stance labels on 184 abstracts) was done by a single annotator, so each rate carries about ±15-20 points of uncertainty. An independent strict re-audit of cluster labels (10 per cluster, fresh sample) gave 0.82 pooled against 0.94 in v2. So cluster precision is probably about 0.82-0.89, not 0.94. ml_ai is 19/25 = 0.76 over both audits, and rhombohedral_multilayer_graphene and heavy_fermion_kondo_qcp scored 6/10 on the fresh sample.
- **The unclassified share is near its limit.** At 9.94% trailing it is only just under the 10% target, and any further taxonomy edit could push it over.
- **Residual clusters are catch-alls.** Together they hold about 22% of trailing in-scope records.
- **Limited arXiv coverage.** The harvest covers only 4 cond-mat categories from 2024-09-24, so arXiv-duplicate shares for other servers are lower bounds.
- **October 2025 dip.** Only topological and spin-liquid shares dip in 2025-10. Harvest totals reconcile and the scope mix is typical, so this is noise, not an artefact. It is enough, though, to decide the spin-liquid 'declining' label.
- **Moving corpus.** The corpus may still change: q6 appended 29 supplement records, 1 of them in-window (arXiv:2510.03256). classified.jsonl should be rebuilt if the corpus changes.

Possible next steps (not implemented):
- **Tighten scope for cross-lists.** Require a cond-mat.* primary category or a keyword hit for cross-listed quant-ph/hep-th records.
- **Wider arXiv title matching.** Match OSTI and Research Square titles against arXiv beyond the 4 harvested categories.
- **Second rater.** Add a second rater for the precision and stance audits.
- **Fix known method regex issues.** "BSE" also matches back-scattered-electron microscopy (GW method), and "generative model" also appears in statistics papers (ML method).
- **Per-server topic distributions.** Compute them for the non-arXiv servers now that classified.jsonl exists.
- **Report leave-one-month-out labels.** Show them for marginal clusters (spin_liquid_frustrated; cdw_nematic_excitonic, which turns rising, with CI low 1.000, when 2024-11 is dropped).
- **Update q6_claims.py stance/status labels** to match this report (UTe2 chiral and bulk RuO2 status; graphite arXiv:2604.14395 and tMoTe2 arXiv:2501.02525 stances), and label the unlabelled UTe2 evidence (arXiv:2305.00589, arXiv:2603.11278).
