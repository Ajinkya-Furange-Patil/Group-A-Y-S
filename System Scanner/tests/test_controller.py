"""
Unit tests for the Scan Controller and logging functionality.
"""

import unittest
import os
import logging
from unittest.mock import patch, MagicMock

from scanner.controller import ScanController
from scanner.models import ScanResult, Finding, FindingCategory, RiskLevel
from main import setup_logging


class TestScanController(unittest.TestCase):
    def setUp(self):
        self.controller = ScanController()

    def test_controller_initialization(self):
        self.assertIsNotNone(self.controller._engine)
        self.assertIsNotNone(self.controller._classifier)

    def test_run_scan(self):
        # Run scan and verify it compiles system information
        result = self.controller.run_scan()
        self.assertIsInstance(result, ScanResult)
        self.assertTrue(len(result.hostname) > 0)
        self.assertTrue(len(result.os_info) > 0)
        self.assertGreaterEqual(result.total_duration_sec, 0.0)
        # Verify that SystemScanner is one of the executed modules and succeeded
        system_module = next((m for m in result.modules if m.name == "SystemScanner"), None)
        self.assertIsNotNone(system_module, "SystemScanner should be executed")
        self.assertEqual(system_module.status, "success")
        self.assertGreater(len(result.findings), 0)


    @patch("scanner.engine.DiscoveryEngine.run_all")
    def test_run_scan_with_error(self, mock_run_all):
        mock_run_all.side_effect = RuntimeError("Mock engine failure")
        # Run scan and ensure it handles the error gracefully without crashing
        result = self.controller.run_scan()
        self.assertIsInstance(result, ScanResult)
        self.assertEqual(len(result.findings), 0)
        self.assertEqual(result.summary.get("total_findings"), 0)


class TestLoggingSetup(unittest.TestCase):
    def tearDown(self):
        # Clean up root logger handlers after tests
        root = logging.getLogger()
        for handler in list(root.handlers):
            root.removeHandler(handler)
            handler.close()
        # Remove log file if it exists
        if os.path.exists("ai_scanner.log"):
            try:
                os.remove("ai_scanner.log")
            except OSError:
                pass

    def test_setup_logging_console_and_file(self):
        setup_logging(verbose=False)
        root = logging.getLogger()
        
        # Verify console handler and file handler exist
        handlers = root.handlers
        self.assertEqual(len(handlers), 2)
        
        console_handler = next((h for h in handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)), None)
        file_handler = next((h for h in handlers if isinstance(h, logging.FileHandler)), None)
        
        self.assertIsNotNone(console_handler)
        self.assertIsNotNone(file_handler)
        
        # Assert logger formats/levels
        self.assertEqual(console_handler.level, logging.INFO)
        self.assertEqual(file_handler.level, logging.DEBUG)
        
        # Verify log file was created
        self.assertTrue(os.path.exists("ai_scanner.log"))

    def test_setup_logging_verbose(self):
        setup_logging(verbose=True)
        root = logging.getLogger()
        
        handlers = root.handlers
        console_handler = next((h for h in handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)), None)
        
        self.assertIsNotNone(console_handler)
        self.assertEqual(console_handler.level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main()
