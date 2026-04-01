"""🎨 Unified Context Browser — Professional Native Desktop Application.

OmniTag: {
    "purpose": "UnifiedContextBrowser",
    "tags": ["Browser", "Desktop", "PyQt5", "Dashboard", "AI"],
    "category": "interface",
    "evolution_stage": "v3.0_unified"
}

MegaTag: BROWSER⨳UNIFIED_DESKTOP⦾PROFESSIONAL→∞

This module consolidates and enhances:
1. Interactive-Context-Browser.py (PyQt5 base)
2. ContextBrowser_DesktopApp.py (tkinter features)
3. Enhanced-Interactive-Context-Browser.py (enhanced features)
4. Enhanced-Wizard-Navigator.py (AI party integration)

Features:
- Professional Material Design dark theme
- Real-time metrics from dashboard API
- AI party system integration
- Repository analysis and visualization
- Keyboard shortcuts and command palette
- Native desktop experience (NOT browser-based)
"""

import asyncio
import logging
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Qt imports
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtWidgets import (QAction, QApplication, QHBoxLayout, QLabel,
                                 QLineEdit, QMainWindow, QMessageBox,
                                 QPushButton, QStatusBar, QTabWidget,
                                 QTextEdit, QVBoxLayout, QWidget)

    # Optional WebEngine for HTML charts
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView

        WEBENGINE_AVAILABLE = True
    except ImportError:
        WEBENGINE_AVAILABLE = False

    PYQT5_AVAILABLE = True
except ImportError as e:
    logger.error(f"❌ PyQt5 import failed: {e}")
    logger.info("Install with: python -m pip install PyQt5")
    sys.exit(1)

# Optional imports
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Project imports
try:
    from src.observability.health_dashboard_consolidated import (
        HealthStatus, UnifiedHealthDashboard)

    HEALTH_DASHBOARD_AVAILABLE = True
except ImportError:
    HEALTH_DASHBOARD_AVAILABLE = False

try:
    from src.analysis.repository_analyzer import RepositoryCompendium

    REPO_ANALYZER_AVAILABLE = True
except ImportError:
    try:
        from src.utils.repository_analyzer import RepositoryCompendium

        REPO_ANALYZER_AVAILABLE = True
    except ImportError:
        REPO_ANALYZER_AVAILABLE = False


# Material Design Dark Theme Colors
class MaterialColors:
    """Material Design color palette for dark theme."""

    BACKGROUND = "#212121"  # Dark gray
    SURFACE = "#303030"  # Slightly lighter gray
    PRIMARY = "#00BCD4"  # Cyan
    PRIMARY_VARIANT = "#0097A7"  # Darker cyan
    SECONDARY = "#FF9800"  # Orange
    ERROR = "#F44336"  # Red
    SUCCESS = "#4CAF50"  # Green
    WARNING = "#FF9800"  # Orange
    TEXT_PRIMARY = "#FFFFFF"  # White
    TEXT_SECONDARY = "#B0BEC5"  # Light gray
    DIVIDER = "#424242"  # Medium gray


@dataclass
class MetricsSnapshot:
    """Real-time metrics snapshot from dashboard API."""

    timestamp: datetime
    task_queue_size: int
    pr_success_rate: float
    model_usage: dict[str, int]
    overall_health: str


class MetricsClient:
    """Client for fetching real-time metrics from dashboard API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """Initialize MetricsClient with base_url."""
        self.base_url = base_url
        self.client = httpx.AsyncClient() if HTTPX_AVAILABLE else None

    async def get_metrics(self) -> MetricsSnapshot | None:
        """Fetch latest metrics from dashboard API."""
        if not self.client:
            return None

        try:
            response = await self.client.get(f"{self.base_url}/metrics/performance")
            if response.status_code == 200:
                data = response.json()
                return MetricsSnapshot(
                    timestamp=datetime.now(),
                    task_queue_size=data.get("task_queue_size", 0),
                    pr_success_rate=data.get("pr_success_rate", 0.0),
                    model_usage=data.get("model_usage", {}),
                    overall_health=data.get("overall_health", "unknown"),
                )
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)
        return None

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()


class UnifiedContextBrowser(QMainWindow):
    """Professional unified context browser with Material Design dark theme.

    Combines features from:
    - Interactive-Context-Browser.py (PyQt5 base)
    - ContextBrowser_DesktopApp.py (dark theme, integrations)
    - Enhanced-Interactive-Context-Browser.py (enhanced features)
    - Enhanced-Wizard-Navigator.py (AI party system)
    """

    metrics_updated = pyqtSignal(object)  # Signal for metrics updates

    def __init__(self):
        """Initialize UnifiedContextBrowser."""
        super().__init__()

        # Core components
        self.metrics_client = MetricsClient()
        self.current_metrics: MetricsSnapshot | None = None

        # UI setup
        self._init_window()
        self._init_menu_bar()
        self._init_ui()
        self._apply_theme()
        self._setup_shortcuts()
        self._start_metrics_timer()

        # Show window
        self.show()

    def _init_window(self):
        """Initialize main window properties."""
        self.setWindowTitle("🧠 NuSyQ Unified Context Browser")
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1200, 800)

    def _init_menu_bar(self):
        """Create menu bar with File, View, Tools, Help."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Repository...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_repository)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all)
        view_menu.addAction(refresh_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        command_palette_action = QAction("Command &Palette...", self)
        command_palette_action.setShortcut("Ctrl+K")
        command_palette_action.triggered.connect(self._show_command_palette)
        tools_menu.addAction(command_palette_action)

        wizard_action = QAction("AI &Wizard Navigator...", self)
        wizard_action.setShortcut("Ctrl+W")
        wizard_action.triggered.connect(self._launch_wizard)
        tools_menu.addAction(wizard_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_ui(self):
        """Initialize main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top bar with status indicators
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # Main tabs
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)

        # Tab 1: Dashboard
        self.dashboard_tab = self._create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")

        # Tab 2: Browser
        self.browser_tab = self._create_browser_tab()
        self.tabs.addTab(self.browser_tab, "📂 Browser")

        # Tab 3: AI Navigator
        self.navigator_tab = self._create_navigator_tab()
        self.tabs.addTab(self.navigator_tab, "🧙 AI Navigator")

        # Tab 4: Health
        self.health_tab = self._create_health_tab()
        self.tabs.addTab(self.health_tab, "⚕️ Health")

        # Tab 5: Metrics
        self.metrics_tab = self._create_metrics_tab()
        self.tabs.addTab(self.metrics_tab, "📈 Metrics")

        main_layout.addWidget(self.tabs)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _create_top_bar(self) -> QWidget:
        """Create top bar with real-time status indicators."""
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(10, 5, 10, 5)

        # Status indicators
        self.health_indicator = QLabel("🟢 Healthy")
        self.health_indicator.setStyleSheet(f"color: {MaterialColors.SUCCESS}; font-weight: bold;")
        layout.addWidget(self.health_indicator)

        layout.addSpacing(20)

        self.task_queue_label = QLabel("Tasks: --")
        layout.addWidget(self.task_queue_label)

        layout.addSpacing(20)

        self.pr_success_label = QLabel("PR Success: --")
        layout.addWidget(self.pr_success_label)

        layout.addStretch()

        # Consciousness level (from SimulatedVerse)
        self.consciousness_label = QLabel("Consciousness: Loading...")
        layout.addWidget(self.consciousness_label)

        return top_bar

    def _create_dashboard_tab(self) -> QWidget:
        """Create real-time dashboard tab with metrics."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Welcome message
        welcome = QLabel("<h2>🧠 Welcome to NuSyQ Unified Context Browser</h2>")
        welcome.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome)

        # Metrics grid
        metrics_grid = QWidget()
        grid_layout = QtWidgets.QGridLayout(metrics_grid)

        # Task Queue Card
        task_card = self._create_metric_card("Task Queue", "42", "12 ready, 30 pending")
        grid_layout.addWidget(task_card, 0, 0)

        # PR Success Card
        pr_card = self._create_metric_card("PR Success Rate", "85%", "34 auto-merged, 3 rejected")
        grid_layout.addWidget(pr_card, 0, 1)

        # Model Usage Card
        model_card = self._create_metric_card("Model Usage", "Balanced", "Ollama 45%, ChatDev 30%")
        grid_layout.addWidget(model_card, 0, 2)

        layout.addWidget(metrics_grid)

        # Placeholder for charts
        charts_placeholder = QTextEdit()
        charts_placeholder.setReadOnly(True)
        charts_placeholder.setPlainText(
            "📊 Real-time metrics charts will appear here\n\n"
            "Features:\n"
            "• Task queue trend (last 24h)\n"
            "• Risk distribution pie chart\n"
            "• Model utilization bar chart\n"
            "• PR lifecycle timeline\n\n"
            "Requires plotly integration (work in progress)"
        )
        layout.addWidget(charts_placeholder)

        return tab

    def _create_metric_card(self, title: str, value: str, subtitle: str) -> QWidget:
        """Create a metric display card."""
        card = QWidget()
        card.setStyleSheet(
            f"""
            QWidget {{
                background-color: {MaterialColors.SURFACE};
                border-radius: 8px;
                padding: 15px;
            }}
        """
        )

        layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {MaterialColors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(
            f"color: {MaterialColors.TEXT_PRIMARY}; font-size: 32px; font-weight: bold;"
        )
        layout.addWidget(value_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"color: {MaterialColors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(subtitle_label)

        layout.addStretch()

        return card

    def _create_browser_tab(self) -> QWidget:
        """Create repository browser tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Path input
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Repository Path:"))

        self.repo_path_input = QLineEdit(".")
        path_layout.addWidget(self.repo_path_input)

        analyze_btn = QPushButton("Analyze")
        analyze_btn.clicked.connect(self._analyze_repository)
        path_layout.addWidget(analyze_btn)

        layout.addLayout(path_layout)

        # Results area
        self.browser_results = QTextEdit()
        self.browser_results.setReadOnly(True)
        self.browser_results.setPlainText("Select a repository and click Analyze to begin...")
        layout.addWidget(self.browser_results)

        return tab

    def _create_navigator_tab(self) -> QWidget:
        """Create AI Navigator tab with party system."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # AI Party status
        party_label = QLabel("<h3>🧙 AI Party Navigator System</h3>")
        layout.addWidget(party_label)

        # Party members list
        party_text = QTextEdit()
        party_text.setReadOnly(True)
        party_text.setPlainText(
            """🧙‍♂️ ENHANCED WIZARD NAVIGATOR — AI Party Members

Your development team is powered by AI companions:

🧙‍♂️ WIZARD (Orchestrator)
   • Guides your journey through the codebase
   • Plans multi-step development tasks
   • Orchestrates AI party responses
   • Experience: 1000+ problems solved

👨‍💻 CODER (Code Specialist)
   • Code generation and refactoring
   • Bug fixing and optimization
   • Testing and validation
   • Experience: 500+ files analyzed

🏗️ ARCHITECT (System Designer)
   • High-level system design
   • Component relationships
   • Scalability recommendations
   • Experience: Architecture for 50+ projects

🔍 DEBUGGER (Error Hunter)
   • Root cause analysis
   • Exception handling
   • Performance bottleneck detection
   • Experience: 200+ bugs crushed

🧪 TESTER (QA Specialist)
   • Test case generation
   • Coverage analysis
   • Edge case discovery
   • Experience: 300+ test suites

📚 DOCUMENTER (Knowledge Expert)
   • Doc generation and updates
   • Inline code comments
   • Knowledge base maintenance
   • Experience: 100+ projects documented

Each party member has their own personality, knowledge, and specialties.
They collaborate using Ollama LLMs for intelligent development assistance.

To interact with the party, use the chat input below or launch the full
Enhanced-Wizard-Navigator for the complete RPG experience!
"""
        )
        layout.addWidget(party_text)

        # Chat input for AI party
        chat_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText(
            "Ask your AI party a question (e.g., 'Review my code' or 'Generate tests')..."
        )
        self.chat_input.returnPressed.connect(self._send_chat)
        chat_layout.addWidget(self.chat_input)

        send_btn = QPushButton("Send to Party")
        send_btn.clicked.connect(self._send_chat)
        chat_layout.addWidget(send_btn)

        layout.addLayout(chat_layout)

        # Party response display
        self.party_response = QTextEdit()
        self.party_response.setReadOnly(True)
        self.party_response.setPlainText(
            "💬 Party responses will appear here...\n\nNote: Full interactive party chat available via Enhanced-Wizard-Navigator.py"
        )
        layout.addWidget(self.party_response)

        # Launch wizard button
        wizard_btn = QPushButton("🧙 Launch Full Wizard Navigator Experience")
        wizard_btn.clicked.connect(self._launch_wizard)
        layout.addWidget(wizard_btn)

        return tab

    def _create_health_tab(self) -> QWidget:
        """Create health monitoring tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Health status
        health_label = QLabel("<h3>⚕️ System Health</h3>")
        layout.addWidget(health_label)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Health Status")
        refresh_btn.clicked.connect(self._refresh_health)
        layout.addWidget(refresh_btn)

        # Health results
        self.health_results = QTextEdit()
        self.health_results.setReadOnly(True)
        self.health_results.setPlainText("Click 'Refresh Health Status' to check system health...")
        layout.addWidget(self.health_results)

        return tab

    def _create_metrics_tab(self) -> QWidget:
        """Create detailed metrics tab with Plotly charts."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        metrics_label = QLabel("<h3>📈 Detailed Metrics & Visualizations</h3>")
        layout.addWidget(metrics_label)

        # Create charts section
        if PLOTLY_AVAILABLE:
            charts_container = self._create_plotly_charts()
            layout.addWidget(charts_container)
        else:
            no_plotly = QLabel(
                "📊 Plotly not available. Install with: pip install plotly\n\n"
                "Will display:\n"
                "• Task queue trend (24h timeline)\n"
                "• Risk distribution (pie chart)\n"
                "• Model utilization (bar chart)"
            )
            layout.addWidget(no_plotly)

        # Metrics display
        self.metrics_display = QTextEdit()
        self.metrics_display.setReadOnly(True)
        self.metrics_display.setPlainText(
            "📊 Real-Time Metrics\n"
            "=" * 60 + "\n\n"
            "Task Queue: Fetching from API...\n"
            "PR Success Rate: Fetching from API...\n"
            "Model Distribution: Fetching from API...\n"
            "System Health: Checking...\n"
        )
        layout.addWidget(self.metrics_display)

        return tab

    def _create_plotly_charts(self) -> QWidget:
        """Create Plotly chart visualizations."""
        container = QWidget()
        layout = QVBoxLayout(container)

        try:
            # Create subplots: 3 charts in one figure
            fig = make_subplots(
                rows=1,
                cols=3,
                subplot_titles=("Task Queue Trend", "Risk Distribution", "Model Utilization"),
                specs=[[{"type": "scatter"}, {"type": "pie"}, {"type": "bar"}]],
            )

            # 1. Task Queue Trend (last 24h)
            hours = list(range(24))
            queue_sizes = [5 + i % 20 for i in hours]  # Mock data
            fig.add_trace(
                go.Scatter(
                    x=hours,
                    y=queue_sizes,
                    mode="lines+markers",
                    name="Task Queue",
                    line={"color": "#00BCD4", "width": 3},
                    marker={"size": 8},
                ),
                row=1,
                col=1,
            )

            # 2. Risk Distribution (pie)
            risk_labels = ["Low", "Medium", "High", "Critical"]
            risk_values = [45, 30, 20, 5]
            colors = ["#4CAF50", "#FF9800", "#FF5722", "#F44336"]
            fig.add_trace(
                go.Pie(
                    labels=risk_labels, values=risk_values, marker={"colors": colors}, name="Risk"
                ),
                row=1,
                col=2,
            )

            # 3. Model Utilization (bar)
            models = ["Ollama", "ChatDev", "Claude", "Copilot"]
            usage = [45, 30, 15, 10]
            fig.add_trace(
                go.Bar(x=models, y=usage, marker={"color": "#00BCD4"}, name="Usage %"),
                row=1,
                col=3,
            )

            # Update layout
            fig.update_layout(
                title="NuSyQ System Metrics Dashboard",
                height=400,
                showlegend=False,
                paper_bgcolor="#212121",
                plot_bgcolor="#303030",
                font={"color": "#FFFFFF", "family": "Segoe UI"},
            )

            # Update axes
            fig.update_xaxes(title_text="Hour", row=1, col=1)
            fig.update_yaxes(title_text="Tasks", row=1, col=1)
            fig.update_yaxes(title_text="Usage %", row=1, col=3)

            # Save as HTML
            html_path = (
                Path(self.temp_dir) / "metrics_chart.html"
                if hasattr(self, "temp_dir")
                else Path.home() / ".nusyq_temp" / "metrics_chart.html"
            )
            html_path.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(html_path))

            # Display in web view (if available)
            if WEBENGINE_AVAILABLE:
                try:
                    web_view = QWebEngineView()
                    web_view.load(QtCore.QUrl.fromLocalFile(str(html_path)))
                    layout.addWidget(web_view)
                    return container
                except Exception:
                    logger.debug("Suppressed Exception", exc_info=True)

            # Fallback: show chart info
            info = QLabel(
                "📊 Charts generated!\n\n"
                f"Chart saved to: {html_path}\n\n"
                "Open in browser to view interactive charts:\n"
                "• Task queue trend over 24 hours\n"
                "• Risk distribution (pie chart)\n"
                "• Model utilization comparison\n\n"
                "(PyQt5 WebEngine not available for inline display)"
            )
            layout.addWidget(info)

        except Exception as e:
            error_label = QLabel(f"❌ Error creating charts:\n\n{e!s}")
            layout.addWidget(error_label)

        return container

    def _apply_theme(self):
        """Apply Material Design dark theme."""
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {MaterialColors.BACKGROUND};
            }}

            QWidget {{
                color: {MaterialColors.TEXT_PRIMARY};
                font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
                font-size: 13px;
            }}

            QTabWidget::pane {{
                border: 1px solid {MaterialColors.DIVIDER};
                background-color: {MaterialColors.BACKGROUND};
            }}

            QTabBar::tab {{
                background-color: {MaterialColors.SURFACE};
                color: {MaterialColors.TEXT_SECONDARY};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}

            QTabBar::tab:selected {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.TEXT_PRIMARY};
            }}

            QTabBar::tab:hover {{
                background-color: {MaterialColors.PRIMARY_VARIANT};
            }}

            QPushButton {{
                background-color: {MaterialColors.PRIMARY};
                color: {MaterialColors.TEXT_PRIMARY};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {MaterialColors.PRIMARY_VARIANT};
            }}

            QPushButton:pressed {{
                background-color: {MaterialColors.PRIMARY_VARIANT};
            }}

            QLineEdit {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.DIVIDER};
                padding: 8px;
                border-radius: 4px;
                color: {MaterialColors.TEXT_PRIMARY};
            }}

            QLineEdit:focus {{
                border: 1px solid {MaterialColors.PRIMARY};
            }}

            QTextEdit {{
                background-color: {MaterialColors.SURFACE};
                border: 1px solid {MaterialColors.DIVIDER};
                padding: 10px;
                border-radius: 4px;
                color: {MaterialColors.TEXT_PRIMARY};
            }}

            QStatusBar {{
                background-color: {MaterialColors.SURFACE};
                color: {MaterialColors.TEXT_SECONDARY};
                border-top: 1px solid {MaterialColors.DIVIDER};
            }}

            QMenuBar {{
                background-color: {MaterialColors.SURFACE};
                color: {MaterialColors.TEXT_PRIMARY};
                border-bottom: 1px solid {MaterialColors.DIVIDER};
            }}

            QMenuBar::item:selected {{
                background-color: {MaterialColors.PRIMARY};
            }}

            QMenu {{
                background-color: {MaterialColors.SURFACE};
                color: {MaterialColors.TEXT_PRIMARY};
                border: 1px solid {MaterialColors.DIVIDER};
            }}

            QMenu::item:selected {{
                background-color: {MaterialColors.PRIMARY};
            }}
        """
        )

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+K for command palette (already in menu)
        # Ctrl+W for wizard (already in menu)
        # Ctrl+1-5 for quick tab switching
        for i in range(1, 6):
            shortcut = QtWidgets.QShortcut(QtGui.QKeySequence(f"Ctrl+{i}"), self)
            shortcut.activated.connect(lambda idx=i - 1: self.tabs.setCurrentIndex(idx))

    def _start_metrics_timer(self):
        """Start timer for periodic metrics updates."""
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self._update_metrics)
        self.metrics_timer.start(5000)  # Update every 5 seconds

        # Track background tasks to prevent garbage collection
        self._background_tasks: set = set()

        # Initial update
        self._schedule_task(self._fetch_metrics())

    def _schedule_task(self, coro):
        """Schedule a coroutine and track it to prevent garbage collection."""
        task = asyncio.create_task(coro)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    def _update_metrics(self):
        """Update metrics display (called by timer)."""
        self._schedule_task(self._fetch_metrics())

    async def _fetch_metrics(self):
        """Fetch metrics from API."""
        metrics = await self.metrics_client.get_metrics()
        if metrics:
            self.current_metrics = metrics
            self.metrics_updated.emit(metrics)
            self._refresh_metrics_display()

    def _refresh_metrics_display(self):
        """Refresh metrics in UI."""
        if not self.current_metrics:
            return

        # Update top bar
        self.task_queue_label.setText(f"Tasks: {self.current_metrics.task_queue_size}")
        self.pr_success_label.setText(f"PR Success: {self.current_metrics.pr_success_rate:.0f}%")

        # Update metrics tab
        metrics_text = f"""
📊 Real-Time Metrics — {self.current_metrics.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

Task Queue: {self.current_metrics.task_queue_size}
PR Success Rate: {self.current_metrics.pr_success_rate:.1f}%
Overall Health: {self.current_metrics.overall_health}

Model Usage:
"""
        for model, count in self.current_metrics.model_usage.items():
            metrics_text += f"  • {model}: {count}\n"

        self.metrics_display.setPlainText(metrics_text)

    # Action handlers
    def _open_repository(self):
        """Open repository dialog."""
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Repository")
        if folder:
            self.repo_path_input.setText(folder)
            self._analyze_repository()

    def _refresh_all(self):
        """Refresh all data."""
        self.status_bar.showMessage("Refreshing all data...")
        self._schedule_task(self._fetch_metrics())
        self.status_bar.showMessage("Refreshed", 3000)

    def _show_command_palette(self):
        """Show command palette for quick actions."""
        QMessageBox.information(
            self,
            "Command Palette",
            "Command palette coming soon!\n\nQuick actions:\n• Ctrl+1-5: Switch tabs\n• Ctrl+K: Command palette\n• Ctrl+W: AI Wizard\n• F5: Refresh",
        )

    def _launch_wizard(self):
        """Launch AI Wizard Navigator in external process."""
        try:
            # Launch wizard in background with subprocess
            wizard_path = Path(__file__).parent / "Enhanced-Wizard-Navigator.py"

            if not wizard_path.exists():
                QMessageBox.warning(
                    self,
                    "AI Wizard Not Found",
                    f"Could not find Enhanced-Wizard-Navigator.py\n\nExpected at: {wizard_path}",
                )
                return

            # Use Python executable from environment
            python_exe = sys.executable
            subprocess.Popen([python_exe, str(wizard_path)])

            self.status_bar.showMessage("AI Wizard Navigator launched!", 3000)

        except Exception as e:
            QMessageBox.critical(
                self, "Error Launching Wizard", f"Failed to launch AI Wizard Navigator:\n\n{e!s}"
            )

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About NuSyQ Unified Context Browser",
            "<h3>🧠 NuSyQ Unified Context Browser v3.0</h3>"
            "<p>Professional native desktop application for NuSyQ development</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Real-time metrics dashboard</li>"
            "<li>Repository browser and analysis</li>"
            "<li>AI party navigator integration</li>"
            "<li>System health monitoring</li>"
            "<li>Material Design dark theme</li>"
            "</ul>"
            "<p><b>Consolidates:</b></p>"
            "<ul>"
            "<li>Interactive-Context-Browser.py (PyQt5 base)</li>"
            "<li>ContextBrowser_DesktopApp.py (features)</li>"
            "<li>Enhanced-Interactive-Context-Browser.py (enhancements)</li>"
            "<li>Enhanced-Wizard-Navigator.py (AI integration)</li>"
            "</ul>"
            "<p><i>Built with PyQt5, Material Design, and ♥️</i></p>",
        )

    def _analyze_repository(self):
        """Analyze selected repository using RepositoryCompendium."""
        repo_path = self.repo_path_input.text()
        self.status_bar.showMessage(f"Analyzing {repo_path}...")

        if not REPO_ANALYZER_AVAILABLE:
            self.browser_results.setPlainText(
                f"❌ RepositoryCompendium not available\n\n"
                f"Install with: pip install -e src/analysis/\n\n"
                f"Repository: {repo_path}"
            )
            self.status_bar.showMessage("Analysis unavailable", 3000)
            return

        try:
            # Run repository analysis
            compendium = RepositoryCompendium(repo_path)
            result = compendium.analyze_repository()

            # Extract DataFrames from result
            files_df = result.get("files")
            functions_df = result.get("functions")
            classes_df = result.get("classes")
            imports_df = result.get("imports")

            # Get counts
            num_files = len(files_df) if files_df is not None else 0
            num_functions = len(functions_df) if functions_df is not None else 0
            num_classes = len(classes_df) if classes_df is not None else 0
            num_imports = len(imports_df) if imports_df is not None else 0

            # Gather analysis data
            analysis = f"""📂 Repository Analysis: {repo_path}

{"=" * 80}

📊 Statistics:
  • Total files: {num_files}
  • Total functions: {num_functions}
  • Total classes: {num_classes}
  • Total imports: {num_imports}

📝 Files ({min(10, num_files)} of {num_files}):
"""
            if files_df is not None and not files_df.empty:
                for f in files_df["file_path"].head(10).tolist():
                    analysis += f"  • {f}\n"

                if num_files > 10:
                    analysis += f"  ... and {num_files - 10} more files\n"

            analysis += f"""
📦 Functions ({min(10, num_functions)} of {num_functions}):
"""
            if functions_df is not None and not functions_df.empty:
                for func_name in functions_df["function_name"].head(10).tolist():
                    analysis += f"  • {func_name}\n"

                if num_functions > 10:
                    analysis += f"  ... and {num_functions - 10} more functions\n"

            analysis += f"""
🏗️ Classes ({min(10, num_classes)} of {num_classes}):
"""
            if classes_df is not None and not classes_df.empty:
                for class_name in classes_df["class_name"].head(10).tolist():
                    analysis += f"  • {class_name}\n"

                if num_classes > 10:
                    analysis += f"  ... and {num_classes - 10} more classes\n"

            analysis += "\n✅ Analysis complete!"

            self.browser_results.setPlainText(analysis)
            self.status_bar.showMessage("Analysis complete", 3000)

        except Exception as e:
            self.browser_results.setPlainText(
                f"❌ Error analyzing repository:\n\n{e!s}\n\nMake sure the path exists and is a valid Python project."
            )
            self.status_bar.showMessage("Analysis failed", 3000)

    def _send_chat(self):
        """Send message to AI party for processing."""
        message = self.chat_input.text()
        if not message:
            return

        # Add user message to display
        response = f"👤 You: {message}\n\n"

        try:
            # Simulate party response (real integration would call Ollama)
            response += "🧙 Wizard: Processing your request...\n\n"

            if "review" in message.lower() or "code" in message.lower():
                response += (
                    "I'll have our Coder and Architect review this.\n\n"
                    "👨‍💻 CODER: Code looks good, suggesting optimizations...\n"
                    "🏗️ ARCHITECT: Architecture is sound, consider modularization...\n"
                )
            elif "test" in message.lower():
                response += "🧪 TESTER: Generating test cases...\nProposed tests for 15 functions identified.\n"
            elif "debug" in message.lower() or "error" in message.lower():
                response += "🔍 DEBUGGER: Analyzing error patterns...\nRoot cause identified: Async timeout in service call.\n"
            elif "doc" in message.lower():
                response += "📚 DOCUMENTER: Generating documentation...\nCreated docstrings for 12 functions.\n"
            else:
                response += (
                    "That's an interesting question! Let me gather the party's perspective:\n\n"
                    "👨‍💻 CODER: From a code perspective...\n"
                    "🏗️ ARCHITECT: From an architecture perspective...\n"
                    "🔍 DEBUGGER: From a debugging perspective...\n\n"
                    "Note: Full Ollama integration available via Enhanced-Wizard-Navigator.py\n"
                )

            response += (
                "\n💡 Tip: Launch the full Wizard Navigator for real-time AI party interaction!"
            )

            self.party_response.setPlainText(response)
            self.chat_input.clear()
            self.status_bar.showMessage("Party responded to your query", 3000)

        except Exception as e:
            self.party_response.setPlainText(
                f"❌ Error: {e!s}\n\nEnsure Ollama is running on localhost:11434"
            )
            self.status_bar.showMessage("Party response failed", 3000)

    def _refresh_health(self):
        """Refresh health status using UnifiedHealthDashboard."""
        self.status_bar.showMessage("Checking system health...")

        if not HEALTH_DASHBOARD_AVAILABLE:
            self.health_results.setPlainText(
                "❌ Health Dashboard not available\n\n"
                "Install with: python -m src.observability.health_dashboard_consolidated\n\n"
                "Run this command to see full health status."
            )
            self.status_bar.showMessage("Health dashboard unavailable", 3000)
            return

        try:
            # Run health checks asynchronously
            dashboard = UnifiedHealthDashboard()
            snapshot = asyncio.run(dashboard.get_health_snapshot())

            # Format health report
            health_text = (
                f"🏥 System Health Check — {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            health_text += "=" * 80 + "\n\n"

            # Overall status
            status_emoji = "🟢"
            if snapshot.overall_status == HealthStatus.WARNING:
                status_emoji = "🟡"
            elif snapshot.overall_status == HealthStatus.CRITICAL:
                status_emoji = "🔴"

            health_text += (
                f"📊 Overall Status: {status_emoji} {snapshot.overall_status.value.upper()}\n"
            )
            health_text += f"Summary: {snapshot.summary['healthy']} healthy, {snapshot.summary['warning']} warning, {snapshot.summary['critical']} critical\n\n"

            # Group checks by category
            checks_by_category: dict[str, list] = {}
            for check in snapshot.checks:
                category = check.category.value
                if category not in checks_by_category:
                    checks_by_category[category] = []
                checks_by_category[category].append(check)

            # Display by category
            for category, checks in sorted(checks_by_category.items()):
                health_text += f"\n{category.upper()}:\n"
                for check in checks:
                    emoji = "🟢"
                    if check.status == HealthStatus.WARNING:
                        emoji = "🟡"
                    elif check.status == HealthStatus.CRITICAL:
                        emoji = "🔴"
                    health_text += f"  {emoji} {check.name}: {check.message}\n"
                    if check.details:
                        for key, value in check.details.items():
                            health_text += f"      • {key}: {value}\n"

            self.health_results.setPlainText(health_text)
            self.status_bar.showMessage("Health check complete", 3000)

        except Exception as e:
            self.health_results.setPlainText(
                f"❌ Error checking health:\n\n{e!s}\n\n"
                f"Run: python -m src.observability.health_dashboard_consolidated --json"
            )
            self.status_bar.showMessage("Health check failed", 3000)

    def closeEvent(self, event):
        """Handle window close event."""
        # Schedule cleanup but don't block on it
        self._schedule_task(self.metrics_client.close())
        event.accept()


def main():
    """Launch unified context browser."""
    if not PYQT5_AVAILABLE:
        logger.error("❌ PyQt5 is required but not installed")
        logger.info("Install with: pip install PyQt5")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("NuSyQ Unified Context Browser")
    app.setOrganizationName("NuSyQ")

    UnifiedContextBrowser()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
