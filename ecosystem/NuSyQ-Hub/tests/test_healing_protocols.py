from src.protocols.healing_protocols import (
    CulturalElement,
    KardeshevCivilization,
)


def test_optimize_and_restore_resource():
    civ = KardeshevCivilization()
    civ.resources = {"energy": 1000}
    civ.resource_priorities["energy"] = 1.5
    civ.resource_targets["energy"] = 800

    optimized = civ.optimize("energy", civ.resources["energy"])
    assert optimized <= 1000
    assert optimized >= 800

    civ.resources["energy"] = optimized
    restored = civ.restore("energy")
    assert restored <= civ.resource_targets["energy"]
    assert restored >= 0


def test_generate_ideas_and_apply():
    civ = KardeshevCivilization()
    civ.environment = {"energy": 100, "materials": 50}
    civ.technologies = civ.generate_new_ideas()

    for tech in civ.technologies:
        civ.environment = tech.apply(civ.environment)

    assert civ.environment["energy"] > 100
    assert civ.environment["materials"] >= 50


def test_cultural_element_evolves():
    element = CulturalElement("Art")
    assert not element.evolved
    element.evolve()
    assert element.evolved
    assert element.mood == "inspired"
