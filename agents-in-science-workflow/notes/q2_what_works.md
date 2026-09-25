# Q2 What works: evidence vs claims, and benchmarks (as of 2026-09-25)

## Established results

- **Coscientist**: a GPT-4 agent planned and ran robotic experiments, including Pd-catalysed cross-coupling optimization. Nature 2023 [@boiko2023coscientist].
- **ChemCrow**: an agent with 18 tools carried out syntheses of an insect repellent and three organocatalysts. Nat Mach Intell 2024 [@chemcrow].
- **A-Lab (contested)**: reported 41 of 58 targets made in 17 days [@alab]. An outside analysis found no new materials and called automated Rietveld analysis of powder XRD "not yet reliable" [@alab_critique]. A 2026 Author Correction followed, and the title now says "inorganic", not "novel" [@alab_correction].
- **Virtual Lab**: agents designed 92 nanobodies. Two bound JN.1 or KP.3 better. The authors' own lab ran the tests. Nature 2025 [@virtuallab].
- **CRISPR-GPT**: guided knockout of four genes and activation of two genes in human cells. Nat Biomed Eng 2025 [@crisprgpt].
- **Google Co-Scientist**: its AML drug-repurposing candidates were confirmed in vitro. Nature 2026 [@coscientist_google]. Its top hypothesis matched a mechanism a lab had confirmed but not published (cf-PICIs hijack phage tails) [@penades_ai][@penades_exp]. Two drugs it suggested were anti-fibrotic in human liver organoids [@liverfibrosis]. The partner labs co-authored with Google.
- **Robin**: in vitro tests confirmed ripasudil and KL001 as candidates for dry AMD. No animal or clinical evidence yet. Nature 2026 [@robin].
- **Biomni**: general biomedical agent with wet-lab case studies. Science 2026 [@huang2026biomni].
- **AlphaEvolve**: found new algorithms that can be proven correct, e.g. 4×4 complex matrix multiplication with 48 scalar multiplications [@alphaevolve]. With outside mathematicians it improved several best-known constructions [@alphaevolve_math]. White papers, but machine-checkable.
- **OpenScholar**: citation accuracy on par with human experts; GPT-4o hallucinated citations 78–90% of the time. Nature 2026 [@openscholar].
- **Review feedback**: in a randomized trial on more than 20,000 ICLR 2025 reviews, 27% of reviewers who got LLM feedback updated their reviews [@iclr_rct]. GPT-4 comments overlap human reviewers about as much as two humans overlap (30.85% vs 28.58%) [@liang_feedback].
- **AI Scientist**: an AI-written paper passed first-round review at a workshop with a 70% acceptance rate (a low bar). Nature 2026 [@aiscientist].
- **Instrument control**: an LLM agent found reference reflections and the orientation matrix on a real synchrotron beamline. Nat Mach Intell 2026 [@xray_scientist]. An AFM agent on real hardware scored 88.3% on documentation tasks but 33.3% on analysis, and "sleepwalked" off instructions [@aila_afm].

## Claims awaiting validation

- **Kosmos (Edison)**: independent scientists judged 79.4% of statements accurate, but only 57.9% of synthesis statements. Claims seven discoveries [@kosmos]. *Validation:* peer review, outside replication, and false-positive rates across all runs.
- **Zochi (Intology)**: says its AI-written paper was accepted at ACL 2025 [@zochi]. *Validation:* an audited record of human vs AI work.
- **Periodic Labs Neon**: 55.3% on an internal XRD test of 134 multiphase patterns, graded by an LLM judge. Claimed to beat frontier models [@periodic_neon]. *Validation:* release the test set, or score against expert Rietveld refinements of public data.
- **Lila Sciences**: an AI-guided loop screened 2,942 catalysts. InMnPdOx stayed below 0.5 V overpotential for 1,000 h in acid (preprint, 2026-09) [@lila_oer]. *Validation:* independent synthesis and durability tests.
- **OpenAI GPT-5 cases**: four new math results, checked only by the human co-authors [@gpt5_science]. *Validation:* refereed publication.
- **OpenAI Navier–Stokes (2026-09)**: Lean certificates claim finite-time blowup (Clay alternatives C/D) [@openai_ns]. *Validation:* experts confirming the formal statements match the Clay problem, then refereed publication.

## Benchmarks

| Benchmark | Measures | Best reported (system, date) | Human/expert baseline | Refs |
|---|---|---|---|---|
| GPQA Diamond | grad-level science MCQ | 95.8% (GPT-6 Astra, 2026-09) | experts 65% (74% adjusted) | [@gpqa][@epoch_hub] |
| HLE | expert closed questions | 54.8% (GPT 6 Astra, 2026-09-09) | none | [@hle][@hle_scale] |
| FrontierScience | olympiad / research tasks | 77% / 25% (GPT-5.2, 2026-01) | — | [@frontierscience] |
| CritPt | unpublished physics research | 32.3% (GPT-5.6 Sol, 2026-07) | — | [@critpt][@epoch_hub] |
| ChemBench | chemistry QA | best models beat best chemist surveyed (2025) | surveyed chemists | [@chembench] |
| MaCBench | chem/materials images (XRD, AFM) | XRD intensity ranking 0.28 (2025) | — | [@macbench] |
| LAB-Bench | practical biology | Claude 3.5 Sonnet (2024-07) | experts clearly ahead | [@labbench] |
| LabSafety Bench | lab hazards | <70% hazard ID (2026) | — | [@labsafety] |
| SciCode | research code | 10.8% main problems (official); 66.9% subproblems (Claude Opus 5.5, 2026-09) | — | [@scicode][@scicode_lb][@aa_scicode] |
| ScienceAgentBench | data-driven discovery code | 42.2% (o1-preview, 3 tries, 2024-10) | — | [@scienceagentbench][@hal_sab] |
| CORE-Bench Hard | reproduce results from code | 95.5%, "solved" (Opus 4.5 + Claude Code) | — | [@corebench][@hal_core] |
| BixBench | bioinformatics | 17% (2025-02) | — | [@bixbench] |
| DiscoveryWorld | simulated discovery | ≤18% completion (2024) | PhD scientists 66% | [@discoveryworld] |
| MLE-bench | Kaggle ML engineering | medal in 64.4% (Famou-Agent 2.0, 2026-02) | Kaggle leaderboards | [@mlebench][@mlebench_lb] |
| MLAgentBench | ML experiments | 37.5% (Claude 3 Opus, 2024) | — | [@mlagentbench] |
| RE-Bench | ML R&D | 4× experts at 2 h (2024-11) | experts 2× agents at 32 h | [@rebench] |
| PaperBench | replicate ICML papers | 21.0% (Claude 3.5 Sonnet, 2025-04) | ML PhDs 41.4% (subset) | [@paperbench] |
| EXP-Bench | full AI experiments | 0.5% (2025-05) | — | [@expbench] |
| SciReplicate-Bench | implement paper algorithms | 39% (2025) | — | [@scireplicate] |
| ReplicationBench | astrophysics replication | ~20% (Claude Sonnet 4.5, 2025-10) | — | [@replicationbench] |
| AstaBench | research assistance | 53.0% (Asta v0, 2025-08) | — | [@astabench][@asta_blog] |
| CURIE | long-context science | 32% (2025-03) | — | [@curie] |
| FIRE-Bench | rediscover ML findings | <50 F1 (2026) | — | [@firebench] |
| Collider-Bench | reproduce LHC analyses | none reliably beats baseline (2026-05) | physicist-in-the-loop | [@colliderbench] |
| AFMBench | real AFM hardware | 33.3% analysis (GPT-4o, 2025) | — | [@aila_afm] |
| APEXA-Bench | synchrotron data reduction | not yet scored (2026-09) | — | [@apexa] |

## What the benchmarks say

- **Closed-form science QA no longer tells models apart.** GPQA is at 95.8%, against 65–74% for experts. HLE reached 54.8%, but about 29% of its chemistry and biology answers conflict with the literature, and the newest scores carry contamination flags [@epoch_hub][@gpqa][@hle_scale][@hle_errors].
- **Well-specified computational tasks are close to solved.** CORE-Bench Hard is declared solved [@hal_core]; agents medal in 64% of MLE-bench competitions [@mlebench_lb]. Humans still lead on RE-Bench at long time budgets [@rebench].
- **Open-ended research is still weak.** Scores are 25% on FrontierScience-Research, about 20% on ReplicationBench, and 0.5% on EXP-Bench [@frontierscience][@replicationbench][@expbench].
- **Analysing lab data is weak, XRD included.** Models find the highest XRD peak with 0.74 accuracy but rank intensities at only 0.28, and assign space groups at 0.45 [@macbench].
- **Almost no benchmark uses real instruments.** AFMBench does [@aila_afm]. The APEXA authors saw a frontier model fabricate a calibration report for commands that never ran [@apexa]. No public benchmark covers closed-loop x-ray or neutron beamtime (diffraction, spectroscopy, imaging).
- **Many scores rest on LLM judges or private test sets**, and saturated benchmarks still have construct-validity problems [@paperbench][@periodic_neon][@corebench_sat].
