"""
AI Discovery Scanner — Endpoint Enforcement Engine (Developer A)

Actively suppresses banned AI agents by terminating their processes and
modifies Windows Registry to disable consumer-grade Windows Copilot features.
"""

from __future__ import annotations

import logging
import platform

import psutil

from scanner.models import FindingCategory, ScanResult

logger = logging.getLogger(__name__)


class EnforcementEngine:
    """Enforcement Engine to actively mitigate discovered high-risk AI agents."""

    def __init__(self, banned_agents: list[str] | None = None) -> None:
        """Initialize the enforcement engine.
        
        Args:
            banned_agents: List of lower-case keywords for banned agents.
        """
        if banned_agents is None:
            self.banned_agents = ["open-interpreter", "autogpt", "babyagi", "chatgpthelper"]
        else:
            self.banned_agents = [agent.lower() for agent in banned_agents]
        logger.info("Enforcement Engine initialized with banned agents: %s", self.banned_agents)

    def terminate_banned_agents(self, scan_result: ScanResult) -> int:
        """Terminate processes associated with banned agents.
        
        Args:
            scan_result: The complete scan result containing findings.
            
        Returns:
            The number of processes successfully terminated.
        """
        terminated_count = 0
        pids_to_kill = set()

        for finding in scan_result.findings:
            title_lower = finding.title.lower()
            desc_lower = finding.description.lower()
            
            is_banned = False
            for banned in self.banned_agents:
                if banned in title_lower or banned in desc_lower or banned in finding.source.lower():
                    is_banned = True
                    break

            if is_banned:
                pid = finding.details.get("pid") or finding.details.get("process_id")
                if pid:
                    try:
                        pids_to_kill.add(int(pid))
                    except (ValueError, TypeError):
                        pass

        for pid in pids_to_kill:
            try:
                p = psutil.Process(pid)
                name = p.name()
                logger.warning("ENFORCEMENT: Terminating banned agent process PID %d (%s)", pid, name)
                p.terminate()
                p.wait(timeout=3)
                terminated_count += 1
                logger.info("Successfully terminated PID %d", pid)
            except psutil.NoSuchProcess:
                logger.debug("Process %d already terminated.", pid)
            except psutil.AccessDenied:
                logger.error("Access Denied: Could not terminate process %d. Please run as Administrator.", pid)
            except Exception as e:
                logger.error("Failed to terminate process %d: %s", pid, e)

        return terminated_count

    def disable_windows_copilot(self) -> bool:
        """Disable Windows Copilot via Registry modification (Windows only).
        
        Returns:
            True if successful or already disabled, False on error.
        """
        if platform.system() != "Windows":
            logger.info("Skipping Copilot disablement: Not running on Windows.")
            return False

        try:
            import winreg
            policy_path = r"SOFTWARE\Policies\Microsoft\Windows\WindowsCopilot"
            
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, policy_path, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ) as key:
                try:
                    val, _ = winreg.QueryValueEx(key, "TurnOffWindowsCopilot")
                    if val == 1:
                        logger.info("Windows Copilot is already disabled in HKCU.")
                        return True
                except FileNotFoundError:
                    pass
                
                logger.warning("ENFORCEMENT: Disabling Windows Copilot in HKCU Registry.")
                winreg.SetValueEx(key, "TurnOffWindowsCopilot", 0, winreg.REG_DWORD, 1)
                return True
                
        except PermissionError:
            logger.error("ENFORCEMENT: PermissionError disabling Windows Copilot. Run as Administrator.")
            return False
        except Exception as e:
            logger.error("ENFORCEMENT: Failed to disable Windows Copilot via Registry: %s", e)
            return False
