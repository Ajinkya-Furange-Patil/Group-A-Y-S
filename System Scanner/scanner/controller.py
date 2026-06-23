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
from scanner.status_tracker import update_scan_status

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

    def __init__(self, quick: bool = False, scan_folder: str | None = None, max_depth: int | None = None, cpu_limit: float = 90.0, ram_limit: float = 25.0, repo_mode: bool = False) -> None:
        """Initialize the Scan Controller with engine and classifier instances."""
        self._engine = DiscoveryEngine(cpu_limit=cpu_limit, ram_limit=ram_limit)
        self._classifier = ClassificationEngine()
        self._quick = quick
        self._scan_folder = scan_folder
        self._max_depth = max_depth
        self._repo_mode = repo_mode
        logger.info("Scan Controller initialized (quick=%s, folder=%s, depth=%s, repo_mode=%s, cpu_limit=%.1f, ram_limit=%.1f)", quick, scan_folder, max_depth, repo_mode, cpu_limit, ram_limit)

    def _register_modules(self) -> None:
        """Register all available scanner modules with the Discovery Engine.

        Attempts to load modules dynamically to support seamless parallel development.
        """
        logger.info("Starting module registration...")

        # ── MODULE 01: System Scanner ────────────────────────────────────
        if not self._repo_mode:
            try:
                from scanner.modules import system_scanner
                self._engine.register_module(system_scanner)
                logger.info("Successfully registered MODULE 01: SystemScanner")
            except ImportError as e:
                logger.error("Failed to import MODULE 01: SystemScanner: %s", e)
        else:
            logger.info("Skipping MODULE 01: SystemScanner in repository scan mode")

        # ── MODULE 02: File Scanner ──────────────────────────────────────
        try:
            from scanner.modules.file_scanner import FileScanner
            self._engine.register_module(FileScanner(quick=self._quick, scan_folder=self._scan_folder, max_depth=self._max_depth))
            logger.info("Successfully registered MODULE 02: FileScanner")
        except ImportError:
            logger.debug("MODULE 02: FileScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 02: FileScanner: %s", e, exc_info=True)

        # ── MODULE 03: Process Scanner ───────────────────────────────────
        if not self._repo_mode:
            try:
                from scanner.modules.process_scanner import ProcessScanner
                self._engine.register_module(ProcessScanner())
                logger.info("Successfully registered MODULE 03: ProcessScanner")
            except ImportError:
                logger.debug("MODULE 03: ProcessScanner not available (ImportError)")
            except Exception as e:
                logger.warning("Failed to initialize MODULE 03: ProcessScanner: %s", e, exc_info=True)
        else:
            logger.info("Skipping MODULE 03: ProcessScanner in repository scan mode")

        # ── MODULE 04: Package Scanner ───────────────────────────────────
        try:
            from scanner.modules.package_scanner import PackageScanner
<<<<<<< HEAD
            self._engine.register_module(PackageScanner(scan_folder=self._scan_folder))
=======
            scan_folder_val = self._scan_folder if self._repo_mode else None
            self._engine.register_module(PackageScanner(scan_folder=scan_folder_val))
>>>>>>> 0216ea5cd9da6e34b7bb5fe5dd3cb97986c49dfe
            logger.info("Successfully registered MODULE 04: PackageScanner")
        except ImportError:
            logger.debug("MODULE 04: PackageScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 04: PackageScanner: %s", e, exc_info=True)

        # ── MODULE 05: Agent Scanner ─────────────────────────────────────
        try:
            from scanner.modules.agent_scanner import AgentScanner
            self._engine.register_module(AgentScanner(scan_folder=self._scan_folder, max_depth=self._max_depth))
            logger.info("Successfully registered MODULE 05: AgentScanner")
        except ImportError:
            logger.debug("MODULE 05: AgentScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 05: AgentScanner: %s", e, exc_info=True)

        # ── MODULE 06: Runtime Scanner ───────────────────────────────────
        try:
            from scanner.modules.runtime_scanner import RuntimeScanner
            scan_folder_val = self._scan_folder if self._repo_mode else None
            self._engine.register_module(RuntimeScanner(scan_folder=scan_folder_val))
            logger.info("Successfully registered MODULE 06: RuntimeScanner")
        except ImportError:
            logger.debug("MODULE 06: RuntimeScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 06: RuntimeScanner: %s", e, exc_info=True)

        # ── MODULE 07: API Scanner ───────────────────────────────────────
        try:
            from scanner.modules.api_scanner import APIScanner
            self._engine.register_module(APIScanner(target_dir=self._scan_folder, max_depth=self._max_depth))
            logger.info("Successfully registered MODULE 07: APIScanner")
        except ImportError:
            logger.debug("MODULE 07: APIScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 07: APIScanner: %s", e, exc_info=True)

        # ── MODULE 08: MCP Scanner ───────────────────────────────────────
        try:
            from scanner.modules.mcp_scanner import MCPScanner
<<<<<<< HEAD
            self._engine.register_module(MCPScanner(scan_folder=self._scan_folder))
=======
            scan_folder_val = self._scan_folder if self._repo_mode else None
            self._engine.register_module(MCPScanner(scan_folder=scan_folder_val))
>>>>>>> 0216ea5cd9da6e34b7bb5fe5dd3cb97986c49dfe
            logger.info("Successfully registered MODULE 08: MCPScanner")
        except ImportError:
            logger.debug("MODULE 08: MCPScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 08: MCPScanner: %s", e, exc_info=True)

        # ── MODULE 09: License Scanner ───────────────────────────────────
        try:
            from scanner.modules.license_scanner import LicenseScanner
            self._engine.register_module(LicenseScanner(scan_folder=self._scan_folder, max_depth=self._max_depth))
            logger.info("Successfully registered MODULE 09: LicenseScanner")
        except ImportError:
            logger.debug("MODULE 09: LicenseScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 09: LicenseScanner: %s", e, exc_info=True)

        # ── MODULE 10: Compliance Scanner ────────────────────────────────
        try:
            from scanner.modules.compliance_scanner import ComplianceScanner
            self._engine.register_module(ComplianceScanner(scan_folder=self._scan_folder, max_depth=self._max_depth))
            logger.info("Successfully registered MODULE 10: ComplianceScanner")
        except ImportError:
            logger.debug("MODULE 10: ComplianceScanner not available (ImportError)")
        except Exception as e:
            logger.warning("Failed to initialize MODULE 10: ComplianceScanner: %s", e, exc_info=True)

        logger.info("Module registration complete. Registered %d active modules.", len(self._engine._modules))

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

        # Initialize result with host metadata or repo details
        if self._repo_mode and self._scan_folder:
            import os
            repo_name = os.path.basename(self._scan_folder)
            hostname = f"GitHub Repo: {repo_name}"
            os_info = "Remote Repository Scan"
        else:
            hostname = socket.gethostname()
            system = platform.system()
            release = platform.release()
            machine = platform.machine()
            if machine == "AMD64":
                machine = "x64"

            os_parts = []
            if system:
                os_parts.append(system)
            if release:
                os_parts.append(release)
            os_info = " ".join(os_parts)
            if machine:
                os_info += f" ({machine})"
            if not os_info:
                os_info = "Unknown OS"

        logger.info("Target Machine: %s", hostname)
        logger.info("Operating System: %s", os_info)

        result = ScanResult(
            hostname=hostname,
            os_info=os_info,
        )

        try:
            # Step 1: Register modules
            logger.info("[1/3] Registering scanner modules...")
            self._register_modules()

            # Step 2: Run all modules through the Discovery Engine
            logger.info("[2/3] Running Discovery Engine on %d modules...", len(self._engine._modules))
            all_findings, module_infos = self._engine.run_all()
            result.modules = module_infos
            logger.info("Discovery Engine complete. Found %d raw findings.", len(all_findings))

            # Step 3: Classify findings
            logger.info("[3/3] Running Classification Engine...")
            update_scan_status("Computing Risk Heuristics...", 60)
            classified_findings = self._classifier.classify(all_findings)
            result.findings = classified_findings
            logger.info("Classification Engine complete. Processed %d findings.", len(classified_findings))

            update_scan_status("Finalizing Results...", 90)

        except Exception as e:
            logger.error("Scan pipeline encountered a top-level error: %s", e, exc_info=True)

        finally:
            result.total_duration_sec = time.time() - scan_start
            result.compute_summary()
            update_scan_status("Complete", 100)

        logger.info("=" * 60)
        logger.info(
            "Scan Complete - %d findings in %.2fs (Risk Score: %s/100)",
            len(result.findings),
            result.total_duration_sec,
            result.summary.get("overall_risk_score", 0.0),
        )
        logger.info("=" * 60)

        return result

