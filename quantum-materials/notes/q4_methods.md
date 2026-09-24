# Q4: Methods used in quantum-materials preprints (trailing vs preceding year)

Inputs: `analysis/classified.jsonl` (taxonomy v2) for ids, windows, the in-scope flag and clusters;
title + abstract text from `corpus/arxiv.jsonl`. Code: `analysis/methods.py`. Numbers:
`analysis/methods.json`. Audit verdicts: `analysis/methods_precision_audit.json`.

Population: in-scope arXiv preprints only. That is **9,878 trailing** (2025-09-24..2026-09-23)
and **8,828 preceding** (2024-09-24..2025-09-23). Other servers are left out because they are few
and keyword-selected. When the v2 method patterns are re-run on the corpus text they give the same
tags as `classified.jsonl` (0 mismatches).

## 1. Precision audit and refined lexicon

For each of the 25 v2 method regexes I drew 10 trailing in-scope arXiv records with that tag
(`random.Random(7)`, sorted ids). For each one I judged from the title and abstract whether the
paper **uses** the technique: the authors measured with it (experimental) or ran the calculation
(computational). A mention does not count. One annotator made all the calls; borderline calls are
noted per item in the audit file.

* 18 methods scored >= 70% and keep their v2 pattern: DFT, DMRG/TN, tight-binding/effective
  models, thin films and muSR (all 100%); NMR, diffraction, QMC and mean-field (90%); ARPES,
  neutron, RIXS/XAS, DMFT and ED (80%); ultrafast, thermodynamics, ML and GW/beyond-DFT (70%,
  right at the threshold).
* 7 methods scored < 70% and were refined in `methods.py`:
  magnetotransport/Hall (30%), optical/Raman/IR (20%), quantum oscillations (40%), high pressure
  (40%), STM/STS (60%), NV/quantum sensing (60%) and phonons/electron-phonon (60%).
  Typical false positives were theory papers that compute a Hall conductivity or an "optical
  response" with DFT, proposals ("detectable via QPI imaging"), "infrared" used in the
  field-theory sense, "Einstein-de Haas", first-principles work "under pressure", generic
  "quantum sensing", "anharmonic" transmon levels, and citations of earlier work.
* How the refined rule works: each method has *strong* phrases (one unhedged match is enough) and
  *weak* phrases. A weak match counts only if (a) the abstract has an experimental cue
  ("measured", "samples", "we grew", "microscopy", or a reliable probe such as ARPES, neutron or
  XRD), or has no theory cue at all, and (b) the match is not preceded by a hedge word
  ("propose", "predict", "could", "reported", "recent", ...). For phonons (a computational method)
  the cue must be a calculation cue instead. High pressure also needs two weak matches.
* Precision of the final rule: STM 0.95 (n=20), NV 0.93 (15), optical 0.85 (13), phonon 0.84 (19),
  high pressure 0.78 (23), transport 0.77 (13), quantum oscillations 0.74 (23). These figures pool
  every judged item that the final rule tags. The rules were tuned on some of those same items, so
  the figures are optimistic. On fresh samples drawn after the final rule (seed 8), quantum
  oscillations scored 0.80 and high pressure 0.70, so both are still borderline.
* Recall cost: the refinement drops many records. Transport goes from 1,875 to 1,098 trailing and
  optical from 841 to 510. In samples of the dropped records (6 per method), 0 to 2 of 6 were real
  uses. So the refined counts are **undercounts**, perhaps by 5-20%. The worst case is optical,
  where plain "photoluminescence/absorption" experiments without a measurement word are lost.
* In total 382 items were judged (250 in the v2 audit, 70 in re-audit round 2, 20 in round 3 and
  42 dropped records).

## 2. Counts, shares and share ratios (refined lexicon)

share = tagged papers / in-scope papers in that window. R = share_T / share_P, with a Poisson 95%
CI: var(log R) ~= 1/T + 1/P + 1/scope_T + 1/scope_P. A * marks a CI that excludes 1.

| Method | Kind | T | P | share T | share P | R | 95% CI | precision |
|---|---|---:|---:|---:|---:|---:|---|---|
| DFT / first-principles | comp | 1490 | 1242 | 15.1% | 14.1% | 1.07 | 0.99-1.16 | 1.0 |
| Magnetotransport / Hall / resistivity | exp | 1098 | 1051 | 11.1% | 11.9% | 0.93 | 0.85-1.02 | 0.3 -> 0.77 |
| Tight-binding / Wannier / effective models | comp | 850 | 763 | 8.6% | 8.6% | 1.00 | 0.90-1.10 | 1.0 |
| Hartree-Fock / mean field / RPA / BdG | comp | 636 | 533 | 6.4% | 6.0% | 1.07 | 0.95-1.20 | 0.9 |
| Thin-film growth (MBE, PLD, CVD, sputtering) | exp | 578 | 490 | 5.9% | 5.5% | 1.05 | 0.93-1.19 | 1.0 |
| Optical / IR / THz / Raman / magneto-optics | exp | 510 | 423 | 5.2% | 4.8% | 1.08 | 0.94-1.23 | 0.2 -> 0.85 |
| Specific heat / magnetization / thermodynamics | exp | 508 | 493 | 5.1% | 5.6% | 0.92 | 0.81-1.05 | 0.7 |
| X-ray / electron diffraction & microscopy | exp | 485 | 407 | 4.9% | 4.6% | 1.06 | 0.93-1.22 | 0.9 |
| DMRG / tensor networks | comp | 476 | 377 | 4.8% | 4.3% | 1.13 | 0.98-1.30 | 1.0 |
| Phonons / electron-phonon / Eliashberg | comp | 360 | 310 | 3.6% | 3.5% | 1.04 | 0.89-1.21 | 0.6 -> 0.84 |
| Machine learning / neural networks | comp | 354 | 231 | 3.6% | 2.6% | **1.37** | 1.16-1.62 * | 0.7 |
| Ultrafast pump-probe / time-resolved | exp | 311 | 278 | 3.1% | 3.1% | 1.00 | 0.85-1.18 | 0.7 |
| ARPES / photoemission | exp | 310 | 263 | 3.1% | 3.0% | 1.05 | 0.89-1.25 | 0.8 |
| Quantum Monte Carlo | comp | 277 | 194 | 2.8% | 2.2% | **1.28** | 1.06-1.54 * | 0.9 |
| Neutron scattering | exp | 271 | 241 | 2.7% | 2.7% | 1.00 | 0.84-1.20 | 0.8 |
| STM / STS / QPI | exp | 258 | 215 | 2.6% | 2.4% | 1.07 | 0.89-1.29 | 0.6 -> 0.95 |
| Exact diagonalization | comp | 256 | 168 | 2.6% | 1.9% | **1.36** | 1.12-1.66 * | 0.8 |
| High pressure / DAC | exp | 186 | 160 | 1.9% | 1.8% | 1.04 | 0.84-1.29 | 0.4 -> 0.78 |
| DMFT / DFT+DMFT | comp | 182 | 157 | 1.8% | 1.8% | 1.04 | 0.83-1.28 | 0.8 |
| RIXS / XAS / XMCD | exp | 164 | 145 | 1.7% | 1.6% | 1.01 | 0.81-1.27 | 0.8 |
| GW / BSE / hybrid / quantum chemistry | comp | 151 | 125 | 1.5% | 1.4% | 1.08 | 0.85-1.37 | 0.7 |
| NMR / NQR | exp | 97 | 91 | 1.0% | 1.0% | 0.95 | 0.71-1.27 | 0.9 |
| Quantum oscillations | exp | 80 | 72 | 0.8% | 0.8% | 0.99 | 0.72-1.37 | 0.4 -> 0.74 |
| muSR | exp | 73 | 85 | 0.7% | 1.0% | 0.77 | 0.56-1.05 | 1.0 |
| NV / scanning SQUID magnetometry | exp | 48 | 36 | 0.5% | 0.4% | 1.19 | 0.77-1.84 | 0.6 -> 0.93 |

Reading: the method mix is **stable**. 22 of 25 share ratios are consistent with 1. Only three
computational methods grew beyond noise: machine learning (x1.37), exact diagonalization (x1.36)
and quantum Monte Carlo (x1.28). DMRG/tensor networks (x1.13) is borderline. muSR (x0.77) is the
only method that may be shrinking, and its CI still includes 1. The same rule is applied to both
windows, so the ratios are less sensitive to imperfect precision than the raw counts are. They
still assume precision is the same in both windows, and I audited only the trailing window.

### Experimental vs computational totals

| | trailing | preceding | R (95% CI) |
|---|---:|---:|---|
| papers with >= 1 experimental tag | 3,299 (33.4%) | 3,036 (34.4%) | 0.97 (0.92-1.03) |
| papers with >= 1 computational tag | 3,732 (37.8%) | 3,133 (35.5%) | 1.07 (1.01-1.13) |
| both kinds | 972 (9.8%) | 824 (9.3%) | |
| computational tag, no experimental tag | 2,760 (27.9%) | 2,309 (26.2%) | 1.07 (1.00-1.14) |
| **no experimental tag** | 6,579 (66.6%) | 5,792 (65.6%) | 1.02 (0.97-1.06) |
| **no method tag at all** | 3,819 (38.7%) | 3,483 (39.5%) | 0.98 (0.93-1.03) |
| tag mentions, experimental / computational | 4,977 / 5,032 | 4,450 / 4,100 | |

* About 28% of in-scope papers are clearly theory or computation (a computational tag and no
  experimental tag). The upper bound of 67% ("no experimental tag") is inflated because 39% of
  papers carry no method tag at all. These are pure analytic theory (field theory, symmetry and
  topology classification), device papers described without technique names, and reviews. Read
  "theory/computation-only" as **28-67%, most likely around one half**.
* The computational share grew slightly and significantly (x1.07). The experimental share is flat.
  This shift is small and is at the level that the refinement's recall losses could produce.
  Before refinement (the v2 lexicon) the ratios were 0.99 for experimental and 1.06 for
  computational, so the direction does not depend on the refinement.

### Top 3 methods per cluster (trailing, multi-label clusters; share of the cluster's papers)

| Cluster | papers | top methods | no exp. tag |
|---|---:|---|---:|
| Nickelates | 222 | thin films 28%; DFT 23%; high pressure 18% | 33% |
| Cuprates | 240 | transport 19%; diffraction 19%; thin films 14% | 34% |
| Iron-based SC | 123 | transport 27%; DFT 24%; thin films 19% | 27% |
| Hydride / high-pressure SC | 61 | phonon/e-ph 48%; DFT 41%; high pressure 31% | 62% |
| Kagome | 310 | DFT 27%; transport 21%; thermodynamics 15% | 45% |
| Altermagnetism | 678 | DFT 35%; tight-binding 13%; transport 13% | 68% |
| FQAH / Chern insulators | 379 | transport 24%; ED 9%; tight-binding 8% | 70% |
| Rhombohedral graphene | 102 | transport 30%; tight-binding 17%; mean field 14% | 56% |
| Moire / twisted 2D | 489 | tight-binding 16%; DFT 16%; transport 14% | 67% |
| Unconventional / topological SC | 945 | transport 14%; mean field/BdG 12%; tight-binding 8% | 72% |
| Spin liquids / frustrated magnets | 484 | thermodynamics 19%; spin-wave/effective models 15%; DMRG 12% | 60% |
| Heavy fermion / Kondo / QCP | 274 | DFT 17%; transport 14%; thermodynamics 13% | 51% |
| vdW magnets / skyrmions / spintronics | 1168 | DFT 25%; transport 15%; tight-binding 10% | 58% |
| CDW / nematic / excitonic | 744 | DFT 18%; optical/Raman 13%; transport 10% | 50% |
| Topological insulators / semimetals | 1149 | DFT 20%; transport 17%; tight-binding 13% | 67% |
| Flat bands / quantum geometry | 852 | transport 26%; DFT 20%; tight-binding 16% | 62% |
| Mott / Hubbard / strange metals | 976 | DFT 16%; DMFT 16%; mean field 11% | 71% |
| Ultrafast / Floquet | 433 | ultrafast 47%; optical 17%; DFT 12% | 44% |
| ML / AI | 229 | ML 97%; DFT 29%; DMRG 10% | 82% |
| Quantum magnetism / ferroic order | 471 | thermodynamics 21%; DFT 18%; neutron 14% | 46% |
| Many-body theory / generalized symmetries | 1181 | DMRG/TN 19%; QMC 8%; tight-binding 7% | 97% |
| Other superconductivity | 572 | thin films 18%; transport 14%; DFT 13% | 59% |

The most experimental clusters (fewest papers without an experimental tag) are iron-based SC,
nickelates, cuprates, ultrafast, kagome and quantum magnetism. The most theory-heavy are
many-body theory, ML, unconventional/topological SC, Mott/Hubbard, FQAH and altermagnetism
(68%, with DFT the single largest method). The ML cluster's 97% ML share is partly circular,
because the cluster and the method use similar keywords.

### Co-occurrences (papers with both tags; lift = observed / expected if independent)

| Pair | trailing: both (share of A) lift | preceding: both (share of A) lift |
|---|---|---|
| ARPES + DFT | 110 (35% of ARPES) 2.35 | 104 (40%) 2.81 |
| STM + DFT | 45 (17% of STM) 1.16 | 47 (22%) 1.55 |
| DFT + DMFT | 84 (46% of DMFT) 3.06 | 62 (39%) 2.81 |
| ML + DFT | 94 (27% of ML) 1.76 | 54 (23%) 1.66 |
| transport + any computational | 245 (22% of transport) 0.59 | 178 (17%) 0.48 |

About one ARPES paper in three reports DFT band calculations, and nearly half of DMFT papers are
DFT+DMFT. The ML+DFT pairing (ML potentials, screening) is growing in absolute terms (54 -> 94).
Transport papers are mostly experimental: lift < 1 against computation, although the share with a
calculation rose from 17% to 22%. The STM+DFT pairing is weak (lift ~1.2-1.6). Caveat: an
abstract often leaves out the supporting DFT, so every pair is a lower bound.

## 3. Exemplars (trailing window; the title shows the method is used)

The exemplar IDs are chosen by hand from the deterministic candidate lists in
`methods.json/exemplar_candidates`, after checking each abstract.

Top 4 experimental methods (by trailing count):
* Magnetotransport: arXiv:2604.26480, "Large magnetoresistance and weak-antilocalization in the nodal-line semimetal VP2"
* Thin-film growth: arXiv:2605.22932, "Thickness-Dependent Spintronic Terahertz Emission in MBE-Grown PtTe2: From Semiconductor to Type-II Dirac Semimetal"
* Optical/Raman: arXiv:2511.15452, "Spinon excitations and spin correlations in the one-dimensional quantum magnet β-VOSO4 probed by Raman spectroscopy"
* Thermodynamics/magnetization: arXiv:2606.10300, "Vortex pinning of Ba0.62K0.38BiO3 investigated by magneto-optical Kerr-effect and magnetization measurements"

Top 4 computational methods:
* DFT: arXiv:2602.07897, "CDW Gap Collapse and Weyl State Restoration in Ta2Se8I via Coherent Phonons: A First-Principles Study"
* Tight-binding / effective models: arXiv:2607.20624, "Ideal Bands in Tight-Binding Models"
* Mean field: arXiv:2510.04132, "Ground state and excitations of quasiperiodic 1D narrow-band moiré systems: a mean field approach"
* DMRG / tensor networks: arXiv:2512.06768, "Real-Time Dynamics in Two Dimensions with Tensor Network States via Time-Dependent Variational Monte Carlo"

Fastest-growing method (highest R among methods with >= 30 trailing papers): machine learning,
R = 1.37 (1.16-1.62):
* arXiv:2602.15178, "Deciphering Majorana Zero Modes in Topological Superconductor FeTe0.55Se0.45 with Machine-Learning-Assisted Spectral Deconvolution"

ED (R = 1.36) is statistically tied with ML. Most of its growth is in the many-body-theory
cluster (54 trailing vs 28 preceding ED papers), with smaller rises in moire (19 vs 11) and
FQAH/Chern (35 vs 28). Fuzzy-sphere work is only 5 vs 2 papers. Example: arXiv:2605.27524.

## 4. Caveats

* These are abstract-level keyword signals, not full-text method sections. An abstract often names
  the headline probe and leaves out supporting ones (DFT, XRD, magnetization). Absolute shares are
  therefore lower bounds, and "no method tag" (39%) is high.
* Precision is uneven. Four unrefined methods sit at exactly 70% (ultrafast, thermodynamics, ML,
  GW), and for all of them n = 10 gives a binomial 95% interval of about 0.35-0.93. Two refined
  methods are borderline on fresh samples (quantum oscillations 0.80, high pressure 0.70). Treat
  small-count methods (NV, muSR, QO, NMR) as indicative only.
* ML growth is the most robust finding, but ML papers also include "AI"/"LLM" framing and
  generative-model papers. Part of the rise may be vocabulary ("AI-driven") rather than method
  adoption. The audit found 3 of 10 ML hits were mentions.
* The windows compare shares, so the result does not depend on overall arXiv volume growth. A
  harvest that is incomplete for the last weeks before the 2026-09-23 run date would bias counts
  but should not bias shares.
* One annotator (an LLM agent) made every judgment. There is no inter-rater check. Borderline
  rules: high-pressure synthesis counts as high-pressure work; analysing others' measured data
  (e.g. ML on ARPES data) counts as use.

## Possible follow-ups (not done)

* Tighten the `BSE` acronym in gw_beyond_dft (it also matches back-scattered-electron microscopy)
  and "generative model" in ML, which also appears in statistics.
* Double-annotate a subset to measure agreement between annotators.
* Audit the preceding window too, to check that precision is stable across windows.
