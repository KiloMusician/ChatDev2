#!/usr/bin/env python3
"""Utility Functions.

AI-Enhanced Helper Functions.
"""

import math

import pygame


def distance(pos1: tuple[int, int], pos2: tuple[int, int]) -> float:
    """Calculate distance between two points."""
    return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(value, max_val))


def load_image(path: str, scale: float = 1.0) -> pygame.Surface:
    """Load and scale image."""
    try:
        image = pygame.image.load(path)
        if scale != 1.0:
            width = int(image.get_width() * scale)
            height = int(image.get_height() * scale)
            image = pygame.transform.scale(image, (width, height))
        return image
    except pygame.error:
        # Create placeholder if image not found
        surface = pygame.Surface((32, 32))
        surface.fill((255, 0, 255))  # Magenta placeholder
        return surface
