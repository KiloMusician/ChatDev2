"""OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

from argparse import Namespace
from pathlib import Path

from copilot_agent_launcher import get_target_files


def test_resolves_to_src_for_simple_names():
    args = Namespace(all_changed=False, files=["__init__.py"])
    result = get_target_files(args)
    assert result == [str(Path("src") / "__init__.py")]


def test_explicit_root_preserved():
    args = Namespace(all_changed=False, files=["./README.md"])
    result = get_target_files(args)
    assert result == ["README.md"]


def test_new_file_auto_relocated_to_src():
    filename = "some_nonexistent_file.txt"
    # Ensure it doesn't exist in either location
    assert not Path(filename).exists()
    assert not (Path("src") / filename).exists()
    args = Namespace(all_changed=False, files=[filename])
    result = get_target_files(args)
    assert result == [str(Path("src") / filename)]
