# Q5: Beyond arXiv. What do the other servers add?

Run date 2026-09-23. Trailing window = 2025-09-24..2026-09-23 (T); preceding = 2024-09-24..2025-09-23 (P).
Script: `analysis/q5_beyond_arxiv.py` -> `analysis/q5.json`. Audit labels: `analysis/q5_audit.json`.
Small API count checks (14 calls, HAL/Zenodo/Crossref only, no arXiv): `analysis/q5_api_checks.json`.

**Bottom line.** Apart from arXiv, only two servers add a meaningful amount of on-topic material
that is not already on arXiv. **OSTI** adds roughly 400-900 records over the two years. These are
mostly DOE-lab journal accepted manuscripts, plus some final reports and datasets. They are
journal-dated, so they tell you what got published, not what is new. **Research Square** adds
roughly 75-130 records. These are "In Review" journal submissions. ChemRxiv and Preprints.org add
tens. HAL adds close to nothing: about 78% of its records are on arXiv, and the rest is off-topic.
Zenodo and TechRxiv are mostly noise, and Zenodo's volume growth follows a surge in uploads across
all of Zenodo, not activity in the field.

## 1. Per-server table

"kept/fetched" is phrase-filter hits over records fetched, taken from the harvest logs.
"arXiv dup" means the record declares an arXiv ID OR its normalized title exactly matches a title
in `corpus/arxiv.jsonl`, or has token-set Jaccard >= 0.8 with one.
Audit rates come from n = 25 records per server (TechRxiv n = 2), sampled with a fresh
`random.Random(11)` per server from the in-window records sorted by id.
"Unique on-topic" = in-window records x (1 - arXiv dup share) x the on-topic rate among audited
records that are not duplicates. The range is the Wilson 95% interval on that rate.

| server | T | P | API total / fetched -> kept hits (unique) | kept/fetched | declared arXiv | arXiv dup (any) | on-topic (research, non-dup) | on-topic content incl. dups | fringe | off-topic | unique on-topic, T+P [95%] | unique, T only | noise |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| osti | 590 | 847 | 20,971 / 15,925 -> 2,146 (1,437) | 0.13 | 4.7% | 29.8% (43% for records dated 2026) | 56% | 80% | 0% | 16% | 744 [517-890]; censoring-corrected 603 [419-722] | 305 [212-365] | **low** |
| researchsquare | 109 | 88 | 8,261 / 8,261 -> 216 (197) | 0.026 | 0% | 25.4% | 48% | 84% | 8% | 8% | 110 [74-132] | 61 [41-73] | **low** |
| chemrxiv | 14 | 12 | 4,004 / 4,004 -> 37 (29) | 0.009 | 0% | 3.8% | 40% | 44% | 4% | 52% | 10 [6-15] | 6 [3-8] | **medium** |
| preprints_org | 25 | 30 | 5,444 / 5,444 -> 65 (57) | 0.012 | 3.6% | 5.5% | 52% | 56% | 24% | 20% | 28 [18-38] | 13 [8-17] | **high** |
| hal | 95 | 28 | 253 / 253 -> 145 (123) | 0.57 | 76.4% | 78.0% | 0% (0/7 non-dups) | 64% | 4% | 20% | 0 [0-10] | 0 [0-7] | **medium** (low within its arXiv mirrors, but everything outside them is noise) |
| zenodo | 1,336 | 122 | 2,208 / 2,208 -> 1,700 (1,458) | 0.77 | 0.1% | 0.5% | 20% | 20% | **68%** | 12% | 290 [129-567] | 266 [118-520] | **high** |
| techrxiv | 1 | 1 | 1,177 / 1,177 -> 2 (2) | 0.002 | 0% | 0% | 0/2 | 0/2 | 2/2 | 0 | 0 [0-1] | 0 | **high** (n = 2) |

For the Crossref servers, "API total" is the sum of `total-results` over the 25 query terms. Crossref
`query.bibliographic` is a ranked relevance search, not a phrase search, so most results are
unrelated. That explains the 1-3% kept rates. For the native servers, the APIs were queried with
quoted phrases, so the kept rates are higher. OSTI hit its 2,000-record cap on 3 terms
(superconductivity, nickelate, strongly correlated), so its volume is a lower bound.

Publication linkage (share of in-window records that show a journal version):
- OSTI: 94% (journal_name or a non-OSTI DOI). 1,150 of 1,437 records are "Accepted Manuscript".
- Preprints.org: 51% have Crossref `is-preprint-of`.
- ChemRxiv: 38% have `is-preprint-of`.
- HAL: 38% carry a journal DOI while still being typed as a preprint.
- Research Square: 29% have `is-preprint-of`. All 197 are labelled "In Review", meaning they were
  submitted to a Springer Nature journal.
- Zenodo: not recorded in the harvest.
- TechRxiv: 0%.

## 2. Caveats on arXiv-duplicate detection and dates

- **The arXiv corpus is narrow, so the dup share is a lower bound.** `corpus/arxiv.jsonl` covers
  only cond-mat.str-el, supr-con, mes-hall and mtrl-sci, starting 2024-09-24. Papers posted only in
  quant-ph, physics.optics or hep, or posted before the window, are not matched. Examples: HAL
  hal:hal-05701179 and hal:hal-05506780 declare arXiv IDs that are not in our arXiv corpus
  (41 of the 94 HAL declared IDs are not in it).
- **OSTI dates are journal publication dates, not first-posting dates.** For the 394 OSTI records
  that match an arXiv title, the arXiv version came first in 87% of cases. The median lead is
  127 days (range -282 to +583). As a result, the dup share rises with the OSTI date: 8% for
  2024Q4, 25-33% for 2025, and 42-47% for 2026Q1-Q2. Early-dated OSTI items look "unique" only
  because their arXiv version predates the harvest. The censoring-corrected estimate uses the 43%
  dup share of records dated 2026 onward, which gives 603 [419-722] unique on-topic records.
  `entry_date` is later than the publication month for 1,290 of 1,437 records.
- **Research Square has the opposite bias.** The arXiv version usually follows or accompanies the
  RS posting (arXiv first in 92% of matches, median lead 35 days). So recent RS records have not yet
  had time to appear on arXiv. The dup share falls from 44-46% (2025Q1-Q2) to 18-23% (2026), and the
  trailing-window unique count is likely overstated by about 20%.
- **Preprints.org sometimes posts before arXiv.** doi:10.20944/preprints202512.0537.v1 ("Zero-Energy
  Bound State Trapped in Line-Shaped Vortex in Topological Superconductor") appeared on arXiv 221 days
  later as arXiv:2607.13194. Also, a declared arXiv ID can be a false positive:
  doi:10.20944/preprints202510.2304.v1 declares arXiv id 2510.03256 (not in our arXiv corpus), which is the paper it *re-analyses*,
  not its own arXiv version.
- **HAL loses published preprints over time (survivorship bias).** The harvest kept only
  docType UNDEFINED (preprint). HAL retypes a deposit to ART once the journal version is attached.
  API check for "superconductivity" by submittedDate:
  - preceding window: 10 preprint vs 546 ART (115 of the ART with an arXiv ID)
  - trailing window: 25 preprint vs 150 ART

  So the 95 T / 28 P split in HAL is an artefact of this retyping, not growth. HAL also back-fills
  old papers. hal:hal-04917967 ("Inductance measurement of YBCO strip-lines made by ion
  irradiation") declares arXiv id 1008.4042, a 2010 paper, deposited in 2025. hal:hal-04794705 declares
  arXiv id 2407.12088, which predates the window.
- **Zenodo dates are user-declared.** `date` is the uploader's `publication_date`. It differs from
  the upload date for 168 of 1,458 records.
- **Zenodo growth is not a quantum-materials signal.** Zenodo preprints across all subjects grew
  7.3x (27,418 P -> 201,419 T, API check). Our quantum-materials hits grew 11x (122 -> 1,336), and
  monthly counts climb from about 5-30 per month in 2025 to 120-200 per month in mid-2026. The
  growth is driven by prolific independent uploaders. One author ("E8 Intelligence Research",
  Caldin) accounts for 152 records, 10% of the file. The "Majorana" term alone keeps 470 records.
- **Base volumes.** Across all subjects, Research Square grew +61% (56,482 -> 90,941 posted-content
  items), ChemRxiv +31% (9,714 -> 12,759), and Preprints.org -3% (31,660 -> 30,844). Quantum-materials
  counts on these servers are too small to support per-server trends: RS 88 -> 109, ChemRxiv 12 -> 14,
  Preprints.org 30 -> 25.
- **Near matches.** Spot checks of Jaccard matches found mostly the same paper with light retitling.
  About 1 in 15 looked questionable, for example "Acoustic Spin Skyrmion Molecule Lattices ..." vs
  "Skyrmion Molecule Lattices ...". There were only 35 near matches in total (4 RS, 30 OSTI, 1 Zenodo),
  so the effect is small.

## 3. Manual audit (one reviewer, title + abstract)

Label counts out of 25 (on / off / fringe / dup / dataset-report):
- ChemRxiv: 10 / 13 / 1 / 1 / 0
- Research Square: 12 / 2 / 2 / 9 / 0
- Preprints.org: 13 / 5 / 6 / 1 / 0
- TechRxiv: 0 / 0 / 2 / 0 / 0 (out of 2)
- Zenodo: 5 / 3 / 17 / 0 / 0
- HAL: 0 / 5 / 1 / 18 / 1
- OSTI: 14 / 4 / 0 / 6 / 1

`duplicate_of_arxiv` takes priority whenever the record is on arXiv. `dup_content` records whether
that duplicate was itself on-topic. With n = 25, each rate carries about ±15-20 points of sampling
uncertainty. Borderline calls are noted in the reasons: CISS "moiré" device claims, the Roeser-Huber
Tc formalism, review-style essays. None was double-coded.

## 4. What each server adds (with example IDs)

**OSTI (DOE repository): the largest non-arXiv contribution, but it lags.** The records are journal
accepted manuscripts from DOE labs. The top research orgs are ORNL (168), BNL (126), LBNL (116),
LANL, Ames, ANL and SLAC. There are also 55 technical/final reports and 19 datasets, which no
preprint server provides. Nothing fringe appeared in the sample. Examples not found on arXiv:
- osti:2560506 - "Pulling Order Back from the Brink of Disorder: Observation of a Nodal-Line Spin Liquid and Fluctuation Stabilized Order in K2IrCl6"
- osti:3818104 - "Spin Stripes and Superconductivity in Bilayer Nickelates"
- osti:3384904 - "Electronic structure of the kagome compound CaTi3Bi4 using high-field torque magnetometry and density functional theory"
- osti:3374335 - "INS data supporting the observation of spin-wave altermagnetic splitting in MnF2" (dataset)
- osti:3377533 - "STM/S Grid LDOS Data and Analysis Code for Deciphering Majorana Zero Modes in Topological Super..." (dataset)
- osti:2537889 - "Magnetism in Moiré Materials" (technical report)

Duplicate example: osti:3027528 "Cavity-altered superconductivity" is the same paper as arXiv:2505.17378.

**Research Square: good-quality journal submissions, a quarter already on arXiv.** All records are
"In Review" Springer Nature submissions. Many experimental papers come from groups that do not use
arXiv. Examples:
- doi:10.21203/rs.3.rs-4705720/v1 - "Parity Breaking and Sublattice Dichotomy in Monolayer FeSe Superconductor"
- doi:10.21203/rs.3.rs-7287112/v1 - "High harmonic generation reflecting the sub-cycle evolution of the Mott transition under a mid-infrared electric field"
- doi:10.21203/rs.3.rs-8743396/v1 - "Bi-Sb alloys irradiated with swift heavy ions as potential topological amorphous superconductors"
- Duplicate: doi:10.21203/rs.3.rs-7755852/v1 "Room-Temperature Superconductivity at 298 K in Ternary La-Sc-H System..." is arXiv:2510.01273.
- Fringe: doi:10.21203/rs.3.rs-10741245/v1 "World-First Realization of Dynamical Quasi-Superconductivity...".

**ChemRxiv: the chemistry side, with heavy term collision.** Half the kept records are off-topic.
Electrochemical "flat band potential" (doi:10.26434/chemrxiv-2025-56l44), molecular "moiré"
assemblies and quantum-chemistry "strongly correlated" methods all pass the phrase filter. The
on-topic remainder is DFT/DMFT and synthesis work on specific compounds:
- doi:10.26434/chemrxiv.15002414/v1 - "Dynamic correlation suppresses antiferromagnetism in heavily doped Fe-pnictide superconductor LaFeAsO1−xFx"
- doi:10.26434/chemrxiv.15007630/v1 - "Mn-Driven Ferromagnetism and Electronic Correlations in Multiferroic Bi5Ti3MnO15 from First Principles"
- doi:10.26434/chemrxiv-2025-95t55 - "Skyrmion-Like Spin Textures Emerging in the Material Derived from Structural Frustration"

**Preprints.org: mixed.** About half the sample is ordinary work, some of it re-analysis of other
groups' data (Talantsev). About a quarter is fringe: room-temperature superconductivity claims and
anti-BCS essays. Examples:
- On-topic: doi:10.20944/preprints202509.2167.v1 "Enhanced Superconductivity near the Pressure-Tuned Quantum Critical Point of Charge-Density-Wave Order in Cu1-δTe"
- On-topic: doi:10.20944/preprints202512.0291.v1 "Anomalous AC Susceptibility Response and Paramagnetic Meissner Phase of EuRbFe4As4 Superconductor"
- On-topic: doi:10.20944/preprints202502.0137.v1 "Two-Band Superconductivity and Transition Temperature Limited by Thermal Fluctuations in Ambient Pressure La3-xPrxNi2O7-d Thin Films"
- Fringe: doi:10.20944/preprints202509.0541.v1 (superconductivity above 0 °C claimed in Y6Cu6O14)
- Fringe: doi:10.20944/preprints202502.1068.v1 ("Zhao theory" ThS room-temperature superconductivity)

**HAL: essentially an arXiv mirror for this topic.** 78% of records are on arXiv. In the sample, all
7 non-duplicates were off-topic ("strongly correlated" in climate or psychology papers, a thesis
stub) or fringe:
- hal:hal-05482717 - "Paramagnetically driven superconducting re-entrance in Eu-doped infinite layer nickelates" (duplicate of arXiv:2601.19473)
- hal:hal-05760014 - "Distinguishing Majorana zero modes from trivial defect states in an iron-based superconductor" (duplicate of arXiv:2606.17499)
- hal:hal-05730561 - "Photochemical ageing drives the browning of urban outflows..." (off-topic)
- hal:hal-04983943 - "Neutrino Physics on the special Superstrings in Metals" (fringe)

**Zenodo: mostly fringe, from independent uploaders.** The fringe material includes
theories-of-everything, "E8/phi-Floquet" series and ether models. A small minority is legitimate
independent theory or proposals:
- doi:10.5281/zenodo.21765888 - "Stiffness Switching on a Local-Unitary Orbit of Exact Condensates"
- doi:10.5281/zenodo.21937346 - "Interface Engineering of Nickelate Superconducting Thin Films by a Graphene Capping Layer: A Low-Cost, Falsifiable Experimental Proposal..."
- doi:10.5281/zenodo.22168481 - "Lithographically Patterned Cobalt Nanoribbons as Magnetic Artificial Pinning Centers in REBCO Coated Conductors..."
- Fringe: doi:10.5281/zenodo.21357073 ("Phi-Floquet 4320th Harmonic Realizes Self-Dual E8 Torus with Fibonacci Anyon Network")
- Fringe: doi:10.5281/zenodo.22052099 ("Superconductivity in the Framework of Spacetime Ladder Theory...Dark Matter Qi-Field")

**TechRxiv:** 2 records, both fringe. doi:10.36227/techrxiv.176369865.59370636/v1 claims a
metamaterial route to 300 K superconductivity. doi:10.36227/techrxiv.172902566.60093072/v1 is a
two-sentence monopole note. Negligible.

**Topic distribution.** Re-run 2026-09-23 with `analysis/classified.jsonl` (taxonomy v2) present;
the result is `topic_distribution` in `analysis/q5.json`. Counts are multi-label cluster
assignments over in-window records; "unclassified" also holds records the classifier put out of
scope. Top 3 clusters per server (unclassified count in brackets):

| server | top 3 clusters (records) | unclassified |
|---|---|---|
| osti | vdw_magnets_topological_magnetism 207, cdw_nematic_excitonic 155, topological_insulators_semimetals 153 | 224 |
| researchsquare | topological_insulators_semimetals 40, moire_twisted_2d 31, cdw_nematic_excitonic 26 | 12 |
| chemrxiv | moire_twisted_2d 10, vdw_magnets_topological_magnetism 6, mott_hubbard_strange_metal 4 | 2 |
| preprints_org | other_superconductivity 8, cuprate_sc 5, unconventional_topological_sc 5 (tie: topological_insulators_semimetals 5) | 10 |
| hal | mott_hubbard_strange_metal 18, unconventional_topological_sc 13, moire_twisted_2d 11 | 40 |
| zenodo | other_superconductivity 220, unconventional_topological_sc 206, topological_insulators_semimetals 87 | 529 |
| techrxiv | other_superconductivity 1, hydride_high_pressure_sc 1 | 0 |

These are keyword-classifier labels, not audit labels. For Zenodo they mostly track fringe
content: 70 of the 206 unconventional_topological_sc assignments come from the single
"E8 Intelligence Research" uploader (152 records). No other Q5 number changed on the re-run.

Note (audit, 2026-09-23): the table column "on-topic (research, non-dup)" actually shows the
on-topic rate over all audited records, including duplicates (e.g. OSTI 14/25 = 56%). The rate
among non-duplicates, which the unique estimates use, is OSTI 74% (14/19), Research Square 75%
(12/16), ChemRxiv 42% (10/24), Preprints.org 54% (13/24), HAL 0% (0/7), Zenodo 20% (5/25),
TechRxiv 0/2. See notes/audit/q5.md.

## 5. Recommended weighting in the landscape

| server | recommendation |
|---|---|
| arXiv | Primary signal (about 9.9k in-scope records in T). All servers below together add about 4% extra unique on-topic material: roughly 390 records in T (OSTI 305, RS 61, others about 20), excluding Zenodo. This is an approximate comparison, because the arXiv scope rule and the non-arXiv phrase filter differ. |
| osti | Use as a secondary, lagging "published output" layer, not a preprint signal. Dedupe against arXiv and do not add it to preprint trend counts. Its datasets and reports can be cited as DOE-lab activity indicators. |
| researchsquare | Include after title dedup. Weight comparable to arXiv per record, but report counts separately. The trailing unique count is overstated (arXiv right-censoring). |
| chemrxiv | Include only after manual or taxonomy screening. Useful for qualitative synthesis/chemistry-side examples. Too small for trends. |
| preprints_org | Only with a manual screen. Never use unscreened counts. Treat room-temperature superconductivity items as fringe by default. |
| hal | Drop for counting (it duplicates arXiv). Its T/P ratio is an artefact of retyping. |
| zenodo | Exclude from counts. At most, mention as a qualitative note on the fringe/independent-upload surge. |
| techrxiv | Exclude. |

## Improvements not done (mentioned, not implemented)

- Match OSTI and Research Square titles against arXiv beyond the four cond-mat categories and
  before 2024-09-24. This would tighten the dup shares; it needs arXiv access, which was not allowed
  here.
- Keep Zenodo `related_identifiers` in the harvest to measure its journal and arXiv linkage.
- Double-code the audit with a second reviewer, and enlarge the samples for Preprints.org and
  ChemRxiv to narrow the ±15-20-point uncertainty.
