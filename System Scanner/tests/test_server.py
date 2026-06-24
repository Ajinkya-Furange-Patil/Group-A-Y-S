"""
Unit tests for the Scan Server (scanner/server.py).
"""

import os
import json
import time
import socket
import urllib.request
import urllib.error
import threading
import unittest
from unittest.mock import patch, MagicMock

from scanner.server import ScanServer, get_local_ip


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind to 127.0.0.1 on port 0 to let the OS auto-assign an open port
        cls.server_instance = ScanServer(host="127.0.0.1", port=0)
        
        cls.server_thread = threading.Thread(target=cls.server_instance.start)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Wait up to 3 seconds for port assignment
        for _ in range(30):
            if cls.server_instance.server is not None:
                cls.port = cls.server_instance.server.server_address[1]
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Test server failed to start in background thread.")

    @classmethod
    def tearDownClass(cls):
        if cls.server_instance.server:
            cls.server_instance.server.shutdown()
        cls.server_thread.join(timeout=2)

    def test_get_local_ip(self):
        ip = get_local_ip()
        self.assertIsNotNone(ip)
        self.assertTrue(isinstance(ip, str))

    def test_get_consent_page(self):
        url = f"http://127.0.0.1:{self.port}/"
        response = urllib.request.urlopen(url)
        self.assertEqual(response.status, 200)
        html = response.read().decode("utf-8")
        self.assertIn("System Scan Authorization", html)
        self.assertIn("AI Discovery Client Portal", html)
        response.close()

    def test_get_nonexistent_report_redirects(self):
        # Temporarily back up dashboard file if present
        has_dashboard = os.path.exists("rendered_dashboard.html")
        if has_dashboard:
            os.rename("rendered_dashboard.html", "rendered_dashboard.html.bak")
        try:
            url = f"http://127.0.0.1:{self.port}/report"
            # It redirects back to / (200 OK)
            response = urllib.request.urlopen(url)
            self.assertEqual(response.status, 200)
            html = response.read().decode("utf-8")
            self.assertIn("System Scan Authorization", html)
            response.close()
        finally:
            if has_dashboard:
                os.rename("rendered_dashboard.html.bak", "rendered_dashboard.html")

    def test_get_results_not_found(self):
        # Temporarily back up report JSON if present
        has_report = os.path.exists("report.json")
        if has_report:
            os.rename("report.json", "report.json.bak")
        try:
            url = f"http://127.0.0.1:{self.port}/api/results"
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(url)
            self.assertEqual(ctx.exception.code, 404)
            ctx.exception.close()
        finally:
            if has_report:
                os.rename("report.json.bak", "report.json")

    @patch("scanner.controller.ScanController.run_scan")
    @patch("scanner.reporter.generate_json_report")
    @patch("scanner.reporter.generate_html_report")
    def test_run_scan_endpoint(self, mock_html, mock_json, mock_run):
        mock_result = MagicMock()
        mock_run.return_value = mock_result
        
        url = f"http://127.0.0.1:{self.port}/run-scan?quick=true"
        response = urllib.request.urlopen(url)
        self.assertEqual(response.status, 200)
        data = json.loads(response.read().decode("utf-8"))
        self.assertIn(data["status"], ["started", "already_running"])
        response.close()
        
        import time
        start_time = time.time()
        while mock_run.call_count == 0 and time.time() - start_time < 5.0:
            time.sleep(0.05)
            
        mock_run.assert_called_once()
        
        start_time = time.time()
        while (mock_json.call_count == 0 or mock_html.call_count == 0) and time.time() - start_time < 5.0:
            time.sleep(0.05)
            
        mock_json.assert_called_once_with(mock_result, "report.json")
        mock_html.assert_called_once_with(mock_result, "rendered_dashboard.html")

    def test_download_client_pdf(self):
        # 1. Test when client_report.pdf does not exist
        if os.path.exists("client_report.pdf"):
            try:
                os.rename("client_report.pdf", "client_report.pdf.bak")
            except Exception:
                pass
        try:
            url = f"http://127.0.0.1:{self.port}/api/download-client-pdf"
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(url)
            self.assertEqual(ctx.exception.code, 404)
            ctx.exception.close()
        finally:
            if os.path.exists("client_report.pdf.bak"):
                try:
                    os.rename("client_report.pdf.bak", "client_report.pdf")
                except Exception:
                    pass

        # 2. Test when client_report.pdf exists
        with open("client_report.pdf", "wb") as f:
            f.write(b"dummy pdf content")
        try:
            url = f"http://127.0.0.1:{self.port}/api/download-client-pdf"
            response = urllib.request.urlopen(url)
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"dummy pdf content")
            self.assertIn("Content-Disposition", response.headers)
            self.assertIn("ai_scan_report_v", response.headers["Content-Disposition"])
            response.close()
        finally:
            if os.path.exists("client_report.pdf"):
                try:
                    os.remove("client_report.pdf")
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
