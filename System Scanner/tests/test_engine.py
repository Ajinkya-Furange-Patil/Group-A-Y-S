"""
Unit tests for the Discovery Engine (scanner/engine.py).
"""

import unittest
import time
from scanner.engine import DiscoveryEngine
from scanner.models import Finding, ModuleInfo, FindingCategory, RiskLevel


class MockRunModule:
    MODULE_NAME = "MockRunModule"
    MODULE_NUMBER = 2

    def __init__(self, findings=None, raise_error=False, delay=0.0):
        self.findings = findings or []
        self.raise_error = raise_error
        self.delay = delay

    def run(self):
        if self.delay > 0:
            time.sleep(self.delay)
        if self.raise_error:
            raise RuntimeError("Mock error in run")
        return self.findings


class MockScanModule:
    MODULE_NAME = "MockScanModule"
    MODULE_NUMBER = 3

    def __init__(self, findings=None, raise_error=False):
        self.findings = findings or []
        self.raise_error = raise_error

    def scan(self):
        if self.raise_error:
            raise ValueError("Mock error in scan")
        return self.findings


def mock_callable_module():
    return [
        Finding(
            module_name="MockCallable",
            title="Callable Finding",
            description="Finding from a callable",
            source="test",
        )
    ]


class TestDiscoveryEngine(unittest.TestCase):
    def setUp(self):
        self.engine = DiscoveryEngine()

    def test_register_module(self):
        # Register a class instance
        module1 = MockRunModule()
        self.engine.register_module(module1)
        self.assertEqual(len(self.engine._modules), 1)
        self.assertIn(module1, self.engine._modules)

        # Register a callable
        self.engine.register_module(mock_callable_module)
        self.assertEqual(len(self.engine._modules), 2)
        self.assertIn(mock_callable_module, self.engine._modules)

    def test_execute_module_run_success(self):
        finding = Finding(
            module_name="MockRunModule",
            title="Model Found",
            description="Mock GGUF model found",
            source="path/to/model.gguf",
        )
        module = MockRunModule(findings=[finding])
        
        findings, info = self.engine._execute_module(module)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].title, "Model Found")
        self.assertEqual(info.name, "MockRunModule")
        self.assertEqual(info.module_number, 2)
        self.assertEqual(info.status, "success")
        self.assertEqual(info.findings_count, 1)
        self.assertIsNone(info.error_message)
        self.assertGreaterEqual(info.duration_sec, 0.0)

    def test_execute_module_scan_success(self):
        finding = Finding(
            module_name="MockScanModule",
            title="Process Found",
            description="Mock Ollama process found",
            source="ollama",
        )
        module = MockScanModule(findings=[finding])
        
        findings, info = self.engine._execute_module(module)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(info.name, "MockScanModule")
        self.assertEqual(info.module_number, 3)
        self.assertEqual(info.status, "success")
        self.assertEqual(info.findings_count, 1)

    def test_execute_module_callable_success(self):
        findings, info = self.engine._execute_module(mock_callable_module)
        self.assertEqual(len(findings), 1)
        self.assertEqual(info.name, "mock_callable_module")
        self.assertEqual(info.status, "success")

    def test_execute_module_invalid_return_type(self):
        # Module returns something invalid (e.g. integer instead of list of Findings)
        def bad_callable():
            return 123
        
        findings, info = self.engine._execute_module(bad_callable)
        self.assertEqual(len(findings), 0)
        self.assertEqual(info.status, "error")
        self.assertIn("Invalid callable return type", info.error_message)

    def test_execute_module_invalid_interface(self):
        # Class that has no run or scan method and is not callable
        class BadModule:
            pass
        
        findings, info = self.engine._execute_module(BadModule())
        self.assertEqual(len(findings), 0)
        self.assertEqual(info.status, "error")
        self.assertIn("must implement", info.error_message)

    def test_execute_module_handle_exceptions(self):
        # Module raising exception in run
        module_run_error = MockRunModule(raise_error=True)
        findings, info = self.engine._execute_module(module_run_error)
        self.assertEqual(len(findings), 0)
        self.assertEqual(info.status, "error")
        self.assertEqual(info.error_message, "Mock error in run")

        # Module raising exception in scan
        module_scan_error = MockScanModule(raise_error=True)
        findings, info = self.engine._execute_module(module_scan_error)
        self.assertEqual(len(findings), 0)
        self.assertEqual(info.status, "error")
        self.assertEqual(info.error_message, "Mock error in scan")

    def test_run_all_parallel_execution(self):
        finding1 = Finding(module_name="M1", title="F1", description="D1", source="S1")
        finding2 = Finding(module_name="M2", title="F2", description="D2", source="S2")
        
        # We run 2 modules. One sleeps for 0.2s, the other for 0.2s.
        # If run sequentially, it takes >= 0.4s. If run in parallel, it should take < 0.35s.
        m1 = MockRunModule(findings=[finding1], delay=0.2)
        m2 = MockRunModule(findings=[finding2], delay=0.2)
        m2.MODULE_NUMBER = 1  # For checking sort order

        self.engine.register_module(m1)
        self.engine.register_module(m2)

        start_time = time.monotonic()
        findings, infos = self.engine.run_all()
        elapsed = time.monotonic() - start_time

        self.assertEqual(len(findings), 2)
        self.assertEqual(len(infos), 2)
        
        # Verify execution was concurrent (total elapsed should be close to 0.2s, not 0.4s)
        self.assertLess(elapsed, 0.6)

        # Verify list is sorted by module number
        self.assertEqual(infos[0].module_number, 1)
        self.assertEqual(infos[1].module_number, 2)


if __name__ == "__main__":
    unittest.main()
