'''Placeholder sprite registry for pvz_THUNLPDemo_2024.'''

from __future__ import annotations

from typing import Callable, Dict, Tuple

from entities import PlantType, ZombieType

SpriteResult = Tuple[str, Tuple[object, ...], Dict[str, object]]


def make_sprite_stub(name: str) -> Callable[..., SpriteResult]:
    '''Return a lightweight draw function reporting the sprite identity.'''

    def draw_stub(*args: object, **kwargs: object) -> SpriteResult:
        return name, args, kwargs

    return draw_stub


PLANT_DRAWINGS: Dict[PlantType, Callable[..., SpriteResult]] = {
    PlantType.SUNFLOWER: make_sprite_stub('sunflower'),
    PlantType.PEASHOOTER: make_sprite_stub('peashooter'),
    PlantType.CHOMPER: make_sprite_stub('chomper'),
}

ZOMBIE_DRAWINGS: Dict[ZombieType, Callable[..., SpriteResult]] = {
    ZombieType.NORMAL: make_sprite_stub('normal_zombie'),
    ZombieType.NEWSPAPER: make_sprite_stub('newspaper_zombie'),
    ZombieType.DANCING: make_sprite_stub('dancing_zombie'),
}


def sprite_summary() -> Dict[str, Tuple[str, ...]]:
    '''Report which placeholders are registered for plants and zombies.'''
    plant_names = tuple(plant.name for plant in PLANT_DRAWINGS.keys())
    zombie_names = tuple(zombie.name for zombie in ZOMBIE_DRAWINGS.keys())
    return {
        'plants': plant_names,
        'zombies': zombie_names,
    }
