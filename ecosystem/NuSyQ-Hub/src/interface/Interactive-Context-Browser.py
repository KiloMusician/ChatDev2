"""Interactive context browser for repository analysis (KILO-FOOLISH Quantum Edition).

OmniTag: [ContextBrowser, PyQtUI, RepoAnalysis, Visualization]
MegaTag: [TOOLHOOK⨳CONTEXT_BROWSER⦾EVOLUTION→Φ.3.1]

This module is part of the KILO-FOOLISH recursively extensible, quantum-inspired, AI-augmented development ecosystem.
It integrates modular logging, context propagation, and advanced tagging per project philosophy.
Now implemented as a native PyQt5 desktop application for an app-like, browserless experience.
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from PyQt5 import QtCore, QtWidgets

# Modular logging system (tag-aware)
try:
    from src.LOGGING.modular_logging_system import log_tagged_event

    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


# Ensure stubs directory is on path for consolidated repository_compendium_stub

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "utils" / "stubs"))
# Context bridge (for context propagation, tagging, memory)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "copilot"))
    from copilot_enhancement_bridge import (MegaTag, OmniTag,
                                            get_enhanced_bridge)

    ENHANCED_BRIDGE = get_enhanced_bridge()
    BRIDGE_AVAILABLE = True
except (ImportError, ModuleNotFoundError, AttributeError):
    ENHANCED_BRIDGE = None
    BRIDGE_AVAILABLE = False

try:
    from repository_compendium_stub import RepositoryCompendium
except ImportError as e:
    msg = (
        "Could not import RepositoryCompendium from utils/repository_analyzer. "
        "Ensure utils/repository_analyzer.py exists and is on PYTHONPATH."
    )
    if LOGGING_AVAILABLE:
        log_tagged_event(
            "context_browser_import_error",
            msg,
            omnitag={"purpose": "import_error", "module": "repository_analyzer"},
            megatag={"type": "ToolHook", "context": "ContextBrowser"},
        )
    raise ImportError(msg) from e


class ContextBrowserApp(QtWidgets.QMainWindow):
    """PyQt5-based context browser for KILO-FOOLISH.

    - Integrates modular logging, tagging, and context propagation.
    - All actions are logged and tagged for traceability.
    - Robust error handling and feedback per project philosophy.
    """

    def __init__(self) -> None:
        """Initialize ContextBrowserApp."""
        super().__init__()
        self.setWindowTitle("KILO-FOOLISH Context Browser")
        self.setGeometry(100, 100, 1200, 800)
        self.analyzer = None
        self.dataframes = {}
        self.session_omnitag = (
            OmniTag(
                purpose="ContextBrowserSession",
                dependencies=["RepositoryCompendium", "PyQt5", "Plotly"],
                context="interactive_analysis",
                evolution_stage="Φ.3.1",
            )
            if BRIDGE_AVAILABLE
            else None
        )
        self.session_megatag = (
            MegaTag(
                tag_type="ToolHook",
                associated_data={"description": "Interactive Context Browser Session"},
                creation_timestamp=str(datetime.now()),
                last_updated=str(datetime.now()),
            )
            if BRIDGE_AVAILABLE
            else None
        )
        self._init_ui()
        if LOGGING_AVAILABLE:
            log_tagged_event(
                "context_browser_start",
                "Session started (PyQt5)",
                omnitag=self.session_omnitag.to_dict() if self.session_omnitag else {},
                megatag=self.session_megatag.to_dict() if self.session_megatag else {},
            )

    def _init_ui(self) -> None:
        # Central widget and layout
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Repo path input and analyze button
        repo_layout = QtWidgets.QHBoxLayout()
        self.repo_path_input = QtWidgets.QLineEdit(".")
        self.analyze_btn = QtWidgets.QPushButton("Analyze Repository")
        self.analyze_btn.clicked.connect(self.analyze_repository)
        repo_layout.addWidget(QtWidgets.QLabel("Repository Path:"))
        repo_layout.addWidget(self.repo_path_input)
        repo_layout.addWidget(self.analyze_btn)
        layout.addLayout(repo_layout)

        # Export button
        self.export_btn = QtWidgets.QPushButton("Export Context Package")
        self.export_btn.clicked.connect(self.export_context_package)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)

        # Tabs for analysis
        self.tabs = QtWidgets.QTabWidget()
        self.overview_tab = QtWidgets.QWidget()
        self.files_tab = QtWidgets.QWidget()
        self.functions_tab = QtWidgets.QWidget()
        self.classes_tab = QtWidgets.QWidget()
        self.imports_tab = QtWidgets.QWidget()
        self.structure_tab = QtWidgets.QWidget()
        self.visual_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.overview_tab, "Overview")
        self.tabs.addTab(self.files_tab, "Files")
        self.tabs.addTab(self.functions_tab, "Functions")
        self.tabs.addTab(self.classes_tab, "Classes")
        self.tabs.addTab(self.imports_tab, "Imports")
        self.tabs.addTab(self.structure_tab, "Structure")
        self.tabs.addTab(self.visual_tab, "Visualizations")
        layout.addWidget(self.tabs)

        # Status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

    def analyze_repository(self) -> None:
        repo_path = self.repo_path_input.text().strip()
        self.status.showMessage("Analyzing repository...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self.analyzer = RepositoryCompendium(repo_path)
            self.dataframes = self.analyzer.analyze_repository()
            self.export_btn.setEnabled(True)
            self.status.showMessage("Analysis complete.")
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "context_browser_analysis",
                    f"Analyzed repository: {repo_path}",
                    omnitag=(self.session_omnitag.to_dict() if self.session_omnitag else {}),
                    megatag=(self.session_megatag.to_dict() if self.session_megatag else {}),
                )
            if BRIDGE_AVAILABLE and ENHANCED_BRIDGE:
                ENHANCED_BRIDGE.propagate_context(
                    context_type="repo_analysis",
                    context_data={
                        "repo_path": repo_path,
                        "timestamp": str(datetime.now()),
                    },
                )
            self._populate_tabs()
        except Exception as e:
            self.status.showMessage(f"Analysis failed: {e}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Analysis failed: {e}")
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "context_browser_error",
                    f"Analysis error: {e}",
                    omnitag=(self.session_omnitag.to_dict() if self.session_omnitag else {}),
                    megatag=(self.session_megatag.to_dict() if self.session_megatag else {}),
                )
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def export_context_package(self) -> None:
        if not self.analyzer:
            return
        try:
            output_path = self.analyzer.export_context_package()
            self.status.showMessage(f"Exported to: {output_path}")
            QtWidgets.QMessageBox.information(self, "Export", f"Exported to: {output_path}")
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "context_browser_export",
                    f"Exported context package: {output_path}",
                    omnitag=(self.session_omnitag.to_dict() if self.session_omnitag else {}),
                    megatag=(self.session_megatag.to_dict() if self.session_megatag else {}),
                )
        except Exception as e:
            self.status.showMessage(f"Export failed: {e}")
            QtWidgets.QMessageBox.critical(self, "Export Error", f"Export failed: {e}")
            if LOGGING_AVAILABLE:
                log_tagged_event(
                    "context_browser_error",
                    f"Export error: {e}",
                    omnitag=(self.session_omnitag.to_dict() if self.session_omnitag else {}),
                    megatag=(self.session_megatag.to_dict() if self.session_megatag else {}),
                )

    def _populate_tabs(self) -> None:
        # Overview Tab
        layout = QtWidgets.QVBoxLayout()
        if "metrics" in self.dataframes and not self.dataframes["metrics"].empty:
            metrics = self.dataframes["metrics"].iloc[0]
            overview_text = (
                f"Total Files: {metrics.get('total_files', 0):,}\n"
                f"Python Files: {metrics.get('python_files', 0):,}\n"
                f"Lines of Code: {metrics.get('total_lines', 0):,}\n"
                f"Functions: {metrics.get('total_functions', 0):,}\n"
                f"Classes: {metrics.get('total_classes', 0):,}\n"
                f"Size (KB): {metrics.get('total_size_kb', 0):.1f}\n"
                f"Avg Complexity: {metrics.get('avg_function_complexity', 0):.1f}\n"
                f"Max Depth: {metrics.get('deepest_directory_level', 0)}"
            )
            label = QtWidgets.QLabel(overview_text)
            layout.addWidget(label)
        self._set_tab_layout(self.overview_tab, layout)

        # Files Tab
        self._populate_table_tab(self.files_tab, "files")
        self._populate_table_tab(self.functions_tab, "functions")
        self._populate_table_tab(self.classes_tab, "classes")
        self._populate_table_tab(self.imports_tab, "imports")
        self._populate_table_tab(self.structure_tab, "structure")
        self._populate_table_tab(
            self.visual_tab, "files"
        )  # Example: show files table in visual tab

    def _populate_table_tab(self, tab, key) -> None:
        layout = QtWidgets.QVBoxLayout()
        if key in self.dataframes and not self.dataframes[key].empty:
            df = self.dataframes[key]
            model = PandasTableModel(df)
            table = QtWidgets.QTableView()
            table.setModel(model)
            table.resizeColumnsToContents()
            layout.addWidget(table)
        else:
            layout.addWidget(QtWidgets.QLabel("No data available."))
        self._set_tab_layout(tab, layout)

    def _set_tab_layout(self, tab, layout) -> None:
        # Remove old layout if exists
        old_layout = tab.layout()
        if old_layout:
            QtWidgets.QWidget().setLayout(old_layout)
        tab.setLayout(layout)


class PandasTableModel(QtCore.QAbstractTableModel):
    def __init__(self, df: pd.DataFrame) -> None:
        """Initialize PandasTableModel with df."""
        super().__init__()
        self._df = df

    def rowCount(self, _parent=None) -> None:
        return self._df.shape[0]

    def columnCount(self, _parent=None) -> None:
        return self._df.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole) -> None:
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            value = self._df.iloc[index.row(), index.column()]
            return str(value)
        return None

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole) -> None:
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self._df.columns[section])
            return str(self._df.index[section])
        return None


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = ContextBrowserApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if LOGGING_AVAILABLE:
        log_tagged_event(
            "context_browser_main",
            "ContextBrowser main entrypoint invoked (PyQt5)",
            omnitag={"purpose": "main_entrypoint"},
            megatag={"type": "ToolHook", "context": "ContextBrowser"},
        )
    try:
        main()
    except Exception as e:
        if LOGGING_AVAILABLE:
            log_tagged_event(
                "context_browser_fatal_error",
                f"Fatal error: {e}",
                omnitag={"purpose": "fatal_error"},
                megatag={"type": "ToolHook", "context": "ContextBrowser"},
            )
        raise
