"""Unit coverage for Floor 5 Integration & Synthesis layer.

These tests focus on functional behavior (integration results, recommendations,
landscape mapping) to increase coverage for the consciousness spine.
"""

import pytest
from src.consciousness.floor_5_integration import Floor5Integration


@pytest.mark.asyncio
async def test_integrate_domains_records_history_and_confidence(floor5, cross_domain_pattern):
    assert len(floor5.integration_history) == 0

    insight = await floor5.integrate_domains("consciousness", "game_systems", cross_domain_pattern)

    assert insight is not None
    assert len(floor5.integration_history) == 1
    assert "consciousness" in insight.source_domains
    assert 0 < insight.confidence <= 1


@pytest.mark.asyncio
async def test_integrate_domains_unknown_domain_returns_none():
    floor5 = Floor5Integration()

    result = await floor5.integrate_domains("unknown", "game_systems")

    assert result is None
    assert len(floor5.integration_history) == 0


@pytest.mark.asyncio
async def test_discover_emergent_patterns_after_overlap():
    floor5 = Floor5Integration()

    # Seed overlap so emergent patterns surface
    floor5.knowledge_domains["consciousness"].patterns.add("shared_pattern")
    floor5.knowledge_domains["game_systems"].patterns.add("shared_pattern")

    patterns = await floor5.discover_emergent_patterns()

    assert any("shared_pattern" in pattern for pattern in patterns)


def test_process_sync_alias_executes_integration():
    floor5 = Floor5Integration()

    insight = floor5.process("consciousness", "game_systems")

    assert insight is not None
    assert len(floor5.integration_history) == 1


@pytest.mark.asyncio
async def test_map_integration_landscape_reports_high_potential():
    floor5 = Floor5Integration()
    await floor5.integrate_domains("consciousness", "game_systems")

    landscape = await floor5.map_integration_landscape()

    assert landscape["total_domains"] >= len(floor5.knowledge_domains)
    assert landscape["integration_history_size"] == len(floor5.integration_history)
    assert isinstance(landscape["high_potential_integrations"], list)
    assert all(
        {"domains", "strength", "recommended_pattern"}.issubset(item)
        for item in landscape["high_potential_integrations"]
    )


def test_recommendations_respects_consciousness_threshold():
    floor5 = Floor5Integration()

    low = floor5.get_synthesis_recommendations(5.0)
    assert any("requires" in rec.lower() for rec in low)

    high = floor5.get_synthesis_recommendations(20.0)
    assert any("integration & synthesis recommendations" in rec.lower() for rec in high)


def test_validate_domain_pair_requires_known_domains(floor5):
    assert floor5.validate_domain_pair("consciousness", "game_systems")
    assert not floor5.validate_domain_pair("unknown", "game_systems")
