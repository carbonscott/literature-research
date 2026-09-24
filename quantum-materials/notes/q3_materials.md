# Q3 Materials: which materials each cluster studies, and which are growing

Script: `analysis/materials.py` (reads `analysis/classified.jsonl` taxonomy v2 plus `corpus/arxiv.jsonl`; writes `analysis/materials.json`).
Population: arXiv records that are in scope. Per-cluster tables use the **trailing window** (2025-09-24..2026-09-23) and the record's **primary cluster**.
In-scope baseline: 9,877 trailing and 8,828 preceding records. `cluster_counts.json` has 9,878 trailing; one classified record has no text row in `arxiv.jsonl`.

## Method in brief

1. **Families**: `families` field from classified.jsonl (24 v2 families). For each cluster: share of records that name any family, and the top 3.
2. **Formula gap check**: formula-like tokens are pulled from the normalized title+abstract (`taxonomy.normalize_text`). A token is kept only if all of these hold:
   - it is made only of real element symbols, with at least 2 distinct elements;
   - no number in it is above 99;
   - it has a number/variable or a two-letter symbol (this drops all-caps acronyms like BCS and NV);
   - it is not a plural acronym (SCs, BICs);
   - it is not part of a parenthesized formula;
   - it is not a structure-type label ("NiAs-type");
   - it is not a coordination unit (NiO6, CuO2 planes);
   - it is not a generic chemical or substrate (H2O, CO2, SiO2, Al2O3, MgO, Si3N4, TiO2, ...).
   Prefixes are dropped (1T-TaS2 -> TaS2, alpha-RuCl3 -> RuCl3), and so is a trailing -x/+x/-delta (YBa2Cu3O7-delta -> YBa2Cu3O7).
   Frequent formulas that no v2 family matches led to **11 extended families**, defined inside `materials.py` (taxonomy.py is unchanged). Each one lists the formula counts that motivated it:
   - conventional SC compounds (NbN 55, MgB2 40, NbTiN 23, TiN 20, Nb3Sn 13)
   - ferroelectrics/multiferroics (BiFeO3 43, BaTiO3 28, In2Se3, CuCrP2S6, plus the word "multiferroic")
   - more kagome (Nb3Cl8 22, LaRu3Si2, HoAgGe, FeSn, RNb6Sn6, RTi3Bi4)
   - TM perovskite oxides (SrIrO3, SrVO3, LSMO, La2NiO4)
   - spin-chain/ladder compounds (Sr2CuO3, BaCo2V2O8, CoNb2O6)
   - spintronic magnets (CoFeB, permalloy, CuMnAs, YIG)
   - more layered dichalcogenides (NiTe2, SnSe2, ZrTe2)
   - more layered magnets (CrOCl, Mn3Si2Te6, Cr1+deltaTe2)
   - more heavy-fermion compounds (CeRh6Ge4, CeNiAsO, LiV2O4)
   - more semiconductors (SiGe, InP, SiC, PbTe)
   - delafossites

   After the extended lexicon, no formula in any cluster's top-10 list lacks a family, except singletons, the substrate SrLaAlO4, and fragments.
3. **Trends**: R = (T/scope_T)/(P/scope_P), with a 95% CI from var(log R) ~= 1/T + 1/P + 1/scope_T + 1/scope_P. R = 1 means the item grew at the same rate as in-scope arXiv as a whole (+11.9%).
4. **Fastest growing**: formulas with T+P >= 30 records, ranked by the **CI lower bound** of R. This favours well-supported growth over small-count spikes.

## Per-cluster leading families (trailing, primary cluster; counts are records)

"share v2" = share of the cluster's records naming any v2 family. "share +ext" = the same share once the extended families are added.

| cluster | N | share v2 | share +ext | leading family (n) | 2nd, 3rd | top formulas | exemplar (title names the family) |
|---|---|---|---|---|---|---|---|
| nickelate_sc | 222 | 0.99 | 0.99 | bilayer/trilayer RP nickelates (168) | infinite-layer (56), cuprates (44) | La3Ni2O7 103, La4Ni3O10 30, SrLaAlO4 11, Pr4Ni3O10 10, La2PrNi2O7 8 | arXiv:2509.20727 "Distinct orbital contributions to electronic and magnetic structures in La4Ni3O10" |
| cuprate_sc | 223 | 1.00 | 1.00 | cuprates (223) | spin-chain cmpds (6), Fe-based (6) | YBa2Cu3O7 35, Bi2Sr2CaCu2O8 26, La2-xSrxCuO4 11, La2CuO4 11 | arXiv:2509.19675 "Quantum criticality in cuprate superconductors revealed by optical conductivity measurement" |
| iron_based_sc | 117 | 0.95 | 0.95 | Fe pnictides/chalcogenides (111) | SrTiO3/KTaO3 interfaces (8), semicond. (3) | FeSe 41, FeTe 19, SrTiO3 7, FeTe0.55Se0.45 6, BaFe2As2 5 | arXiv:2509.23591 "Fabrication of oxide/FeSe multilayer films using the PLD technique" |
| hydride_high_pressure_sc | 57 | 0.68 | 0.68 | hydrides (34) | graphene (4), conventional SC (2) | LaH10 11, H3S 9, LaSc2H24 5, CaH6 3, YH9 3, MgZrH6 3 | arXiv:2510.10720 "Revisiting YH9 Superconductivity and Predicting High-Tc in GdYH5" |
| kagome | 308 | 0.46 | 0.53 | other kagome metals (63) = AV3Sb5 (63) | ext kagome (23) | CsV3Sb5 39, CsCr3Sb5 10, Co3Sn2S2 10, FeGe 9, RbV3Sb5 8, Fe3Sn2 8 | arXiv:2510.01053 "Interacting spin and charge density waves in kagome metal FeGe" |
| altermagnetism | 660 | 0.38 | 0.44 | altermagnet candidates (203) | multiferroics (34), vdW magnets (13) | MnTe 60, CrSb 50, RuO2 33, KV2Se2O 25, MnF2 13 | arXiv:2509.19932 "Exploration of Altermagnetism in RuO2" |
| fractional_qah_chern | 364 | 0.40 | 0.40 | graphene multilayers (75) | TMDs (52), Weyl/Dirac list (35, i.e. MoTe2) | MoTe2 32, GaAs 16, WSe2 12, MnBi2Te4 4 | arXiv:2509.19978 "Non-ohmic to ohmic crossover in the breakdown of the quantum Hall states in graphene ..." |
| rhombohedral_multilayer_graphene | 81 | 1.00 | 1.00 | graphene multilayers (81) | TMDs (8), hBN (4) | WSe2 4 (others singletons) | arXiv:2509.21759 "Hexagonal boron nitride/bilayer graphene moire superlattices ..." |
| moire_twisted_2d | 405 | 0.80 | 0.83 | graphene multilayers (187) | TMDs (149), hBN (42) | WSe2 65, MoTe2 29, WS2 25, MoSe2 21, MoS2 17 | arXiv:2510.02444 "Four Moire materials at One Magic Angle in Helical Quadrilayer Graphene" |
| unconventional_topological_sc | 717 | 0.34 | 0.36 | semiconductor 2DEG/nanowires (64) | UTe2/f-electron (54), TMDs (46) | UTe2 40, NbSe2 18, InAs 14, Sr2RuO4 12, TaS2 12, CeRh2As2 11 | arXiv:2510.00305 "Gate-tunable Josephson parametric amplifiers based on semiconductor nanowires" |
| spin_liquid_frustrated | 387 | 0.31 | 0.34 | frustrated rare-earth/triangular/pyrochlore (64) | Kitaev materials (39), iridates (8) | RuCl3 21, Na3Co2SbO6 4, Na2Co2TeO6 4, Dy2Ti2O7 3 | arXiv:2509.20199 "Random singlet physics in the S = 1/2 pyrochlore antiferromagnet NaCdCu2F7" |
| heavy_fermion_kondo_qcp | 162 | 0.26 | 0.31 | UTe2/f-electron list (26) | ext heavy fermion (8), semicond. (5) | CeCoIn5 6, CeRh6Ge4 4, SmB6 4, YbRh2Si2 3 | arXiv:2509.19684 "Hybridization gap and f-electron effect evolutions with Cd- and Sn-doping in CeCoIn5 ..." |
| vdw_magnets_topological_magnetism | 820 | 0.43 | 0.55 | vdW magnets (234) | multiferroics (90), TMDs (38) | CrSBr 57, MnBi2Te4 26, CrI3 22, NiPS3 20, Fe3GeTe2 20, Fe3GaTe2 15 | arXiv:2509.22303 "Self-organization mechanism in Bridgman-grown MnBi2Te4/(Bi2Te3)n ..." |
| cdw_nematic_excitonic | 390 | 0.52 | 0.55 | TMDs (132) | excitonic/CDW list (49), Mott oxides (22) | TaS2 31, WSe2 21, MoSe2 20, TiSe2 17, Ta2NiSe5 10, NbSe2 10 | arXiv:2510.00556 "Excitons and Optical Response in Excitonic Insulator Candidate TiSe2" |
| topological_insulators_semimetals | 678 | 0.31 | 0.33 | Weyl/Dirac semimetals (86) | graphene (45), TMDs (36) | WTe2 18, Bi2Se3 12, Bi2Te3 9, TaIrTe4 8, TaAs 8, ZrTe5 8 | arXiv:2510.06618 "Intrinsic ultrafast edge photocurrent dynamics in WTe2 driven by broken crystal symmetry" |
| flat_band_quantum_geometry | 297 | 0.22 | 0.23 | graphene multilayers (26) | TMDs (18), oxide interfaces (5) | MoS2 5 (rest <= 2) | arXiv:2601.08586 "Sublattice polarization and filamentary superconductivity in strained graphene" |
| mott_hubbard_strange_metal | 533 | 0.30 | 0.32 | iridates/Mott oxides (76) | SrTiO3/KTaO3 (44), cuprates (22) | SrTiO3 28, VO2 21, KTaO3 14, LaAlO3 11, V2O3 10 | arXiv:2509.20337 "Spin-polaron fingerprints in the optical conductivity of iridates" |
| ultrafast_floquet_noneq | 136 | 0.15 | 0.21 | graphene multilayers (8) | TMDs (6), conventional SC (6) | K3C60 3 (rest <= 2) | arXiv:2603.28724 "Robust Floquet-induced gap in irradiated graphite" |
| ml_ai | 115 | 0.12 | 0.14 | 3-way tie (3 each): cuprates, semicond., Mott oxides | - | all singletons | arXiv:2512.10909 "Electronic crystals and quasicrystals in semiconductor quantum wells: an AI-powered discovery" (semiconductor family; no cuprate title) |
| quantum_magnetism_ferroic_order | 471 | 0.18 | 0.25 | ferroelectrics/multiferroics, ext (17) | graphene (16), altermagnet cands (15) | SrRuO3 7, RuO2 5, SrTiO3 5, Cr2O3 4, BiFeO3 4 | arXiv:2604.05220 "Many-body description of two-dimensional van der Waals ferroelectric alpha-In2Se3" |
| quantum_many_body_theory | 1181 | 0.02 | 0.02 | graphene (9) | semicond. (8), cuprates (3) | Fe4S4 4 (quantum-chemistry benchmark) | arXiv:2512.20559 "Plasmon excitations in half-filled graphene: ... QMC and RPA" |
| other_superconductivity | 571 | 0.18 | **0.28** | conventional SC compounds, ext (59) | semicond. (33), TMDs (24) | NbN 17, MgB2 10, NbTiN 9, NbSe2 9, Nb3Sn 7, InAs 7 | arXiv:2509.19697 "Roles of Fe-ion irradiation on MgB2 thin films ..." |
| (in scope, no cluster) | 982 | 0.21 | 0.24 | graphene (81) | TMDs (41), semicond. (31) | MoS2 14, GaAs 12, SiC 8, InAs 7 | arXiv:2510.00760 "Valley Hall Viscosity in Gapped Graphene with and without a Magnetic Field" |

What the table shows:
- **Material-defined clusters are well covered.** Nickelate, cuprate, Fe-based, rhombohedral and moire clusters have >= 80% family coverage, and one compound dominates each. La3Ni2O7 alone is in 46% of nickelate-cluster records; FeSe is in 35% of Fe-based records.
- **Phenomenon-defined clusters are poorly covered** (15-45%). These are theory-heavy clusters, where abstracts name models rather than materials. quantum_many_body_theory names a material in only 2% of records. This is expected, not a lexicon gap: the formula extraction finds no frequent unmatched compounds there.
- **Extended families mattered most** in three clusters:
  - other_superconductivity: 0.18 -> 0.28. The conventional/device superconductors (NbN, MgB2, NbTiN, Nb3Sn) were missing from v2.
  - vdw_magnets_topological_magnetism: 0.43 -> 0.55, from multiferroic vdW such as NiI2 and CuCrP2S6.
  - quantum_magnetism_ferroic_order: 0.18 -> 0.25.
  Kagome gained 0.07 (Nb3Cl8, LaRu3Si2, HoAgGe, RNb6Sn6).
- Cross-cluster use of materials:
  - TMDs lead cdw_nematic_excitonic (TaS2, TiSe2) and also appear in FQAH (MoTe2).
  - WSe2/MoSe2 in the CDW cluster are mostly moire and excitonic-insulator bilayers.
  - Semiconductor nanowires (InAs) lead unconventional_topological_sc, ahead of UTe2. That cluster is a mix of Majorana/hybrid-device work and bulk UTe2/CeRh2As2/Sr2RuO4.

## Family and formula trends (all in-scope arXiv; trailing vs preceding)

Top 20 families by T+P (v2 + extended):

| family | T | P | R | 95% CI |
|---|---|---|---|---|
| graphene_multilayers | 653 | 595 | 0.98 | 0.88-1.10 |
| tmds | 593 | 484 | 1.10 | 0.97-1.24 |
| cuprates | 364 | 346 | 0.94 | 0.81-1.09 |
| vdw_magnets | 296 | 288 | 0.92 | 0.78-1.08 |
| semiconductor_2deg_and_qw | 228 | 223 | 0.91 | 0.76-1.10 |
| weyl_dirac_semimetals | 220 | 228 | 0.86 | 0.72-1.04 |
| **altermagnet_candidates** | 254 | 128 | **1.77** | **1.43-2.20** |
| ext_ferroelectrics_multiferroics | 182 | 178 | 0.91 | 0.74-1.13 |
| nickelates_bilayer_trilayer_rp | 172 | 160 | 0.96 | 0.77-1.19 |
| iridates_mott_oxides | 175 | 145 | 1.08 | 0.86-1.35 |
| iron_pnictides_chalcogenides | 159 | 157 | 0.91 | 0.73-1.13 |
| other_kagome_metals | 118 | 130 | 0.81 | 0.63-1.04 |
| srtio3_ktao3_oxide_interfaces | 127 | 103 | 1.10 | 0.85-1.43 |
| hbn | 121 | 100 | 1.08 | 0.83-1.41 |
| mnbi2te4_bi2se3_tetradymites | 97 | 113 | 0.77 | 0.58-1.01 |
| frustrated_rare_earth_and_triangular | 93 | 104 | 0.80 | 0.60-1.06 |
| ext_conventional_sc_compounds | 97 | 82 | 1.06 | 0.79-1.42 |
| ute2_heavy_fermion_f_electron | 88 | 77 | 1.02 | 0.75-1.39 |
| **av3sb5_kagome** | 64 | 80 | **0.72** | **0.51-0.995** |
| ext_semiconductors_more | 78 | 60 | 1.16 | 0.83-1.63 |

Outside the top 20, **kitaev_materials** is the clearest decliner: 49 vs 70, R = 0.63 (0.43-0.90). ext_kagome_more also fell: 37 vs 52, R = 0.64 (0.42-0.97).

Top 20 formulas by T+P:

| formula | T | P | R | 95% CI |
|---|---|---|---|---|
| La3Ni2O7 | 105 | 121 | 0.78 | 0.60-1.01 |
| WSe2 | 131 | 91 | 1.29 | 0.98-1.68 |
| MoTe2 | 88 | 77 | 1.02 | 0.75-1.39 |
| SrTiO3 | 70 | 63 | 0.99 | 0.71-1.40 |
| CrSBr | 67 | 56 | 1.07 | 0.75-1.53 |
| NbSe2 | 55 | 62 | 0.79 | 0.55-1.14 |
| TaS2 | 53 | 53 | 0.89 | 0.61-1.31 |
| **MnTe** | 65 | 39 | **1.49** | **1.00-2.22** |
| MoS2 | 55 | 46 | 1.07 | 0.72-1.58 |
| FeSe | 48 | 45 | 0.95 | 0.63-1.43 |
| RuO2 | 51 | 41 | 1.11 | 0.74-1.68 |
| WS2 | 52 | 39 | 1.19 | 0.79-1.81 |
| **MnBi2Te4** | 37 | 52 | **0.64** | **0.42-0.97** |
| MoSe2 | 51 | 33 | 1.38 | 0.89-2.14 |
| UTe2 | 44 | 38 | 1.04 | 0.67-1.60 |
| CsV3Sb5 | 40 | 37 | 0.97 | 0.62-1.51 |
| **CrSb** | 52 | 20 | **2.32** | **1.39-3.90** |
| GaAs | 43 | 29 | 1.33 | 0.83-2.12 |
| InAs | 37 | 34 | 0.97 | 0.61-1.55 |
| WTe2 | 34 | 35 | 0.87 | 0.54-1.39 |

## Fastest-growing materials (T+P >= 30, ranked by CI lower bound)

| rank | formula | T | P | R (95% CI) | exemplar (trailing, title names it) |
|---|---|---|---|---|---|
| 1 | CrSb | 52 | 20 | 2.32 (1.39-3.90) | arXiv:2509.21303 "Topological nontrivial berry phase in altermagnet CrSb" |
| 2 | YBa2Cu3O7 | 38 | 18 | 1.89 (1.08-3.31) | arXiv:2509.26095 "The diffusion-driven orthorhombic to tetragonal transition in YBa2Cu3O7 derived with a machine learning interatomic potential" |
| 3 | MnTe | 65 | 39 | 1.49 (1.00-2.22) | arXiv:2509.20120 "Multipole analysis of spin currents in altermagnetic MnTe" |
| 4 | WSe2 | 131 | 91 | 1.29 (0.98-1.68) | arXiv:2510.11088 "Local-Antisymmetric Flat Band and Coexisting Correlated stripe charge orders in WSe2-Modulated Twisted Bilayer Graphene" |
| 5 | MoSe2 | 51 | 33 | 1.38 (0.89-2.14) | arXiv:2510.19596 "Atomic displacements drive flat band formation ... in near-60 degree twisted MoSe2/WSe2 bilayers" |

How to read the growth results:
- **Only CrSb, YBa2Cu3O7 and MnTe have CIs that exclude 1.** MnTe's lower bound is exactly 1.00, so it is borderline. WSe2 and MoSe2 are "probably growing a little" (point estimates 1.3-1.4, CIs include 1).
- **Altermagnetism is the one robust materials story.** Its two lead compounds (CrSb, MnTe) and the altermagnet-candidate family (R = 1.77, 1.43-2.20) all rise together. RuO2 is flat (R = 1.11, 0.74-1.68), possibly because reports questioned its altermagnetic order and attention moved to other compounds (an interpretation, not tested here).
  - The candidate family's monthly counts stay high through the trailing window (15-28 per month vs 1-19 per month in the preceding one). This is a sustained rise, not one burst.
  - The top CrSb authors appear in only 3 of 52 trailing records, so no single group dominates.
- **The YBa2Cu3O7 rise is a device/defect/metrology signal, not new pairing physics.** Trailing records cluster in:
  - one group's pseudogap/fluctuation-conductivity series (5 records share an author);
  - machine-learned interatomic potentials for radiation damage (4 records share an author);
  - He-ion-written Josephson junctions and resonators.
  Treat it as author-concentrated, and so as weak evidence of field-wide growth.
- **Cooling signals**:
  - MnBi2Te4: R = 0.64 (0.42-0.97).
  - Kitaev materials, mostly RuCl3: R = 0.63 (0.43-0.90).
  - AV3Sb5 kagome: R = 0.72 (0.51-0.995).
  - La3Ni2O7: R = 0.78 (0.60-1.01), even though it is still the most-named compound in the corpus. Its preceding window held the 2024-25 thin-film/ambient-pressure boom, so a share decline from a high base still means about 105 La3Ni2O7 records per year. The bilayer/trilayer nickelate family as a whole is flat (R = 0.96).

## Caveats

- **Counts are text mentions, not study subjects.** A formula in an abstract can be a substrate (SrTiO3, SrLaAlO4, hBN), a comparison, or a gating layer. WSe2 growth is partly WSe2 used as a spin-orbit proximity or moire layer on graphene (see the exemplar).
- **Family regexes overlap.** MoTe2 and WTe2 count in both `tmds` and `weyl_dirac_semimetals`. MnBi2Te4 counts in both tetradymites and vdW magnets. Family rows are therefore not additive.
- **The "multiferroic" word inflates `ext_ferroelectrics_multiferroics`**: in the altermagnet and vdW clusters, 243 of its 336 pattern hits are the word, not a formula. It measures "multiferroic framing" more than specific compounds.
- **The formula extractor has known misses and false positives.** It misses formulas inside parentheses (SrCu2(BO3)2, Co2(PO4)2, Pb-apatite "LK-99") and alloy notation such as (Bi,Sb)2Te3; those are left to the family regexes. Rare false positives remain, e.g. FP64 (a floating-point format) and quantum-chemistry clusters like Fe4S4 in the theory cluster; none reach any top-20 list.
- **Scope**: arXiv only. Harvest covered cond-mat.str-el, supr-con, mes-hall and mtrl-sci (including cross-lists); hep/quant-ph-only primaries are not in the corpus. Preprint counts reflect posting behaviour (group size, repeat postings of series), not importance. The ratio R already controls for the +11.9% overall in-scope growth.
- The Poisson CI ignores overdispersion from author series (see YBa2Cu3O7), so real uncertainty is wider than shown.

Machine-readable output, including full per-family counts per cluster, top-10 formulas per cluster, the extended lexicon and exclusion rules, and growth rankings for formulas (top 25) and families: `analysis/materials.json`.
