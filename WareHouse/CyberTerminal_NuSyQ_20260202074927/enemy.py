"""
Enemy class represents enemy characters in the game.
Handles enemy behavior and rendering.
"""
import pygame
class Enemy:
    def __init__(self, game):
        self.game = game
        self.image = pygame.Surface((50, 50))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(center=(200, 300))
    def update(self):
        # Basic enemy movement logic
        self.rect.x += 1
    def render(self, screen):
        screen.blit(self.image, self.rect)