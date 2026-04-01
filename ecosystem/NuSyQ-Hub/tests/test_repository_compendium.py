"""OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import os

import pandas as pd
from src.analysis.repository_analyzer import RepositoryCompendium


def test_analyze_repository_returns_expected_keys(tmp_path):
    # Setup a temporary repo with a simple Python file
    file_py = tmp_path / "test_file.py"
    file_py.write_text(
        """
# sample python file
def foo():
    return 42
""",
        encoding="utf-8",
    )

    comp = RepositoryCompendium(tmp_path)
    result = comp.analyze_repository()

    # Should return a dict with DataFrame values
    expected_keys = {"metrics", "files", "functions", "classes", "imports", "structure"}
    assert isinstance(result, dict)
    assert set(result.keys()) == expected_keys

    # Each entry should be a pandas DataFrame
    for key, df in result.items():
        assert isinstance(df, pd.DataFrame), f"{key} is not a DataFrame"

    # Check metrics dataframe has required columns
    metrics_cols = {
        "total_files",
        "python_files",
        "total_lines",
        "total_functions",
        "total_size_kb",
        "total_classes",
        "avg_lines_per_function",
        "deepest_directory_level",
    }
    assert metrics_cols.issubset(result["metrics"].columns)

    # Check files dataframe includes our test file
    files_df = result["files"]
    assert any(
        "test_file.py" in fp for fp in files_df["file_path"]
    ), "test_file.py not found in files"


def test_export_context_package_creates_zip(tmp_path):
    # Create a simple directory structure
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "a.txt").write_text("contents")

    comp = RepositoryCompendium(tmp_path)
    archive_path = comp.export_context_package(output_name="mypkg")

    # Archive should exist and end with .zip
    assert archive_path.endswith("mypkg.zip")
    assert os.path.isfile(archive_path)

    # Ensure zip archive contains the file
    import zipfile

    with zipfile.ZipFile(archive_path, "r") as z:
        namelist = z.namelist()
        assert any("subdir/a.txt" in name or "subdir\\a.txt" in name for name in namelist)
