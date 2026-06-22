# Bugfix Requirements Document

## Introduction

The System Scanner application provides both CLI and UI modes for scanning and detecting AI frameworks, models, processes, and agents on host machines. Currently, there is a critical detection discrepancy between these two modes: CLI mode correctly detects 52+ items, while UI mode only detects 47 items, missing approximately 5+ AI agents including Kiro, Codex, Antigravity, and Copilot. This inconsistency violates the principle of feature parity between operational modes and compromises the reliability and trustworthiness of the scanner's results.

The bug appears to be rooted in data fetching, filtering, or scanning logic specific to the UI mode, causing certain items—particularly AI agents—to be omitted from detection. This fix will ensure both modes execute identical scanning logic and produce consistent, accurate results.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the scanner runs in CLI mode THEN the system detects 52 or more items including AI agents (Kiro, Codex, Antigravity, Copilot, etc.)

1.2 WHEN the scanner runs in UI mode THEN the system detects only 47 items, missing 5+ AI agents that are correctly detected in CLI mode

1.3 WHEN comparing detection results between CLI and UI modes THEN the system shows inconsistent item counts and missing agent detections in UI mode

1.4 WHEN AI agents like Kiro, Codex, Antigravity, and Copilot are present on the system THEN the UI mode fails to detect them while CLI mode succeeds

### Expected Behavior (Correct)

2.1 WHEN the scanner runs in CLI mode THEN the system SHALL detect all AI frameworks, models, processes, and agents present on the host machine

2.2 WHEN the scanner runs in UI mode THEN the system SHALL detect exactly the same AI frameworks, models, processes, and agents as CLI mode

2.3 WHEN comparing detection results between CLI and UI modes THEN the system SHALL display identical item counts and detection results

2.4 WHEN AI agents like Kiro, Codex, Antigravity, and Copilot are present on the system THEN the system SHALL detect them consistently in both CLI and UI modes using updated heuristics, regex patterns, or signatures

2.5 WHEN the scanner executes in any operational mode (CLI or UI) THEN the system SHALL use identical scanning logic, data fetching mechanisms, and filtering criteria

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the scanner successfully detects items in CLI mode before the fix THEN the system SHALL CONTINUE TO detect those same items in CLI mode after the fix

3.2 WHEN the scanner generates JSON and HTML reports THEN the system SHALL CONTINUE TO produce reports in the same formats with the same structure

3.3 WHEN the scanner executes individual scanner modules (SystemScanner, FileScanner, ProcessScanner, PackageScanner, AgentScanner, RuntimeScanner, APIScanner) THEN the system SHALL CONTINUE TO execute each module with the same parameters and configurations

3.4 WHEN the scanner displays results in the UI dashboard THEN the system SHALL CONTINUE TO render findings with the same visual presentation and categorization

3.5 WHEN the scanner encounters access-restricted paths or permission errors THEN the system SHALL CONTINUE TO handle exceptions gracefully without crashing

3.6 WHEN the scanner runs in quick scan mode THEN the system SHALL CONTINUE TO apply depth-limited scanning for fast demo runs

3.7 WHEN the scanner operates over local network in server mode THEN the system SHALL CONTINUE TO serve the consent portal and remote scanning functionality
