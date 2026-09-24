# Taxonomy changelog

Taxonomy v2 is **frozen** (analysis/taxonomy.py, `TAXONOMY_VERSION = "v2"`).
Every lane should read the per-record cache `analysis/classified.jsonl`
(built by `analysis/build_classified.py`) instead of re-classifying.

## v1 -> v2 summary

| | v1 | v2 |
|---|---|---|
| clusters | 18 | 22 (4 new; 3 of them "residual" fallbacks) |
| arXiv in scope, trailing / preceding | 9,905 / 8,868 | 9,878 / 8,828 |
| unclassified share of in-scope arXiv, trailing / preceding | 17.0% / 16.8% | **9.9% / 9.7%** |
| precision spot-check (15 per cluster, 330 items) | not done | 311/330 = 0.94; every cluster >= 0.80 |
| full classification of 38.6k windowed records | ~6-7 min, not cached | 300 s single process, ~24 s with 16 workers (`--workers`) |

### 1. Matching rules (apply to all clusters)
* **Evidence rule** (`has_evidence`): a cluster needs a *title* hit, or **at least two hits** in
  title + abstract. In the first v2 draft, most spot-check errors were single passing
  mentions ("as in the cuprates", "... for strongly correlated systems", "applications in spintronics").
* **Title-only phrases** (`title_patterns`) for generic framing words that are wrong even when
  repeated: "strongly correlated / correlated state/phase/system / electron correlation" (Mott),
  "non-equilibrium" (ultrafast), plain "quantum Hall" / "Landau level" (FQAH).
* **Residual clusters** (`residual: True`, last in the order): assigned only when no other cluster
  matched, and at most one of them, so their multi-label count equals their primary count.
* `classify(text, title=None)` gains a `title` argument; new `classify_record(record)`,
  `scope_reason(record)`, `record_title(record)`, `RESIDUAL_CLUSTER_KEYS`.

### 2. New clusters
* `flat_band_quantum_geometry` (non-residual, placed after the topological cluster): **decision on
  plain flat bands** - they get their own cluster instead of being spread over existing ones. Flat
  bands in kagome / moire / rhombohedral graphene keep those more specific primary labels because
  those clusters come first. Berry curvature, quantum metric/geometry, nonlinear Hall, orbital Hall /
  orbital magnetization, Berry phase and (intrinsic) anomalous Hall/Nernst responses moved here out
  of `topological_insulators_semimetals`.
* `quantum_magnetism_ferroic_order` (residual): magnetic order, quantum magnets, spin-chain/ladder/
  dimer **compounds**, spin-orbit-entangled and multipolar magnets, plus non-magnetic ferroic order
  (ferroelectric, ferroaxial, polar metals).
* `quantum_many_body_theory` (residual): tensor networks, lattice gauge theories, non-invertible /
  higher-form / subsystem symmetries and anomalies, SPT & topological order, anyons (moved here from
  the FQAH cluster), scars / fragmentation / MBL / thermalization / integrability, measurement-induced
  transitions, entanglement, CFT & RG, generic quantum criticality, spin-chain **models**, polarons,
  Fermi liquids / diagrammatics / QMC, quantum simulation and open (Lindbladian) many-body dynamics.
* `other_superconductivity` (residual): conventional / phonon-mediated and new superconductors,
  high-entropy alloys, vortices, SC films, junctions and devices incl. qubit/resonator materials,
  applied SC, and other pairing condensates (superfluid He, atomic Fermi superfluids). Colour
  (QCD), holographic superconductors and neutron-star matter are excluded.

### 3. Narrowed / fixed existing clusters
* `topological_insulators_semimetals`: Berry/quantum-geometry terms moved out; "topological order"
  moved out; excludes interacting-topological-order contexts (anyons, SPT, TQFT, F-symbols,
  mixed-state, higher Berry phase) and more classical-wave contexts (photonic lattices/braids,
  split-ring resonators, topological lasers, plasmas); adds non-Hermitian band topology / skin effect,
  band inversion, bulk-boundary correspondence, winding number.
* `mott_hubbard_strange_metal`: generic correlation phrases title-only (see above); adds DMFT,
  manganites / CMR, "Hundness"; drops bare "oxide interface" (matched SC-device oxides).
* `heavy_fermion_kondo_qcp`: generic "quantum critical"/QCP moved to many-body theory; keeps
  metallic/itinerant/Kondo quantum criticality; adds f-electron and valence-transition terms.
  Label now "... metallic quantum criticality".
* `fractional_qah_chern`: bare "Chern number" dropped, "Chern band(s)" added; generic anyons moved out.
* `altermagnetism`: adds p-wave / odd-parity / "unconventional" magnets (they were being labelled as
  p-wave superconductivity); `unconventional_topological_sc` no longer matches "p-wave magnet".
* `iron_based_sc`: generic "pnictide(s)" dropped (manganese pnictides); `Fe2Se2O` altermagnets
  excluded; `BaFe2(As1-xPx)2` style formulas added.
* `cdw_nematic_excitonic`: NbSe2 alone no longer implies CDW; "Peierls" only as transition /
  instability / spin-Peierls (not Peierls substitution); nematic fluids / ferroelectric nematics excluded.
* `rhombohedral_multilayer_graphene` / `moire_twisted_2d`: twisted mono-bilayer, helical trilayer and
  "moire bilayer graphene" go to moire; "magic angle spinning" (NMR) excluded from moire.
* `spin_liquid_frustrated`: "Kitaev" no longer matches Sachdev-Ye-Kitaev; adds RVB.
* `vdw_magnets_topological_magnetism`: "spintronic" under the evidence rule; label adds multiferroics.
* `hydride_high_pressure_sc`: label now says it also holds room-temperature SC claims (LK-99 etc.).

### 4. Scope rule
Unchanged except one new context veto: the "topological" keyword is ignored in classical-wave
contexts (topological photonics / acoustics / mechanics, metamaterials, phononic crystals,
topolectric circuits, topological lasers, topological data analysis / optimization). Effect: 27 fewer
in-scope arXiv records in the trailing window (9,905 -> 9,878) and 40 fewer in the preceding window.

## Precision spot-check (v2, frozen)

Method: for each cluster, sorted ids of trailing-window arXiv records whose `primary_cluster` is that
cluster, then `random.Random(42).sample(ids, 15)` (`analysis/sample_precision_audit.py`). The primary
label was judged against the paper's main topic from the title (abstract where needed). Per-item
verdicts and notes: `analysis/precision_audit_v2.json`.

Caveats: one annotator (the agent that built the rules); n = 15 per cluster, so each value is roughly
+/-15-20 points (95% interval); only the PRIMARY label was audited, not multi-labels. Multi-label
counts of broad clusters (TI, Mott, vdW/spintronics, flat bands/quantum geometry, CDW/excitons)
still include secondary topics and should not be read as "papers about X".

Clusters that were below 0.80 during development and were tightened and re-audited on a fresh
sample: heavy fermion (9/15 -> 15/15), FQAH/Chern (11/15 -> 15/15), topological insulators (11/15 ->
13/15), Mott/Hubbard (about 10/15 -> 12/15), and in the first draft the residual clusters
(other superconductivity about 8/15, many-body theory about 9/15) before the evidence rule.
Mott/Hubbard and ML/AI sit exactly at 0.80: treat their counts as the noisiest.

| key | label | trailing primary | trailing multi | preceding primary | preceding multi | audited precision (n=15) |
|---|---|---|---|---|---|---|
| `nickelate_sc` | Nickelates (bilayer/trilayer & infinite-layer) and nickelate superconductivity | 222 | 222 | 211 | 211 | 14/15 = 0.93 |
| `cuprate_sc` | Cuprate superconductivity | 223 | 240 | 192 | 212 | 13/15 = 0.87 |
| `iron_based_sc` | Iron-based superconductivity (pnictides & chalcogenides) | 117 | 123 | 117 | 121 | 14/15 = 0.93 |
| `hydride_high_pressure_sc` | Hydride / high-pressure superconductivity (incl. room-temperature SC claims) | 57 | 61 | 52 | 58 | 15/15 = 1.00 |
| `kagome` | Kagome metals & kagome materials | 308 | 310 | 313 | 313 | 15/15 = 1.00 |
| `altermagnetism` | Altermagnetism, p-wave/unconventional magnets & non-relativistic spin splitting | 660 | 678 | 414 | 421 | 15/15 = 1.00 |
| `fractional_qah_chern` | Fractional / quantum anomalous Hall & Chern insulators (incl. quantum Hall, Landau levels) | 364 | 379 | 363 | 372 | 15/15 = 1.00 |
| `rhombohedral_multilayer_graphene` | Rhombohedral / multilayer (untwisted) graphene | 81 | 102 | 63 | 84 | 15/15 = 1.00 |
| `moire_twisted_2d` | Moire & twisted 2D systems (TBG, twisted TMDs, moire heterostructures) | 405 | 489 | 335 | 419 | 14/15 = 0.93 |
| `unconventional_topological_sc` | Unconventional & topological superconductivity, Majorana, SC diode/Josephson devices | 717 | 945 | 693 | 858 | 14/15 = 0.93 |
| `spin_liquid_frustrated` | Quantum spin liquids & frustrated magnetism (Kitaev, triangular, pyrochlore) | 387 | 484 | 407 | 504 | 14/15 = 0.93 |
| `heavy_fermion_kondo_qcp` | Heavy fermions, Kondo physics & metallic quantum criticality | 162 | 274 | 151 | 261 | 15/15 = 1.00 |
| `vdw_magnets_topological_magnetism` | 2D/van der Waals magnets, skyrmions, topological magnetism, multiferroics & spintronics/magnonics | 820 | 1168 | 784 | 1097 | 14/15 = 0.93 |
| `cdw_nematic_excitonic` | Charge/spin density waves, nematicity, Wigner crystals & excitonic insulators/excitons | 390 | 744 | 310 | 657 | 15/15 = 1.00 |
| `topological_insulators_semimetals` | Topological insulators & semimetals (Weyl/Dirac/nodal), band topology incl. non-Hermitian | 678 | 1149 | 712 | 1197 | 13/15 = 0.87 |
| `flat_band_quantum_geometry` | Flat bands & quantum geometry (quantum metric, Berry curvature; anomalous, nonlinear & orbital Hall responses) | 297 | 852 | 243 | 709 | 15/15 = 1.00 |
| `mott_hubbard_strange_metal` | Mott/Hubbard physics, strange metals & correlated oxides | 533 | 976 | 454 | 875 | 12/15 = 0.80 |
| `ultrafast_floquet_noneq` | Ultrafast, Floquet & nonequilibrium quantum materials | 136 | 433 | 131 | 376 | 14/15 = 0.93 |
| `ml_ai` | Machine learning / AI for quantum materials | 115 | 229 | 93 | 162 | 12/15 = 0.80 |
| `quantum_magnetism_ferroic_order` | Quantum & low-dimensional magnetism and ferroic order (antiferro/ferrimagnets, spin-chain/ladder/dimer compounds, spin-orbit-entangled & multipolar magnets, ferroelectric/ferroaxial order) | 471 | 471 | 440 | 440 | 15/15 = 1.00 |
| `quantum_many_body_theory` | Quantum many-body theory & generalized symmetries (tensor networks, spin-chain & lattice-gauge models, non-invertible/higher-form symmetries, SPT/topological order & anyons, scars, entanglement) | 1181 | 1181 | 988 | 988 | 15/15 = 1.00 |
| `other_superconductivity` | Other superconductivity & superfluidity (conventional/phonon-mediated & new superconductors, vortices, SC films & devices incl. qubit/resonator materials, applied SC, superfluid He) | 572 | 572 | 506 | 506 | 13/15 = 0.87 |

Unclassified in-scope arXiv records (982 trailing / 856 preceding) are mostly cross-listings from
quant-ph, hep-th and physics.* that are in scope only through the cond-mat.str-el / supr-con
category rule (quantum-information hardware, holography, photonics), electronic-structure methods,
instrumentation, and single-mention keyword hits that the evidence rule no longer trusts.
Non-arXiv servers have higher unclassified shares (zenodo 25%, hal 32% trailing), partly because
many records there have short or empty abstracts.

## Files
* `analysis/taxonomy.py` - v2 rules (frozen)
* `analysis/test_taxonomy.py` - 61 positive, 17 negative, 17 guard, 6 evidence-rule cases (all pass)
* `analysis/build_classified.py` -> `analysis/classified.jsonl` (38,594 windowed records, all servers)
* `analysis/count_clusters.py` -> `analysis/cluster_counts.json` (reads classified.jsonl; `--live` re-classifies)
* `analysis/sample_precision_audit.py`, `analysis/precision_audit_v2.json`
