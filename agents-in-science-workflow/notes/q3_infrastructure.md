# Q3 Infrastructure: how science agents are built and connected (state as of 2026-09-25)

## 1. Models

- **Frontier API models** (GPT-5, Gemini 2.5, Claude) remain the default engine [@gpt5card][@gemini25][@claudecards], but frameworks are multi-provider: ChemGraph takes OpenAI, Anthropic, Google, Argonne's Argo gateway or local Ollama [@chemgraphrepo]; Biomni defaults to Claude but accepts local endpoints [@biomnirepo]; Co-Scientist is built on Gemini [@gottweis2026coscientist].
- **Open-weight reasoning models** make self-hosting practical. DeepSeek-R1 (Nature 2025) showed pure reinforcement learning (RL) can produce reasoning; weights are downloadable [@deepseekr1][@deepseekr1hf]. gpt-oss-120b/20b are Apache-2.0 and tuned for tool use [@gptoss]; see also Qwen3 [@qwen3] and Llama 3 [@llama3]. gpt-oss-120b drove an agent swarm on Aurora [@aurora_mof] and is always-on at OLCF [@olcfinf].
- **Science-tuned models:** ether0, a 24B chemistry reasoning model RL-trained on 640,730 problems, beat frontier models and experts on molecular design [@ether0]. Intern-S1 is an open scientific multimodal MoE (28B active/241B total) [@interns1]. Aviary showed trained open agents matching frontier agents at up to 100x lower inference cost [@aviary]. In DOE: AuroraGPT (training/deploying science foundation models on leadership computing) [@auroragpt] and ORNL's FORGE [@forge].
- **On-prem vs API:** FIRST was built for private, secure inference that generates "billions of tokens daily on-premises" without commercial cloud [@first]. NNSA runs OpenAI o-series models on Venado's classified network [@venado]. NERSC warns against putting credentials into external AI services and holds users responsible for agent actions [@nersccoding]. (Export control: no primary source found.)

## 2. Agent frameworks and science toolkits

- **General frameworks** all implement the ReAct reason–act–observe loop [@react]. Examples: LangGraph [@langgraph]; AutoGen [@autogen], now in maintenance mode with users pointed to Microsoft Agent Framework [@autogenrepo][@msaf], plus the AG2 community continuation [@ag2]; CrewAI [@crewai]; smolagents [@smolagents]; LlamaIndex [@llamaindex]; DSPy [@dspy].
- **Vendor SDKs:** OpenAI Agents SDK (handoffs, guardrails, tracing, MCP) [@oaiagents]; Claude Agent SDK (Claude Code loop with tools, hooks, subagents, permissions, MCP) [@claudesdk]; Google ADK (model-agnostic incl. vLLM; A2A and MCP) [@adk].
- **Science toolkits:** Aviary (training gym) [@aviary]; Academy (stateful, asynchronous agents across HPC, instruments, repositories) [@academy][@academyrepo]; ChemGraph (LangGraph+ASE+RDKit+MCP, executing via Parsl or Globus Compute on Aurora/Polaris) [@chemgraph][@chemgraphrepo]; Biomni [@biomni_biorxiv]; ToolUniverse (>1000 tools behind a native MCP server) [@tooluniverse][@tooluniverserepo].
- **Pattern:** a science toolkit is usually a thin layer over a general orchestrator plus a domain tool registry. Its value is in the tools, not the loop.

## 3. Tool protocols

- **MCP** was introduced on 25 Nov 2024 [@mcpintro]. On 9 Dec 2025 it moved to the Agentic AI Foundation (AAIF) under the Linux Foundation, with maintainers and the SEP process unchanged [@mcpaaif][@lfaaif].
  - The 2025-11-25 revision added experimental *tasks* for durable, polled requests [@mcpchg2511].
  - The 2026-07-28 revision made MCP stateless, moved tasks into an official extension, and deprecated Roots, Sampling and Logging [@mcpchg2607][@mcpspec].
- **A2A** was created by Google and became a Linux Foundation project in June 2025 [@a2alf]. It reached v1.0 and joined AAIF in Aug 2026. Its framing: MCP is the "vertical" agent-to-tool layer and A2A the "horizontal" agent-to-agent layer [@a2aaaif][@a2aspec].
- **Lower-level options:** JSON-Schema function calling [@oaifc], OpenAPI descriptions [@openapi], and lightweight "skills" (SKILL.md folders loaded on demand) [@agentskills] and AGENTS.md [@agentsmd]. Skills are already used at the ALS (Lightfall) [@lightfall] and SNS (EQSANS-CLI) [@eqsans].
- **Science MCP examples:** Globus Labs built thin MCP servers over Globus Transfer, Compute and Search, facility status APIs and an event fabric [@mcpscihpc][@sciencemcps]. PROV-AGENT uses MCP to record agent provenance [@provagent]. An APS beamline agent supports MCP in both directions [@eaa]. LAP proposes an agent-to-instrument layer with reservations and a safety-fence handshake [@lap].
- **Security:**
  - Indirect prompt injection is well documented [@greshake], and tool poisoning was first disclosed in 2025 [@invariant].
  - MCPTox tested 45 live servers: o1-mini's attack success rate was 72.8%, and no model refused more than 3% of attacks [@mcptox].
  - In HPC, a "hijacked authorized agent" acts with valid user credentials [@hpcagentsec].
  - Official guidance: [@mcpsecbp].

## 4. Connection to workflow and HPC systems

- **Execution fabric:**
  - Globus Compute (from funcX) [@funcx][@globuscompute] and Parsl [@parsl] run agents' tool calls on HPC; LangChain-Parsl ran agent-launched MD concurrently on Polaris [@lcparsl].
  - On Aurora, a planner agent split work among executor agents sharing one Parsl-backed MCP server [@aurora_mof].
- **Inference at DOE centers:**
  - ALCF FIRST: Globus Auth/Compute, OpenAI-compatible API, vLLM [@first][@alcfinf]. OLCF: vLLM, OpenAI-compatible, S3M tokens [@olcfinf].
  - NERSC: Slurm+vLLM serving [@nerscml] and coding-agent guidance for Perlmutter [@nersccoding].
- **IRI:** the blueprint calls for dynamic integration of experiment, simulation, AI and analysis [@iriblueprint]. The IRI Facility API standardizes status, account, compute/jobs, filesystem, storage and task endpoints, with instances at NERSC, ALCF and ESnet [@iriapi]; SLAC hosts a fork [@iriapislac]. The Genesis Mission platform explicitly includes AI agents and autonomous experimentation [@genesis].
- **Cross-facility:** ORNL steered an additive-manufacturing experiment across its Manufacturing Demonstration Facility and OLCF [@ornlagents]. An LLM agent with Pegasus skills generated a 2,679-job workflow [@pegasusagent].
- **Experiment control:** Bluesky, Ophyd, EPICS and Tiled are the plug points [@bluesky][@ophyd][@epics][@tiled]. Examples:
  - Bluesky-integrated (non-LLM) AI agents at NSLS-II [@nsls2ai]
  - VISION voice control [@vision]
  - EnvTrace, which checks agent-written control code against a beamline digital twin [@envtrace]
  - APEXA [@apexa] and NeuDiff (TOPAZ) [@neudiff]
- **Sandboxing and permissions:**
  - Biomni runs LLM-written code "with full system privileges" by default [@biomnirepo].
  - NERSC recommends workspace-write mode and sandboxes [@nersccoding].
  - APEXA's deterministic guard allowed 0/200 adversarial motor violations, against 15/200 for a safety prompt, and it caught a fabricated calibration report [@apexa].
  - NeuDiff uses allowlisted tools and fail-closed gates [@neudiff].

## Stack at a glance

| Layer | Common choices | What facilities should watch |
|---|---|---|
| Models | GPT-5/Gemini/Claude APIs; gpt-oss, Qwen3, DeepSeek-R1 self-hosted; ether0, Intern-S1 [@gptoss][@qwen3][@ether0] | Center-hosted OpenAI-compatible endpoints [@first][@olcfinf]; data-sensitivity rules [@venado] |
| Frameworks | LangGraph, vendor SDKs, Academy, ChemGraph, ToolUniverse [@langgraph][@claudesdk][@academy] | AutoGen churn [@autogenrepo]; code-execution privileges [@biomnirepo] |
| Protocols | MCP, A2A, function calling, skills [@mcpspec][@a2aspec][@agentskills] | Stateless MCP + tasks extension [@mcpchg2607]; tool poisoning [@mcptox] |
| Workflow/HPC | Globus Compute, Parsl, IRI API, Bluesky/EPICS [@funcx][@parsl][@iriapi][@bluesky] | MCP-wrapped facility APIs [@mcpscihpc]; provenance [@provagent] |

## Implications for facility deployments

- Wrap existing stacks (IRI API, Bluesky, Tiled) in MCP or skill/CLI layers rather than rebuilding them, as Globus Labs, ALS and SNS teams did [@mcpscihpc][@lightfall][@eqsans].
- Plan for model portability. Open-weight models served through OpenAI-compatible endpoints already run at ALCF and OLCF [@first][@olcfinf].
- Enforce safety in the tool layer, not the prompt: allowlists, execution-integrity guards and fail-closed gates [@apexa][@neudiff].
- Treat tool metadata and logs as untrusted input. Agents acting under user credentials are a new HPC threat class [@mcptox][@hpcagentsec].
- Record agent provenance from day one [@provagent].
