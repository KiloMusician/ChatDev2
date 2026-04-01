"""Jupyter Notebook Executor - Programmatic notebook execution and orchestration.

This module provides capabilities for:
- Executing Jupyter notebooks programmatically
- Parameterized notebook runs
- Output extraction and analysis
- Notebook-driven workflows and pipelines
- Integration with agent orchestration

Use Cases:
- Data analysis automation
- Report generation
- Visual analytics
- Experiment tracking
- Model training workflows

OmniTag: jupyter_executor, notebook_automation, data_pipeline
MegaTag: JUPYTER_ORCHESTRATION, NOTEBOOK_AUTOMATION, DATA_WORKFLOWS
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class NotebookExecution:
    """Represents a notebook execution result."""

    notebook_path: str
    status: str  # success, failed, timeout
    output_path: str | None = None
    execution_time_seconds: float = 0.0
    cell_count: int = 0
    error_cells: list[int] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotebookPipeline:
    """Represents a pipeline of notebook executions."""

    pipeline_id: str
    name: str
    notebooks: list[str]
    parameters: dict[str, Any] = field(default_factory=dict)
    executions: list[NotebookExecution] = field(default_factory=list)
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class JupyterExecutor:
    """Orchestrates Jupyter notebook execution and workflows."""

    def __init__(self, notebooks_dir: Path | None = None) -> None:
        """Initialize JupyterExecutor with notebooks_dir."""
        self.notebooks_dir = notebooks_dir or Path(".")
        self.execution_history: list[NotebookExecution] = []
        self.pipelines: dict[str, NotebookPipeline] = {}

        # Check if nbconvert is available
        self.nbconvert_available = self._check_nbconvert()

        logger.info("📓 Jupyter Executor initialized")

    def _check_nbconvert(self) -> bool:
        """Check if jupyter nbconvert is available."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "jupyter", "nbconvert", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def discover_notebooks(
        self, pattern: str = "**/*.ipynb", exclude_checkpoints: bool = True
    ) -> list[Path]:
        """Discover Jupyter notebooks in the notebooks directory."""
        notebooks = list(self.notebooks_dir.glob(pattern))

        if exclude_checkpoints:
            notebooks = [nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)]

        logger.info(f"🔍 Discovered {len(notebooks)} notebooks")

        return notebooks

    def execute_notebook(
        self,
        notebook_path: Path | str,
        parameters: dict[str, Any] | None = None,
        output_path: Path | str | None = None,
        timeout: int = 300,
        kernel: str | None = None,
    ) -> NotebookExecution:
        """Execute a Jupyter notebook programmatically."""
        del parameters
        notebook_path = Path(notebook_path)

        if not notebook_path.exists():
            raise FileNotFoundError(f"Notebook not found: {notebook_path}")

        execution = NotebookExecution(notebook_path=str(notebook_path), status="running")

        start_time = datetime.now()

        try:
            # Determine output path
            if output_path is None:
                output_path = notebook_path.parent / f"{notebook_path.stem}_executed.ipynb"
            else:
                output_path = Path(output_path)

            # Build nbconvert command
            cmd = [
                sys.executable,
                "-m",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace" if output_path == notebook_path else "--output",
            ]

            if output_path != notebook_path:
                cmd.append(str(output_path))

            cmd.append(str(notebook_path))

            # Add kernel if specified
            if kernel:
                cmd.extend(["--ExecutePreprocessor.kernel_name", kernel])

            # Add timeout
            cmd.extend(["--ExecutePreprocessor.timeout", str(timeout)])

            # Execute notebook
            logger.info(f"▶️  Executing notebook: {notebook_path.name}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10,  # Add buffer to timeout
                check=False,
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            execution.execution_time_seconds = execution_time

            if result.returncode == 0:
                execution.status = "success"
                execution.output_path = str(output_path)

                # Extract outputs from executed notebook
                if output_path.exists():
                    execution.outputs = self._extract_notebook_outputs(output_path)
                    execution.cell_count = execution.outputs.get("cell_count", 0)

                logger.info(
                    f"✅ Notebook executed successfully in {execution_time:.2f}s: {notebook_path.name}"
                )

            else:
                execution.status = "failed"
                execution.error_messages.append(result.stderr)

                logger.error(f"❌ Notebook execution failed: {notebook_path.name}")
                logger.error(f"   Error: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            execution.status = "timeout"
            execution.error_messages.append(f"Execution exceeded {timeout}s timeout")

            logger.error(f"⏱️  Notebook execution timeout: {notebook_path.name}")

        except Exception as e:
            execution.status = "failed"
            execution.error_messages.append(str(e))

            logger.error(f"❌ Notebook execution error: {e}")

        self.execution_history.append(execution)

        return execution

    def execute_pipeline(
        self, pipeline: NotebookPipeline, stop_on_error: bool = True
    ) -> NotebookPipeline:
        """Execute a pipeline of notebooks in sequence."""
        pipeline.status = "running"

        logger.info(f"🔄 Executing pipeline: {pipeline.name} ({len(pipeline.notebooks)} notebooks)")

        for i, notebook_path in enumerate(pipeline.notebooks):
            logger.info(f"   Step {i + 1}/{len(pipeline.notebooks)}: {Path(notebook_path).name}")

            execution = self.execute_notebook(
                notebook_path=notebook_path, parameters=pipeline.parameters
            )

            pipeline.executions.append(execution)

            if execution.status != "success" and stop_on_error:
                pipeline.status = "failed"
                logger.error(f"❌ Pipeline failed at step {i + 1}")
                return pipeline

        pipeline.status = "completed"
        logger.info(f"✅ Pipeline completed: {pipeline.name}")

        return pipeline

    def create_pipeline(
        self,
        name: str,
        notebooks: list[str | Path],
        parameters: dict[str, Any] | None = None,
    ) -> NotebookPipeline:
        """Create a new notebook pipeline."""
        pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        pipeline = NotebookPipeline(
            pipeline_id=pipeline_id,
            name=name,
            notebooks=[str(nb) for nb in notebooks],
            parameters=parameters or {},
        )

        self.pipelines[pipeline_id] = pipeline

        logger.info(f"📋 Created pipeline: {name} ({len(notebooks)} notebooks)")

        return pipeline

    def _extract_notebook_outputs(self, notebook_path: Path) -> dict[str, Any]:
        """Extract outputs from an executed notebook."""
        try:
            with open(notebook_path, encoding="utf-8") as f:
                nb_data = json.load(f)

            cells = nb_data.get("cells", [])
            outputs = {
                "cell_count": len(cells),
                "code_cells": sum(1 for c in cells if c.get("cell_type") == "code"),
                "markdown_cells": sum(1 for c in cells if c.get("cell_type") == "markdown"),
                "outputs": [],
                "errors": [],
            }

            # Extract outputs and errors
            for i, cell in enumerate(cells):
                if cell.get("cell_type") != "code":
                    continue

                cell_outputs = cell.get("outputs", [])

                for output in cell_outputs:
                    output_type = output.get("output_type")

                    if output_type == "error":
                        outputs["errors"].append(
                            {
                                "cell_index": i,
                                "ename": output.get("ename"),
                                "evalue": output.get("evalue"),
                                "traceback": output.get("traceback", [])[:5],  # First 5 lines
                            }
                        )

                    elif output_type in ["execute_result", "display_data"]:
                        # Extract text/plain outputs
                        data = output.get("data", {})
                        if "text/plain" in data:
                            outputs["outputs"].append(
                                {
                                    "cell_index": i,
                                    "type": output_type,
                                    "text": data["text/plain"][:200],  # Truncate
                                }
                            )

            return outputs

        except Exception as e:
            logger.error(f"Error extracting notebook outputs: {e}")
            return {"error": str(e)}

    def get_execution_stats(self) -> dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.status == "success")
        failed = sum(1 for e in self.execution_history if e.status == "failed")
        timeout = sum(1 for e in self.execution_history if e.status == "timeout")

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "timeout": timeout,
            "success_rate": successful / total if total > 0 else 0,
            "average_duration": sum(e.execution_time_seconds for e in self.execution_history)
            / total,
            "total_duration": sum(e.execution_time_seconds for e in self.execution_history),
        }

    def get_pipeline_status(self, pipeline_id: str) -> NotebookPipeline | None:
        """Get status of a pipeline."""
        return self.pipelines.get(pipeline_id)

    def list_pipelines(self) -> list[NotebookPipeline]:
        """List all pipelines."""
        return list(self.pipelines.values())


# Global executor instance
_executor: JupyterExecutor | None = None


def get_jupyter_executor(notebooks_dir: Path | None = None) -> JupyterExecutor:
    """Get or create the global Jupyter executor."""
    global _executor
    if _executor is None:
        _executor = JupyterExecutor(notebooks_dir=notebooks_dir)
    return _executor
