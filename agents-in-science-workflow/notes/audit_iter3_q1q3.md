# Audit iteration 3: qualitative claims in Q1 and Q3 (run 2026-09-25)

Scope: the qualitative and remaining factual statements in `report/parts/q1.html` and `report/parts/q3.html`. For each, I asked whether the cited source supports the sentence it is attached to. This covers system descriptions, organizations, dates, what a framework or protocol does, strong words ("almost every", "default") and evidence labels. I did not re-check the headline numbers from `audit_iter2.json`. Where a sentence depends on one of those numbers, I checked only the wording around it.

Sources used: arXiv abstracts and arXiv HTML full text; OpenAlex and Crossref records (abstracts, dates, affiliations); GitHub READMEs and the GitHub API; official docs (OLCF, NERSC, Claude Agent SDK, agentskills.io, Bluesky/Tiled); DOE/NNSA, FutureHouse and Intology pages; and, for MARS and Prism, where the publisher or product page was blocked, press coverage. Machine-readable results are in `audit_iter3_q1q3.json`. Every `old` string occurs exactly once in its part file, and a dry run that applied all five replacements succeeded.

## Counts

| Status | Q1 | Q3 | Total |
|---|---|---|---|
| confirmed | 28 | 28 | 56 |
| corrected | 1 | 2 | 3 |
| unsupported | 0 | 2 | 2 |
| **total checked** | 29 | 32 | 61 |

## Corrected / unsupported items

| # | File | Claim | Key | Status | What the source says | Fix (new text) |
|---|---|---|---|---|---|---|
| 1 | q3.html | ORNL agents steered an additive-manufacturing experiment across MDF and OLCF | ornlagents | corrected | Abstract: evaluated "through a realistic end-to-end workflow that employs a simulated version of the manufacturing facility"; paper text: "We simulated the 3D printer and SCOPS service." | ORNL agents steered an additive-manufacturing workflow linking OLCF with a simulated version of its Manufacturing Demonstration Facility [@ornlagents]. |
| 2 | q1.html | FutureHouse spun out Edison Scientific to commercialize Kosmos | futurehouse2025edison | corrected | The announcement (Nov 5, 2025) says the spinout will develop and deploy "our AI Scientist for commercial applications" and never names Kosmos. The Kosmos preprint says it runs "Edison Scientific agents". | FutureHouse spun out Edison Scientific to commercialize its AI Scientist; Kosmos is built from Edison Scientific agents [@futurehouse2025edison; @mitchener2025kosmos]. |
| 3 | q3.html | FIRST "generates billions of tokens daily on-premises" | first | corrected | The abstract describes a capability ("allowing researchers to generate billions of tokens daily on-premises"), not a measured production rate. | it lets researchers generate "billions of tokens daily on-premises" without commercial cloud [@first] |
| 4 | q3.html | Frontier models such as GPT-5 via vendor APIs "are still the default engine" [@gpt5card] | gpt5card | unsupported | The GPT-5 system card describes the model only. It cannot show what science agents use by default. Co-Scientist ("built on Gemini") and the Biomni README ("Required: Anthropic API Key for Claude models") are examples that do support the claim. | Frontier models such as GPT-5 [@gpt5card], called through vendor APIs, are still the default engine; Co-Scientist, for example, is built on Gemini, and Biomni's setup expects Claude [@gottweis2026coscientist; @biomnirepo]. |
| 5 | q3.html | "Almost every framework implements ReAct" [@react] | react | unsupported | The 2022 ReAct paper introduces the reason/act/observe pattern. It cannot support a count of how many frameworks use it today. | Frameworks typically build on ReAct, the loop in which the model reasons, calls a tool (acts), reads the result (observes) and repeats [@react]. |

## Notable confirmations (strong words and 2025–2026 items)

- **2026 venues:** OpenAlex publication dates confirm the 2026 venue claims: Co-Scientist (Nature, 2026-05-19), Robin (Nature, 2026-05-19), The AI Scientist (Nature, 2026-03-25), OpenScholar (Nature, 2026-02-04) and Biomni (Science, 2026-07-09).
- **Q1 catalog counts:** The Q1 taxonomy counts all match `report/catalog.json`. That includes 83 systems (58 general, 25 facility), L2 41, L3 21, L4 13 and L1 8; 12 of 14 literature systems are L2; the experiment stage has 26 systems (13 of them facility) and holds 15 of the 21 L3 systems; no experiment-stage system is L4.
- **Q1 source quotes:**
  - The AI Scientist warning is quoted verbatim.
  - The Agents4Science statement on human involvement is supported: "Accepted papers involved more human guidance than rejected papers."
  - AutoResearchClaw's targeted collaboration "consistently outperforms both full autonomy and exhaustive step-by-step oversight."
  - Zochi: Intology's post says the paper was "accepted into the main proceedings of ACL" 2025.
- **Q3 infrastructure:** These claims match the READMEs, docs and APIs:
  - IRI API groups and instances at NERSC, ALCF and ESnet. The SLAC repo is a GitHub fork (`fork: true`).
  - ChemGraph's providers and execution backends.
  - AutoGen's maintenance mode.
  - OLCF's vLLM service, OpenAI-compatible endpoints, S3M tokens and gpt-oss-120b.
  - NERSC's workspace-write guidance.
  - Biomni's warning about running with full system privileges.
- **VISION:** Confirmed at NSLS-II 11-BM CMS. The generated code goes to Bluesky only after the user confirms it.

## Notes for whoever applies the fixes

- **Highest impact:** #1 (ORNL). As written, the text says agents steered a real cross-facility experiment, but the manufacturing side was simulated. The same key (`ornlagents`) and its `supports` field ("cross-facility MDF-OLCF additive manufacturing experiment") may carry this claim into Q4. Worth checking there too.
- **refs.json label (not a part-file fix):** `react` is labeled `Preprint` although its venue field says ICLR 2023, which is peer-reviewed. `bianchi2025agents4science` is labeled `Peer-reviewed`, but its Nature Biotechnology article type is still unverified (the publisher page redirected to a login). Neither label is quoted in the q1 or q3 text.
- **Minor, left as confirmed:** "Globus Compute (formerly funcX)" is common knowledge; the cited 2020 funcX paper cannot state the rename. EnvTrace is mainly an evaluation method. Its digital twin "also enabl[es] the pre-execution validation of live experiments", so the Q3 wording holds.
