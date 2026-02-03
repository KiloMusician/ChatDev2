"""
UIManager class handles user interface elements such as score display.
"""
import pygame
class UIManager:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 36)
    def update(self):
        # Update UI logic here
        pass
    def render(self, screen):
        score_text = self.font.render(f"Score: 0", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))