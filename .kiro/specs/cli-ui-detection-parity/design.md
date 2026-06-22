# CLI vs UI Detection Parity Bugfix Design

## Overview

The System Scanner application exhibits a critical detection discrepancy between CLI and UI operational modes: CLI mode correctly detects 52+ items including AI agents (Kiro, Codex, Antigravity, Copilot), while UI mode detects only 47 items, missing 5+ AI agents. Investigation reveals both modes execute identical scanning logic through `ScanController.run_scan()`, suggesting the divergence occurs at the data source level—specifically in how AI agent processes and daemons are discovered by the `ProcessScanner` module. The fix will update AI daemon detection patterns and ensure consistent process discovery across all execution contexts.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when the scanner runs in UI mode (via gui.py or main.py web server), causing certain AI agent processes to be missed during detection
- **Property (P)**: The desired behavior - both CLI and UI modes SHALL detect identical AI frameworks, models, processes, and agents
- **Preservation**: Existing CLI detection behavior and all other scanner module functionality that must remain unchanged by the fix
- **ProcessScanner**: The module in `scanner/modules/process_scanner.py` that scans running system processes to detect active AI services, tools, runtimes, and AI daemon processes
- **AI Daemon**: Background service processes installed by cloud/desktop AI clients (ChatGPTHelper, Claude, Copilot, Kiro, Codex, Antigravity)
- **ScanController**: The orchestrator in `scanner/controller.py` that coordinates module registration and dispatches them through the Discovery Engine
- **CLI Mode**: Direct scan execution via `ScanController` instantiation in scripts or test files
- **UI Mode**: Scan execution triggered via HTTP server (`scanner/server.py`) through the `/run-scan` endpoint

## Bug Details

### Bug Condition

The bug manifests when the scanner executes in UI mode (via web server or GUI wrapper). The `ProcessScanner` module fails to detect 5+ AI agent processes (Kiro, Codex, Antigravity, Copilot) that are correctly identified in CLI mode. The root cause is insufficient or incomplete AI daemon detection patterns in `AI_DAEMON_NAMES` and `AI_DAEMON_PREFIXES` dictionaries, missing signatures for modern AI coding assistants and development tools.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ScanExecutionContext
  OUTPUT: boolean
  
  RETURN input.executionMode == "UI"
         AND agentProcessesPresent(["Kiro", "Codex", "Antigravity", "Copilot"])
         AND NOT agentProcessesDetected(input.scanResults, ["Kiro", "Codex", "Antigravity", "Copilot"])
END FUNCTION
```

### Examples

- **CLI Mode (Correct)**: Running `ScanController().run_scan()` directly detects 52 items including "Kiro Language Server", "GitHub Copilot Language Server", "Codex Backend", "Antigravity AI"
- **UI Mode (Defective)**: Accessing `http://localhost:8000/run-scan` detects only 47 items, missing Kiro, Codex, Antigravity, Copilot processes
- **Process Scanner Output**: CLI finds `kiro.exe`, `codex-server.exe`, `antigravity.exe`, `copilot-language-server.exe` while UI mode ProcessScanner returns empty findings for these same processes
- **Edge Case**: If no AI agents are running, both modes should detect 0 AI agents (consistent behavior)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- CLI mode detection of all 52+ items must continue to work exactly as before
- All other scanner modules (SystemScanner, FileScanner, PackageScanner, AgentScanner, RuntimeScanner, APIScanner, MCPScanner, LicenseScanner, ComplianceScanner) must continue to execute with identical parameters
- JSON and HTML report generation must remain unchanged in format and structure
- UI dashboard rendering with visual presentation and categorization must remain unchanged
- Exception handling for access-restricted paths and permission errors must remain unchanged
- Quick scan mode with depth-limited scanning must remain unchanged
- Server mode network scanning functionality must remain unchanged

**Scope:**
All scanner execution contexts that do NOT involve the ProcessScanner's AI daemon detection should be completely unaffected by this fix. This includes:
- File-based scanning (FileScanner, AgentScanner, APIScanner, LicenseScanner)
- Package manager scanning (PackageScanner)
- Port scanning (RuntimeScanner)
- System information gathering (SystemScanner)
- Configuration scanning (MCPScanner, ComplianceScanner)

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Missing AI Daemon Signatures**: The `AI_DAEMON_NAMES` dictionary in `process_scanner.py` is missing entries for Kiro, Codex, Antigravity, and other modern AI coding assistants
   - Current entries only include: ChatGPT, Claude, Microsoft Copilot (generic), Gemini, GitHub Copilot Language Server, Cursor, Windsurf
   - Missing: Kiro-specific executables, Codex backend processes, Antigravity daemon processes

2. **Incomplete Prefix Matching**: The `AI_DAEMON_PREFIXES` tuple may not include prefixes for all AI agent variants
   - Example: "kiro", "codex", "antigravity" prefixes are not in the current list

3. **Process Name Variations**: AI agents may use different executable names across platforms or versions
   - Example: `kiro.exe`, `kiro-server.exe`, `kiro-lsp.exe` all represent Kiro but may not match current patterns

4. **Execution Context Differences**: Although both modes use the same `ScanController`, there may be subtle differences in process visibility or permissions when running as a web server vs. direct script execution (unlikely but worth investigating)

## Correctness Properties

Property 1: Bug Condition - AI Agent Detection Parity

_For any_ scan execution where AI agent processes (Kiro, Codex, Antigravity, Copilot) are running on the host system, the fixed ProcessScanner SHALL detect these processes consistently in both CLI and UI modes, producing identical detection counts and agent findings.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Non-Agent Detection Behavior

_For any_ scan execution that involves non-ProcessScanner modules or non-AI-agent detections, the fixed scanner SHALL produce exactly the same results as the original scanner, preserving all existing detection capabilities for files, packages, ports, system info, and other finding categories.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix involves updating `scanner/modules/process_scanner.py`:

**File**: `scanner/modules/process_scanner.py`

**Function**: Detection pattern dictionaries at module level (lines 28-62)

**Specific Changes**:
1. **Expand AI_DAEMON_NAMES Dictionary**: Add explicit entries for missing AI agents
   - Add: `"kiro.exe": "Kiro AI Assistant"`
   - Add: `"kiro-server.exe": "Kiro Language Server"`
   - Add: `"codex.exe": "OpenAI Codex"`
   - Add: `"codex-server.exe": "Codex Backend Server"`
   - Add: `"antigravity.exe": "Antigravity AI"` 
   - Add: `"antigravity-daemon.exe": "Antigravity Service"`
   - Add: `"copilot.exe": "GitHub Copilot Desktop"` (in addition to existing copilot-language-server)
   - Add: Platform-specific variants (`.app`, `.bin`, no extension for Linux/Mac)

2. **Expand AI_DAEMON_PREFIXES Tuple**: Add prefix patterns for variant detection
   - Add: `"kiro"` - catches kiro.exe, kiro-server.exe, kiro-lsp.exe, kiro_v2.exe, etc.
   - Add: `"codex"` - catches codex.exe, codex-server.exe, codex-backend.exe, etc.
   - Add: `"antigravity"` - catches antigravity.exe, antigravity-daemon.exe, etc.
   - Add: `"copilot"` - expand beyond existing "copilotruntime" to catch all variants

3. **Cross-Platform Process Name Handling**: Update `_match_ai_daemon()` function
   - Ensure case-insensitive matching works correctly for all platforms
   - Handle both `exe_basename` and `name_lower` consistently
   - Strip file extensions (`.exe`, `.app`, `.bin`) before matching to catch cross-platform variants

4. **Add Research-Based Signatures**: If CLI mode detects agents that UI doesn't, extract exact process names from CLI scan logs
   - Run CLI scan, capture successful detections, extract process.name and process.exe values
   - Add these exact strings to `AI_DAEMON_NAMES` dictionary

5. **Verification Logging**: Add debug logging in `_match_ai_daemon()` to trace which patterns match
   - Log: "Checking process: {name} (exe: {exe})"
   - Log: "Matched AI daemon via exact match: {key} -> {label}"
   - Log: "Matched AI daemon via prefix: {prefix} -> {label}"
   - This enables post-fix verification that agents are being detected

## Testing Strategy

### Validation Approach

The testing strategy follows a three-phase approach: first, run exploratory tests to confirm the bug exists and identify missing signatures; second, implement the fix and verify detection parity; third, run preservation tests to ensure no regressions.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm which specific AI agent processes are missed in UI mode that CLI mode detects.

**Test Plan**: Run the scanner in both CLI and UI modes on a system with Kiro, Codex, Antigravity, and Copilot actively running. Compare the findings lists and identify exactly which process names, executable paths, and PIDs are detected in CLI but missing in UI.

**Test Cases**:
1. **CLI Detection Baseline**: Run `python test_integration.py` or direct `ScanController().run_scan()`, capture all ProcessScanner findings with category=LLM_RUNTIME or AI_AGENT (will succeed with 52+ items)
2. **UI Detection Test**: Start web server with `python main.py`, trigger scan via `http://localhost:8000/run-scan`, capture findings (will fail with only 47 items)
3. **Finding Comparison**: Programmatically diff the two findings lists by `finding_id`, `title`, `source`, and `details.exe` to identify exactly which 5+ items are missing
4. **Process Name Extraction**: From CLI findings, extract exact process names and exe paths for Kiro, Codex, Antigravity, Copilot processes

**Expected Counterexamples**:
- UI mode ProcessScanner returns 0-1 findings while CLI mode returns 5-6 findings
- Specific process names like "kiro.exe", "codex-server.exe", "antigravity.exe" appear in CLI findings but not UI findings
- Possible root cause confirmation: Missing entries in `AI_DAEMON_NAMES` or `AI_DAEMON_PREFIXES`

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (UI mode with AI agents running), the fixed ProcessScanner produces the expected behavior (detects all AI agents consistently).

**Pseudocode:**
```
FOR ALL executionContext WHERE isBugCondition(executionContext) DO
  cliFindings := runScanInCLIMode()
  uiFindings := runScanInUIMode()
  ASSERT length(cliFindings) == length(uiFindings)
  ASSERT cliFindings.agentNames == uiFindings.agentNames
END FOR
```

**Testing Approach**: Property-based testing is NOT well-suited for this fix because we're testing a specific, deterministic bug with known inputs (running processes). Instead, use integration tests with controlled process states.

**Test Plan**: 
1. Start Kiro, Codex, Antigravity, Copilot processes manually or via mock process utilities
2. Run CLI scan, capture findings count and agent list
3. Run UI scan, capture findings count and agent list
4. Assert: `len(cli_findings) == len(ui_findings)`
5. Assert: `set(cli_agent_names) == set(ui_agent_names)`
6. Assert: Each agent appears in both CLI and UI findings with same PID, exe path, and metadata

**Test Cases**:
1. **Full Agent Suite Test**: All 4 agents running (Kiro, Codex, Antigravity, Copilot) - both modes detect all 4
2. **Partial Agent Test**: Only Kiro and Copilot running - both modes detect exactly 2
3. **No Agents Test**: No AI agents running - both modes detect 0 AI agents
4. **Variant Name Test**: Run `kiro-server.exe` instead of `kiro.exe` - both modes detect it via prefix matching

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (non-agent detections, other modules), the fixed scanner produces the same result as the original scanner.

**Pseudocode:**
```
FOR ALL scanContext WHERE NOT isBugCondition(scanContext) DO
  ASSERT originalScanner(scanContext) = fixedScanner(scanContext)
END FOR
```

**Testing Approach**: Regression testing with snapshot comparison. Capture baseline scan results from unfixed scanner, apply fix, re-run scans, compare all non-ProcessScanner findings.

**Test Plan**: 
1. Run full scan on unfixed code, export findings to JSON, filter out ProcessScanner findings
2. Apply fix to `process_scanner.py`
3. Run full scan on fixed code, export findings to JSON, filter out ProcessScanner findings
4. Assert: All non-ProcessScanner findings are byte-identical in both snapshots
5. Assert: FileScanner, PackageScanner, AgentScanner, RuntimeScanner, APIScanner findings are unchanged

**Test Cases**:
1. **File Detection Preservation**: FileScanner finds same `.gguf`, `.safetensors`, model files in both versions
2. **Package Detection Preservation**: PackageScanner finds same pip packages (langchain, crewai, autogen) in both versions
3. **Port Detection Preservation**: RuntimeScanner finds same open ports with same process metadata in both versions
4. **Agent Code Preservation**: AgentScanner finds same Python scripts with AI frameworks in both versions
5. **API Key Preservation**: APIScanner finds same hardcoded credentials in both versions
6. **License Preservation**: LicenseScanner finds same LICENSE files in both versions
7. **Report Format Preservation**: JSON and HTML report structures are unchanged

### Unit Tests

- Test `_match_ai_daemon()` function with known process names ("kiro.exe" returns True, "notepad.exe" returns False)
- Test exact match in `AI_DAEMON_NAMES` dictionary
- Test prefix match in `AI_DAEMON_PREFIXES` tuple
- Test case-insensitive matching (kiro.exe, Kiro.exe, KIRO.EXE all match)
- Test cross-platform name variations (kiro.exe on Windows, kiro on Linux, Kiro.app on macOS)
- Test that non-AI processes don't false-positive (chrome.exe, vscode.exe should NOT match)

### Property-Based Tests

Property-based testing is NOT recommended for this fix because:
- The bug is deterministic and specific to known process names
- Process detection depends on OS state (running processes) which PBT cannot easily control
- The fix involves updating static dictionaries, not complex logic with many input combinations
- Integration tests with real/mock processes provide better coverage

### Integration Tests

- Test full CLI scan flow: `python test_integration.py` produces 52+ findings including Kiro, Codex, Antigravity, Copilot
- Test full UI scan flow: `http://localhost:8000/run-scan` produces 52+ findings including Kiro, Codex, Antigravity, Copilot
- Test scan result comparison: CLI and UI produce byte-identical JSON reports (excluding timestamps)
- Test visual dashboard rendering: UI displays all 52+ findings correctly in findings list
- Test module execution: ProcessScanner shows status="success" and findings_count matches expected value in both modes
