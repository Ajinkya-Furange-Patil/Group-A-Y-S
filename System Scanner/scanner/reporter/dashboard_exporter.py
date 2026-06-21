"""
AI Discovery Scanner — Dashboard Exporter (Developer C · Sprint 2)

Generates a static HTML dashboard to visualize the 180-day ICT log retention history.
Connects to the LogRetentionDB and builds a modern, responsive HTML page with Chart.js.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from scanner.reporter.log_retention import LogRetentionDB

logger = logging.getLogger(__name__)


class DashboardExporter:
    """Exports 180-day scan history from LogRetentionDB to a static HTML dashboard."""

    def __init__(self, db_path: str = "ai_scanner_history.db"):
        self.db_path = db_path

    def export(self, output_path: str = "dashboard.html", days: int = 180) -> bool:
        """Fetch history and write it to an HTML dashboard file."""
        try:
            with LogRetentionDB(self.db_path) as db:
                trend = db.get_trend_summary(days=days)
                stats = db.get_stats()
        except Exception as e:
            logger.error("DashboardExporter: Failed to read from LogRetentionDB: %s", e)
            return False

        html_content = self._generate_html(trend, stats)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("Dashboard successfully exported to %s", output_path)
            return True
        except Exception as e:
            logger.error("DashboardExporter: Failed to write HTML file: %s", e)
            return False

    def _generate_html(self, trend: dict[str, Any], stats: dict[str, Any]) -> str:
        """Generate the HTML string using the fetched trend data."""
        
        # Prepare data for Chart.js
        labels = []
        risk_scores = []
        findings_counts = []
        
        for scan in trend.get("scans", []):
            try:
                # Format to short date/time
                dt = datetime.fromisoformat(scan["scan_timestamp"])
                labels.append(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                labels.append(scan["scan_timestamp"])
                
            risk_scores.append(scan["overall_risk_score"])
            findings_counts.append(scan["total_findings"])

        chart_data_json = json.dumps({
            "labels": labels,
            "risk_scores": risk_scores,
            "findings_counts": findings_counts,
        })

        # Build recent scans table HTML
        scans_html = ""
        for scan in reversed(trend.get("scans", [])[-20:]): # Show up to 20 recent scans
            risk_color = "#10b981" # Green
            score = scan['overall_risk_score']
            if score >= 75:
                risk_color = "#ef4444" # Red
            elif score >= 50:
                risk_color = "#f97316" # Orange
            elif score >= 25:
                risk_color = "#eab308" # Yellow
                
            try:
                dt = datetime.fromisoformat(scan['scan_timestamp'])
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                timestamp_str = scan['scan_timestamp']

            scans_html += f"""
            <tr class="border-b border-gray-200 hover:bg-gray-50">
                <td class="py-3 px-4 font-mono text-sm">{scan['scan_id']}</td>
                <td class="py-3 px-4">{timestamp_str}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 rounded text-white font-bold text-sm" style="background-color: {risk_color}">
                        {score:.1f}
                    </span>
                </td>
                <td class="py-3 px-4">{scan['total_findings']}</td>
            </tr>
            """

        if not scans_html:
            scans_html = "<tr><td colspan='4' class='py-4 text-center text-gray-500'>No scan history available</td></tr>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Discovery Scanner - 180-Day ICT Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f3f4f6;
        }}
    </style>
</head>
<body class="text-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        <!-- Header -->
        <div class="flex items-center justify-between bg-white p-6 rounded-lg shadow-sm mb-6 border border-gray-100">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">AI Discovery Scanner Dashboard</h1>
                <p class="text-sm text-gray-500 mt-1">CERT-In 180-Day ICT Log Retention Archive</p>
            </div>
            <div class="text-right">
                <p class="text-sm font-medium text-gray-600">Generated On</p>
                <p class="text-sm font-bold text-gray-900">{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100 border-l-4 border-l-blue-500">
                <p class="text-sm font-medium text-gray-500">Scans in Last {trend['period_days']} Days</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{trend['scan_count']}</p>
            </div>
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100 border-l-4 border-l-yellow-500">
                <p class="text-sm font-medium text-gray-500">Average Risk Score</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{trend['avg_risk']:.1f}</p>
            </div>
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100 border-l-4 border-l-red-500">
                <p class="text-sm font-medium text-gray-500">Peak Risk Score</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{trend['max_risk']:.1f}</p>
            </div>
            <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-100 border-l-4 border-l-indigo-500">
                <p class="text-sm font-medium text-gray-500">Total Findings Recorded</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{trend['total_findings']}</p>
            </div>
        </div>

        <!-- Chart Section -->
        <div class="bg-white p-6 rounded-lg shadow-sm mb-6 border border-gray-100">
            <h2 class="text-lg font-semibold text-gray-900 mb-4">Risk Score Trend</h2>
            <div class="relative h-80 w-full">
                <canvas id="trendChart"></canvas>
            </div>
        </div>

        <!-- History Table -->
        <div class="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-100">
            <div class="px-6 py-4 border-b border-gray-100 bg-gray-50">
                <h2 class="text-lg font-semibold text-gray-900">Recent Scans</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full text-left">
                    <thead class="bg-gray-100 text-gray-600 text-xs uppercase font-semibold">
                        <tr>
                            <th class="py-3 px-4">Scan ID</th>
                            <th class="py-3 px-4">Timestamp (UTC)</th>
                            <th class="py-3 px-4">Risk Score</th>
                            <th class="py-3 px-4">Findings Count</th>
                        </tr>
                    </thead>
                    <tbody class="text-gray-700 text-sm">
                        {scans_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Footer -->
        <div class="mt-8 text-center text-xs text-gray-400">
            <p>Database size: {round(stats.get('db_size_bytes', 0) / 1024, 1)} KB &bull; Oldest Record: {stats.get('oldest_record', 'N/A')}</p>
        </div>

    </div>

    <script>
        const chartData = {chart_data_json};
        
        const ctx = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: chartData.labels,
                datasets: [{{
                    label: 'Overall Risk Score',
                    data: chartData.risk_scores,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    yAxisID: 'y'
                }},
                {{
                    label: 'Findings Count',
                    data: chartData.findings_counts,
                    borderColor: '#6366f1',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    fill: false,
                    tension: 0.3,
                    yAxisID: 'y1'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                plugins: {{
                    legend: {{ position: 'top' }}
                }},
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{ display: true, text: 'Risk Score (0-100)' }},
                        min: 0,
                        max: 100
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{ display: true, text: 'Number of Findings' }},
                        grid: {{ drawOnChartArea: false }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
