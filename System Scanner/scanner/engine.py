"""
AI Discovery Scanner — Discovery Engine

The Discovery Engine dispatches all scanner modules concurrently using
ThreadPoolExecutor and collects their findings.

Classes:
    DiscoveryEngine — Parallel module dispatcher
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from scanner.models import Finding, ModuleInfo

logger = logging.getLogger(__name__)


class DiscoveryEngine:
    """Dispatches scanner modules in parallel and collects results."""

    def __init__(self) -> None:
        """Initialize the Discovery Engine with an empty module registry."""
        self._modules: list[Any] = []
        logger.info("Discovery Engine initialized")

    def register_module(self, module: Any) -> None:
        """Register a scanner module for execution.

        Args:
            module: A module object, class instance, or function to execute.
        """
        self._modules.append(module)
        name = getattr(module, "MODULE_NAME", getattr(module, "__name__", type(module).__name__))
        logger.debug("Registered module: %s", name)

    def _execute_module(self, module: Any) -> tuple[list[Finding], ModuleInfo]:
        """Execute a single module, measure its duration, and catch exceptions safely.

        Args:
            module: The module object or function to run.

        Returns:
            A tuple of (findings, module_info).
        """
        module_name = getattr(module, "MODULE_NAME", None)
        if not module_name:
            module_name = getattr(module, "__name__", type(module).__name__)

        module_number = getattr(module, "MODULE_NUMBER", 0)
        logger.info("Starting execution of module: %s (Module #%d)", module_name, module_number)
        start_time = time.monotonic()
        findings: list[Finding] = []

        info = ModuleInfo(
            name=module_name,
            module_number=module_number,
            status="pending",
        )

        try:
            # Check for standard methods: run() -> tuple[list[Finding], ModuleInfo] or list[Finding]
            if hasattr(module, "run") and callable(getattr(module, "run")):
                logger.debug("Running module %s via standard run() method", module_name)
                result = module.run()
                if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], ModuleInfo):
                    findings, info = result
                elif isinstance(result, list):
                    findings = result
                    info.status = "success"
                else:
                    raise TypeError(f"Invalid run() return type: {type(result)}")
            
            # Check for scan() -> list[Finding]
            elif hasattr(module, "scan") and callable(getattr(module, "scan")):
                logger.debug("Running module %s via scan() method", module_name)
                result = module.scan()
                if isinstance(result, list):
                    findings = result
                    info.status = "success"
                else:
                    raise TypeError(f"Invalid scan() return type: {type(result)}")
            
            # Check if callable directly
            elif callable(module):
                logger.debug("Running module %s directly as a callable", module_name)
                result = module()
                if isinstance(result, list):
                    findings = result
                    info.status = "success"
                else:
                    raise TypeError(f"Invalid callable return type: {type(result)}")
            
            else:
                raise AttributeError("Module must implement 'run()', 'scan()', or be callable.")

            if info.status == "pending":
                info.status = "success"

            info.findings_count = len(findings)
            duration = time.monotonic() - start_time
            info.duration_sec = duration
            logger.info("  [OK] %s completed successfully in %.3fs: found %d findings", module_name, duration, len(findings))

        except Exception as e:
            duration = time.monotonic() - start_time
            logger.error("  [FAIL] %s error after %.3fs: %s", module_name, duration, e, exc_info=True)
            info.status = "error"
            info.error_message = str(e)
            info.findings_count = 0
            findings = []
        finally:
            if info.duration_sec == 0.0:
                info.duration_sec = time.monotonic() - start_time

        return findings, info

    def run_all(self) -> tuple[list[Finding], list[ModuleInfo]]:
        """Execute all registered modules concurrently using ThreadPoolExecutor.

        Returns:
            A tuple of (all_findings, module_infos) aggregated from all modules.
        """
        logger.info("Discovery Engine: Dispatching %d modules in parallel...", len(self._modules))

        all_findings: list[Finding] = []
        module_infos: list[ModuleInfo] = []

        if not self._modules:
            logger.warning("Discovery Engine: No modules registered to execute.")
            return all_findings, module_infos

        max_workers = len(self._modules)
        logger.debug("ThreadPoolExecutor initialized with max_workers=%d", max_workers)
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ScannerModule") as executor:
            future_to_module = {
                executor.submit(self._execute_module, module): module
                for module in self._modules
            }

            for future in as_completed(future_to_module):
                module = future_to_module[future]
                name = getattr(module, "MODULE_NAME", type(module).__name__)
                try:
                    findings, info = future.result()
                    all_findings.extend(findings)
                    module_infos.append(info)
                    logger.debug("Discovery Engine: Aggregated results from %s", name)
                except Exception as e:
                    logger.error("Discovery Engine: Thread error executing %s: %s", name, e, exc_info=True)

        # Sort modules by module number for consistent ordering
        module_infos.sort(key=lambda x: x.module_number)

        logger.info(
            "Discovery Engine execution complete: collected %d findings across %d successfully executed modules",
            len(all_findings),
            sum(1 for m in module_infos if m.status == "success"),
        )
        return all_findings, module_infos

