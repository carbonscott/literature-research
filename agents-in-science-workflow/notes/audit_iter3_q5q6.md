# Audit iteration 3: citation and consistency check of q5.html, q6.html, summary.html (run 2026-09-25)

Scope: factual and qualitative statements not covered by the iter2 number audit. This includes policy statements, what studies found, safety claims and "first/only/none" wording. For q6.html, each prompt's section link was checked against the target parts file. For summary.html, each bullet was checked against q1–q5.html and report/catalog.json.

Sources used: arXiv abstracts and HTML full text, OpenAlex and Crossref abstracts and dates, the official policy pages (ICLR, ICML, NeurIPS, ICMJE, Nature, NIH, NSF, NERSC, DOE, Agents4Science, Pangram, Anthropic), OSTI, and the cached full texts of the SSRL and Agents4Science papers.

Machine-readable results: `audit_iter3_q5q6.json` (76 entries). Every `old` string occurs exactly once in its file. All replacements were test-applied in sequence without conflicts. Every key in `new` exists in refs.json.

## Counts

| Status | q5.html | q6.html | summary.html | Total |
|---|---|---|---|---|
| confirmed | 35 | 18 | 8 | 61 |
| corrected | 3 | 10 | 2 | 15 |
| unsupported | 0 | 0 | 0 | 0 |
| **Total checked** | 38 | 28 | 10 | 76 |

All 25 section links in q6.html and summary.html resolve to existing ids. Five q6 links pointed to a section that does not hold the cited evidence; they are fixed below.

## Corrected items

| # | File | Statement | Key(s) | Problem | Fix (new text) |
|---|---|---|---|---|---|
| 1 | q5 | ICLR 2026 "checked references automatically" | iclr2026response | The ICLR post names no automated reference checking. Area chairs found the cases, and LLM-detection tools were used only for triage. It does support desk rejection. | "...treated hallucinated references as an ethics violation and desk-rejected papers containing them; area chairs found the cases, with LLM-detection tools used for triage" |
| 2 | q5 | Risk register: "Automated reference checks; desk rejection [@iclr2026response]" | iclr2026response | Same as #1. Automated checking comes from RefChecker. | "Automated reference checks [@russinovich2026phantom]; desk rejection [@iclr2026response]" |
| 3 | q5 | Kapoor: cost, holdouts and non-standardization "causing" pervasive irreproducibility | kapoor2024agents | The abstract ties irreproducibility only to non-standard evaluation practices. | "...ignore cost and lack holdout sets, and non-standard evaluation practices lead to..." |
| 4 | q6 | Answer: agents "tune accelerators" | q4_als_agentic | The ALS paper runs multistage machine-physics experiments; it does not tune. | "run accelerator experiments" |
| 5 | q6 | "The first real-beamline agent kept a person relaying every command" | q4_xray_scientist | "First" refers to the team's own first trial. VISION (2025) and APS agents ran on beamlines earlier. | "In its first real-beamline trial, the SSRL agent had a person relay every command" |
| 6 | q6 | Tool poisoning (MCPTox), linked only to Q5 safety | mcptox | MCPTox is discussed in Q3 protocols, not Q5. | Add a "Q3 protocols" link |
| 7 | q6 | "models rank powder-XRD peak intensities poorly" | macbench | MaCBench and Q2 say "XRD", not powder XRD. | "XRD peak intensities" |
| 8 | q6 | Digital twin scores "agent-written" control code, linked to Q5 | q4_envtrace | EnvTrace scores code written by more than 30 LLMs. It is discussed in Q4 steering and Q3, not Q5. The benchmark-flaw claim had no key. | "LLM-written", a Q4 steering link, and [@zhu2025abc] on the benchmark-flaw clause |
| 9 | q6 | VISION / NERSC / Genesis evidence linked to "Q4 programs" | q4_vision; nersccoding; whitehouse2025genesis | The claims are supported: NERSC says "do not paste credentials, tokens, or private keys into prompts". But Q4 programs holds only Genesis. VISION-local and Genesis compliance are in Q4 status (constraints), and NERSC is in Q3 hpc. | Links become "Q3 workflow and HPC; Q4 constraints" |
| 10 | q6 | MCP-for-Globus / IRI API / Bluesky linked to "Q4 status" | mcpscihpc; iriapi; q4_bluesky | mcpscihpc and iriapi are in Q3 hpc. | Add a "Q3 workflow and HPC" link |
| 11 | q6 | "NIH limits applications substantially developed by AI" | nih2025originality | NIH says such applications are not original. "Limits" can be misread as the separate 6-per-PI cap. | "NIH does not count applications substantially developed by AI as original" |
| 12 | q6 | SNS proposal rankings "correlated only partly" with human rankings | q4_proposal_llm | The authors say rankings "correlate strongly (Spearman ρ≈0.2–0.8, ≥0.5 after outlier removal)". | "correlated with human rankings at ρ≈0.2–0.8, at over 100× lower cost" (matches Q4) |
| 13 | q6 | "Visiting users already rely on facility chatbots", linked to Q5 | q4_esac | This is one chatbot, with no usage or reliance data. It is discussed in Q4 analysis, not Q5. | "A facility chatbot already serves visiting EQ-SANS users [@q4_esac] (Q4 analysis link)" |
| 14 | summary | L4 systems "cluster where results can be checked automatically ... code and proofs [@lu2026aiscientist; @novikov2025alphaevolve]" | novikov2025alphaevolve | catalog.json rates AlphaEvolve L3, not L4. Q1 says L4 systems sit where the experiment is "code, existing data or a proof". 6 of the 13 L4 systems are data-driven report writers, which are not automatically checkable. | "...sit where the "experiment" is code, existing data or a proof, such as machine-learning papers, data-driven reports and mathematics [@lu2026aiscientist; @mitchener2025kosmos; @feng2026aletheia]" |
| 15 | summary | Agents "replicate far fewer papers than human experts" | paperbench | PaperBench reports a rubric replication score (21.0% vs 41.4% for ML PhDs on a subset), not a count of papers. | "score well below human experts at replicating papers" |

## Notes (confirmed, but worth knowing)

- **refs.json:** the `supports` field of `iclr2026response` says "automated reference checking". The source does not say this, and the field should be corrected so the error does not come back.
- **ICLR collusion rule:** a hidden prompt counts as collusion only if it "results in a positive LLM-generated review". The short Q5 wording is acceptable.
- **Sakana test:** the 42% failure rate is 5 of 12 experiments, a small sample.
- **ORNL workshop:** it was organized by ORNL/OLCF staff but held in Denver. "Led by ORNL" would be slightly more exact than "hosted by ORNL".
- **"No DOE-wide equivalent" (Q5 credit):** no counter-evidence was found. The DOE SC merit-review page has no generative-AI section. The claim is suitably hedged.
- **ALS paper date:** online 2026-01-16; the DOI was registered in Dec 2025. "2026 work" in the summary is correct.
- **Summary, last bullet:** "Genesis sets the DOE policy frame" is an interpretation. Genesis is discussed in Q4 programs and Q6, but the bullet links only Q5 and Q6. A Q4 link is optional; there is no factual conflict.
