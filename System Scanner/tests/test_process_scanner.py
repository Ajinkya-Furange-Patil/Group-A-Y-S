"""
Unit tests for the Process Scanner module (scanner/modules/process_scanner.py).
"""

import unittest
from unittest.mock import MagicMock, patch

import psutil
from scanner.modules import process_scanner
from scanner.models import FindingCategory, RiskLevel


class MockProcess:
    def __init__(
        self,
        pid,
        name,
        cmdline,
        exe,
        username="testuser",
        rss=104857600,  # 100 MB
        cpu=1.5,
        create_time=1700000000.0,
        raise_on_cmdline=False,
    ):
        self.pid = pid
        self._name = name
        self._cmdline = cmdline
        self._exe = exe
        self._username = username
        self._rss = rss
        self._cpu = cpu
        self._create_time = create_time
        self.raise_on_cmdline = raise_on_cmdline

    def name(self):
        return self._name

    def cmdline(self):
        if self.raise_on_cmdline:
            raise psutil.AccessDenied()
        return self._cmdline

    def exe(self):
        return self._exe

    def username(self):
        return self._username

    def cpu_percent(self):
        return self._cpu

    def memory_info(self):
        mem = MagicMock()
        mem.rss = self._rss
        return mem

    def create_time(self):
        return self._create_time


class TestProcessScanner(unittest.TestCase):
    @patch("psutil.process_iter")
    def test_run_discovery(self, mock_process_iter):
        # Set up mock processes
        proc_ollama = MockProcess(
            pid=1001,
            name="ollama.exe",
            cmdline=["C:/Users/User/AppData/Local/Programs/Ollama/ollama.exe", "serve"],
            exe="C:/Users/User/AppData/Local/Programs/Ollama/ollama.exe",
        )
        proc_chrome = MockProcess(
            pid=1002,
            name="chrome.exe",
            cmdline=["chrome.exe", "--new-window"],
            exe="C:/Program Files/Google/Chrome/Application/chrome.exe",
        )
        proc_python_ai = MockProcess(
            pid=1003,
            name="python.exe",
            cmdline=["python", "my_langchain_agent.py", "--verbose"],
            exe="C:/Python310/python.exe",
        )
        proc_python_normal = MockProcess(
            pid=1004,
            name="python.exe",
            cmdline=["python", "simple_calculator.py"],
            exe="C:/Python310/python.exe",
        )
        proc_access_denied = MockProcess(
            pid=1005,
            name="System",
            cmdline=[],
            exe="",
            raise_on_cmdline=True,
        )

        mock_process_iter.return_value = [
            proc_ollama,
            proc_chrome,
            proc_python_ai,
            proc_python_normal,
            proc_access_denied,
        ]

        # Execute
        findings, info = process_scanner.run()

        self.assertEqual(info.status, "success")
        self.assertEqual(len(findings), 2)
        self.assertEqual(info.findings_count, 2)

        # Check ollama process finding
        f_ollama = next(f for f in findings if f.source == "ollama.exe")
        self.assertEqual(f_ollama.title, "ollama.exe")
        self.assertIn("Ollama", f_ollama.description)
        self.assertEqual(f_ollama.risk_level, RiskLevel.MEDIUM)
        self.assertEqual(f_ollama.details["pid"], 1001)
        self.assertEqual(f_ollama.details["memory_rss_mb"], 100.0)

        # Check python AI process finding
        f_python = next(f for f in findings if f.source == "python.exe")
        self.assertEqual(f_python.title, "python.exe (my_langchain_agent.py)")
        self.assertIn("my_langchain_agent.py", f_python.description)
        self.assertEqual(f_python.details["pid"], 1003)
        self.assertEqual(f_python.details["matched_keyword"], "langchain")

    @patch("psutil.process_iter")
    def test_process_scanner_wrapper(self, mock_process_iter):
        proc_ollama = MockProcess(
            pid=1001,
            name="ollama.exe",
            cmdline=["ollama", "serve"],
            exe="ollama.exe",
        )
        mock_process_iter.return_value = [proc_ollama]

        scanner = process_scanner.ProcessScanner()
        self.assertEqual(scanner.MODULE_NAME, "ProcessScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 3)

        findings = scanner.scan()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].title, "ollama.exe")


if __name__ == "__main__":
    unittest.main()
