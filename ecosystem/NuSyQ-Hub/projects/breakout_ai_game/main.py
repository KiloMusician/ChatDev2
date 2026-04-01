import sys

import pygame

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 100, 20
BALL_SIZE = 20
BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_PADDING = 10
BRICK_OFFSET_X = 30
BRICK_OFFSET_Y = 30

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout Game")

# Paddle and ball settings
paddle_x = WIDTH // 2 - PADDLE_WIDTH // 2
paddle_y = HEIGHT - PADDLE_HEIGHT - 10
paddle_speed = 5

ball_x = WIDTH // 2 - BALL_SIZE // 2
ball_y = HEIGHT // 2 - BALL_SIZE // 2
ball_speed_x = 3
ball_speed_y = 3

# Bricks setup
bricks = []
for row in range(BRICK_ROWS):
    for col in range(BRICK_COLS):
        brick = pygame.Rect(
            BRICK_OFFSET_X + (BRICK_PADDING + BALL_SIZE) * col,
            BRICK_OFFSET_Y + (BRICK_PADDING + BALL_SIZE) * row,
            BALL_SIZE,
            BALL_SIZE,
        )
        bricks.append(brick)

# Game loop
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Get keys pressed
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle_x > 0:
        paddle_x -= paddle_speed
    if keys[pygame.K_RIGHT] and paddle_x < WIDTH - PADDLE_WIDTH:
        paddle_x += paddle_speed

    # Move ball
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # Ball collision with walls
    if ball_x <= 0 or ball_x >= WIDTH - BALL_SIZE:
        ball_speed_x = -ball_speed_x
    if ball_y <= 0:
        ball_speed_y = -ball_speed_y

    # Ball collision with paddle
    ball_rect = pygame.Rect(ball_x, ball_y, BALL_SIZE, BALL_SIZE)
    paddle_rect = pygame.Rect(paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
    if ball_rect.colliderect(paddle_rect):
        ball_speed_y = -ball_speed_y

    # Ball collision with bricks
    for brick in bricks[:]:
        if brick.colliderect(ball_rect):
            bricks.remove(brick)
            ball_speed_y = -ball_speed_y

    # Clear screen
    screen.fill(BLACK)

    # Draw paddle, ball, and bricks
    pygame.draw.rect(screen, WHITE, (paddle_x, paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.ellipse(screen, WHITE, (ball_x, ball_y, BALL_SIZE, BALL_SIZE))
    for brick in bricks:
        pygame.draw.rect(screen, RED, brick)

    # Update display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)
