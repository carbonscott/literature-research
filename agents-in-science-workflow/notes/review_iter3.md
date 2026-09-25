# Reader review, iteration 3 (run 2026-09-25)

Reviewer stance: a DOE x-ray/neutron facility scientist, or a university collaborator, who is expert in their field but not in AI. Edits are in `review_iter3.json`: 30 edits (summary 6, q1 2, q2 4, q3 3, q4 6, q5 4, appendix glossary 5). A dry run (edits applied to a scratch copy, then built) passes `check_report.py --offline`. No facts, numbers or citation markers were changed.

## Overall assessment

The report is strong. It is well sourced, its caveats are honest, and it is clearly organized around questions this audience asks. The Q4 facility section and the Q6 prompts are the most valuable parts for the session. Most one-line answers are accurate takeaways.

There are three kinds of problems. First, a few internal contradictions that an expert reader will notice and that cost credibility (see issue 1). Second, AI jargon that is never defined, even though the report's main safety message depends on it: reward hacking, allowlisted tools, fail-closed gates, deterministic guards, frontier model, tokens, rollouts, desk rejection, and the conference and DOE acronyms. Third, heavy repetition across sections. The same five or six facility examples appear up to six times each, which makes Q3 to Q6 feel longer than they are.

The "At a glance" summary was mostly accurate. It left out three things the sections say: the L3 tier, where all six closed-loop facility systems sit; Q4's main caveat that facility steering is mostly single-campaign demonstrations; and the fact that Genesis is covered in Q4, not Q5. The edits fix all three.

Q4 is the part this audience will read most closely. It groups steering systems by lab but analysis systems by function. As a result, the ORNL (CNMS, SNS) heading lists no SNS system, and APS work is split across three subsections. One edit adds a road-map sentence. Restructuring options are listed below.

## Top 5 issues

1. **Contradictions between sections** (fixed by edits):
   - The Q2 heading says "peer-reviewed or independently validated", but the note right under it says "not independently replicated".
   - Q5 gives CORE-Bench as "21%" while Q2 says 95.5% and "declared solved".
   - Q5 calls 32.4% the "best" ScienceAgentBench score, then reports 42.2%.
   - The summary cites AlphaEvolve for an "L4" claim, but AlphaEvolve is L3 in the catalog.
2. **Undefined jargon and acronyms.** The edits add 16 glossary terms and define MCP, IRI, NNSA, FASST, ICMJE, CIF and checkCIF where they first appear.
3. **Q4 is hard to navigate by facility** (partly fixed by the road-map edit; see the structural suggestions).
4. **Repetition.** The APEXA fabricated report and its 0/200 vs 15/200 result appear in Q2, Q3, Q4, Q5 (three times) and Q6 (twice). The SSRL human relay appears about six times, Osprey plan review four times, and the A-Lab critique four times.
5. **Q6 is too long for 60 to 90 minutes.** It has 9 prompts, each with two or three sub-questions, which leaves about 7 to 10 minutes per prompt with no time for an opening or a wrap-up.

## Structural suggestions (not turned into edits)

- **Q6:**
  - Mark 4 or 5 core prompts. Prompts 1, 2, 4, 6 and 8 cover human oversight, safety, verification, standards and funding.
  - Group the prompts into three blocks of about 20 minutes each: at the beamline (1, 2, 4), shared infrastructure and data (3, 5, 6), and programs and people (7, 8, 9).
  - End each prompt with the output the room should produce, such as "a list of actions that always need approval" or "one candidate joint benchmark".
  - Prompt 5 cites a NERSC credentials rule that Q3 never discusses. Either add it to Q3 sandboxing or link Q5 instead.
- **Q4:**
  - Consider one per-lab table (steering, analysis, assistants, precursors) placed before the detailed lists.
  - The LCLS Bayesian-optimization item appears twice (the SLAC bullets and precursor item 6).
  - The status-table row "ALS agent / Osprey: Deployed" merges a one-off demonstration with a deployed framework. Split it into two rows.
  - ChatEED is a question-answering assistant but sits under "steering".
  - The DOE programs bullets are dense with dollar amounts. A small table (program, date, amount, relevance to facilities) would help facility managers.
- **Repetition:**
  - State each flagship facility example once in full, in Q4. Elsewhere, mention it briefly and link to Q4.
  - Cut the Q5 "For facilities" notes down to the recommended actions only.
  - Q3's "Stack at a glance" table repeats the six-layer list above it.
  - Q1's "What is new in 2026" repeats trends 2 and 6.
- **Q2 benchmarks table (26 rows):** for this audience, keep about 8 rows in the body (GPQA, HLE, CritPt, MaCBench, LabSafety, PaperBench, EXP-Bench, APEXA-Bench) and move the rest to the appendix.
- **Numbers to check (need a fact-checker; wording edits cannot fix them):**
  - A-Lab shows "41 of 58" in Q2 but "none of the 43 claimed novel materials" in Q5. Readers will see a mismatch, so explain where each count comes from.
  - Q1 says "6 of the L3 systems" are at facilities. This is correct (6 of 21, all in the experiment stage), but the sentence is dense.
- **Smaller wording fixes left out to stay within 30 edits:**
  - Q2: explain the AFM agent that "sleepwalked" (drifted off its instructions). Unpack "Clay alternatives C/D" in the Navier–Stokes row. Make "GPT 6 Astra" and "GPT-6 Astra" consistent. Change "two bound JN.1 or KP.3 better" to "...variants better". Define F1.
  - Q3: ether0 "24B" means 24 billion parameters. Gloss SDK, ASE/RDKit, "SLAC hosts a fork" (its own copy of the code), "AutoGen churn", CLI and W3C PROV. Explain "stateless" MCP (no sessions). Spell EQSANS and EQ-SANS consistently.
  - Q4: expand ASCR. Add "EPICS" before "IOC" (input/output controller). Give ρ as a Spearman rank correlation (the reference supports this). Expand BM25 (a keyword-search baseline). Rewrite "federated microservices" (INTERSECT) in plain words. Rephrase "SLAC was not one of them" as "SLAC was not among the nine labs".
  - Q5: "fell significantly more" needs a comparison ("than the human ideas' scores"). Spell out the LLM-judge biases (favoring the first answer, longer answers and their own outputs). Define holdout sets, GSM8k/GSM1k, "multiverse checks" and "canary prompts". State that the 2.30–4.23 scores came from AI reviewers.
