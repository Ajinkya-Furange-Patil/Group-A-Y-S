"""
AI Discovery Scanner — Scan Controller

The Scan Controller is the central orchestrator of the entire scan pipeline.
It coordinates module registration, dispatches them through the Discovery Engine,
passes results through the Classification Engine, and produces the final ScanResult.

Flow:
    ScanController.run_scan()
        → DiscoveryEngine.run_all()          (parallel module execution)
        → ClassificationEngine.classify()    (categorize findings)
        → ScanResult                         (aggregated output)

Classes:
    ScanController — Main scan orchestrator
"""

from __future__ import annotations

import logging
import platform
import socket
import time

from scanner.classifier import ClassificationEngine
from scanner.engine import DiscoveryEngine
from scanner.models import ScanResult

logger = logging.getLogger(__name__)


class ScanController:
    """Orchestrates the full AI Discovery scan pipeline.

    Responsibilities:
        - Initializes the Discovery Engine and Classification Engine
        - Registers all scanner modules
        - Triggers the scan and aggregates results
        - Handles top-level errors gracefully

    Usage:
        controller = ScanController()
        result = controller.run_scan()
    """

    def __init__(self) -> None:
        """Initialize the Scan Controller with engine and classifier instances."""
        self._engine = DiscoveryEngine()
        self._classifier = ClassificationEngine()
        logger.info("Scan Controller initialized")

    def _register_modules(self) -> None:
        """Register all available scanner modules with the Discovery Engine.

        Note:
            Day 1 stub — no modules registered yet. As Person B implements
            each module, they will be imported and registered here.
        """
        # ── MODULE 01: System Scanner ────────────────────────────────────
        from scanner.modules.system_scanner import SystemScanner
        self._engine.register_module(SystemScanner())

        # ── MODULE 02: File Scanner ──────────────────────────────────────
        # Will be added by Person B (Day 2)
        # from scanner.modules.file_scanner import FileScanner
        # self._engine.register_module(FileScanner())

        # ── MODULE 03: Process Scanner ───────────────────────────────────
        # Will be added by Person B (Day 2)
        # from scanner.modules.process_scanner import ProcessScanner
        # self._engine.register_module(ProcessScanner())

        # ── MODULE 04: Package Scanner ───────────────────────────────────
        # Will be added by Person B (Day 3)
        # from scanner.modules.package_scanner import PackageScanner
        # self._engine.register_module(PackageScanner())

        # ── MODULE 05: Agent Scanner ─────────────────────────────────────
        # Will be added by Person B (Day 3)
        # from scanner.modules.agent_scanner import AgentScanner
        # self._engine.register_module(AgentScanner())

        # ── MODULE 06: Runtime Scanner ───────────────────────────────────
        # Will be added by Person B (Day 3)
        # from scanner.modules.runtime_scanner import RuntimeScanner
        # self._engine.register_module(RuntimeScanner())

        # ── MODULE 07: API Scanner ───────────────────────────────────────
        from scanner.modules.api_scanner import APIScanner
        self._engine.register_module(APIScanner())

        logger.info("Module registration complete. Registered %d modules.", len(self._engine._modules))

    def run_scan(self) -> ScanResult:
        """Execute the full AI Discovery scan pipeline.

        Steps:
            1. Register all scanner modules
            2. Dispatch modules via Discovery Engine (parallel)
            3. Classify findings via Classification Engine
            4. Build and return the aggregated ScanResult

        Returns:
            A ScanResult containing all findings, module metadata, and summary.
        """
        logger.info("=" * 60)
        logger.info("AI DISCOVERY SCANNER - Scan Started")
        logger.info("=" * 60)

        scan_start = time.time()

        # Initialize result with host metadata
        result = ScanResult(
            hostname=socket.gethostname(),
            os_info=f"{platform.system()} {platform.release()} ({platform.machine()})",
        )

        try:
            # Step 1: Register modules
            logger.info("[1/3] Registering scanner modules...")
            self._register_modules()

            # Step 2: Run all modules through the Discovery Engine
            logger.info("[2/3] Running Discovery Engine...")
            all_findings, module_infos = self._engine.run_all()
            result.modules = module_infos

            # Step 3: Classify findings
            logger.info("[3/3] Running Classification Engine...")
            classified_findings = self._classifier.classify(all_findings)
            result.findings = classified_findings

        except Exception as e:
            logger.error("Scan pipeline error: %s", e, exc_info=True)

        finally:
            result.total_duration_sec = time.time() - scan_start
            result.compute_summary()

        logger.info("=" * 60)
        logger.info(
            "Scan Complete - %d findings in %.2fs",
            len(result.findings),
            result.total_duration_sec,
        )
        logger.info("=" * 60)

        return result
