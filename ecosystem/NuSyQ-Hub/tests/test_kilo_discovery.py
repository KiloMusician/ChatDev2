"""Unit tests for the KILO discovery system (basic smoke tests)."""

from pathlib import Path

from src.tools.kilo_discovery_system import create_discovery_system


def test_basic_discovery_and_index(tmp_path: Path):
    """Create a small repo and validate discovery and indexing."""
    # Create a temporary repo structure
    repo = tmp_path / "repo"
    repo.mkdir()

    # Create a simple coordinator python file
    coord_file = repo / "ai_coordinator.py"
    coord_file.write_text('''"""Module docstring for coordinator

OmniTag: {
    "purpose": "Test coordinator",
}
"""

class TestCoordinator:
    """Class docstring with MegaTag: {"type": "Coordinator"}
    """

    def run(self):
        pass
''')

    # Create discovery system pointed at temp repo
    system = create_discovery_system(repo)

    # Run discovery for coordinators
    coords = system.discover_components_by_pattern("coordinators")
    assert isinstance(coords, list)
    assert any(c.name == "ai_coordinator" or c.name == "TestCoordinator" for c in coords)

    # Ensure tags were parsed
    found = False
    for c in coords:
        if c.name == "ai_coordinator" and getattr(c, "tags", {}):
            # Should have omni_purpose from module docstring
            assert "omni_purpose" in c.tags
            found = True
    assert found

    # Generate index
    index = system.generate_component_index()
    assert "components" in index
    assert index["metadata"]["total_files_scanned"] > 0

    # Cleanup index file
    idx_file = repo / "KILO_COMPONENT_INDEX.json"
    if idx_file.exists():
        idx_file.unlink()
