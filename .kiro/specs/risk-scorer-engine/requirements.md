# Requirements Document

## Introduction

The Risk Scorer Engine is a comprehensive risk assessment system for the AI Discovery System Scanner. The engine evaluates discovered AI agents, LLM runtimes, and related artifacts across five weighted dimensions to produce a composite risk score ranging from 0 to 100. This scoring system enables enterprise security teams to prioritize remediation efforts, enforce governance policies, and maintain regulatory compliance with Indian cybersecurity frameworks including DPDP Act, SEBI CSCRF, and CERT-In mandates.

The Risk Scorer Engine integrates with existing scanner modules (Registry Scanner, Port Scanner, Package Scanner, MCP Scanner, Process Scanner) and extends the Finding data model with multidimensional risk metadata. Risk scores are deterministic, reproducible, and displayed through interactive HTML/CSS visualizations in the dashboard reporting layer.

## Glossary

- **Risk_Scorer_Engine**: The core computational system responsible for calculating composite risk scores across five dimensions
- **Finding**: A single discovered AI artifact produced by scanner modules, extended with risk scoring metadata
- **Security_Risk**: Risk dimension measuring shell execution capabilities, filesystem modification permissions, MCP tool usage, and privilege escalation indicators (25% weight)
- **Data_Privacy_Risk**: Risk dimension measuring data transmission destinations, cloud inference usage, model training settings, and PII handling patterns (25% weight)
- **Compliance_Risk**: Risk dimension measuring DPDP Act compliance, local log availability, SOC visibility, and audit trail completeness (25% weight)
- **Supply_Chain_Risk**: Risk dimension measuring unverified package signatures, open-source dependency vulnerabilities, CVE baselines, and license compliance (15% weight)
- **Operational_Risk**: Risk dimension measuring infinite reasoning loop detection, dependency maintenance status, vendor lock-in risks, and runtime stability (10% weight)
- **Composite_Risk_Score**: The weighted sum of all five risk dimensions, normalized to a value between 0 and 100
- **Risk_Level**: A categorical severity classification (CRITICAL, HIGH, MEDIUM, LOW, INFO) derived from the Composite_Risk_Score
- **Scanner_Module**: An individual telemetry collection component (Registry Scanner, Port Scanner, Package Scanner, MCP Scanner, Process Scanner)
- **Dashboard**: The Jinja2-based HTML reporting interface that displays risk visualizations
- **ThreadPoolExecutor**: Python concurrent execution mechanism used for parallel scanner module processing
- **MCP**: Model Context Protocol, a configuration format for AI agent tool integrations
- **CVE**: Common Vulnerabilities and Exposures database identifier
- **DPDP_Act**: Digital Personal Data Protection Act (India)
- **SEBI_CSCRF**: Securities and Exchange Board of India Cyber Security and Cyber Resilience Framework
- **CERT_In**: Indian Computer Emergency Response Team
- **SOC**: Security Operations Center
- **PII**: Personally Identifiable Information
- **AGPL**: GNU Affero General Public License, a copyleft license requiring disclosure

## Requirements

### Requirement 1: Scanner Module Integration

**User Story:** As a security engineer, I want all telemetry scanner modules to execute in parallel without crashing the entire scan, so that I can reliably collect risk assessment data even when individual modules encounter errors.

#### Acceptance Criteria

1. WHEN the Scanner_Controller initializes, THE Risk_Scorer_Engine SHALL register all available Scanner_Modules through the module discovery mechanism
2. THE Scanner_Controller SHALL execute all registered Scanner_Modules using ThreadPoolExecutor with concurrent thread allocation
3. WHEN a Scanner_Module encounters a filesystem permission error, THE Scanner_Module SHALL log the error and continue execution without raising an exception
4. WHEN a Scanner_Module encounters a file access error, THE Scanner_Module SHALL log the error and continue execution without raising an exception
5. IF a Scanner_Module execution fails completely, THEN THE Scanner_Controller SHALL record the failure status in ModuleInfo and continue processing remaining modules
6. THE Scanner_Controller SHALL aggregate all Finding objects from successfully executed Scanner_Modules into the ScanResult findings list
7. WHEN all Scanner_Modules complete execution, THE Scanner_Controller SHALL compute summary statistics including module success count and failure count

### Requirement 2: Security Risk Dimension Calculation

**User Story:** As a security analyst, I want to measure security risks based on agent capabilities, so that I can identify agents with dangerous execution permissions.

#### Acceptance Criteria

1. WHEN a Finding contains shell execution capability indicators, THE Risk_Scorer_Engine SHALL assign a Security_Risk subscore between 0 and 25
2. THE Risk_Scorer_Engine SHALL detect shell execution indicators by searching Finding details for keywords including "shell", "exec", "command", "subprocess", "bash", and "powershell"
3. WHEN a Finding indicates filesystem modification permissions, THE Risk_Scorer_Engine SHALL increase the Security_Risk subscore proportionally
4. THE Risk_Scorer_Engine SHALL detect filesystem modification indicators by searching Finding details for keywords including "write", "delete", "modify", "chmod", and "filesystem"
5. WHEN a Finding contains MCP tool configurations, THE Risk_Scorer_Engine SHALL analyze tool permissions and increase the Security_Risk subscore for high-risk tools
6. THE Risk_Scorer_Engine SHALL identify high-risk MCP tools including those with "filesystem", "shell", "network", and "database" capabilities
7. WHEN a Finding indicates privilege escalation capabilities, THE Risk_Scorer_Engine SHALL assign the maximum Security_Risk subscore of 25
8. THE Risk_Scorer_Engine SHALL detect privilege escalation indicators by searching Finding details for keywords including "sudo", "admin", "elevated", "root", and "administrator"

### Requirement 3: Data Privacy Risk Dimension Calculation

**User Story:** As a compliance officer, I want to assess data privacy risks based on external data transmission, so that I can enforce data residency and privacy policies.

#### Acceptance Criteria

1. WHEN a Finding contains external API endpoints, THE Risk_Scorer_Engine SHALL assign a Data_Privacy_Risk subscore between 0 and 25
2. THE Risk_Scorer_Engine SHALL detect external API endpoints by parsing Finding details for URL patterns matching cloud inference providers
3. THE Risk_Scorer_Engine SHALL maintain a list of high-risk cloud inference providers including "api.openai.com", "api.anthropic.com", "generativelanguage.googleapis.com", and "api.cohere.ai"
4. WHEN a Finding indicates usage of high-risk cloud inference providers, THE Risk_Scorer_Engine SHALL assign a Data_Privacy_Risk subscore of at least 18
5. WHEN a Finding contains model training or data collection settings, THE Risk_Scorer_Engine SHALL increase the Data_Privacy_Risk subscore proportionally
6. THE Risk_Scorer_Engine SHALL detect data collection indicators by searching Finding details for keywords including "telemetry", "analytics", "training", "feedback", and "opt-out"
7. WHEN a Finding indicates PII handling without encryption, THE Risk_Scorer_Engine SHALL increase the Data_Privacy_Risk subscore by at least 5 points
8. THE Risk_Scorer_Engine SHALL detect PII handling indicators by searching Finding details for keywords including "personal data", "user information", "email", "phone", and "address"

### Requirement 4: Compliance Risk Dimension Calculation

**User Story:** As a regulatory compliance manager, I want to evaluate compliance with Indian cybersecurity regulations, so that I can avoid regulatory penalties and ensure audit readiness.

#### Acceptance Criteria

1. WHEN a Finding lacks local logging capabilities, THE Risk_Scorer_Engine SHALL assign a Compliance_Risk subscore between 15 and 25
2. THE Risk_Scorer_Engine SHALL detect local logging capabilities by searching Finding details for keywords including "log", "audit", "trace", and "record"
3. WHEN a Finding indicates cloud-only logging without local retention, THE Risk_Scorer_Engine SHALL assign a Compliance_Risk subscore of at least 20
4. WHEN a Finding demonstrates SOC visibility through standard logging formats, THE Risk_Scorer_Engine SHALL reduce the Compliance_Risk subscore by up to 10 points
5. THE Risk_Scorer_Engine SHALL recognize SOC-compatible logging formats including "syslog", "json", "csv", and "cef"
6. WHEN a Finding lacks audit trail completeness indicators, THE Risk_Scorer_Engine SHALL increase the Compliance_Risk subscore by at least 5 points
7. THE Risk_Scorer_Engine SHALL detect audit trail indicators by searching Finding details for keywords including "immutable", "tamper-proof", "signed", and "timestamped"
8. WHEN a Finding violates DPDP_Act data residency requirements, THE Risk_Scorer_Engine SHALL assign the maximum Compliance_Risk subscore of 25

### Requirement 5: Supply Chain Risk Dimension Calculation

**User Story:** As a software supply chain security analyst, I want to identify unverified packages and vulnerable dependencies, so that I can mitigate supply chain attacks.

#### Acceptance Criteria

1. WHEN a Finding represents an unverified package without cryptographic signature, THE Risk_Scorer_Engine SHALL assign a Supply_Chain_Risk subscore between 10 and 15
2. THE Risk_Scorer_Engine SHALL detect signature verification status by checking Finding details for "signature_verified" or "hash_verified" boolean fields
3. WHEN a Finding contains AGPL license indicators, THE Risk_Scorer_Engine SHALL assign a Supply_Chain_Risk subscore of at least 12
4. THE Risk_Scorer_Engine SHALL detect AGPL licenses by searching Finding details for keywords including "AGPL", "GNU Affero", and "agpl-3.0"
5. WHEN a Finding references known CVE identifiers, THE Risk_Scorer_Engine SHALL increase the Supply_Chain_Risk subscore proportionally based on CVE severity
6. THE Risk_Scorer_Engine SHALL parse Finding details for CVE identifier patterns matching the regular expression "CVE-\d{4}-\d{4,}"
7. WHEN a Finding indicates dependency maintenance status as "unmaintained" or "deprecated", THE Risk_Scorer_Engine SHALL increase the Supply_Chain_Risk subscore by at least 3 points
8. THE Risk_Scorer_Engine SHALL detect maintenance status indicators by searching Finding details for keywords including "deprecated", "unmaintained", "archived", and "end-of-life"

### Requirement 6: Operational Risk Dimension Calculation

**User Story:** As a system reliability engineer, I want to identify operational risks like infinite loops and vendor lock-in, so that I can maintain system stability and avoid platform dependencies.

#### Acceptance Criteria

1. WHEN a Finding indicates infinite reasoning loop potential, THE Risk_Scorer_Engine SHALL assign an Operational_Risk subscore between 7 and 10
2. THE Risk_Scorer_Engine SHALL detect infinite loop indicators by searching Finding details for keywords including "autonomous", "loop", "recursive", "continuous", and "self-directed"
3. WHEN a Finding demonstrates vendor lock-in characteristics, THE Risk_Scorer_Engine SHALL increase the Operational_Risk subscore by at least 3 points
4. THE Risk_Scorer_Engine SHALL detect vendor lock-in indicators by searching Finding details for keywords including "proprietary", "closed-source", "vendor-specific", and "non-portable"
5. WHEN a Finding indicates runtime stability issues, THE Risk_Scorer_Engine SHALL increase the Operational_Risk subscore proportionally
6. THE Risk_Scorer_Engine SHALL detect stability indicators by searching Finding details for keywords including "crash", "memory leak", "unstable", "beta", and "experimental"
7. WHEN a Finding lacks dependency isolation mechanisms, THE Risk_Scorer_Engine SHALL increase the Operational_Risk subscore by at least 2 points
8. THE Risk_Scorer_Engine SHALL detect isolation indicators by searching Finding details for keywords including "sandbox", "container", "isolated", and "virtualized"

### Requirement 7: Composite Risk Score Computation

**User Story:** As a security operations manager, I want a single composite risk score for each agent, so that I can quickly prioritize remediation efforts.

#### Acceptance Criteria

1. THE Risk_Scorer_Engine SHALL compute the Composite_Risk_Score as the sum of all five weighted dimension subscores
2. THE Risk_Scorer_Engine SHALL apply dimension weights: Security_Risk * 0.25, Data_Privacy_Risk * 0.25, Compliance_Risk * 0.25, Supply_Chain_Risk * 0.15, Operational_Risk * 0.10
3. THE Risk_Scorer_Engine SHALL normalize the Composite_Risk_Score to a value between 0 and 100
4. WHEN the Composite_Risk_Score is computed, THE Risk_Scorer_Engine SHALL round the score to one decimal place
5. THE Risk_Scorer_Engine SHALL store the Composite_Risk_Score in the Finding details dictionary under the key "composite_risk_score"
6. THE Risk_Scorer_Engine SHALL store all five dimension subscores in the Finding details dictionary under keys "security_risk", "data_privacy_risk", "compliance_risk", "supply_chain_risk", and "operational_risk"
7. FOR ALL Finding objects processed by the Risk_Scorer_Engine, the computation SHALL produce identical Composite_Risk_Score values when executed multiple times with the same input data (deterministic property)
8. WHEN the Risk_Scorer_Engine processes a Finding with no risk indicators, THE Risk_Scorer_Engine SHALL assign a Composite_Risk_Score of 0.0

### Requirement 8: Risk Level Classification

**User Story:** As a dashboard user, I want clear risk severity labels, so that I can immediately understand the threat level of each agent.

#### Acceptance Criteria

1. WHEN the Composite_Risk_Score is between 76 and 100, THE Risk_Scorer_Engine SHALL assign a Risk_Level of CRITICAL
2. WHEN the Composite_Risk_Score is between 51 and 75, THE Risk_Scorer_Engine SHALL assign a Risk_Level of HIGH
3. WHEN the Composite_Risk_Score is between 26 and 50, THE Risk_Scorer_Engine SHALL assign a Risk_Level of MEDIUM
4. WHEN the Composite_Risk_Score is between 1 and 25, THE Risk_Scorer_Engine SHALL assign a Risk_Level of LOW
5. WHEN the Composite_Risk_Score is 0, THE Risk_Scorer_Engine SHALL assign a Risk_Level of INFO
6. THE Risk_Scorer_Engine SHALL update the Finding risk_level attribute with the computed Risk_Level enum value
7. THE Risk_Scorer_Engine SHALL store the Risk_Level string representation in the Finding details dictionary under the key "risk_level_label"

### Requirement 9: Dashboard Risk Dimension Visualization

**User Story:** As a security analyst, I want to see detailed risk breakdowns for each agent on the dashboard, so that I can understand which dimensions contribute most to the overall risk.

#### Acceptance Criteria

1. WHEN the Dashboard renders a Finding card, THE Dashboard SHALL display a horizontal progress bar for each of the five risk dimensions
2. THE Dashboard SHALL render the Security_Risk progress bar with a fill percentage equal to (Security_Risk / 25) * 100
3. THE Dashboard SHALL render the Data_Privacy_Risk progress bar with a fill percentage equal to (Data_Privacy_Risk / 25) * 100
4. THE Dashboard SHALL render the Compliance_Risk progress bar with a fill percentage equal to (Compliance_Risk / 25) * 100
5. THE Dashboard SHALL render the Supply_Chain_Risk progress bar with a fill percentage equal to (Supply_Chain_Risk / 15) * 100
6. THE Dashboard SHALL render the Operational_Risk progress bar with a fill percentage equal to (Operational_Risk / 10) * 100
7. THE Dashboard SHALL display numeric risk dimension values with one decimal place precision
8. THE Dashboard SHALL apply color coding to progress bars: red for scores above 75% of maximum, orange for 50-75%, yellow for 25-50%, and green for below 25%

### Requirement 10: Dashboard Composite Risk Score Display

**User Story:** As an executive stakeholder, I want to see the overall risk score prominently displayed on each agent card, so that I can quickly assess the enterprise threat landscape.

#### Acceptance Criteria

1. WHEN the Dashboard renders a Finding card, THE Dashboard SHALL display the Composite_Risk_Score in a large, bold font at the top of the card
2. THE Dashboard SHALL format the Composite_Risk_Score as a whole number followed by "/100"
3. THE Dashboard SHALL apply color coding to the Composite_Risk_Score display: red for CRITICAL, orange for HIGH, yellow for MEDIUM, green for LOW, and blue for INFO
4. THE Dashboard SHALL display the Risk_Level label below the Composite_Risk_Score using uppercase text
5. WHEN the Composite_Risk_Score exceeds 75, THE Dashboard SHALL add a pulsing animation effect to the score display
6. THE Dashboard SHALL display a circular radial gauge visualization for the Composite_Risk_Score on the summary dashboard panel
7. THE Dashboard SHALL render the radial gauge with a fill percentage equal to Composite_Risk_Score percentage
8. THE Dashboard SHALL apply gradient coloring to the radial gauge transitioning from green (0) to red (100)

### Requirement 11: Critical Risk Alert Badges

**User Story:** As a security incident responder, I want immediate visual alerts for critical risk factors, so that I can quickly identify agents requiring urgent remediation.

#### Acceptance Criteria

1. WHEN a Finding contains AGPL license indicators, THE Dashboard SHALL display a red "AGPL DETECTED" badge on the Finding card
2. WHEN a Finding indicates MCP poisoning risk through unauthorized external MCP servers, THE Dashboard SHALL display a red "MCP RISK" badge on the Finding card
3. WHEN a Finding represents an unverified package without signature verification, THE Dashboard SHALL display an orange "UNVERIFIED" badge on the Finding card
4. WHEN a Finding contains high-risk network connections to external cloud inference APIs, THE Dashboard SHALL display an orange "EXTERNAL API" badge on the Finding card
5. WHEN a Finding indicates shell execution capabilities, THE Dashboard SHALL display a red "SHELL ACCESS" badge on the Finding card
6. THE Dashboard SHALL position alert badges in a horizontal row below the Finding title
7. THE Dashboard SHALL limit the maximum number of displayed alert badges to 5 per Finding card
8. WHEN more than 5 alert conditions are detected, THE Dashboard SHALL display the 5 highest priority badges and a "+N more" indicator

### Requirement 12: Risk Score Determinism and Reproducibility

**User Story:** As a compliance auditor, I want risk scores to be consistent and reproducible, so that I can validate scoring accuracy and maintain audit trails.

#### Acceptance Criteria

1. FOR ALL Finding objects with identical input data, THE Risk_Scorer_Engine SHALL produce identical Composite_Risk_Score values across multiple executions (round-trip property)
2. THE Risk_Scorer_Engine SHALL document the scoring algorithm version in the ScanResult metadata dictionary
3. WHEN the Risk_Scorer_Engine algorithm is updated, THE Risk_Scorer_Engine SHALL increment the algorithm version number
4. THE Risk_Scorer_Engine SHALL store the algorithm version number in each Finding details dictionary under the key "scoring_algorithm_version"
5. THE Risk_Scorer_Engine SHALL log all input parameters and computed subscores for each Finding to enable audit trail reconstruction
6. WHEN a Finding is reprocessed after score computation, THE Risk_Scorer_Engine SHALL preserve the original Composite_Risk_Score unless input data has changed
7. THE Risk_Scorer_Engine SHALL implement input data change detection by comparing Finding details dictionary hash values
8. FOR ALL Finding objects processed in a single scan, THE Risk_Scorer_Engine SHALL apply consistent dimension weights and scoring thresholds (invariant property)

### Requirement 13: Error Handling and Graceful Degradation

**User Story:** As a system administrator, I want the Risk Scorer Engine to handle missing or malformed data gracefully, so that risk scoring never crashes the entire scan.

#### Acceptance Criteria

1. WHEN a Finding details dictionary is missing expected risk indicator fields, THE Risk_Scorer_Engine SHALL assign a dimension subscore of 0 for that dimension
2. WHEN a Finding details dictionary contains malformed data types, THE Risk_Scorer_Engine SHALL log a warning and assign a dimension subscore of 0 for that dimension
3. IF the Risk_Scorer_Engine encounters an unexpected exception during score calculation, THEN THE Risk_Scorer_Engine SHALL log the exception with full stack trace and assign a Composite_Risk_Score of 0
4. THE Risk_Scorer_Engine SHALL set a "scoring_error" flag in the Finding details dictionary when error handling is triggered
5. WHEN the Risk_Scorer_Engine handles an error, THE Risk_Scorer_Engine SHALL continue processing remaining Finding objects without terminating execution
6. THE Risk_Scorer_Engine SHALL validate all numeric subscores are within expected ranges (0-25, 0-15, 0-10) before computing the Composite_Risk_Score
7. IF a dimension subscore exceeds its maximum value, THEN THE Risk_Scorer_Engine SHALL clamp the subscore to the maximum and log a warning
8. THE Risk_Scorer_Engine SHALL implement timeout protection limiting score calculation to 5 seconds per Finding object

### Requirement 14: Performance Optimization for Large Scans

**User Story:** As a DevOps engineer, I want the Risk Scorer Engine to process thousands of findings efficiently, so that scan execution time remains under 2 minutes for typical enterprise environments.

#### Acceptance Criteria

1. THE Risk_Scorer_Engine SHALL compute risk scores for at least 50 Finding objects per second on standard hardware
2. THE Risk_Scorer_Engine SHALL use in-memory data structures for all risk computation to avoid disk I/O bottlenecks
3. THE Risk_Scorer_Engine SHALL pre-compile all regular expression patterns used for keyword detection during initialization
4. THE Risk_Scorer_Engine SHALL cache keyword search results within a single scan execution to avoid redundant string matching
5. WHEN processing more than 100 Finding objects, THE Risk_Scorer_Engine SHALL use batch processing with chunk sizes of 50 findings
6. THE Risk_Scorer_Engine SHALL limit memory consumption to less than 500 MB for scans containing up to 1000 Finding objects
7. THE Risk_Scorer_Engine SHALL log performance metrics including total processing time and findings-per-second throughput
8. WHEN the Risk_Scorer_Engine completes processing, THE Risk_Scorer_Engine SHALL include performance statistics in the ScanResult summary dictionary
