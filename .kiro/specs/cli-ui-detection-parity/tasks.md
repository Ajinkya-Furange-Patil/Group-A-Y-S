# Implementation Plan

## Overview

This implementation plan follows the exploratory bugfix workflow to fix the CLI vs UI detection parity bug where UI mode misses 5+ AI agents (Kiro, Codex, Antigravity, Copilot) that CLI mode correctly detects. The approach is: **Explore** the bug BEFORE fixing it, **Preserve** existing behavior, **Implement** the fix with understanding, and **Validate** completeness.

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "name": "Exploration Phase",
      "tasks": ["1"]
    },
    {
      "name": "Preservation Baseline Phase",
      "tasks": ["2"]
    },
    {
      "name": "Implementation Phase",
      "tasks": ["3.1", "3.2", "3.3"]
    },
    {
      "name": "Verification Phase",
      "tasks": ["3.4", "3.5"]
    },
    {
      "name": "Final Checkpoint",
      "tasks": ["4"]
    }
  ]
}
```

**Visual Dependency Flow:**
```
1. Write bug condition exploration test
   ↓
2. Write preservation property tests (BEFORE implementing fix)
   ↓
3. Fix for CLI vs UI AI Agent Detection Parity
   ├── 3.1 Expand AI_DAEMON_NAMES dictionary
   ├── 3.2 Expand AI_DAEMON_PREFIXES tuple
   ├── 3.3 Add debug logging to _match_ai_daemon()
   ├── 3.4 Verify bug condition exploration test now passes
   └── 3.5 Verify preservation tests still pass
   ↓
4. Checkpoint - Ensure all tests pass
```

**Critical Dependencies:**
- Task 1 MUST complete before Task 3 (exploration identifies missing signatures)
- Task 2 MUST complete before Task 3 (preservation baseline must be established)
- Task 3.1, 3.2, 3.3 can be done in parallel
- Task 3.4 depends on completion of 3.1, 3.2, 3.3
- Task 3.5 depends on completion of 3.1, 3.2, 3.3
- Task 4 depends on all previous tasks

---

## Tasks

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - AI Agent Detection Parity Across CLI and UI Modes
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists by comparing CLI vs UI detection results
  - **Scoped PBT Approach**: For this deterministic bug, scope the property to concrete failing cases - specifically test detection of Kiro, Codex, Antigravity, and Copilot processes
  - Create test file `tests/test_cli_ui_parity_bug.py` with two test functions:
    - `test_cli_detection_baseline()` - Run scan in CLI mode, assert detects 52+ items, capture ProcessScanner findings
    - `test_ui_detection_parity()` - Start web server, trigger scan via HTTP, capture findings, compare to CLI baseline
  - Test implementation details from Bug Condition in design:
    - Assert: `input.executionMode == "UI"`
    - Assert: `agentProcessesPresent(["Kiro", "Codex", "Antigravity", "Copilot"])` (check if processes are running on system)
    - Assert: `NOT agentProcessesDetected(input.scanResults, ["Kiro", "Codex", "Antigravity", "Copilot"])` (UI mode should fail to detect them)
  - The test assertions should match the Expected Behavior Properties from design:
    - Property 1: CLI and UI modes SHALL detect identical AI agent counts
    - Property 1: CLI and UI modes SHALL detect identical agent names (Kiro, Codex, Antigravity, Copilot)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS with output like "UI mode detected 47 items, CLI mode detected 52 items - missing agents: Kiro, Codex, Antigravity, Copilot, X"
  - Document counterexamples found to understand root cause:
    - Extract exact process names from CLI findings (e.g., "kiro.exe", "codex-server.exe", "antigravity.exe")
    - Extract exe paths and PIDs to confirm processes are running
    - Log which AI_DAEMON_NAMES or AI_DAEMON_PREFIXES entries are missing
  - Mark task complete when test is written, run, failure is documented, and missing signatures are identified
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Agent Detection Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (all scanner modules except ProcessScanner AI daemon detection)
  - Create test file `tests/test_preservation_regression.py` with test functions:
    - `test_file_scanner_preservation()` - Verify FileScanner finds same `.gguf`, `.safetensors`, model files
    - `test_package_scanner_preservation()` - Verify PackageScanner finds same pip packages (langchain, crewai, autogen)
    - `test_runtime_scanner_preservation()` - Verify RuntimeScanner finds same open ports with same process metadata
    - `test_agent_scanner_preservation()` - Verify AgentScanner finds same Python scripts with AI frameworks
    - `test_api_scanner_preservation()` - Verify APIScanner finds same hardcoded credentials
    - `test_license_scanner_preservation()` - Verify LicenseScanner finds same LICENSE files
    - `test_report_format_preservation()` - Verify JSON and HTML report structures are unchanged
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - For all scanner modules WHERE module != ProcessScanner, findings SHALL be identical before and after fix
    - For all execution contexts WHERE NOT isBugCondition(context), results SHALL be unchanged
  - Property-based testing generates many test cases for stronger guarantees:
    - Use hypothesis or similar library to generate random scan configurations (scan_paths, depths, quick_mode flags)
    - Assert: For each configuration, non-ProcessScanner findings are identical in unfixed vs fixed code
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Capture baseline findings as JSON snapshots for later comparison:
    - Save CLI scan results to `tests/baseline_cli_findings.json`
    - Save UI scan results to `tests/baseline_ui_findings.json`
    - Filter out ProcessScanner AI daemon findings (these are the buggy part)
    - All other findings serve as preservation baseline
  - Mark task complete when tests are written, run, passing on unfixed code, and baseline snapshots are saved
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 3. Fix for CLI vs UI AI Agent Detection Parity

  - [ ] 3.1 Expand AI_DAEMON_NAMES dictionary with missing AI agent signatures
    - Open file: `scanner/modules/process_scanner.py`
    - Locate: `AI_DAEMON_NAMES` dictionary (lines ~35-52)
    - Add the following entries based on counterexamples from exploration test:
      - `"kiro.exe": "Kiro AI Assistant"`
      - `"kiro-server.exe": "Kiro Language Server"`
      - `"kiro-lsp.exe": "Kiro LSP"`
      - `"codex.exe": "OpenAI Codex"`
      - `"codex-server.exe": "Codex Backend Server"`
      - `"codex-backend.exe": "Codex Backend"`
      - `"antigravity.exe": "Antigravity AI"`
      - `"antigravity-daemon.exe": "Antigravity Service"`
      - `"antigravity-server.exe": "Antigravity Server"`
      - `"copilot.exe": "GitHub Copilot Desktop"` (complement existing copilot-language-server.exe)
    - Add cross-platform variants (if exploration test identifies them):
      - Linux/Mac: `"kiro": "Kiro AI Assistant"`, `"codex": "OpenAI Codex"`, `"antigravity": "Antigravity AI"`
      - macOS: `"kiro.app": "Kiro AI Assistant"`, `"codex.app": "OpenAI Codex"`
    - _Bug_Condition: isBugCondition(input) where input.executionMode == "UI" AND agentProcessesPresent(["Kiro", "Codex", "Antigravity", "Copilot"]) AND NOT agentProcessesDetected(input.scanResults)_
    - _Expected_Behavior: For all execution contexts (CLI and UI), ProcessScanner SHALL detect identical AI agent processes_
    - _Preservation: Non-ProcessScanner modules SHALL produce identical results; CLI detection SHALL remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 3.2 Expand AI_DAEMON_PREFIXES tuple for variant detection
    - Locate: `AI_DAEMON_PREFIXES` tuple (lines ~54-61)
    - Add the following prefix patterns to catch versioned/variant executables:
      - `"kiro"` - catches kiro.exe, kiro-server.exe, kiro-lsp.exe, kiro_v2.exe, kiro-3.0.exe
      - `"codex"` - catches codex.exe, codex-server.exe, codex-backend.exe, codex_v2.exe
      - `"antigravity"` - catches antigravity.exe, antigravity-daemon.exe, antigravity-server.exe
    - Expand `"copilot"` prefix matching (currently only "copilotruntime" exists):
      - Change: `"copilotruntime"` to `"copilot"` (broader match)
      - This will catch: copilot.exe, copilotruntime.exe, copilot-agent.exe, copilot-language-server.exe
    - _Bug_Condition: isBugCondition(input) from design_
    - _Expected_Behavior: expectedBehavior(result) from design_
    - _Preservation: Preservation Requirements from design_
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ] 3.3 Add debug logging to _match_ai_daemon() function for verification
    - Locate: `_match_ai_daemon()` function (lines ~153-180)
    - At the start of the function (after parameter extraction), add:
      ```python
      logger.debug(
          "ProcessScanner: Checking process '%s' (exe: '%s') against AI daemon patterns",
          name, exe
      )
      ```
    - In the exact match section (after successful match), add:
      ```python
      logger.debug(
          "ProcessScanner: Matched AI daemon via exact match: %s -> %s",
          key, label
      )
      ```
    - In the prefix match section (after successful match), add:
      ```python
      logger.debug(
          "ProcessScanner: Matched AI daemon via prefix '%s' -> %s",
          prefix, label
      )
      ```
    - This enables post-fix verification that agents are being detected correctly
    - Verify logging output during test runs to confirm pattern matching works
    - _Bug_Condition: isBugCondition(input) from design_
    - _Expected_Behavior: expectedBehavior(result) from design_
    - _Preservation: Preservation Requirements from design_
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [ ] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - AI Agent Detection Parity Across CLI and UI Modes
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (CLI and UI should detect identical agents)
    - Run: `pytest tests/test_cli_ui_parity_bug.py -v`
    - When this test passes, it confirms the expected behavior is satisfied:
      - CLI mode detects 52+ items including Kiro, Codex, Antigravity, Copilot
      - UI mode detects 52+ items including Kiro, Codex, Antigravity, Copilot
      - Detection counts are identical between modes
      - Agent names and PIDs match between modes
    - **EXPECTED OUTCOME**: Test PASSES with output like "CLI detected 52 items, UI detected 52 items - all agents present"
    - Review debug logs to confirm AI daemon pattern matching is working:
      - Should see: "Matched AI daemon via exact match: kiro.exe -> Kiro AI Assistant"
      - Should see: "Matched AI daemon via prefix 'codex' -> Codex"
    - If test still fails, investigate further:
      - Check if process names from exploration test match added dictionary entries
      - Check if case-insensitive matching is working correctly
      - Check if cross-platform name handling is needed
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Agent Detection Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run: `pytest tests/test_preservation_regression.py -v`
    - **EXPECTED OUTCOME**: All preservation tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix:
      - FileScanner finds same model files as baseline
      - PackageScanner finds same pip packages as baseline
      - RuntimeScanner finds same open ports as baseline
      - AgentScanner finds same Python scripts as baseline
      - APIScanner finds same credentials as baseline
      - LicenseScanner finds same LICENSE files as baseline
      - Report format matches baseline structure
    - Compare new scan results to baseline snapshots:
      - Load `tests/baseline_cli_findings.json` and `tests/baseline_ui_findings.json`
      - Run new scans, filter out ProcessScanner findings
      - Assert: Non-ProcessScanner findings are byte-identical to baseline
    - If any preservation test fails, investigate regression:
      - Check if any unintended changes were made to other scanner modules
      - Check if report generation logic was accidentally modified
      - Revert any changes outside of `process_scanner.py` AI daemon detection
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest tests/ -v`
  - Verify both exploration test (task 1) and preservation tests (task 2) pass
  - Run manual verification scans:
    - CLI mode: `python -c "from scanner.controller import ScanController; ScanController().run_scan()"`
    - UI mode: `python main.py` then navigate to `http://localhost:8000/run-scan`
  - Compare detection counts and agent lists between CLI and UI modes
  - Confirm UI mode now detects 52+ items (same as CLI mode)
  - Confirm all AI agents (Kiro, Codex, Antigravity, Copilot) are present in UI scan results
  - Review debug logs to ensure pattern matching is working correctly for all agents
  - If any issues arise, ask the user for guidance before proceeding
  - Mark task complete when all tests pass and manual verification confirms parity

---

## Notes

- **Exploration First**: Task 1 MUST be completed before implementing any fixes (task 3). The exploration test will identify exactly which process names are missing from detection patterns.
- **Preservation First**: Task 2 MUST be completed before implementing fixes to establish a baseline for regression testing.
- **No New Tests in Verification**: Tasks 3.4 and 3.5 re-run existing tests from tasks 1 and 2 - do NOT write new tests in these steps.
- **Deterministic Bug**: This is a deterministic bug with known inputs (running processes), so property-based testing is limited. Integration tests with real/mock processes provide better coverage.
- **Cross-Platform Consideration**: If exploration test reveals different process names on Linux/macOS, update `AI_DAEMON_NAMES` accordingly with platform-specific variants.
- **Debug Logging**: The debug logging added in task 3.3 is crucial for post-fix verification - review logs carefully during task 3.4.
