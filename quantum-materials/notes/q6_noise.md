# Q6 Noise: contested and unreplicated high-visibility claims (run date 2026-09-23)

Data: `analysis/q6.json`. Code: `analysis/noise_filter.py` (scoring and sweep, local files only),
`analysis/q6_claims.py` (claim definitions and hand labels read from abstracts),
`analysis/fetch_arxiv_supplement.py` (arXiv `id_list` lookups).
Windows: trailing = 2025-09-24..2026-09-23, preceding = 2024-09-24..2025-09-23.

## Q6

### How to read this

- A preprint counts as **supportive**, **critical** (null result or critique) or **neutral** based on what
  its title and abstract say about the claim as worded below. I did not read full texts.
- **Groups** means distinct last authors. Every paper that shares at least one author (first initial +
  surname) with the original group counts as that one group.
- **Noise score** comes from `analysis/noise_filter.py`. A claim is **noisy** at a score of 3 or more.
  **Watch** means the claim is not noisy, but nothing independent exists yet (F1 = +2).
- These are preprint signals. The counts are small, the labels are one reader's judgement from abstracts,
  and a high score means "treat as unconfirmed". It does not mean "wrong".

### Filter definition (checkable from corpus metadata plus the hand stance labels)

| feature | points | test |
|---|---|---|
| F1 | +2 | no supportive **experiment** in the corpus from outside the original group (skipped if the originals are themselves two independent observations) |
| F2 | +1 each, max +2 | in-window Comment / Reply / Response records or null-result experiments in the thread |
| F3 | +3 | an original or supportive record says in its arXiv comment that it is withdrawn or retracted |
| F4 | +1 | the original abstract uses onset-only, filamentary, small-fraction, single-sample or "signs of possible" wording |
| F5 | +1 / -1 | +1 if the original has no DOI, journal-ref or "accepted/in press" note more than 12 months after posting; -1 if it is linked to a peer-reviewed venue |
| F6 | +1 | positive follow-ups exist and **all** of them share an author with the original group |
| F7 | +1 | **new in this iteration:** in-window critical records outnumber supportive ones |

Changes from the scout's proposal:
- F7 is new. Without it, a claim refuted by many independent nulls (bulk RuO2, UTe2 chirality) scores the
  same as one with only a couple of critiques.
- F2 also counts null-result experiments whose titles are not "Comment on". An example is the failed
  LaSc2H24 synthesis, arXiv:2605.29985.
- F5 also accepts "accepted / in press / to appear" in the arXiv comment, plus a manual `known_venue`
  taken from the scout notes (used 2 times). arXiv DOI metadata lags publication. For example,
  arXiv:2309.17436 has only "Nature, in press".

### Ranked claims: the 10 chosen for Q6

Counts are in-window labelled preprints: supportive / critical, with distinct groups in brackets.
"Exp" counts experiments only.

| rank | claim | status | score | supportive (groups) | critical (groups) | independent supportive exp |
|---|---|---|---|---|---|---|
| 1 | LK-99 room-temperature SC in Cu-doped lead apatite | refuted | **6** | 1 (1), theory only | 3 (3), all exp | 0 |
| 2 | Microsoft topological gap protocol / Majorana parity readout | contested | **5** | 3 (1) | 5 (3) | 0 |
| 3 | Room-temperature SC in LaSc2H24 (250 GPa) | contested | **5** | 1 (1) | 1 (1) | 0 |
| 4 | Ambient room-temperature SC in graphite | unreplicated | **5** | 2 (2), theory only | 1 (1) | 0 |
| 5 | RuO2 as a bulk room-temperature altermagnet | refuted | **4** | 0 | 14 (13), 11 exp | 0 |
| 6 | Chiral (TRSB) zero-field SC in UTe2 | refuted | **4** | 0 | 4 (3), all STM | 0 |
| 7 | 151 K ambient SC in pressure-quenched Hg-1223 | unreplicated | 1 (**watch**) | 0 | 0 | 0 |
| 8 | TRSB / loop currents in kagome AV3Sb5 | contested | 1 | 10 (9) | 5 (5) | 7 |
| 9 | Bulk ~80 K SC in pressurized La3Ni2O7 | partially_replicated | 1 | 10 (6) | 4 (3) | 4 |
| 10 | Half-quantized thermal Hall in alpha-RuCl3 | contested | 0 | 4 (2) | 1 (1) | 1 |

The other scored claims are in `q6.json`:

| claim | status | score |
|---|---|---|
| UTe2 pair-density wave | contested | 3 |
| FQSH in 2.1-degree tMoTe2 | unreplicated | 3 |
| RuO2 thin-film altermagnetism | contested | 1; 15 supportive / 11 critical, 11 vs 9 groups |
| Ambient SC in strained nickelate films | partially_replicated | 1; 12 supportive from 9 groups, 8 independent |
| Hydride flux trapping | contested | 1 |
| Ta2NiSe5 excitonic insulator | contested | 1; 5 vs 4 groups |
| Rhombohedral-graphene chiral SC | partially_replicated | -1 |
| Rhombohedral-graphene FQAH | partially_replicated | -1 |

### Per-claim evidence (score breakdown, then in-corpus IDs on both sides)

**1. LK-99 (refuted, 6 = F1 2 + F2 2 + F5 1 + F7 1).**
- The original is arXiv:2307.12008 "The First Room-Temperature Ambient-Pressure Superconductor" (2023,
  outside the window, fetched into the supplement). It has no DOI 1,159 days after posting.
- Every in-window experiment is null:
  - arXiv:2603.23377 "Glassy magnetic freezing of interacting clusters in LK-99-family materials": the
    anomalies come from CuS and are not superconductivity.
  - doi:10.21203/rs.3.rs-10086532/v1 "Absence of Bulk Room-Temperature Superconductivity in
    Cu/S-Substituted Oxide Lead Apatite".
  - osti:2586715 "Microscopic Characterization of Pb10-xCux(PO4)6O by 31P and 63/65Cu NMR Measurements":
    a non-magnetic insulator.
- The only positive item is a Zenodo theory note, doi:10.5281/zenodo.20779430.

**2. Microsoft TGP (contested, 5 = F1 2 + F2 2 - F5 1 + F6 1 + F7 1).**
- Originals: arXiv:2207.02472 "InAs-Al Hybrid Devices Passing the Topological Gap Protocol" (PRB) and
  arXiv:2401.09549 "Interferometric Single-Shot Parity Measurement in an InAs-Al Hybrid Device" (Nature).
- Critical side:
  - Two Legg Comments: arXiv:2502.19560 "Comment on 'InAs-Al hybrid devices passing the topological gap
    protocol'..." and arXiv:2503.08944 "Comment on 'Interferometric single-shot parity measurement...'".
  - Three theory papers: arXiv:2505.23741, arXiv:2603.12256 (both argue that capacitance or inductance
    signals alone do not prove Majoranas) and arXiv:2504.01069 (a bias in the scattering invariant).
- All three positive follow-ups come from the Microsoft consortium (they share C. Nayak as an author):
  arXiv:2504.13240 "Response to recent comments...", arXiv:2507.08795 "Distinct Lifetimes for X and Z Loop
  Measurements in a Majorana Tetron Device" and arXiv:2606.03884 "20 Second Parity Lifetime in an InAs--Pb
  Tetron Device".
- No independent device replication is in the corpus.

**3. LaSc2H24 (contested, 5 = F1 2 + F2 1 + F4 1 + F6 1).**
- The original is arXiv:2510.01273 "Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System
  at High-pressure Conditions". It is also on Research Square as doi:10.21203/rs.3.rs-7755852/v1.
- The abstract quotes an *onset* of 271-298 K, which fires F4, although it also reports zero resistance
  and field suppression over 13 runs. It has no venue yet, but is 359 days old, just under the 12-month
  line.
- The only positive follow-up is same-group theory: arXiv:2601.01398 "Isotropic Superconductivity in
  Room-temperature Superconductor LaSc2H24" (Y. Ma).
- The independent null is arXiv:2605.29985 "Stability Analysis of Superconductivity in P6/mmm-LaSc2H24 and
  its Experimental Reproducibility from La-Sc Alloys". It reports 7 failed syntheses and no SC at 245-300 K.
  Caveat: it used a different precursor route.

**4. Graphite room-temperature SC (unreplicated, 5 = F1 2 + F2 1 + F4 1 + F5 1).**
- Three unrelated preparations from three groups, none replicated:
  - arXiv:2410.18020 "Magnetic field sorting of superconducting graphite particles with Tc>400K". No DOI
    after 700 days.
  - arXiv:2510.03256 "Signs of Possible High-Temperature Superconductivity in Graphite Intercalated with
    Lithium-Based Alloys" (Eremets group). The high-Tc fraction is below 0.1% (supplement record).
  - arXiv:2609.15712 "Wrinkles and Magnetic Flux Trapping in Graphite Nanoflakes...".
- Support is theory only:
  - doi:10.20944/preprints202510.2304.v1 (Talantsev's analysis of the 2510.03256 data). Talantsev has
    co-authored with Minkov/Eremets before, so its independence is weak.
  - doi:10.21203/rs.3.rs-5876926/v1 (graphite-alkane pairing).
- The closest related ambient claim was taken back in substance by its own authors: arXiv:2604.14395
  "Revisiting apparent ideal diamagnetism at ambient conditions in graphene-n-heptane-permalloy systems".
  The signal was an artifact.

**5. RuO2 bulk altermagnet (refuted, 4 = F1 2 + F2 2 - F5 1 + F7 1).**
- The original is arXiv:1901.00445 "Crystal Hall effect in Collinear Antiferromagnets" (Sci. Adv.).
- 11 in-window experiments on bulk crystals from separate groups are null. Examples:
  - arXiv:2410.05850 "Crystal structure and absence of magnetic order in single crystalline RuO2"
    (neutron diffraction).
  - arXiv:2503.20621 "The Fermi surface of RuO2 measured by quantum oscillations".
  - arXiv:2511.00399 "Absence of magnetic order and magnetic fluctuations in RuO2" (NMR).
  - arXiv:2510.13767 "Structural origin of resonant diffraction in RuO2".
  - arXiv:2604.10659 "Surface ferrimagnetic order in RuO2 film": bulk non-magnetic.
- DMC theory agrees: arXiv:2603.16125.
- No in-window supportive bulk measurement exists. The only in-thread Comment, arXiv:2604.10105, attacks a
  null paper and does not claim magnetism.
- **The live question is thin films.** A separate claim covers it: contested, score 1.
  - Supportive examples: arXiv:2412.18220 "Spin-Splitting Magnetoresistance in Altermagnetic RuO2 Thin
    Films" and arXiv:2606.26023 "Epitaxial Strain Activates Altermagnetic Spin-Splitting Torques in
    RuO2(100)".
  - Critical examples: arXiv:2601.06791 "Absence of magnetic order in epitaxial RuO2 revealed by X-ray
    linear dichroism" and arXiv:2510.13781 "Resonant diffraction and photoemission inconsistent with
    altermagnetism in epitaxial RuO2 films".

**6. UTe2 chiral SC (refuted, 4 = F1 2 + F2 2 - F5 1 + F7 1).**
- Originals: arXiv:2002.02539 "Weyl Superconductivity in UTe2" (Hayes et al.)
  and arXiv:2105.13721 "Chiral superconductivity in UTe2 probed by anisotropic low-energy excitations".
- All four in-window studies are STM and favour a non-chiral B3u state:
  - arXiv:2501.16636 "Pair Wavefunction Symmetry in UTe2 from Zero-Energy Surface State Visualization".
  - arXiv:2503.17450 "Observation of Persistent Zero Modes and Superconducting Vortex Doublets in UTe2".
  - arXiv:2503.17761 "Odd-Parity Quasiparticle Interference in the Superconductive Surface State of UTe2".
  - arXiv:2602.02490 "Visualizing the Odd-parity Superconducting Order Parameter...".
- Only 2-3 groups stand behind these, since the Davis alumni overlap.
- Multicomponent SC survives only near a pressure/field tetracritical point: arXiv:2603.17905 (neutral).
- The PDW part is a separate claim (score 3, contested):
  - Supportive, original group: arXiv:2603.08688 "Evidence of intertwined pair density and charge density
    wave orders in UTe2".
  - Critical, independent: arXiv:2504.12505 "Surface charge density wave in UTe2" and arXiv:2603.27211
    "Magnetic-field-tunable commensurate multi-q charge orders on UTe2 (011) surface".

**7. Hg-1223 pressure quench (unreplicated, 1 = F1 2 - F5 1; watch).**
- The original is arXiv:2603.12437 "Ambient-pressure 151-K superconductivity in HgBa2Ca2Cu3O8+δ via
  pressure quench" (PNAS).
- The corpus has no independent attempt, positive or null. The same group's earlier method paper,
  arXiv:2502.01881 "Creation, stabilization, and study at ambient pressure of pressure-induced
  superconductivity in Bi0.5Sb1.5Te3", is labelled neutral.
- **The filter does not flag it.** It is peer reviewed, only 6 months old, and has drawn no response yet.
  That is exactly the blind spot the "watch" flag exists for.

**8. AV3Sb5 TRSB (contested, 1 = F2 2 - F5 1).**
- The original is arXiv:2106.13443 "Time-reversal symmetry-breaking charge order in a kagome
  superconductor".
- 7 independent supportive experiments. Examples:
  - arXiv:2605.05101 "Microscopic evidence for imaginary charge density wave in a kagome metal".
  - arXiv:2606.25251 "NMR evidence for a loop-current state with broken C6 symmetry...".
  - arXiv:2505.05150 "Probing orbital magnetism of a kagome metal CsV3Sb5 by a tuning fork resonator".
- The null side:
  - arXiv:2510.26010 "High Resolution Polar Kerr Effect Studies of Cs3Sb5 and ScV6Sn6..." found no
    spontaneous Kerr signal.
  - arXiv:2503.15849 finds the Hall anomaly comes from small Fermi pockets.
- Two Comment/Reply pairs in the trailing window:
  - arXiv:2509.22634 "Limitations of detecting... in scanning tunneling microscopy" with its reply
    arXiv:2510.01305.
  - arXiv:2608.13579 "Comment on: Microscopic signatures of an imaginary charge density wave..." with its
    reply arXiv:2608.24927.
- This is a real two-sided dispute, not single-group noise.

**9. La3Ni2O7 under pressure (partially_replicated, 1 = F2 2 - F5 1).**
- The original is arXiv:2305.09586 "Superconductivity near 80 Kelvin in single crystals of La3Ni2O7 under
  pressure".
- 4 independent supportive experiments. Examples:
  - arXiv:2501.14584 "Bulk superconductivity up to 96 K in pressurized nickelate single crystals".
  - arXiv:2410.10275 "Imaging the Meissner effect in pressurized bilayer nickelate...".
  - arXiv:2607.27607 "Single-crystal structural phase diagram of stoichiometric bilayer nickelate La3Ni2O7
    under hydrostatic pressure".
- The dispute has narrowed to the size of the volume fraction:
  - arXiv:2510.02429 "Uncovering origins of heterogeneous superconductivity in La3Ni2O7 using quantum
    sensors".
  - The Korolev-Talantsev comments arXiv:2602.19282 and arXiv:2602.23240, with replies arXiv:2602.23842
    and arXiv:2603.01062.
- The strained-film version replicated faster than any other claim here: 8 independent experiments. Examples:
  - arXiv:2501.08022 "Superconductivity and normal-state transport in compressively strained La2PrNi2O7
    thin films".
  - arXiv:2506.15319 "Strain-tuning for superconductivity in La3Ni2O7 thin films".
  - One qualifying null: arXiv:2604.07807 "Granular Superconductivity in La2PrNi2O7-δ Thin Films".

**10. RuCl3 half-quantized thermal Hall (contested, 0 = F2 1 - F5 1).**
- The original is arXiv:1805.05022 "Majorana quantization and half-integer thermal quantum Hall effect in a
  Kitaev spin liquid".
- 3 of the 4 supportive in-window experiments come from the original Kyoto/Tokyo team, for example
  arXiv:2410.18342 "Magnetothermal transport in ultraclean single crystals..." and arXiv:2505.00971.
- The one independent supportive study is arXiv:2505.05417 "Evidence of chiral fermion edge modes through
  geometric engineering of thermal Hall in α-RuCl3". It keeps F1 at 0.
- The main counter-evidence is arXiv:2510.06443 "Phonon Hall Viscosity and the Intrinsic Thermal Hall
  Effect of α-RuCl3" (Nature 2026).
- The score is low because one independent study exists. The claim's credibility rests on 1 group versus 1.

### Corrections to the scout's candidate list

1. arXiv:2409.13504 exists, but was posted on 2024-09-20, four days **before** the window. It was added
   to the supplement with window null.
2. arXiv:2104.03925 is Hirsch-Marsiglio's flux-trapping proposal, not the Minkov/Eremets experiment. The
   experimental original is arXiv:2206.14108 "Trapped magnetic flux in hydrogen-rich high-temperature
   superconductors".
3. Several papers are not what their position in the list suggests:
   - arXiv:2602.15606 is DFT+U theory of a *hypothetical* altermagnetic state, not a pro experiment.
   - arXiv:2601.01398 is same-group theory.
   - arXiv:2605.13303 (Zeldov) has L. Ju, the original author, as a co-author, so it is not independent.
   - arXiv:2608.24989 does not address the 2.1-degree FQSH claim.
4. Every other in-window candidate ID exists in the corpus. Their abstracts match the scout's description.

### Sweep of the arXiv corpus (titles; arxiv.jsonl only, 35,295 records)

| category | trailing | preceding |
|---|---|---|
| Comment on / Reply to / Response to comments / Matters Arising | 22 | 22 |
| "Absence of" / "No evidence" / "Failure to" titles (excluding "in the absence of") | 20 | 30 |
| Revisiting / Re-examination titles | 26 | 35 |
| Withdrawn / retracted (arXiv comment) | 8 | 3 |

- 109 of the 165 records are in the quantum-materials scope rule. The rate is about 1 Comment/Reply per
  800 preprints.
- Comment/Reply records bunch in three kinds of topic:
  - **Majorana / topological SC** (preceding window): arXiv:2502.19560, arXiv:2503.08944,
    arXiv:2504.13240, arXiv:2501.03986, arXiv:2509.05153.
  - **Kagome and altermagnets** (trailing window): arXiv:2510.01305, arXiv:2608.13579, arXiv:2608.24927,
    arXiv:2605.28861, arXiv:2604.10105, arXiv:2606.27975, arXiv:2609.25357.
  - **Superconductivity evidence debates**:
    - Hydrides and the Meissner effect: arXiv:2412.05291, arXiv:2410.14704, arXiv:2411.18629.
    - Nickelates: arXiv:2602.23842, arXiv:2603.01062.
    - Cuprates: arXiv:2504.18531, arXiv:2509.14105, arXiv:2609.00467.
- Null titles bunch in **altermagnetism**:
  - RuO2: arXiv:2410.05850, arXiv:2503.07985, arXiv:2511.00399, arXiv:2601.06791.
  - MnF2: arXiv:2412.03545.
- Other null titles fall in orbital/spin torque (arXiv:2501.10260, arXiv:2603.04889, arXiv:2606.14868),
  kagome, and Majorana (arXiv:2604.24858 "Absence of Quasi-Majorana False Positives in Full-Shell Hybrid
  Nanowires").
- **Withdrawals** do not touch any Q6 claim:
  - About half are procedural (authorship or approval, papers split): arXiv:2606.11912, arXiv:2607.11298,
    arXiv:2504.21616, arXiv:2507.15170.
  - The content withdrawals are: an error in a Green's function (arXiv:2411.04294), flawed claims
    (arXiv:2605.26957), incorrect expressions (arXiv:2606.16674), incomplete analysis (arXiv:2607.14461),
    and a possible THz artifact in an inverse orbital Hall claim (arXiv:2512.19065).
- The sweep **undercounts**. Some critiques carry ordinary titles, for example arXiv:2509.22634,
  arXiv:2602.19282, arXiv:2602.23240 and arXiv:2605.29985. So the claim-level hand labels, not title
  regexes, drive F2.

### Caveats

- Labels come from abstracts only. "Supportive" often means "consistent with", as in arXiv:2412.02469
  ("implying possible").
- Counting groups by surname and initial can merge unrelated people. "M. Wang" is the La3Ni2O7 original
  author, which marks 2509.11557 and 2410.06602 as same-group. It can also miss collaborations.
  Crystal-grower co-authorship (UTe2, AV3Sb5) links critics to the original group.
- The corpus covers four cond-mat categories. Papers outside them were added only by 5 id_list requests
  (29 records in `corpus/arxiv_supplement.jsonl`, all but 1 outside the window). Some replication attempts
  may therefore be missing.
- Topic neighbourhoods are much larger than the labelled sets, for example 18 labelled of 104 RuO2 hits.
  Unlabelled hits are mostly theory or unrelated device work. The counts are floors, not censuses.
- Venue linkage uses arXiv metadata as harvested. Two originals needed a manual `known_venue` from the
  scout notes (Ta2NiSe5, tMoTe2 FQSH).
