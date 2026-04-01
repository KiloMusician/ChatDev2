import pytest
from src.consciousness.floor_5_integration import Floor5Integration, IntegrationPattern


@pytest.fixture()
def floor5() -> Floor5Integration:
    return Floor5Integration()


def test_validate_domain_pair_unknown(floor5: Floor5Integration) -> None:
    assert not floor5.validate_domain_pair("unknown_a", "unknown_b")


def test_integrate_known_domains_records_history(floor5: Floor5Integration) -> None:
    insight = floor5.integrate("consciousness", "game_systems", IntegrationPattern.CROSS_DOMAIN)

    assert insight is not None
    assert set(insight.source_domains) == {"consciousness", "game_systems"}
    assert floor5.integration_history, "integration history should record successful syntheses"


def test_get_synthesis_recommendations_gates_by_consciousness(floor5: Floor5Integration) -> None:
    gated = floor5.get_synthesis_recommendations(current_consciousness=10.0)
    assert gated[0].startswith("⚠️ Floor 5 requires")

    unlocked = floor5.get_synthesis_recommendations(current_consciousness=20.0)
    assert any("Integration" in line for line in unlocked)
