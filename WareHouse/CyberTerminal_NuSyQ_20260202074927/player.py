"""
Player class represents the player character in the game.
Handles player movement and rendering.
"""
import pygame
class Player:
    def __init__(self, game):
        self.game = game
        self.image = pygame.Surface((50, 50))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(400, 300))
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= 5
        if keys[pygame.K_RIGHT]:
            self.rect.x += 5
        if keys[pygame.K_UP]:
            self.rect.y -= 5
        if keys[pygame.K_DOWN]:
            self.rect.y += 5
    def render(self, screen):
        screen.blit(self.image, self.rect)