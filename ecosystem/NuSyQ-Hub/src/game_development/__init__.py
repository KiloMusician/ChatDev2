"""Game development pipeline and framework integration (ZETA21).

Provides PyGame/Arcade-based game development pipeline with AI-assisted
tooling, roguelike framework, and game object scaffolding.

OmniTag: {
    "purpose": "game_development_pipeline",
    "tags": ["Games", "Pipeline", "PyGame", "Arcade", "Roguelike"],
    "category": "game_systems",
    "evolution_stage": "v1.0"
}
"""

from .zeta21_game_pipeline import GameDevPipeline, initialize_game_dev_pipeline

__all__ = [
    "GameDevPipeline",
    "initialize_game_dev_pipeline",
]
