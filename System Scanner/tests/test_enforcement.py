import unittest
from unittest.mock import patch, MagicMock

from scanner.enforcement import EnforcementEngine
from scanner.models import ScanResult, Finding, FindingCategory, RiskLevel

class TestEnforcementEngine(unittest.TestCase):
    
    def setUp(self):
        self.engine = EnforcementEngine()
        
    @patch('psutil.Process')
    def test_terminate_banned_agents(self, mock_process_class):
        # Create mock finding
        finding = Finding(
            module_name="ProcessScanner",
            title="AutoGPT Agent Found",
            description="Process matches autogpt signature.",
            source="C:/Path/To/autogpt.exe",
            category=FindingCategory.AI_AGENT,
            risk_level=RiskLevel.CRITICAL,
            details={"pid": 1234, "name": "autogpt.exe"}
        )
        scan_result = ScanResult()
        scan_result.findings.append(finding)
        
        # Create mock process instance
        mock_proc_instance = MagicMock()
        mock_proc_instance.name.return_value = "autogpt.exe"
        mock_process_class.return_value = mock_proc_instance
        
        terminated_count = self.engine.terminate_banned_agents(scan_result)
        
        # Verify process was killed
        mock_proc_instance.terminate.assert_called_once()
        self.assertEqual(terminated_count, 1)

    @patch('psutil.process_iter')
    def test_terminate_banned_agents_not_found(self, mock_process_iter):
        finding = Finding(
            module_name="ProcessScanner",
            title="Banned Agent Found",
            description="Process matches banned agent signature.",
            source="C:/Path/To/BannedAgent.exe",
            category=FindingCategory.AI_AGENT,
            risk_level=RiskLevel.CRITICAL,
            details={"pid": 1234, "name": "BannedAgent.exe"}
        )
        scan_result = ScanResult()
        scan_result.findings.append(finding)
        
        # Different PID
        mock_proc = MagicMock()
        mock_proc.info = {"pid": 9999, "name": "Other.exe", "exe": "C:/Path/To/Other.exe"}
        mock_process_iter.return_value = [mock_proc]
        
        terminated_count = self.engine.terminate_banned_agents(scan_result)
        
        mock_proc.terminate.assert_not_called()
        self.assertEqual(terminated_count, 0)
        
    @patch('platform.system')
    def test_disable_windows_copilot_not_windows(self, mock_system):
        mock_system.return_value = "Linux"
        result = self.engine.disable_windows_copilot()
        self.assertFalse(result)

    @patch('platform.system')
    @patch('winreg.CreateKeyEx')
    @patch('winreg.SetValueEx')
    @patch('winreg.QueryValueEx')
    def test_disable_windows_copilot(self, mock_query, mock_set_value, mock_create_key, mock_system):
        mock_system.return_value = "Windows"
        mock_query.side_effect = FileNotFoundError() # Simulate key missing initially
        
        result = self.engine.disable_windows_copilot()
        self.assertTrue(result)
        mock_create_key.assert_called()
        mock_set_value.assert_called()
