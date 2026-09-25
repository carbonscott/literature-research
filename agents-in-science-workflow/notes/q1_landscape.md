# Q1 Landscape: AI agents across the scientific workflow (state as of 2026-09-25)

Scope: 58 general-science systems (a few 2023 landmarks, mostly 2024-2026). DOE x-ray/neutron facility systems are covered separately. Rows: `catalog_general.json`; references: `q1.refs.json`.

## Taxonomy: stage x autonomy (row counts)

| Stage | L1 Assistant | L2 Tool-using | L3 Closed-loop | L4 End-to-end | Total |
|---|---|---|---|---|---|
| Literature & ideation | 0 | 9 | 0 | 0 | 9 |
| Hypothesis generation | 0 | 5 | 4 | 1 | 10 |
| Experiment design & self-driving labs | 0 | 4 | 9 | 0 | 13 |
| Data analysis & simulation | 0 | 8 | 2 | 4 | 14 |
| Writing & review | 4 | 2 | 0 | 6 | 12 |
| Total | 4 | 28 | 15 | 11 | 58 |

- Literature tools sit at L2: retrieve-read-cite agents such as PaperQA2, OpenScholar and Ai2 Scholar QA/Asta [@skarlinski2024paperqa2; @asai2026openscholar; @singh2025scholarqa; @bragg2025astabench], plus deep-research products [@google2024deepresearch; @futurehouse2025platform].
- Experiment design has the most L3 systems, running closed loops on real robots and instruments: Coscientist, CRESt, k-agents, MARS [@boiko2023coscientist; @zhang2025crest; @cao2025kagents; @shi2026mars]. A-Lab and the Liverpool mobile-robot lab are included as non-LLM autonomous-discovery baselines [@szymanski2023alab; @dai2024mobilerobots].
- L4 systems cluster where the "experiment" is code or a proof: ML papers (AI Scientist, AI-Researcher) [@lu2026aiscientist; @tang2025airesearcher], data-driven reports (Kosmos, data-to-paper) [@mitchener2025kosmos; @ifargan2025datatopaper] and mathematics (Aletheia) [@feng2026aletheia].
- Review tools are mostly L1 assistants that inform human reviewers [@liang2024feedback; @thakkar2026reviewfeedback].

## Key trends 2024 -> 2026

1. **From single-tool agents to multi-agent "AI scientists."** Systems from 2023-24 wrapped one LLM around domain tools, e.g. ChemCrow's 18 chemistry tools [@bran2024chemcrow] and CRISPR-GPT [@qu2025crisprgpt]. By 2025-26 the usual design is a team of role-specialized agents with critique loops: Co-Scientist's generate-critique-refine tournament [@gottweis2026coscientist], Virtual Lab's "PI" agent with specialist agents [@swanson2025virtuallab], Robin's literature and data-analysis agents [@ghareeb2026robin], and Kosmos's shared world model across ~200 agent rollouts per run [@mitchener2025kosmos].

2. **Flagship claims reached high-profile journals.** In 2026 Co-Scientist, Robin, The AI Scientist and OpenScholar appeared in Nature and Biomni in Science [@gottweis2026coscientist; @ghareeb2026robin; @lu2026aiscientist; @asai2026openscholar; @huang2026biomni]. Workhorse simulation agents also gained peer-reviewed versions [@campbell2026mdcrow; @pham2026chemgraph; @chiang2025llamp].

3. **Commercial and frontier-lab entrants.** Google DeepMind covers hypotheses, algorithms, scientific software and maths (Co-Scientist, AlphaEvolve, ERA, Aletheia) [@novikov2025alphaevolve; @aygun2025era]. OpenAI published GPT-5 science case studies and launched the Prism writing workspace [@bubeck2025gpt5science; @openai2026prism]. FutureHouse spun out Edison Scientific to commercialize Kosmos [@futurehouse2025edison]. Sakana AI and Intology built end-to-end paper-writing agents [@lu2026aiscientist; @intology2025zochi]. Periodic Labs and Lila Sciences describe AI scientists coupled to their own autonomous labs [@periodiclabs; @lila]. Deep-research products made L2 literature agents widely available [@google2024deepresearch; @ai2_2025asta].

4. **Autonomy is highest where checking is cheap.** L4 and strong L3 results appear where an automatic check exists (benchmark score, code evaluator, proof check): AlphaEvolve found a 4x4 complex matrix multiplication with 48 scalar multiplications [@novikov2025alphaevolve]; DeepScientist tested ~1,100 ideas over a month [@weng2026deepscientist]. In wet labs, humans still run or approve experiments (Robin, Virtual Lab) [@ghareeb2026robin; @swanson2025virtuallab]. At Agents4Science, human input was higher in hypothesis and design stages, AI autonomy higher in analysis and writing, and accepted papers had more human guidance [@bianchi2025agents4science].

5. **Evaluation lags capability (the "verification gap").** Independent checks are rare and mixed. An external lab found Co-Scientist's top hypothesis matched its unpublished result [@penades2025cfpici], but an independent analysis disputed A-Lab's novelty claims [@leeman2024alabcritique]. LLM ideas judged more novel than experts' lost that edge after execution [@si2025ideas; @si2025gap]. About one in five Kosmos statements was not judged accurate [@mitchener2025kosmos]. Only ~44% of Agents4Science submissions had no flagged references [@bianchi2025agents4science]. A 2026 survey found 38% of 24 runnable systems report any novelty verification [@ding2026verificationgap], and AstaBench concludes AI remains far from solving research assistance [@bragg2025astabench].

6. **AI enters peer review; targeted human oversight beats full autonomy.** GPT-4 feedback overlapped with human reviews about as much as two reviewers overlap [@liang2024feedback]; in a randomized ICLR 2025 trial, 27% of reviewers given LLM feedback updated their reviews [@thakkar2026reviewfeedback]. The AI Scientist authors warn of "taxing overwhelmed review systems" [@lu2026aiscientist]. Human feedback improved Agent Laboratory outputs [@schmidgall2025agentlab], data-to-paper needs human co-piloting as goals get complex [@ifargan2025datatopaper], and AutoResearchClaw found targeted interventions beat both full autonomy and step-by-step oversight [@liu2026autoresearchclaw].

**National labs (non-facility):** A-Lab and LLaMP (LBNL / Materials Project), ChemGraph (Argonne) and AutoLabs (PNNL) wrap agents around each lab's own simulation and automation stack [@szymanski2023alab; @chiang2025llamp; @pham2026chemgraph; @panapitiya2026autolabs].

## What is new in 2026

2026 brought peer-reviewed "AI scientist" papers (Co-Scientist, Robin and The AI Scientist in Nature; Biomni in Science) and randomized evidence on AI in peer review [@thakkar2026reviewfeedback]. New systems pushed autonomy in mathematics (Aletheia: one paper with no human intervention, four open Erdős problems solved autonomously, 6 of 10 FirstProof problems) [@feng2026aletheia; @feng2026firstproof], in robotic materials labs (MARS) [@shi2026mars], and in open-source research pipelines with explicit human-intervention modes (AutoResearchClaw) [@liu2026autoresearchclaw]. OpenAI's Prism put an LLM inside LaTeX manuscript editing [@openai2026prism]. Critiques sharpened: a position paper argues current agents work as co-scientists but are not built for autonomous discovery [@bisht2026notbuilt], and a survey frames verifying agent claims as the field's central bottleneck [@ding2026verificationgap]. In the US, the November 2025 Genesis Mission order directs DOE to build a platform that includes AI agents and autonomous experimentation [@whitehouse2025genesis].

**Caveats:** autonomy labels are our judgment from each paper's own description. Vendor claims (Zochi, FutureHouse Platform, Prism) are not independently verified.
