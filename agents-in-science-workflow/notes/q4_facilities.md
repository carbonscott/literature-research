# Q4 Facilities: AI agents at DOE x-ray and neutron user facilities (state as of 2026-09-25)

**Bottom line.** LLM agents have moved from chat assistants (2023–24) to supervised control of real beamlines, accelerators and microscopes (2025–26). Instrument steering is still mostly single-campaign demonstrations. Deployed systems are mainly knowledge assistants, data-reduction agents and one accelerator control-room framework.

## (a) Steering beamlines, instruments and accelerators

- **SLAC SSRL.** An LLM agent aligned a single crystal on the BL17-2 six-circle diffractometer [@q4_xray_scientist].
  - MCP tools wrap SPEC commands; it found reference reflections and the orientation matrix.
  - Developed in a virtual diffractometer (Claude Sonnet 4, Gemini 2.5 Flash benchmarked); Claude Opus 4 ran on the real beamline.
  - A human relayed each command without modification, for safety [@q4_xray_scientist].
- **BNL NSLS-II / CFN.** VISION turns voice or text into Bluesky code at 11-BM CMS [@q4_vision].
  - First voice-controlled x-ray scattering experiment; beamline models run locally, GPT-4o in the cloud for other functions [@q4_vision].
  - It grew out of an open-source-LLM prototype [@q4_vision_prototype].
  - EnvTrace scores control code from more than 30 LLMs against a beamline digital twin [@q4_envtrace].
- **Argonne APS / CNM.**
  - CALMS combines documentation retrieval with instrument tool calls [@q4_calms].
  - Human-in-the-loop agents run an x-ray nanoprobe beamline and a robotic materials station, improving with feedback [@q4_learn_on_job].
  - Vision-language agents (EAA) automate zone-plate focusing and feature search at an imaging beamline [@q4_eaa].
  - For an MCP-compatible atomic layer deposition (ALD) reactor, only recent reasoning models solved process-discovery tasks [@q4_ald_agent].
- **LBNL.**
  - An agent ran multistage machine-physics experiments on the ALS accelerator, cutting preparation time ~100x within operator safety constraints [@q4_als_agentic].
  - Osprey, the framework behind it, requires human review of a complete plan before any hardware action [@q4_osprey].
  - Semantic channel finding maps natural-language intent to control signals; proof-of-concepts ran at four facilities [@q4_channel_finding].
  - Lightfall, a beamline control platform with a built-in agent, is in testing at COSMIC-Scattering [@q4_lightfall].
  - TEM Agent controls microscope subsystems, data management and HPC through MCP [@q4_tem_agent].
  - The air-free A-Lab's agent chose 352 syntheses [@q4_alab_gpss].
- **ORNL.**
  - At CNMS, GPT-4 wrote scanning-probe microscope code but struggled with in-depth experiment design [@q4_liu_spm].
  - INTERSECT provides federated microservices for multi-facility autonomous experiments [@q4_intersect_toolkit] [@q4_intersect_page].
- **Accelerator logbooks.** ChatEED (SLAC) answers operator questions from the e-log [@q4_chateed]; retrieval-augmented e-log search was demonstrated at Fermilab, JLab, LBNL and SLAC [@q4_elog_accel].
- **International.**
  - DESY: LLM accelerator tuning from an operator prompt [@q4_kaiser_sciadv], the GAIA assistant [@q4_gaia], and a proposed multi-agent control design [@q4_sulc_agentic_accel].
  - CSNS (China) runs a Rietveld refinement agent for external users [@q4_rongzai].
  - None found from ESRF, Diamond, European XFEL or PSI.
- **Outlook.** NIST authors argue agentic AI will manage multi-instrument labs [@q4_kusne_multiagent].

## (b) Pre-LLM autonomous-experiment precursors

1. Gaussian-process autonomous x-ray scattering (the gpCAM lineage) [@q4_kriging_2019] [@q4_gp_natrevphys].
2. CAMEO: closed-loop Bayesian active learning at SSRL that found a new Ge-Sb-Te phase-change material [@q4_cameo].
3. ANDiE: neutron diffraction that determined Néel temperatures 5-fold more efficiently [@q4_andie].
4. Argonne FAST: autonomous scanning microscopy that needed under 25% of the sample [@q4_kandel_fast]; edge-AI ptychography at 2 kHz [@q4_edge_ptycho].
5. Bluesky-hosted agents coordinating multi-beamline measurements at NSLS-II [@q4_maffettone_multimodal] [@q4_corrao_multibeamline].
6. LCLS physics-guided Bayesian optimization for aligning a 12-parameter split-and-delay optic [@q4_lcls_bo]; ORNL edge-to-exascale steering at SNS [@q4_ornl_edge_exascale].

## (c) Facility data analysis and knowledge assistants

- **NeuDiff Agent (SNS TOPAZ).** It goes from raw data to a validated CIF.
  - Safeguards: allowlisted tools, fail-closed gates, and full provenance.
  - Time fell from 435 to 86.5–94.4 min, with no checkCIF A/B alerts [@q4_neudiff].
- **SNS small-angle tools.**
  - SasAgent drives SasView [@q4_sasagent].
  - EQSANS-CLI lets an external agent run reductions from Slack [@q4_eqsans_cli].
  - VULCAN's reduction pipeline was written with an AI coding agent [@q4_vulcan_reduction].
- **APEXA (APS)** is a deployed calibration and integration agent with 61 tools [@q4_apexa].
  - A frontier model fabricated a calibration report for commands that never ran.
  - Motor-control violations against a simulated IOC: 0/200 with its deterministic guard, 15/200 with a safety prompt alone.
- **Other analysis agents.** PEAR uses multiple agents for ptychography [@q4_pear]. AgentBuild builds a GSAS-II Rietveld agent from a scientist-written contract [@q4_agentbuild].
- **Knowledge assistants.**
  - ESAC: a chatbot for EQ-SANS users [@q4_esac].
  - APS-RAG, deployed for staff: 70.3% versus 63.8% strict recall [@q4_aps_rag].
  - SNS proposal ranking: correlation with human rankings of ρ≈0.2–0.8, at over 100x lower cost [@q4_proposal_llm].

## (d) DOE programs and policy

- **Genesis Mission executive order (Nov 24, 2025).** It creates a platform that explicitly includes "AI agents" and autonomous experimentation [@q4_genesis_eo].
  - Milestones at 60, 90, 120, 240 and 270 days; the 240-day step reviews robotic laboratories.
  - It requires classification, cybersecurity and export-control compliance.
- **Genesis follow-up.**
  - 26 challenges, including "Enhancing Particle Accelerators for Discovery" and "Achieving AI-Driven Autonomous Laboratories" [@q4_genesis_challenges]. The autonomous-labs challenge names user facilities as its "nucleus" [@q4_genesis_autolabs].
  - Agreements with 24 organizations, among them Anthropic, AWS, Google, NVIDIA and OpenAI [@q4_genesis_mous].
  - Jul 2026: >$5B across 278 projects [@q4_genesis_5b], plus >$800M from partners [@q4_genesis_800m] [@q4_genesis_doe_page].
  - An Office of Science advisory subcommittee's high-performance-magnets milestones include connecting autonomous labs to user facilities [@q4_scac_genesis].
- **American Science Cloud (AmSC).**
  - Established by Public Law 119-21, Sec. 50404 ($150M) [@q4_pl119_21], with an ASCR lab call [@q4_amsc_lab25_3555].
  - It links 17 labs and 28 user facilities [@q4_lbnl_amsc].
  - The multi-lab SYNAPS-I project targets real-time analysis at light and neutron sources [@q4_lbnl_amsc] [@q4_synaps_release].
- **Funding and solicitations.** >$320M, including 14 robotics and autonomous-experiment projects [@q4_doe_ai_investments]; robotics testbeds (about $30M) [@q4_lab26_3601].
- **FASST.** Roadmap and request for information in 2024 [@q4_fasst_roadmap] [@q4_fasst_rfi]. Our inference: Genesis now plays FASST's umbrella role.
- **1,000 Scientist AI Jam (Feb 28, 2025).** Nine labs (not SLAC), >1,400 scientists [@q4_llnl_aijam] [@q4_ornl_aijam] [@q4_anthropic_aijam].
- **Partnerships.**
  - OpenAI models on LANL's Venado supercomputer [@q4_lanl_openai] [@q4_nnsa_venado].
  - Anthropic's DOE partnership, including instrument MCP servers [@q4_anthropic_doe]; Claude at LLNL [@q4_anthropic_llnl].
  - NVIDIA Solstice and Equinox at Argonne [@q4_doe_nvidia_oracle]; AMD Lux and Discovery at ORNL [@q4_doe_amd_lux].
- **Integrated Research Infrastructure (IRI).** Blueprint and program [@q4_iri_aba] [@q4_iri_program].

## (e) Status summary

### Facility agent systems

| system | facility/lab | technique | what the agent controls or analyzes | status | ref |
|---|---|---|---|---|---|
| AI X-ray scientist | SLAC SSRL | crystal diffraction | diffractometer motors, detector | demonstrated | [@q4_xray_scientist] |
| VISION | BNL NSLS-II | x-ray scattering | Bluesky motors, detector | demonstrated | [@q4_vision] |
| Learn-on-the-job agents | Argonne APS/CNM | nanoprobe, robotics | multi-task workflows | demonstrated | [@q4_learn_on_job] |
| EAA | Argonne APS | x-ray imaging | focusing, feature search | demonstrated | [@q4_eaa] |
| ALS agent / Osprey | LBNL ALS | accelerator | control channels, archiver | deployed | [@q4_als_agentic] [@q4_osprey] |
| Lightfall | LBNL ALS | coherent scattering | devices, GP scans | testing | [@q4_lightfall] |
| TEM Agent | LBNL Molecular Foundry | TEM | microscope, HPC | demonstrated | [@q4_tem_agent] |
| NeuDiff Agent | ORNL SNS | neutron crystallography | reduction to CIF | demonstrated | [@q4_neudiff] |
| SasAgent / EQSANS-CLI | ORNL SNS | SANS | fitting, reduction | demonstrated | [@q4_sasagent] [@q4_eqsans_cli] |
| APEXA | Argonne APS | diffraction | calibration, integration | deployed | [@q4_apexa] |
| APS-RAG | Argonne APS | operations | logbooks, control data | deployed | [@q4_aps_rag] |
| ChatEED | SLAC | accelerator operations | e-log retrieval | demonstrated | [@q4_chateed] |
| Rongzai | CSNS | neutron powder diffraction | Rietveld refinement | deployed | [@q4_rongzai] |
| Genesis platform | DOE | all | autonomous experimentation | proposed | [@q4_genesis_eo] |

**Integration points.**
- Instrument control: SPEC [@q4_xray_scientist], Bluesky [@q4_vision] [@q4_bluesky], and control-system channels [@q4_osprey].
- Data and workflows: Tiled/Prefect/gpCAM [@q4_als_petra] [@q4_tiled].
- MCP as the tool layer [@q4_eaa] [@q4_aps_rag].
- Computing: leadership-class HPC agent serving [@q4_agentic_hpc] and IRI/AmSC APIs [@q4_amsc_lab25_3555].

**Facility-specific constraints.**
- **Beamtime.** LCLS beam time is "extremely valuable and limited" [@q4_lcls_cognitive]. The SSRL team did all development in simulation [@q4_xray_scientist].
- **Safety.**
  - Human relay [@q4_xray_scientist] and plan review [@q4_osprey].
  - Allowlisted tools [@q4_neudiff] and deterministic guards [@q4_apexa].
  - Checking against a digital twin before execution [@q4_envtrace].
- **User turnover.** Visiting users need guidance [@q4_esac], and agents must work zero-shot, without long training periods [@q4_base_scale].
- **Security and data policy.** Mandated under Genesis [@q4_genesis_eo]. VISION keeps its beamline models local [@q4_vision].
- **Verification.** Checking results, not generating ideas, is now the bottleneck [@q4_trust_roadmap] [@q4_aisle].
