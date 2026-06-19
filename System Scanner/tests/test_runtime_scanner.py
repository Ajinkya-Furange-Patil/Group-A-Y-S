"""
Unit tests for the Runtime Scanner module (scanner/modules/runtime_scanner.py).
"""

import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from scanner.models import FindingCategory, RiskLevel
from scanner.modules import runtime_scanner


class TestRuntimeScanner(unittest.TestCase):
    @patch("pathlib.Path.home")
    @patch("socket.socket")
    def test_run_only_installed_directories(self, mock_socket_class, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            mock_home.return_value = temp_path

            # Create the directories
            (temp_path / ".ollama").mkdir()
            (temp_path / "lmstudio").mkdir()

            # Setup socket to return 111 (Connection refused / port closed)
            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 111
            mock_socket_class.return_value.__enter__.return_value = mock_socket

            findings, info = runtime_scanner.run()

            self.assertEqual(info.status, "success")
            self.assertEqual(len(findings), 2)
            self.assertEqual(info.findings_count, 2)

            # Check Ollama installed finding
            f_ollama = next(f for f in findings if f.source == "ollama")
            self.assertEqual(f_ollama.title, "Ollama Local Directory (Installed)")
            self.assertEqual(f_ollama.risk_level, RiskLevel.LOW)
            self.assertEqual(f_ollama.details["port_11434_open"], False)
            self.assertEqual(f_ollama.details["dir_ollama_exists"], True)

            # Check LM Studio installed finding
            f_lm = next(f for f in findings if f.source == "lmstudio")
            self.assertEqual(f_lm.title, "LM Studio Local Install Detected")
            self.assertEqual(f_lm.risk_level, RiskLevel.LOW)

    @patch("pathlib.Path.home")
    @patch("socket.socket")
    def test_run_active_and_installed(self, mock_socket_class, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            mock_home.return_value = temp_path

            # Create Ollama directory
            (temp_path / ".ollama").mkdir()

            # Setup socket to connect successfully on 11434, but fail on others
            mock_socket = MagicMock()
            def connect_ex_side_effect(address):
                host, port = address
                if port == 11434:
                    return 0  # Success
                return 111  # Closed

            mock_socket.connect_ex.side_effect = connect_ex_side_effect
            mock_socket_class.return_value.__enter__.return_value = mock_socket

            findings, info = runtime_scanner.run()

            self.assertEqual(info.status, "success")
            self.assertEqual(len(findings), 1)

            f_ollama = findings[0]
            self.assertEqual(f_ollama.title, "Ollama LLM Runtime (Active & Installed)")
            self.assertEqual(f_ollama.risk_level, RiskLevel.MEDIUM)
            self.assertEqual(f_ollama.details["port_11434_open"], True)
            self.assertEqual(f_ollama.details["dir_ollama_exists"], True)

    @patch("pathlib.Path.home")
    @patch("socket.socket")
    def test_run_active_ports_only(self, mock_socket_class, mock_home):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            mock_home.return_value = temp_path

            # No directories created

            # Open ports 8000 and 8080
            mock_socket = MagicMock()
            def connect_ex_side_effect(address):
                host, port = address
                if port in [8000, 8080]:
                    return 0  # Success
                return 111  # Closed

            mock_socket.connect_ex.side_effect = connect_ex_side_effect
            mock_socket_class.return_value.__enter__.return_value = mock_socket

            findings, info = runtime_scanner.run()

            self.assertEqual(info.status, "success")
            self.assertEqual(len(findings), 2)

            # Check port findings
            f_8000 = next(f for f in findings if f.details.get("port") == 8000)
            self.assertEqual(f_8000.title, "Active LLM Service Port: 8000")
            self.assertEqual(f_8000.risk_level, RiskLevel.MEDIUM)
            self.assertEqual(f_8000.category, FindingCategory.LLM_RUNTIME)

            f_8080 = next(f for f in findings if f.details.get("port") == 8080)
            self.assertEqual(f_8080.title, "Active LLM Service Port: 8080")
            self.assertEqual(f_8080.risk_level, RiskLevel.MEDIUM)

    @patch("psutil.net_connections")
    @patch("psutil.Process")
    def test_find_process_for_port_success(self, mock_process_class, mock_net_connections):
        # Setup mock connection
        mock_conn = MagicMock()
        mock_conn.laddr.port = 11434
        mock_conn.status = "LISTEN"
        mock_conn.pid = 4567
        mock_net_connections.return_value = [mock_conn]

        # Setup mock process
        mock_proc = MagicMock()
        mock_proc.name.return_value = "ollama.exe"
        mock_proc.cmdline.return_value = ["ollama", "serve"]
        mock_process_class.return_value = mock_proc

        result = runtime_scanner._find_process_for_port(11434)
        self.assertIsNotNone(result)
        self.assertEqual(result["process_id"], 4567)
        self.assertEqual(result["process_name"], "ollama.exe")
        self.assertEqual(result["process_cmdline"], ["ollama", "serve"])

    @patch("psutil.net_connections")
    @patch("psutil.process_iter")
    def test_find_process_for_port_fallback(self, mock_process_iter, mock_net_connections):
        # Force net_connections to raise AccessDenied
        import psutil
        mock_net_connections.side_effect = psutil.AccessDenied()

        # Setup mock process iteration
        mock_proc = MagicMock()
        mock_proc.pid = 7890
        mock_proc.name.return_value = "lmstudio.exe"
        mock_proc.cmdline.return_value = ["lmstudio", "--port", "1234"]
        
        mock_conn = MagicMock()
        mock_conn.laddr.port = 1234
        mock_conn.status = "LISTEN"
        mock_proc.connections.return_value = [mock_conn]

        mock_process_iter.return_value = [mock_proc]

        result = runtime_scanner._find_process_for_port(1234)
        self.assertIsNotNone(result)
        self.assertEqual(result["process_id"], 7890)
        self.assertEqual(result["process_name"], "lmstudio.exe")
        self.assertEqual(result["process_cmdline"], ["lmstudio", "--port", "1234"])

    def test_class_wrapper(self):
        scanner = runtime_scanner.RuntimeScanner()
        self.assertEqual(scanner.MODULE_NAME, "RuntimeScanner")
        self.assertEqual(scanner.MODULE_NUMBER, 6)

        with patch.object(runtime_scanner, "run") as mock_run:
            mock_run.return_value = ([], runtime_scanner.ModuleInfo(name="RuntimeScanner", module_number=6))
            findings = scanner.scan()
            self.assertEqual(findings, [])
            mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
