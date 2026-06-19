# AI Bill of Materials (AI-BOM) vs. AI Discovery Scanner
## Comparative Analysis

**Document version:** 1.0  
**Date:** June 2026  
**Project:** Group-A-Y-S AI Discovery Scanner  
**Authors:** Group A-Y-S

---

## Table of Contents

1. [Overview of AI-BOM](#1-overview-of-ai-bom)
2. [Similarity Analysis — Table 1](#2-similarity-analysis--table-1)
3. [AI-BOM Components Missing from Our System — Table 2](#3-ai-bom-components-missing-from-our-system--table-2)
4. [Capabilities Present in Our System but Not Typically in AI-BOM — Table 3](#4-capabilities-present-in-our-system-but-not-typically-in-ai-bom--table-3)
5. [Future Enhancement Opportunities — Table 4](#5-future-enhancement-opportunities--table-4)
6. [Executive Summary](#6-executive-summary)

---

## 1. Overview of AI-BOM

### What Is an AI Bill of Materials?

An **AI Bill of Materials (AI-BOM)** is a structured, machine-readable inventory of every AI-related component present in a system, product, or organisation's environment. Modelled after the Software Bill of Materials (SBOM) concept that became a US federal requirement after Executive Order 14028 (2021), the AI-BOM extends the scope to address the unique complexity of AI deployments: pre-trained models, training datasets, agent orchestration frameworks, external API integrations, MCP servers, and the governance metadata that binds them together.

The primary purpose of an AI-BOM is to give security teams, compliance officers, and enterprise architects a **single authoritative record** of what AI components exist, where they are, what they can do, who owns them, and what risks they carry — enabling informed decisions about governance, procurement, incident response, and regulatory compliance (e.g., EU AI Act, NIST AI RMF, ISO/IEC 42001).

### Standard AI-BOM Components

A comprehensive AI-BOM typically contains the following component categories:

| Category | Description |
|---|---|
| **AI Applications** | End-user or enterprise AI products (e.g., Copilot, ChatGPT Desktop, Claude Desktop) installed in the environment |
| **AI Models** | Pre-trained or fine-tuned model weights and files (.gguf, .safetensors, .pt, .onnx, .h5), including model architecture, provider, and licence |
| **Datasets** | Training, fine-tuning, evaluation, or retrieval datasets — names, sources, licences, and data categories |
| **AI Agents** | Autonomous agent frameworks and instances (LangChain, CrewAI, AutoGen, custom agents), their tools, and permission scopes |
| **APIs & External Services** | Third-party AI API integrations (OpenAI, Anthropic, Google Gemini, Cohere, Hugging Face), including endpoints, credentials, and rate limits |
| **MCP Servers** | Model Context Protocol server registrations — command, transport type, permissions granted, and exposed tools |
| **Dependencies & Packages** | AI/ML libraries and SDKs (PyTorch, TensorFlow, Transformers, LangChain) with name, version, and known CVEs |
| **LLM Runtimes** | Local inference engines actively running on the machine (Ollama, LM Studio, vLLM, llama.cpp) |
| **Permissions & Access Controls** | What the AI system can read, write, execute, or connect to — file system, network, database, OS-level permissions |
| **Version Information** | Component versions, hash/digest of model files, provenance metadata |
| **Risk Metadata** | Assigned risk levels, threat classifications, compliance flags, licence obligations |
| **Governance & Ownership** | Owner, team, business unit, data classification, deployment environment, review status |
| **Audit Trail** | History of changes to AI components — when first discovered, modified, approved, or retired |

---

## 2. Similarity Analysis — Table 1

The following table maps each standard AI-BOM component category to the current capabilities of the AI Discovery Scanner's eight modules.

**Support Levels:**
- ✅ **Supported** — the scanner actively detects and reports this component with meaningful metadata
- 🔶 **Partial** — the scanner detects aspects of this component but coverage or detail is incomplete
- ❌ **Not Supported** — the scanner has no current capability for this component

| AI-BOM Component | AI-BOM Detail Required | Scanner Module(s) | Support Level | Notes |
|---|---|---|---|---|
| **AI Applications** | Name, version, install path, publisher, enabled/disabled state | MODULE 01 SystemScanner (Copilot registry), MODULE 03 ProcessScanner (daemon detection) | 🔶 Partial | Detects Copilot via registry and active AI desktop apps (Claude, ChatGPT, Cursor) via process scanning. Does not enumerate all installed AI applications from OS app registries (Add/Remove Programs, MSI database, AppX full list). |
| **AI Models (files)** | File name, path, size, format, hash, provider, licence | MODULE 02 FileScanner | ✅ Supported | Detects .gguf, .safetensors, .pt, .pth, .onnx, .ckpt, .h5 with path, size, and modification date. Hash/digest and licence metadata not yet captured. |
| **Datasets** | Dataset name, source URL, licence, data categories, size | — | ❌ Not Supported | No module scans for dataset files or dataset registry entries. |
| **AI Agents (source code)** | Framework, file, instantiation pattern, tool bindings, permissions | MODULE 05 AgentScanner | ✅ Supported | Detects LangChain, CrewAI, AutoGen imports and instantiations in .py files with file path and line number. Tool bindings and runtime permissions not captured. |
| **AI Agents (running)** | PID, memory, active tools, live connections | MODULE 03 ProcessScanner | 🔶 Partial | Detects Python processes running agent frameworks via command-line keyword matching. No structured enumeration of active tools or agent state. |
| **APIs & External Services** | Endpoint, credential type, provider, masked key, env source | MODULE 07 APIScanner | ✅ Supported | Scans files and environment variables for OpenAI, Anthropic, Google, Cohere, NVIDIA, Hugging Face, AWS, GitHub tokens with masking. Endpoint URLs not captured. |
| **MCP Servers** | Server name, command, args, transport, env vars, tools | MODULE 08 MCPScanner | ✅ Supported | Parses Claude Desktop, Cursor, VS Code, Windsurf, Kiro, and generic .mcp.json configs. Captures command, args, transport, masked env vars. Exposed tool enumeration not implemented. |
| **Dependencies — Python** | Package name, version, install path | MODULE 04 PackageScanner (pip, pip-global, pipx, uv, conda) | ✅ Supported | Active venv + global Python installs + pipx + uv + conda (base + named envs). No CVE lookup. |
| **Dependencies — Node.js** | Package name, version, install path | MODULE 04 PackageScanner (npm, NVM, Volta, pnpm, Yarn) | ✅ Supported | Global npm prefix with 9 candidate path strategies. Workspace/local node_modules not scanned. |
| **Dependencies — macOS** | Formula name, version, prefix path | MODULE 04 PackageScanner (Homebrew) | ✅ Supported | Homebrew formula list with version and install prefix. Casks not currently scanned. |
| **LLM Runtimes** | Runtime name, port, directory, active status | MODULE 06 RuntimeScanner | ✅ Supported | Port scanning (11434, 1234, 8000, 5000, 8080) + directory detection (~/.ollama, lmstudio). Cross-confirms active+installed state. |
| **Permissions & Access Controls** | Filesystem paths, network permissions, OS capabilities | MODULE 08 MCPScanner (MCP server permissions) | 🔶 Partial | MCP server configs reveal file paths and API access scopes granted to AI tools. OS-level IAM, ACL, or sandbox permissions not inspected. |
| **Version Information** | Component versions, model file hash/digest | MODULE 04 PackageScanner (versions), MODULE 02 FileScanner (file metadata) | 🔶 Partial | Package versions captured. Model file SHA-256 hash not computed. Provenance URLs not tracked. |
| **Risk Metadata** | Risk level, confidence score, category | All modules → ClassificationEngine | ✅ Supported | Every finding carries RiskLevel (CRITICAL/HIGH/MEDIUM/LOW/INFO), FindingCategory, and confidence score (0.0–1.0). |
| **Governance & Ownership** | Owner, team, environment, review status, approval | — | ❌ Not Supported | No concept of component ownership, business unit assignment, or approval workflow exists in the current system. |
| **Audit Trail** | Discovery history, change detection, first-seen / last-seen | — | ❌ Not Supported | Each scan is a point-in-time snapshot. No persistent store or delta comparison between scans. |
| **Model Provenance** | Training data source, model card URL, HuggingFace model ID | — | ❌ Not Supported | Model files are detected by extension only; no lookup of model cards or registry metadata. |
| **Licence Obligations** | AI model licence (MIT, Apache, GPL, commercial), usage restrictions | — | ❌ Not Supported | Licence information is not captured for any component. |
| **Known Vulnerabilities (CVE)** | CVE IDs for packages, models, or runtimes | — | ❌ Not Supported | No integration with NVD, OSV, or any vulnerability database. |

---

## 3. AI-BOM Components Missing from Our System — Table 2

The following components are defined in standard AI-BOM frameworks but are currently absent from the AI Discovery Scanner.

| Missing Component | AI-BOM Relevance | Why It Matters | Effort to Add |
|---|---|---|---|
| **Training & Fine-tuning Datasets** | Core AI-BOM asset — datasets are the "ingredients" of AI models | Data licence violations, GDPR/privacy exposure from training data, bias and fairness audits all require dataset provenance | High — requires dataset registry integration or file-pattern heuristics |
| **Model Provenance Metadata** | Links model files to their origin (HuggingFace Hub, Ollama registry, custom training run) | Attribution, licence compliance, supply chain integrity verification | Medium — HuggingFace Hub API can be queried for `.gguf` / `.safetensors` files found on disk |
| **Model File Hash / Digest** | SHA-256 or BLAKE3 fingerprint of model weight files | Integrity verification, tamper detection, reproducibility, SBOM toolchain compatibility | Low — add one `hashlib` call in FileScanner |
| **AI Component Licence Information** | Licence type per model, package, and dataset | Legal and compliance obligations differ across MIT, Apache 2.0, GPL, CC-BY-NC, and proprietary licences | Medium — PyPI metadata includes licence; model licences require Hub lookup |
| **Vulnerability / CVE Data** | Known CVEs in AI packages and frameworks | PyTorch, TensorFlow, Transformers, and other packages have published CVEs; unpatched vulnerabilities = direct security risk | Medium — integrate with OSV API or `pip-audit` output |
| **AI Component Ownership & Governance** | Owner (person/team), environment tag (dev/prod), review status, approval date | Regulatory compliance (EU AI Act Art. 9, ISO 42001) requires documented accountability for each AI component | Medium — needs a structured metadata layer / config file approach |
| **Audit Trail & Change History** | First-seen timestamp, last-seen timestamp, delta between scans | Detects new AI components being introduced, components being removed or version-bumped without approval | High — requires persistent database and scan-over-scan comparison engine |
| **Exposed MCP Tool Enumeration** | The specific tools each MCP server exposes (e.g., `read_file`, `execute_query`) | Tools define the actual capability surface; a filesystem MCP server with `write` tool is far more dangerous than one with `read_only` | Medium — requires calling the MCP `tools/list` endpoint at runtime |
| **Network Egress & Data Flow Mapping** | Which AI components are making outbound connections and to which endpoints | Data exfiltration risk, GDPR data transfer compliance, shadow AI calling unapproved external services | High — requires network traffic analysis beyond process-level connection snapshots |
| **AI System Deployment Context** | Is this component in dev, staging, or production? Is it containerised? | Risk context changes dramatically between a developer's laptop and a production API gateway | Medium — requires tagging / environment configuration |
| **AI Model Performance & Drift Metadata** | Model accuracy benchmarks, drift indicators, evaluation dataset results | Operational AI risk — degraded models making business decisions | Very High — outside the scope of static scanning; requires runtime monitoring integration |
| **Data Classification of Inputs/Outputs** | What data categories the AI component processes (PII, financial, medical) | GDPR, HIPAA, PCI-DSS compliance depend on knowing what data flows through each AI component | High — requires semantic data classification pipeline |
| **Third-party AI Service SLAs & Terms** | Contract terms, data retention policies, opt-out of training flags for API providers | Contractual and regulatory risk from data being sent to third-party models without appropriate agreements | Low (metadata) — can be maintained as a lookup table keyed on provider name |
| **Container & Cloud AI Services** | AI workloads running in Docker, Kubernetes, cloud ML platforms (SageMaker, Vertex AI, Azure ML) | Enterprise AI increasingly runs in containers; a host-only scanner misses the majority of the attack surface | Very High — requires container registry API integration, Kubernetes API scanning |

---

## 4. Capabilities Present in Our System but Not Typically Included in AI-BOM — Table 3

The AI Discovery Scanner includes several active and OS-specific detection capabilities that go beyond what a traditional AI-BOM framework specifies. AI-BOM is primarily an **inventory format** — it describes *what* components exist. Our scanner goes further by actively probing *what is happening right now*.

| Scanner Capability | Module | Description | Why It Exceeds AI-BOM Scope |
|---|---|---|---|
| **Active Process Memory Scanning** | MODULE 03 ProcessScanner | For flagged AI daemon processes (Claude.exe, ChatGPTHelper.exe, etc.), the scanner performs live memory telemetry: enumerates memory-mapped files (surfacing loaded model weights), open file handles (surfacing config and credential files being read), and active network connections (surfacing API calls in progress) | AI-BOM is a static inventory record. Memory-level telemetry is runtime forensics — closer to EDR (Endpoint Detection & Response) than an inventory format |
| **Windows Registry Scanning** | MODULE 01 SystemScanner | Queries HKLM and HKCU for Microsoft Copilot AppX package registrations and the `TurnOffWindowsCopilot` Group Policy DWORD, reporting whether Copilot is installed, staged, or explicitly disabled by MDM/policy | Registry-level OS configuration is an operational security control — AI-BOM does not specify registry checks |
| **Active Port Scanning** | MODULE 06 RuntimeScanner | Probes localhost ports 11434, 1234, 8000, 5000, and 8080 with TCP connect checks to detect whether LLM API servers (Ollama, LM Studio, vLLM) are actively listening and accepting connections | AI-BOM captures installed components, not their live network posture; active port probing is a network security assessment technique |
| **Cross-Confirmation Logic** | MODULE 06 RuntimeScanner | Combines port scan results with directory detection to produce differentiated findings: "Active & Installed" vs. "Active Only" vs. "Installed but Inactive" — three distinct risk levels | AI-BOM records a component's presence; the active/inactive operational state distinction is a runtime observability concern |
| **AI Daemon Background Service Detection** | MODULE 03 ProcessScanner | Maintains a curated dictionary of known AI daemon executables (ChatGPTHelper.exe, Claude.exe, CopilotRuntime.exe, Cursor.exe, Windsurf.exe, etc.) and detects them by exact name and prefix-matching for versioned variants | AI-BOM inventories components the organisation knows about and has declared; daemon detection is adversarial/shadow-IT detection |
| **Python Process AI Workload Detection** | MODULE 03 ProcessScanner | Inspects command-line arguments of running Python processes to identify undeclared AI workloads (torch, transformers, langchain, gradio scripts) even when they are not registered in any package manager | This detects undeclared, transient AI workloads — shadow AI in execution. AI-BOM only captures declared components |
| **Global Package Manager Breadth** | MODULE 04 PackageScanner | Scans 7 package ecosystems simultaneously: pip (active), pip (global installs), npm global (9 path strategies including NVM/Volta/pnpm/Yarn), pipx, uv, Homebrew, and conda (base + all named envs) | AI-BOM specifies *what* dependency data to record; the multi-ecosystem discovery sweep is a scanner engineering capability, not part of the BOM specification |
| **MCP Config Risk Classification** | MODULE 08 MCPScanner | Automatically classifies each MCP server entry by risk level (CRITICAL for filesystem/DB access, HIGH for shell commands or embedded secrets, MEDIUM for API-access services) and masks secrets in env blocks | AI-BOM records MCP server registrations; automated risk classification and credential masking are security analysis capabilities layered on top |
| **Multi-format MCP Config Parsing** | MODULE 08 MCPScanner | Parses 5 different IDE/tool config schemas (Claude Desktop, Cursor, VS Code, Windsurf, Kiro) plus generic file discovery, normalising all into a unified mcpServers representation — including tolerance for JSON-with-comments and trailing commas | A BOM specification defines the schema for recording MCP components; normalising across multiple proprietary formats is a discovery engineering problem |
| **Source Code Agent Signature Detection** | MODULE 05 AgentScanner | Walks Python source files to find AI agent framework imports and object instantiations via regex — detecting LangChain, CrewAI, AutoGen, Agent(), Crew(), AssistantAgent() patterns at the code level | AI-BOM typically records deployed components; source-code-level agent detection finds components that have not yet been deployed but exist in the development environment |
| **GPU Detection** | MODULE 01 SystemScanner | Detects NVIDIA GPUs via nvidia-smi and any GPU via WMIC, reporting VRAM, driver version, and detection method | GPU presence is hardware context, not an AI-BOM component per se, but it is critical for understanding inference capability and potential for running models that were not declared |
| **Parallelised Multi-Module Execution** | DiscoveryEngine | All 8 modules execute concurrently via ThreadPoolExecutor with a real-time spinner/progress display and per-module timing metadata | Scan orchestration and performance engineering are implementation concerns; AI-BOM specifications describe data format, not how the inventory is collected |
| **Structured Risk Scoring** | ClassificationEngine + ScanResult | Every finding receives a RiskLevel (CRITICAL/HIGH/MEDIUM/LOW/INFO) with a numeric score (0–100), and the overall scan produces an aggregate risk score across all findings | AI-BOM may include risk metadata fields, but automated rule-based risk scoring with aggregate scoring across all discovered components is a security analytics capability |
| **OS Directory Exclusion Optimization** | MODULE 02 FileScanner, MODULE 04 PackageScanner | Maintains a 60+ entry exclusion list for OS system directories (Windows, System32, WinSxS, Program Files, Linux /proc /sys /usr, macOS Library) to prevent scanning irrelevant paths and maintain responsiveness | Performance optimization during discovery is an engineering concern not addressed by BOM format specifications |

---

## 5. Future Enhancement Opportunities — Table 4

The following capabilities are not present in standard AI-BOM frameworks or in the current scanner, but would provide significant value for enterprise AI governance, security, and compliance.

| Enhancement | Value Domain | Description | Priority | Estimated Effort |
|---|---|---|---|---|
| **Persistent Scan Database & Delta Detection** | Governance, Audit | Store scan results in a local SQLite or JSON database indexed by scan ID and timestamp. On each subsequent scan, compute a delta (new components, removed components, version changes) and alert on unexpected AI additions or removals | Governance, Audit Trail | Medium — add a persistence layer and diff engine to ScanResult |
| **Model File SHA-256 Hashing & Integrity Verification** | Security, Supply Chain | Compute cryptographic hashes of discovered model weight files (.gguf, .safetensors, .pt) and optionally compare them against known-good hashes from HuggingFace Hub or an internal registry | Security, Supply Chain | Low — one hashlib call per file; Hub API lookup is optional |
| **CVE / Vulnerability Lookup Integration** | Security | After PackageScanner collects package names and versions, query the OSV.dev API or run `pip-audit` to surface known CVEs in discovered AI packages (e.g., CVE-2024-XXXXX in older Transformers releases) | Security | Medium — async HTTP requests to OSV API, cache results |
| **HuggingFace Hub Model Card Lookup** | Governance, Compliance | For model files identified by FileScanner, attempt to resolve the model name from HuggingFace Hub to retrieve model card metadata: licence, training data disclosure, intended use, and known limitations | Compliance, Licence | Medium — requires fuzzy filename-to-model-id matching |
| **MCP Tool Surface Enumeration** | Security, Governance | At scan time, connect to each discovered MCP server (if running) and call `tools/list` to enumerate the actual tools it exposes. Flag high-privilege tools (write_file, execute_command, run_query) | Security | Medium — requires MCP client implementation (stdio/SSE) |
| **AI Component Ownership Tagging** | Governance | Allow teams to maintain a `.aibom-config.yaml` file in their repository declaring ownership (team, owner, environment, approved-by) for AI components. The scanner merges declared ownership with discovered components | Governance, Compliance | Low — YAML config file reader + merge step in controller |
| **Network Egress Monitoring** | Security | Extend ProcessScanner's existing connection telemetry into a continuous background mode that captures outbound connections from AI processes over time, not just a point-in-time snapshot, building a map of AI data flows | Security, Privacy | High — requires background agent or eBPF/ETW integration |
| **Container & Docker AI Workload Scanning** | Enterprise Security | Scan running Docker containers and images for AI-related layers, environment variables (API keys), and entrypoints. Detect AI models mounted as volumes or embedded in images | Security | High — requires Docker SDK integration |
| **Kubernetes / Cloud ML Platform Discovery** | Enterprise Governance | Query Kubernetes cluster resources (Pods, ConfigMaps, Secrets) for AI workloads, or integrate with cloud ML platform APIs (SageMaker, Vertex AI, Azure ML) to extend the BOM beyond the local machine | Enterprise Governance | Very High — separate scanner modules per cloud provider |
| **SBOM Export Format (SPDX / CycloneDX AI BOM Profile)** | Compliance, Toolchain | Export scan results in SPDX 2.3 or CycloneDX 1.6 AI BOM profile format, enabling interoperability with existing SBOM toolchains, licence scanners, and vulnerability databases | Compliance, Interoperability | Medium — JSON serialisation mapping; schema is well-defined |
| **EU AI Act Risk Category Tagging** | Regulatory Compliance | Map discovered AI applications and models to EU AI Act risk categories (Prohibited, High-Risk, Limited-Risk, Minimal-Risk) based on use-case heuristics and component metadata | Regulatory Compliance | Medium — rule-based classification layer; requires use-case tagging input |
| **NIST AI RMF / ISO 42001 Control Mapping** | Governance | For each discovered AI component, map findings to relevant NIST AI RMF function/category codes (GOVERN, MAP, MEASURE, MANAGE) or ISO/IEC 42001 control objectives | Governance | Low — lookup table mapping component categories to control IDs |
| **Scheduled & Continuous Scanning** | Operations | Implement a background service / scheduled task mode that runs scans on a configurable interval (hourly, daily), stores results in the persistent database, and sends alerts (email, webhook, Slack) when new high-risk AI components are discovered | Operations, Detection | High — requires daemon mode, scheduler, and alerting integration |
| **AI Policy Enforcement Engine** | Governance, Compliance | Allow organisations to define an AI policy file (e.g., "no unapproved LLM runtimes," "all API keys must be in a secrets manager," "no filesystem MCP servers in production") and fail the scan with policy violation findings | Governance | Medium — policy DSL + findings evaluation pass |
| **Remediation Guidance Engine** | Security Operations | For each finding, generate actionable remediation steps tailored to the specific component (e.g., "Rotate this Anthropic API key at console.anthropic.com," "Disable Windows Copilot via GPO key WindowsCopilot/TurnOffWindowsCopilot=1") | Security Operations | Low to Medium — static guidance lookup table per finding category |
| **Multi-Machine / Enterprise Fleet Scanning** | Enterprise | Extend from single-host to fleet mode — deploy the scanner as an agent, collect scan results centrally, and produce an organisation-wide AI component inventory across all machines | Enterprise | Very High — requires central collector, agent deployment, and fleet management |
| **IDE & Browser Extension AI Detection** | Shadow AI Detection | Detect AI-enabled browser extensions (Chrome/Edge extensions with AI capabilities) and IDE plugins (GitHub Copilot, Codeium, Tabnine, Continue) installed in user profiles | Shadow AI | Medium — browser extension manifests are readable files; IDE extension dirs are discoverable |
| **Fine-tuning Job & Training Run Detection** | MLOps | Detect active or recent ML training/fine-tuning jobs from wandb run directories, MLflow experiment stores, HuggingFace Trainer checkpoints, and Jupyter notebook kernels running training scripts | MLOps, Governance | High — requires integration with ML experiment tracking tools |

---

## 6. Executive Summary

### Current Overlap Between AI-BOM and Our System

The AI Discovery Scanner currently provides strong coverage of the **detection and classification** layer of an AI-BOM. Out of the 14 standard AI-BOM component categories analysed, the scanner fully supports 8 (57%) and partially supports 4 (29%), leaving only 2 (14%) completely unaddressed (datasets and governance/ownership records). In practical terms, this means the scanner can produce a **technically accurate point-in-time inventory** of AI models, packages, runtimes, agents, API keys, and MCP server configurations for a developer workstation or server. This covers the most operationally relevant AI-BOM data for security and IT teams.

The 8-module architecture maps cleanly to the core AI-BOM component taxonomy:

| Scanner Module | AI-BOM Categories Covered |
|---|---|
| MODULE 01 SystemScanner | AI Applications (Copilot), System Context |
| MODULE 02 FileScanner | AI Models |
| MODULE 03 ProcessScanner | AI Applications (running daemons), LLM Runtimes (process-level) |
| MODULE 04 PackageScanner | Dependencies (Python, Node.js, macOS) |
| MODULE 05 AgentScanner | AI Agents (source code) |
| MODULE 06 RuntimeScanner | LLM Runtimes (port + directory) |
| MODULE 07 APIScanner | APIs & External Services, Configuration |
| MODULE 08 MCPScanner | MCP Servers, Permissions (partial) |

### Key Gaps to Address for a Full AI-BOM Solution

Three categories of gaps separate the current scanner from a comprehensive AI-BOM platform:

**1. Metadata Depth Gaps (achievable with low-to-medium effort)**
The scanner finds components but does not enrich them with BOM-quality metadata: model file hashes are not computed, package licences are not retrieved, CVEs are not looked up, and model provenance is not resolved from the HuggingFace Hub. These are primarily API integration tasks that can be added as post-processing enrichment steps without changing the core architecture.

**2. Structural Gaps (require new design)**
The most significant structural gap is the absence of persistence and audit trail. A BOM is not useful as a one-shot scan — it must track what changed between scans, flag new AI components, and maintain a history of approvals and retirements. A lightweight SQLite persistence layer with delta comparison would close this gap. The second structural gap is the complete absence of dataset discovery, which requires a fundamentally different approach (semantic file classification rather than extension matching).

**3. Scope Gaps (require significant new capability)**
The scanner is currently a single-host tool. Enterprise AI governance requires fleet-wide inventory, container/Kubernetes scanning, and cloud ML platform integration. These are multi-sprint investments that would transform the scanner into an enterprise platform.

### Strategic Recommendations and Roadmap Priorities

**Immediate (Sprint 1–2):**
- Add SHA-256 hashing to FileScanner — low effort, high BOM value, enables integrity verification
- Add OSV/pip-audit CVE lookup to PackageScanner — directly addresses security compliance requirements
- Add model provenance lookup from HuggingFace Hub for discovered `.gguf` and `.safetensors` files
- Add SPDX/CycloneDX export to the report generator — enables toolchain interoperability

**Short-term (Sprint 3–5):**
- Implement persistent scan database (SQLite) with delta detection and first-seen/last-seen timestamps
- Add AI component ownership tagging via a `.aibom-config.yaml` convention
- Implement AI policy enforcement engine with configurable rules
- Add remediation guidance to all finding categories

**Medium-term (Sprint 6–10):**
- Build dataset discovery module using file-pattern and metadata heuristics
- Implement MCP tool surface enumeration (connect to running servers and call `tools/list`)
- Add EU AI Act risk category tagging and NIST AI RMF control mapping
- Implement scheduled/continuous scanning mode with webhook alerting

**Long-term (Platform Evolution):**
- Multi-machine fleet scanning with a central collector service
- Container and Kubernetes AI workload scanning modules
- Cloud ML platform integrations (SageMaker, Vertex AI, Azure ML)
- Full AI-BOM platform with a governance workflow (review, approve, retire) and regulatory compliance reporting dashboard

The AI Discovery Scanner is well-positioned to evolve from a powerful point-in-time security tool into a comprehensive AI-BOM platform. The core architecture — modular, parallel, classification-aware — is the right foundation. The path forward is enrichment, persistence, and scale.

---

*This document is maintained in the `documentation/` folder of the Group-A-Y-S repository. Update after each major sprint or when new scanner modules are added.*
