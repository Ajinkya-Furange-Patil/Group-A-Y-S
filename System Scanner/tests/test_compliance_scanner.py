import unittest
from unittest.mock import patch, MagicMock
import pathlib

from scanner.modules.compliance_scanner import ComplianceScanner
from scanner.models import ScanResult, Finding, FindingCategory, RiskLevel

class TestComplianceScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = ComplianceScanner()

    @patch('psutil.process_iter')
    @patch('psutil.net_connections')
    def test_dpdp_compliance(self, mock_net_connections, mock_process_iter):
        # Mock an AI agent process
        mock_proc = MagicMock()
        mock_proc.info = {'pid': 1234, 'name': 'ollama.exe'}
        mock_process_iter.return_value = [mock_proc]
        
        # Mock a connection to an external IP
        mock_conn = MagicMock()
        mock_conn.pid = 1234
        mock_conn.status = 'ESTABLISHED'
        mock_conn.raddr = MagicMock()
        mock_conn.raddr.ip = "8.8.8.8"
        mock_conn.raddr.port = 443
        mock_net_connections.return_value = [mock_conn]
        
        findings = self.scanner.scan()
        dpdp_findings = [f for f in findings if "DPDP" in f.title]
        self.assertTrue(len(dpdp_findings) > 0)
        self.assertEqual(dpdp_findings[0].risk_level, RiskLevel.HIGH)

    def test_certin_compliance(self):
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            self.scanner.scan_folder = tmpdir
            
            # The log file won't exist in the empty tmpdir
            findings = self.scanner.scan()
            
            certin_findings = [f for f in findings if "CERT-In Risk: Missing Audit Logging" in f.title]
            self.assertTrue(len(certin_findings) > 0)
            self.assertEqual(certin_findings[0].risk_level, RiskLevel.HIGH)
