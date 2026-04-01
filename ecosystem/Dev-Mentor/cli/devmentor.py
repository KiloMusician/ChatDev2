"""
DevMentor Replit Stack - CLI

This CLI is a *companion* to the VS Code-native repository core.
It wraps the same allow-listed scripts used by the Web UI.

Examples:
  python -m cli.devmentor status
  python -m cli.devmentor start
  python -m cli.devmentor export
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich import print
from rich.panel import Panel

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = REPO_ROOT
SCRIPTS_DIR = CORE_DIR / "scripts"
BOOTSTRAP_SCRIPT = SCRIPTS_DIR / "devmentor_bootstrap.py"

app = typer.Typer(add_completion=True, no_args_is_help=True)


def _run(cmd: list[str]) -> int:
    proc = subprocess.run(
        cmd,
        cwd=str(CORE_DIR),
        text=True,
        capture_output=True,  # nosec B603
    )
    out = ""
    if proc.stdout:
        out += proc.stdout
    if proc.stderr:
        out += ("\n" if out else "") + proc.stderr

    output = out if out.strip() else "(no output)"
    print(Panel.fit(output, title="DevMentor", border_style="cyan"))
    return proc.returncode


@app.command()
def status():
    """Show current DevMentor status."""
    return _run(["python", str(SCRIPTS_DIR / "devmentor_status.py")])


@app.command()
def start():
    """Start/resume the mentorship flow."""
    return _run([
        "python",
        str(BOOTSTRAP_SCRIPT),
        "start",
    ])


@app.command("next")
def next_step():
    """Advance to the next step (awards XP if applicable)."""
    return _run([
        "python",
        str(BOOTSTRAP_SCRIPT),
        "next",
    ])


@app.command()
def diagnose():
    """Run environment diagnostics."""
    return _run([
        "python",
        str(BOOTSTRAP_SCRIPT),
        "diagnose",
    ])


@app.command()
def validate():
    """Validate the current challenge."""
    return _run(["python", str(SCRIPTS_DIR / "devmentor_validate.py")])


@app.command()
def export():
    """Export a portable zip (Replit -> VS Code)."""
    return _run([
        "python",
        str(SCRIPTS_DIR / "devmentor_portable.py"),
        "export",
    ])


@app.command()
def import_zip(path: Path = typer.Argument(..., exists=True, dir_okay=False)):
    """Import a previously exported portable zip."""
    return _run([
        "python",
        str(SCRIPTS_DIR / "devmentor_portable.py"),
        "import",
        str(path),
    ])


@app.command()
def ops(
    command: str = typer.Argument(
        "all",
        help=(
            "Ops command: doctor, check, fix, prune, graph, report, all"
        ),
    ),
):
    """Run zero-token ops commands.

    Available: doctor, check, fix, prune, graph, report, all
    """
    return _run([
        "python",
        str(SCRIPTS_DIR / "devmentor_ops.py"),
        command,
    ])


@app.command()
def play(
    server: str = typer.Option("http://localhost:7337", "--server", "-s",
                               help="Game server URL"),
):
    """Play Terminal Depths in the terminal (connects to game server)."""
    try:
        from .play import run_cli
    except ImportError:
        repo_root = str(REPO_ROOT)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        from cli.play import run_cli
    run_cli(server)


@app.command()
def serve(host: str = "0.0.0.0", port: int = 7337):
    """Run the Web UI backend (FastAPI)."""
    from uvicorn import run
    run("app.backend.main:app", host=host, port=port, reload=False)


def main():
    app()


if __name__ == "__main__":
    main()
