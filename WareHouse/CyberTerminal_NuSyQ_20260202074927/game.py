"""
Game class manages the game loop, state, and interactions between different components.
"""
import pygame
from player import Player
from enemy import Enemy
from level import Level
from ui_manager import UIManager
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = True
        self.player = Player(self)
        self.enemy = Enemy(self)
        self.level = Level(self)
        self.ui_manager = UIManager(self)
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # Add more event handling here
    def update(self):
        self.player.update()
        self.enemy.update()
        self.level.update()
        self.ui_manager.update()
    def render(self):
        self.screen.fill((0, 0, 0))
        self.level.render(self.screen)
        self.player.render(self.screen)
        self.enemy.render(self.screen)
        self.ui_manager.render(self.screen)
        pygame.display.flip()