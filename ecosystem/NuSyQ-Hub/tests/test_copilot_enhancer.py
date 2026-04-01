from pathlib import Path

from src.copilot.copilot_workspace_enhancer import CopilotWorkspaceEnhancer


def test_enhance_workspace_minimal(tmp_path: Path):
    # Create minimal workspace structure
    (tmp_path / "src" / "ai").mkdir(parents=True, exist_ok=True)
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    enhancer = CopilotWorkspaceEnhancer(tmp_path)
    enhancer.analyze_workspace_structure()
    assert isinstance(enhancer.workspace_context, dict)
