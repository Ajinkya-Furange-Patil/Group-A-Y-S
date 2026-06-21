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

    def __init__(self, cpu_limit: float = 90.0, ram_limit: float = 25.0) -> None:
        """Initialize the Discovery Engine with an empty module registry."""
        self._modules: list[Any] = []
        self.cpu_limit = cpu_limit
        self.ram_limit = ram_limit
        logger.info("Discovery Engine initialized with limits CPU: %.1f%%, RAM: %.1f%%", cpu_limit, ram_limit)

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
        import sys
        import time

        # Temporarily set console handler levels to WARNING to prevent logging output from corrupting the spinner
        console_handlers = []
        root_logger = logging.getLogger()
        for h in root_logger.handlers:
            if isinstance(h, logging.StreamHandler) and getattr(h, "stream", None) == sys.stdout:
                console_handlers.append((h, h.level))
                h.setLevel(logging.WARNING)

        total_modules = len(self._modules)
        completed_modules = 0
        spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_idx = 0

        # ANSI styles
        RESET = "\033[0m"
        BOLD = "\033[1m"
        GOLD = "\033[38;5;220m"
        AMBER = "\033[38;5;214m"
        DIM = "\033[2m"

        try:
            with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ScannerModule") as executor:
                future_to_module = {
                    executor.submit(self._execute_module, module): module
                    for module in self._modules
                }

                while completed_modules < total_modules:
                    completed_modules = sum(1 for f in future_to_module if f.done())
                    percent = int((completed_modules / total_modules) * 100)
                    
                    bar_length = 20
                    filled_length = int(bar_length * completed_modules // total_modules)
                    bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    
                    spin = spinner[spinner_idx % len(spinner)]
                    spinner_idx += 1
                    
                    running_names = []
                    for f, mod in future_to_module.items():
                        if not f.done():
                            name = getattr(mod, "MODULE_NAME", getattr(mod, "__name__", type(mod).__name__))
                            running_names.append(name)
                    
                    running_str = ", ".join(running_names[:2])
                    if len(running_names) > 2:
                        running_str += f" (+{len(running_names) - 2} more)"
                    
                    status_text = f"Scanning ({running_str})..." if running_names else "Wrapping up..."
                    
                    try:
                        sys.stdout.write(f"\r{GOLD}{spin}{RESET} {AMBER}[{bar}]{RESET} {BOLD}{percent}%{RESET} | {DIM}{status_text}{RESET}")
                        sys.stdout.flush()
                    except UnicodeEncodeError:
                        ascii_spin = ["|", "/", "-", "\\"][spinner_idx % 4]
                        # Replace block characters with '#' and '=' for non-UTF8/CP1252 shells
                        ascii_bar = "#" * filled_length + "-" * (bar_length - filled_length)
                        try:
                            sys.stdout.write(f"\r{GOLD}{ascii_spin}{RESET} {AMBER}[{ascii_bar}]{RESET} {BOLD}{percent}%{RESET} | {DIM}{status_text}{RESET}")
                            sys.stdout.flush()
                        except Exception:
                            pass
                    
                    try:
                        import psutil
                        process = psutil.Process()
                        
                        # Calculate relative memory percentage (Process RSS / Total Hardware RAM)
                        mem_info = process.memory_info().rss
                        total_mem = psutil.virtual_memory().total
                        mem_pct = (mem_info / total_mem) * 100.0
                        
                        # CPU percentage
                        cpu_pct = process.cpu_percent(interval=None)

                        if mem_pct > self.ram_limit or cpu_pct > self.cpu_limit:
                            logger.error("Resource limits exceeded (RAM: %.1f%% / %.1f%%, CPU: %.1f%% / %.1f%%). Aborting remaining modules.", mem_pct, self.ram_limit, cpu_pct, self.cpu_limit)
                            # Restore terminal and print abort message
                            sys.stdout.write(f"\r\033[31m[!] ABORTING: Execution limit bounds exceeded (RAM: {mem_pct:.1f}%, CPU: {cpu_pct:.1f}%)\033[0m" + " " * 20 + "\n")
                            sys.stdout.flush()
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                    except Exception as e:
                        logger.debug("Failed to profile process: %s", e)
                        
                    time.sleep(0.1)

                sys.stdout.write("\r" + " " * 85 + "\r")
                sys.stdout.flush()

                # Collect findings and metadata from completed tasks
                for future in future_to_module:
                    module = future_to_module[future]
                    name = getattr(module, "MODULE_NAME", getattr(module, "__name__", type(module).__name__))
                    try:
                        findings, info = future.result()
                        all_findings.extend(findings)
                        module_infos.append(info)
                        logger.debug("Discovery Engine: Aggregated results from %s", name)
                    except Exception as e:
                        logger.error("Discovery Engine: Thread error executing %s: %s", name, e, exc_info=True)
        finally:
            # Restore console log level configuration
            for h, level in console_handlers:
                h.setLevel(level)

        # Sort modules by module number for consistent ordering
        module_infos.sort(key=lambda x: x.module_number)

        logger.info(
            "Discovery Engine execution complete: collected %d findings across %d successfully executed modules",
            len(all_findings),
            sum(1 for m in module_infos if m.status == "success"),
        )
        return all_findings, module_infos

