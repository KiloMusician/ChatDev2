"""VS Code Metrics Visualization UI.

Real-time metrics dashboard as VS Code extension/webview.

[OmniTag: vscode_metrics_ui, observability, visualization, dashboard]
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.tools.token_metrics_dashboard import TokenMetricsDashboard


class VSCodeMetricsUI:
    """Generates HTML/JavaScript for VS Code metrics visualization."""

    def __init__(self, state_dir: Path = Path("state")):
        """Initialize VS Code UI generator.

        Args:
            state_dir: Directory containing metrics data
        """
        self.state_dir = state_dir
        self.dashboard = TokenMetricsDashboard(state_dir)

    def generate_html_ui(self) -> str:
        """Generate complete HTML UI for metrics visualization.

        Returns:
            HTML string for VS Code webview
        """
        summary = self.dashboard.get_summary()

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SNS-Core Metrics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%);
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #404050;
        }}

        h1 {{
            font-size: 28px;
            background: linear-gradient(135deg, #00ff88 0%, #00ccff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .timestamp {{
            color: #888;
            font-size: 12px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%);
            border: 1px solid #404050;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            border-color: #00ff88;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.1);
        }}

        .metric-label {{
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #00ff88;
            margin-bottom: 8px;
        }}

        .metric-subtext {{
            color: #666;
            font-size: 13px;
        }}

        .chart-section {{
            background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%);
            border: 1px solid #404050;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}

        .chart-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #00ccff;
        }}

        canvas {{
            max-height: 300px;
        }}

        .leaderboard {{
            background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%);
            border: 1px solid #404050;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }}

        .leaderboard-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #00ccff;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th {{
            background: #1e1e2e;
            padding: 12px;
            text-align: left;
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #404050;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #303040;
        }}

        tr:hover {{
            background: #303040;
        }}

        .rank {{
            font-weight: bold;
            color: #00ff88;
            min-width: 30px;
        }}

        .operation {{
            color: #00ccff;
        }}

        .savings {{
            color: #00ff88;
            font-weight: 600;
        }}

        .cost {{
            color: #ffaa00;
        }}

        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            padding: 20px;
            border-top: 1px solid #404050;
            margin-top: 30px;
        }}

        .stats-row {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .stat {{
            flex: 1;
            min-width: 150px;
        }}

        .refresh-button {{
            background: #00ff88;
            color: #1e1e2e;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .refresh-button:hover {{
            background: #00ccff;
            box-shadow: 0 5px 15px rgba(0, 204, 255, 0.3);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>🚀 SNS-Core Metrics Dashboard</h1>
                <p class="timestamp">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            <button class="refresh-button" onclick="location.reload()">⟳ Refresh</button>
        </header>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Tokens Saved</div>
                <div class="metric-value">{summary.get("total_tokens_saved", 0):,}</div>
                <div class="metric-subtext">across all conversions</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Average Savings Rate</div>
                <div class="metric-value">{summary.get("avg_savings_pct", 0):.1f}%</div>
                <div class="metric-subtext">per conversion</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Total Cost Savings</div>
                <div class="metric-value">${{summary.get('total_cost_savings_usd', 0):.2f}}</div>
                <div class="metric-subtext">at GPT-4 rates</div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Conversions Made</div>
                <div class="metric-value">{summary.get("conversion_count", 0)}</div>
                <div class="metric-subtext">SNS operations</div>
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-title">📊 Savings Trend (Last 24h)</div>
            <canvas id="savingsChart"></canvas>
        </div>

        <div class="leaderboard">
            <div class="leaderboard-title">🏆 Top Operations by Savings</div>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Operation</th>
                        <th>Tokens Saved</th>
                        <th>Savings %</th>
                        <th>Cost Saved</th>
                    </tr>
                </thead>
                <tbody id="leaderboardBody">
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>SNS-Core Metrics Dashboard • Real-time token optimization tracking</p>
            <p>Powered by NuSyQ-Hub Zero-Token System</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script>
        const metricsData = {json.dumps(summary)};

        // Initialize chart
        const ctx = document.getElementById('savingsChart');
        if (ctx) {{
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: metricsData.hourly_labels || ['0h', '6h', '12h', '18h', '24h'],
                    datasets: [{{
                        label: 'Tokens Saved',
                        data: metricsData.hourly_savings || [0, 100, 250, 400, 650],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#00ff88',
                        pointBorderColor: '#1e1e2e',
                        pointBorderWidth: 2,
                        pointRadius: 5
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            labels: {{ color: '#888' }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            grid: {{ color: '#303040' }},
                            ticks: {{ color: '#888' }}
                        }},
                        x: {{
                            grid: {{ display: false }},
                            ticks: {{ color: '#888' }}
                        }}
                    }}
                }}
            }});
        }}

        // Populate leaderboard
        const leaderboard = metricsData.leaderboard || [];
        const leaderboardBody = document.getElementById('leaderboardBody');
        leaderboard.slice(0, 10).forEach((item, index) => {{
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="rank">#{{index + 1}}</td>
                <td class="operation">{{item.operation}}</td>
                <td class="savings">{{item.tokens_saved:,}}</td>
                <td class="savings">{{item.savings_pct}}%</td>
                <td class="cost">${{item.cost_saved.toFixed(4)}}</td>
            `;
            leaderboardBody.appendChild(row);
        }});

        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>"""

    def generate_extension_config(self) -> dict[str, Any]:
        """Generate VS Code extension configuration.

        Returns:
            Extension package.json configuration
        """
        return {
            "name": "sns-metrics-dashboard",
            "displayName": "SNS-Core Metrics Dashboard",
            "description": "Real-time visualization of SNS-Core token optimization metrics",
            "version": "1.0.0",
            "publisher": "nusyq",
            "engines": {"vscode": "^1.75.0"},
            "categories": ["Other", "Visualization"],
            "activationEvents": [
                "onCommand:sns-metrics.show",
                "onView:sns-metrics-view",
            ],
            "main": "./extension.js",
            "contributes": {
                "commands": [
                    {
                        "command": "sns-metrics.show",
                        "title": "Show SNS-Core Metrics Dashboard",
                        "category": "SNS-Core",
                    },
                    {
                        "command": "sns-metrics.refresh",
                        "title": "Refresh Metrics",
                        "category": "SNS-Core",
                    },
                ],
                "views": {
                    "sns-metrics": [
                        {
                            "id": "sns-metrics-view",
                            "name": "Metrics Dashboard",
                            "when": "true",
                        }
                    ]
                },
                "viewsContainers": {
                    "activitybar": [
                        {
                            "id": "sns-metrics",
                            "title": "SNS Metrics",
                            "icon": "resources/icon.svg",
                        }
                    ]
                },
            },
        }

    def save_webview_to_file(self, output_path: Path = Path("web") / "sns-metrics.html") -> None:
        """Save webview HTML to file.

        Args:
            output_path: Where to save HTML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(self.generate_html_ui())


def create_vscode_metrics_ui(state_dir: Path = Path("state")) -> VSCodeMetricsUI:
    """Factory function to create VS Code UI."""
    return VSCodeMetricsUI(state_dir)
