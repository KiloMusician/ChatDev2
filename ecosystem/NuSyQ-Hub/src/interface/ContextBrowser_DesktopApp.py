"""🖥️ Enhanced Context Browser - Native Desktop App.

A native tkinter-based version that runs as a true desktop application.
"""

import contextlib
import os
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.stubs.repository_compendium_stub import RepositoryCompendium

    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False

try:
    from config.service_config import ServiceConfig
except ImportError:  # pragma: no cover - fallback for zipped/bundled runs
    ServiceConfig = None


def _default_context_browser_url() -> str:
    """Compute a non-hardcoded fallback context browser URL."""
    env_base = os.environ.get("CONTEXT_BROWSER_BASE_URL") or os.environ.get("STREAMLIT_BASE_URL")
    if env_base:
        return env_base

    host = os.environ.get("CONTEXT_BROWSER_HOST") or os.environ.get(
        "STREAMLIT_HOST",
        "http://127.0.0.1",
    )
    port = os.environ.get("CONTEXT_BROWSER_PORT") or os.environ.get(
        "STREAMLIT_PORT",
        "8501",
    )
    return f"{host.rstrip('/')}:" + str(port)


class ContextBrowserApp:
    """Native desktop application for repository context browsing."""

    def __init__(self) -> None:
        """Initialize ContextBrowserApp."""
        self.root = tk.Tk()
        self.root.title("🔍 Enhanced Context Browser - Desktop App")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2b2b2b")

        # set app icon (if available)
        with contextlib.suppress(FileNotFoundError, OSError, tk.TclError):  # icon optional
            self.root.iconbitmap(default="icon.ico")

        # Data
        self.current_repo = None
        self.analysis_data: dict[str, Any] = {}
        self.streamlit_process = None
        self.context_browser_url = (
            ServiceConfig.get_context_browser_url()
            if ServiceConfig
            else _default_context_browser_url()
        )
        self.context_browser_host, self.context_browser_port = self._parse_context_browser_url(
            self.context_browser_url
        )

        self.setup_ui()
        self.setup_styles()

    def setup_styles(self) -> None:
        """Setup dark theme styles."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure dark theme
        style.configure("TLabel", background="#2b2b2b", foreground="#ffffff")
        style.configure("TButton", background="#404040", foreground="#ffffff")
        style.configure("TFrame", background="#2b2b2b")
        style.configure("TNotebook", background="#2b2b2b", foreground="#ffffff")
        style.configure("TNotebook.Tab", background="#404040", foreground="#ffffff")

    def setup_ui(self) -> None:
        """Setup the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_label = ttk.Label(
            header_frame,
            text="🔍 Enhanced Context Browser",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(side=tk.LEFT)

        # Repository selection
        repo_frame = ttk.Frame(header_frame)
        repo_frame.pack(side=tk.RIGHT)

        ttk.Label(repo_frame, text="Repository:").pack(side=tk.LEFT, padx=(0, 5))

        self.repo_var = tk.StringVar(value=str(Path.cwd()))
        self.repo_entry = ttk.Entry(repo_frame, textvariable=self.repo_var, width=50)
        self.repo_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(repo_frame, text="Browse", command=self.browse_repository).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(repo_frame, text="Analyze", command=self.analyze_repository).pack(side=tk.LEFT)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(action_frame, text="🚀 Launch Web App", command=self.launch_web_app).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(action_frame, text="📊 Quick Analysis", command=self.quick_analysis).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(action_frame, text="📜 View Logs", command=self.view_logs).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(action_frame, text="⚙️ Settings", command=self.show_settings).pack(side=tk.RIGHT)

        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Analysis tab
        self.analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_tab, text="📊 Analysis")
        self.setup_analysis_tab()

        # Files tab
        self.files_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.files_tab, text="📁 Files")
        self.setup_files_tab()

        # Logs tab
        self.logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.logs_tab, text="📜 Logs")
        self.setup_logs_tab()

        # Console tab
        self.console_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.console_tab, text="💻 Console")
        self.setup_console_tab()

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Select a repository to begin analysis")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def setup_analysis_tab(self) -> None:
        """Setup analysis results tab."""
        # Analysis summary
        summary_frame = ttk.LabelFrame(self.analysis_tab, text="📊 Analysis Summary")
        summary_frame.pack(fill=tk.X, padx=5, pady=5)

        self.summary_text = scrolledtext.ScrolledText(
            summary_frame,
            height=8,
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff",
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Metrics frame
        metrics_frame = ttk.LabelFrame(self.analysis_tab, text="📈 Key Metrics")
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create metrics display
        self.metrics_frame_inner = ttk.Frame(metrics_frame)
        self.metrics_frame_inner.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Initial metrics
        self.update_metrics_display({})

    def setup_files_tab(self) -> None:
        """Setup files browser tab."""
        # File tree
        tree_frame = ttk.Frame(self.files_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview for files
        columns = ("Type", "Size", "Lines", "Health")
        self.file_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")

        # Configure columns
        self.file_tree.heading("#0", text="File Path")
        self.file_tree.heading("Type", text="Type")
        self.file_tree.heading("Size", text="Size (KB)")
        self.file_tree.heading("Lines", text="Lines")
        self.file_tree.heading("Health", text="Health Score")

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)

        self.file_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack components
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_logs_tab(self) -> None:
        """Setup logs viewer tab."""
        logs_control_frame = ttk.Frame(self.logs_tab)
        logs_control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(logs_control_frame, text="Log File:").pack(side=tk.LEFT)

        self.log_file_var = tk.StringVar(value="file_organization_audit.log")
        log_combo = ttk.Combobox(
            logs_control_frame,
            textvariable=self.log_file_var,
            values=[
                "file_organization_audit.log",
                "import_health_check.log",
                "logs/ollama_integration.log",
                "logs/chatdev_integration.log",
            ],
        )
        log_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        ttk.Button(logs_control_frame, text="🔄 Refresh", command=self.refresh_logs).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # Log display
        self.log_display = scrolledtext.ScrolledText(
            self.logs_tab,
            bg="#1e1e1e",
            fg="#00ff00",  # Green text for terminal feel
            insertbackground="#ffffff",
            font=("Consolas", 9),
        )
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def setup_console_tab(self) -> None:
        """Setup interactive console tab."""
        # Command input
        cmd_frame = ttk.Frame(self.console_tab)
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(cmd_frame, text="Command:").pack(side=tk.LEFT)

        self.cmd_var = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_frame, textvariable=self.cmd_var)
        cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        cmd_entry.bind("<Return>", self.execute_command)

        ttk.Button(cmd_frame, text="Execute", command=self.execute_command).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        # Output display
        self.console_output = scrolledtext.ScrolledText(
            self.console_tab,
            bg="#0c0c0c",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=("Consolas", 10),
        )
        self.console_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Welcome message
        self.console_output.insert(tk.END, "🖥️ Enhanced Context Browser Console\n")
        self.console_output.insert(tk.END, "=" * 50 + "\n")
        self.console_output.insert(tk.END, "Available commands:\n")
        self.console_output.insert(tk.END, "  analyze <path>    - Analyze repository\n")
        self.console_output.insert(tk.END, "  launch-web        - Launch web interface\n")
        self.console_output.insert(tk.END, "  clear             - Clear console\n")
        self.console_output.insert(tk.END, "  help              - Show this help\n\n")

    def browse_repository(self) -> None:
        """Browse for repository folder."""
        folder = filedialog.askdirectory(title="Select Repository Folder")
        if folder:
            self.repo_var.set(folder)

    def analyze_repository(self) -> None:
        """Analyze the selected repository."""
        repo_path = self.repo_var.get()
        if not repo_path or not Path(repo_path).exists():
            messagebox.showerror("Error", "Please select a valid repository path")
            return

        self.status_var.set("Analyzing repository...")

        def run_analysis() -> None:
            try:
                if ANALYSIS_AVAILABLE:
                    analyzer = RepositoryCompendium(repo_path)
                    self.analysis_data = analyzer.analyze_repository()

                    # Update UI in main thread
                    self.root.after(0, self.update_analysis_display)
                else:
                    # Fallback analysis
                    self.analysis_data = self.basic_file_analysis(repo_path)
                    self.root.after(0, self.update_analysis_display)

            except Exception as e:
                self.root.after(0, lambda err=e: messagebox.showerror("Analysis Error", str(err)))
                self.root.after(0, lambda: self.status_var.set("Analysis failed"))

        # Run analysis in background thread
        threading.Thread(target=run_analysis, daemon=True).start()

    def basic_file_analysis(self, repo_path) -> None:
        """Basic file analysis when advanced analysis isn't available."""
        repo_path = Path(repo_path)
        files_data: list[Any] = []
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    files_data.append(
                        {
                            "file_path": str(file_path.relative_to(repo_path)),
                            "file_type": file_path.suffix.lstrip(".") or "unknown",
                            "size_kb": stat.st_size / 1024,
                            "line_count": (
                                self.count_lines(file_path)
                                if file_path.suffix in [".py", ".js", ".ts", ".md"]
                                else 0
                            ),
                        }
                    )
                except (OSError, PermissionError):
                    continue

        import pandas as pd

        return {
            "files": pd.DataFrame(files_data),
            "metrics": pd.DataFrame(
                [
                    {
                        "total_files": len(files_data),
                        "total_size_kb": sum(f["size_kb"] for f in files_data),
                        "python_files": len([f for f in files_data if f["file_type"] == "py"]),
                    }
                ]
            ),
        }

    def count_lines(self, file_path) -> None:
        """Count lines in a text file."""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return len(f.readlines())
        except (FileNotFoundError, UnicodeDecodeError, OSError):
            return 0

    def update_analysis_display(self) -> None:
        """Update the analysis display with new data."""
        self.status_var.set("Analysis complete")

        # Update summary
        self.summary_text.delete(1.0, tk.END)

        if "metrics" in self.analysis_data and not self.analysis_data["metrics"].empty:
            metrics = self.analysis_data["metrics"].iloc[0]
            summary = f"""🔍 Repository Analysis Complete

📊 Summary:
• Total Files: {metrics.get("total_files", "N/A")}
• Python Files: {metrics.get("python_files", "N/A")}
• Total Size: {metrics.get("total_size_kb", 0):.1f} KB
• Lines of Code: {metrics.get("total_lines", "N/A")}

✅ Analysis completed successfully!
Use the tabs above to explore different aspects of your repository.
"""
            self.summary_text.insert(tk.END, summary)

            # Update metrics display
            self.update_metrics_display(metrics)

        # Update file tree
        self.update_file_tree()

    def update_metrics_display(self, metrics) -> None:
        """Update the metrics display."""
        # Clear existing metrics
        for widget in self.metrics_frame_inner.winfo_children():
            widget.destroy()

        # Create metric cards
        metrics_list = [
            ("📁 Files", metrics.get("total_files", 0)),
            ("🐍 Python", metrics.get("python_files", 0)),
            ("📏 Lines", metrics.get("total_lines", 0)),
            ("💾 Size KB", f"{metrics.get('total_size_kb', 0):.1f}"),
        ]

        for i, (label, value) in enumerate(metrics_list):
            frame = ttk.Frame(self.metrics_frame_inner)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

            ttk.Label(frame, text=label, font=("Arial", 10, "bold")).pack()
            ttk.Label(frame, text=str(value), font=("Arial", 14)).pack()

        # Configure grid weights
        for i in range(len(metrics_list)):
            self.metrics_frame_inner.columnconfigure(i, weight=1)

    def update_file_tree(self) -> None:
        """Update the file tree with analysis data."""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if "files" in self.analysis_data and not self.analysis_data["files"].empty:
            files_df = self.analysis_data["files"]

            for _, row in files_df.iterrows():
                file_path = row.get("file_path", "")
                file_type = row.get("file_type", "unknown")
                size_kb = f"{row.get('size_kb', 0):.1f}"
                line_count = row.get("line_count", 0)
                health_score = (
                    f"{row.get('health_score', 85):.0f}%" if "health_score" in row else "85%"
                )

                self.file_tree.insert(
                    "",
                    tk.END,
                    text=file_path,
                    values=(file_type, size_kb, line_count, health_score),
                )

    def launch_web_app(self) -> None:
        """Launch the Streamlit web interface."""
        app_path = Path(__file__).parent / "Enhanced-Interactive-Context-Browser-Fixed.py"

        if self.streamlit_process and self.streamlit_process.poll() is None:
            messagebox.showinfo("Info", "Web app is already running!")
            if os.environ.get("NUSYQ_CONTEXT_BROWSER_AUTO_OPEN", "1").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }:
                webbrowser.open(self.context_browser_url)
            return

        try:
            # Launch Streamlit
            cmd = [
                "streamlit",
                "run",
                str(app_path),
                "--server.headless=false",
                "--browser.gatherUsageStats=false",
                "--theme.base=dark",
                f"--server.address={self.context_browser_host}",
                f"--server.port={self.context_browser_port}",
            ]

            self.streamlit_process = subprocess.Popen(cmd)
            self.status_var.set("Web app launched - opening browser...")

            # Open browser after a short delay (configurable via env var)
            if os.environ.get("NUSYQ_CONTEXT_BROWSER_AUTO_OPEN", "1").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }:
                self.root.after(3000, lambda: webbrowser.open(self.context_browser_url))

        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch web app: {e}")

    def quick_analysis(self) -> None:
        """Run quick analysis."""
        repo_path = self.repo_var.get()
        if repo_path:
            self.analyze_repository()
        else:
            messagebox.showwarning("Warning", "Please select a repository first")

    @staticmethod
    def _parse_context_browser_url(url: str) -> tuple[str, int]:
        """Return (host, port) tuple for the configured context browser URL."""
        parsed = urlparse(url if "://" in url else f"http://{url}")
        host = parsed.hostname or "localhost"
        port = parsed.port or 8501
        return host, port

    def view_logs(self) -> None:
        """Switch to logs tab and refresh."""
        self.notebook.select(self.logs_tab)
        self.refresh_logs()

    def refresh_logs(self) -> None:
        """Refresh the log display."""
        log_file = self.log_file_var.get()
        repo_path = Path(self.repo_var.get()) if self.repo_var.get() else Path.cwd()
        log_path = repo_path / log_file

        self.log_display.delete(1.0, tk.END)

        if log_path.exists():
            try:
                with open(log_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    self.log_display.insert(tk.END, content)
                    # Scroll to bottom
                    self.log_display.see(tk.END)
            except Exception as e:
                self.log_display.insert(tk.END, f"Error reading log: {e}")
        else:
            self.log_display.insert(tk.END, f"Log file not found: {log_path}")

    def execute_command(self, _event=None) -> None:
        """Execute command in console."""
        command = self.cmd_var.get().strip()
        if not command:
            return

        # Clear input
        self.cmd_var.set("")

        # Show command
        self.console_output.insert(tk.END, f"> {command}\n")

        # Execute command
        if command == "clear":
            self.console_output.delete(1.0, tk.END)
        elif command == "help":
            help_text = """Available commands:
  analyze <path>    - Analyze repository at path
  launch-web        - Launch web interface
  clear             - Clear console
  help              - Show this help

"""
            self.console_output.insert(tk.END, help_text)
        elif command == "launch-web":
            self.launch_web_app()
            self.console_output.insert(tk.END, "Launching web interface...\n")
        elif command.startswith("analyze "):
            path = command[8:].strip()
            if path:
                self.repo_var.set(path)
                self.analyze_repository()
                self.console_output.insert(tk.END, f"Analyzing {path}...\n")
            else:
                self.console_output.insert(tk.END, "Usage: analyze <path>\n")
        else:
            self.console_output.insert(tk.END, f"Unknown command: {command}\n")

        # Scroll to bottom
        self.console_output.see(tk.END)

    def show_settings(self) -> None:
        """Show settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg="#2b2b2b")

        ttk.Label(
            settings_window,
            text="⚙️ Enhanced Context Browser Settings",
            font=("Arial", 12, "bold"),
        ).pack(pady=10)

        # Theme setting
        theme_frame = ttk.LabelFrame(settings_window, text="Appearance")
        theme_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        theme_combo = ttk.Combobox(theme_frame, values=["Dark", "Light"], state="readonly")
        theme_combo.set("Dark")
        theme_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Analysis settings
        analysis_frame = ttk.LabelFrame(settings_window, text="Analysis")
        analysis_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(analysis_frame, text="Enable syntax analysis").grid(
            row=0, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Checkbutton(analysis_frame, text="Enable import checking").grid(
            row=1, column=0, sticky="w", padx=5, pady=2
        )
        ttk.Checkbutton(analysis_frame, text="Generate intelligent tags").grid(
            row=2, column=0, sticky="w", padx=5, pady=2
        )

        # Buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Save", command=settings_window.destroy).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT)

    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()

        # Cleanup
        if self.streamlit_process and self.streamlit_process.poll() is None:
            self.streamlit_process.terminate()


def main() -> None:
    """Main function."""
    app = ContextBrowserApp()
    app.run()


if __name__ == "__main__":
    main()
