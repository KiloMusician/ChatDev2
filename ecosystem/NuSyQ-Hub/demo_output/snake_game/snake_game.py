#!/usr/bin/env python3
"""Snake Game - AI Generated Demo"""

import random
import sys

import pygame

# Initialize pygame
pygame.init()

# Constants
GRID_SIZE = 20
CELL_SIZE = 20
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE
FPS = 10

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)


class Snake:
    def __init__(self):
        self.body = [(GRID_SIZE // 2, GRID_SIZE // 2)]
        self.direction = (1, 0)

    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % GRID_SIZE, (head_y + dy) % GRID_SIZE)
        self.body.insert(0, new_head)

    def grow(self):
        pass  # Don't remove tail

    def shrink(self):
        self.body.pop()

    def check_collision(self):
        head = self.body[0]
        return head in self.body[1:]


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game - AI Demo")
        self.clock = pygame.time.Clock()
        self.snake = Snake()
        self.food = self.spawn_food()
        self.score = 0
        self.running = True

    def spawn_food(self):
        while True:
            pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            if pos not in self.snake.body:
                return pos

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.snake.direction != (0, 1):
                    self.snake.direction = (0, -1)
                elif event.key == pygame.K_DOWN and self.snake.direction != (0, -1):
                    self.snake.direction = (0, 1)
                elif event.key == pygame.K_LEFT and self.snake.direction != (1, 0):
                    self.snake.direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0):
                    self.snake.direction = (1, 0)

    def update(self):
        self.snake.move()

        # Check food collision
        if self.snake.body[0] == self.food:
            self.snake.grow()
            self.food = self.spawn_food()
            self.score += 10
        else:
            self.snake.shrink()

        # Check self collision
        if self.snake.check_collision():
            self.running = False

    def draw(self):
        self.screen.fill(BLACK)

        # Draw snake
        for segment in self.snake.body:
            rect = pygame.Rect(segment[0] * CELL_SIZE, segment[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, GREEN, rect)

        # Draw food
        food_rect = pygame.Rect(
            self.food[0] * CELL_SIZE, self.food[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE
        )
        pygame.draw.rect(self.screen, RED, food_rect)

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
