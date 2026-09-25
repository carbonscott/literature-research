# Audit iteration 3: system catalog (run 2026-09-25)

Rows checked: **83** (58 general, 25 facility), all rows in `report/catalog.json`. Change proposals: **20** on **16** rows (15 facility, 5 general). Machine-readable proposals: `audit_iter3_catalog.json`. The catalog files were not edited.

## Method

- **Sources.** arXiv API records (27 cited IDs plus 20 preprint versions of DOI-cited works), OpenAlex and Crossref records for all 51 cited DOIs (abstracts, affiliations, dates, other versions), venue confirmation (OpenReview records or the authors' arXiv comments) for the 8 arXiv-cited rows labelled peer-reviewed, and full text for NeuDiff Agent (PMC), Rongzai, ALS accelerator agent, CycleResearcher, EAA, AI X-ray scientist and VISION. Vendor pages were checked for FutureHouse and the Stanford Agentic Reviewer.
- **Mechanical checks.** evidence_type against the cited ref (kind, venue, evidence); year against the earliest public version (arXiv, bioRxiv, ChemRxiv, Research Square, SSRN); organization against author affiliations; one_line word count (all 83 are within 25 words) and figures against the abstract.
- **Judgment checks.** Autonomy and stage for every row against the abstract (and full text where the label was in doubt). A change was proposed only when the source clearly contradicts the label.

## Changes by field

| Field | Changes |
|---|---|
| autonomy | 4 |
| stage | 0 |
| spans | 1 |
| evidence_type | 1 |
| year | 11 |
| organization | 0 |
| one_line | 3 |
| **Total** | **20** |

Mechanical checks that passed: evidence_type matches the cited ref on 82 of 83 rows (the 8 arXiv-cited "Peer-reviewed" rows all have confirmed ICLR, ICML or NeurIPS acceptances); organization matches the source affiliations on all 83 rows; 72 of 83 years match the first public release.

## Table of changes

| # | Row | Lane | Field | Old | New | Reason (source evidence) |
|---|---|---|---|---|---|---|
| 1 | ALS accelerator agentic AI | facility | autonomy | L3 Closed-loop | L2 Tool-using agent | Plan-first: 'before any tool is called, the system generates a complete execution plan'; operator approval for all control-system writes. Demo ran a user-specified 30-point ID-gap hysteresis scan once; no agent observe-and-replan cycles. Same design as Osprey (L2). |
| 2 | NeuDiff Agent | facility | autonomy | L4 End-to-end | L2 Tool-using agent | Paper calls itself a 'governed, tool-using AI workflow'; 'The user authorizes each tool execution and approves any corrective action' at gates. One analysis task (TOPAZ data to CIF), no experiments or paper, so not L4 'minimal human help'. |
| 3 | Rongzai agent | facility | autonomy | L4 End-to-end | L3 Closed-loop | Source: 'iterative decision-execution-evaluation loop' against GSAS-II 'until convergence', with a 'refine pause' for user instructions. One refinement task on given data and known starting structures; the 'report' is a refinement report, not a research paper, so L3 not L4. |
| 4 | CycleResearcher / CycleReviewer | general | autonomy | L4 End-to-end | L1 Assistant | Paper: 'all experimental results mentioned in the generated papers within this work were fabricated'; 'execution of actual experiments is beyond the scope'; humans or other agents must run experiments. Drafts papers without tools, so not L4 (goal to experiments to paper). |
| 5 | CycleResearcher / CycleReviewer | general | spans | [Hypothesis generation, Data analysis & simulation] | [Hypothesis generation] | No data analysis or simulation is run: experimental results in generated papers are fabricated by the model (paper, Sec. 3 and Limitations). |
| 6 | Ai2 Asta agents + AstaBench | general | evidence_type | Preprint | Peer-reviewed | arXiv 2510.21652 comment 'Published as a conference paper at ICLR 2026'; OpenReview lists it as 'ICLR 2026 Oral'. refs.json entry bragg2025astabench (venue 'arXiv preprint', evidence 'Preprint') needs the same update. |
| 7 | AI X-ray scientist | facility | year | 2026 | 2025 | Research Square preprint 10.21203/rs.3.rs-7456716/v1 posted 2025 (Crossref); NMI article says 'Received 25 August 2025' and links the preprint. Journal version 2026. |
| 8 | ALS accelerator agentic AI | facility | year | 2026 | 2025 | First released as arXiv 2509.17255 on 2025-09-21; Phys. Rev. Research version published 2025-12-05, so 2026 is wrong under either reading. |
| 9 | CALMS | facility | year | 2024 | 2023 | First released as arXiv 2312.01291 on 2023-12-03; npj Comput Mater version 2024-11-05. |
| 10 | ESAC | facility | year | 2025 | 2024 | First released as arXiv 2407.19075 on 2024-07-26; SoftwareX version 2025-06-11. |
| 11 | Instrument agents that learn on the job | facility | year | 2026 | 2025 | First released as arXiv 2509.00098 on 2025-08-27 (Research Square 2025-10-27); npj Comput Mater version 2026-03-06. |
| 12 | LLM accelerator tuning | facility | year | 2025 | 2024 | First released as arXiv 2405.08888 on 2024-05-14; Science Advances version 2025. |
| 13 | LLM proposal ranking | facility | year | 2026 | 2025 | First released as arXiv 2512.10895 on 2025-12-11; Scientific Reports version 2026-09-25. |
| 14 | Osprey | facility | year | 2026 | 2025 | First released as arXiv 2508.15066 on 2025-08-20; APL Machine Learning version 2026-02-04. |
| 15 | SasAgent | facility | year | 2026 | 2025 | First released as arXiv 2509.05363 on 2025-09-04; J. Appl. Cryst. version 2026-03-28. |
| 16 | TEM Agent | facility | year | 2026 | 2025 | First released as arXiv 2511.08819 on 2025-11-11; npj Comput Mater version 2026-06-10. |
| 17 | VISION | facility | year | 2025 | 2024 | First released as arXiv 2412.18161 on 2024-12-24; MLST version 2025-05-16. |
| 18 | LLM proposal ranking | facility | one_line | Pairwise LLM ranking of beamtime proposals from three SNS beamlines tracks human rankings at over 100x lower cost. | Pairwise LLM ranking of proposals from three SNS beamlines correlates with human rankings (Spearman 0.2-0.8) at over 100x lower cost. | 'Tracks human rankings' overstates agreement: abstract reports Spearman rho about 0.2-0.8 across beamlines (>=0.5 after 10% outlier removal) and 'over two orders of magnitude' lower cost. |
| 19 | A-Lab | general | one_line | Robotic solid-state synthesis with computation, literature-trained recipe models and active learning; reported 41 of 58 targets in 17 days (novelty later disputed). | Robotic solid-state synthesis with computation, literature-trained recipe models and active learning; reported 41 of 58 targets in 17 days; 2026 correction confirms 36. | Align with the 2026 Author Correction already used in Q2 (doi 10.1038/s41586-025-09992-y, ref key alab_correction): 36 of 40 remaining successes confirmed, 4 inconclusive, 1 removed. Row cites only szymanski2023alab; the report text should cite alab_correction next to it. |
| 20 | CycleResearcher / CycleReviewer | general | one_line | Open LLMs trained with feedback from an automated reviewer; CycleReviewer cut score-prediction error 26.89% versus individual human reviewers. | Open LLMs trained with automated-reviewer feedback draft full papers whose experimental results are fabricated, not run; CycleReviewer cut score error 26.89% versus individual reviewers. | Current line omits that no experiments are run: the paper states all experimental results in generated papers were fabricated. Numbers unchanged (26.89% MAE reduction vs individual human reviewers). |

## Effect on the Q1 taxonomy table (stage x autonomy)

- **Facility lane:** L4 goes from 2 to 0 (NeuDiff moves to L2, Rongzai to L3). The ALS accelerator agent moves from L3 to L2. Facility totals change from L1 4 / L2 13 / L3 6 / L4 2 to L1 4 / L2 15 / L3 6 / L4 0.
- **General lane:** Writing & review changes from L1 4 / L4 6 to L1 5 / L4 5 (CycleResearcher).
- After these changes no facility row is L4. The most autonomous facility agents run closed loops on one instrument or analysis task: AI X-ray scientist, EAA focusing, A-Lab GPSS, NSLS-II multi-beamline agents, the DESY tuning agent and, after this audit, Rongzai.

## Follow-ups outside the catalog rows

- `refs.json` / `notes/q1.refs.json`: update `bragg2025astabench` venue to ICLR 2026 and evidence to Peer-reviewed so the ref and the row agree.
- A-Lab: if the new one_line is used, cite `alab_correction` next to `szymanski2023alab` wherever the row appears in the text.
- Q4 bottom line ("chat assistants (2023-24) to supervised control of real beamlines, accelerators and microscopes (2025-26)"): with the corrected years, instrument control started earlier. CALMS (Dec 2023) operated an instrument conversationally, the DESY tuning agent (May 2024) tuned an accelerator subsystem, and VISION (Dec 2024) ran a voice-controlled beamline experiment. Recheck the date ranges.
- The year fixes change the catalog sort order (stage, then year).

## Checked but not changed (borderline; source does not clearly contradict)

- **VISION (L2):** each generated command needs user confirmation before it goes to Bluesky, which is close to the L1 pattern of the ORNL SPM row. Kept L2.
- **ChatEED (L1) vs APS-RAG (L2):** both are agentic RAG over logbooks. APS-RAG documents a ReAct tool executor over MCP; the ChatEED workshop paper describes the design without an evaluation. Kept as is.
- **APEXA (Preprint):** the arXiv comment says it was accepted at the 4th TPC Workshop at SC'26 (not yet held). Keep "Preprint" until the proceedings appear.
- **FunSearch (Hypothesis generation) vs AlphaEvolve (Data analysis & simulation):** both are the same evolutionary code-search method, labelled with different primary stages. Worth making consistent, but neither label is contradicted by its source.
- **POPPER (L2):** runs sequential falsification tests until an error-controlled stopping rule, which could count as L3. Kept L2.
- **MARS one_line** ("19 LLM agents and 16 domain tools"): no abstract was available from Crossref, OpenAlex, Semantic Scholar or Europe PMC, and the publisher page blocked access, so it could not be verified. It is not contradicted.
- **AI X-ray scientist one_line** ("human relayed commands") is confirmed: in the real-beamline demo a human passed on the agent's exact commands only to meet facility safety rules. L3 is confirmed.
