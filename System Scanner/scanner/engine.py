"""
AI Discovery Scanner — Discovery Engine (Stub)

The Discovery Engine dispatches all scanner modules concurrently using
ThreadPoolExecutor and collects their findings. This is a Day 1 stub
that will be fully implemented on Day 2 by Person A.

Classes:
    DiscoveryEngine — Parallel module dispatcher
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from scanner.models import Finding, ModuleInfo

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Dispatches scanner modules in parallel and collects results.

    This is a stub implementation for Day 1. The full ThreadPoolExecutor-based
    parallel dispatch will be implemented on Day 2.
    """

    def __init__(self) -> None:
        """Initialize the Discovery Engine with an empty module registry."""
        self._modules: list = []
        logger.info("Discovery Engine initialized (stub mode)")

    def register_module(self, module: object) -> None:
        """Register a scanner module for execution.

        Args:
            module: A scanner module instance that implements a `scan()` method.
        """
        self._modules.append(module)
        logger.debug("Registered module: %s", type(module).__name__)

    def run_all(self) -> tuple[list[Finding], list[ModuleInfo]]:
        """Execute all registered modules and collect results.

        Returns:
            A tuple of (all_findings, module_infos) aggregated from all modules.

        Note:
            Day 1 stub — returns empty results. Full parallel implementation on Day 2.
        """
        logger.info("Discovery Engine: Running %d modules (stub mode)...", len(self._modules))

        all_findings: list[Finding] = []
        module_infos: list[ModuleInfo] = []

        # Stub: iterate modules sequentially (parallel dispatch on Day 2)
        for module in self._modules:
            module_name = type(module).__name__
            module_number = getattr(module, "MODULE_NUMBER", 0)
            start_time = time.time()

            info = ModuleInfo(
                name=module_name,
                module_number=module_number,
                status="success",
                duration_sec=0.0,
                findings_count=0,
            )

            try:
                # Each module must implement a scan() -> list[Finding] method
                if hasattr(module, "scan"):
                    findings = module.scan()
                    info.findings_count = len(findings)
                    all_findings.extend(findings)
                    logger.info("  [OK] %s: %d findings", module_name, len(findings))
                else:
                    info.status = "skipped"
                    logger.warning("  [SKIP] %s: No scan() method found, skipping", module_name)
            except Exception as e:
                info.status = "error"
                info.error_message = str(e)
                logger.error("  [FAIL] %s: %s", module_name, e)
            finally:
                info.duration_sec = time.time() - start_time
                module_infos.append(info)

        logger.info(
            "Discovery Engine: Complete. %d findings from %d modules.",
            len(all_findings),
            len(module_infos),
        )
        return all_findings, module_infos
