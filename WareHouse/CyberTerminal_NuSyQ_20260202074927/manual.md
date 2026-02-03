# CyberTerminal Game User Manual

This manual provides a detailed guide on how to install and use the CyberTerminal game. The game is developed using Python and Pygame and can be translated into GDScript for use in Godot.

## Introduction

CyberTerminal is a simple game where you control a player character that can move around the screen. An enemy moves towards the player, and a basic UI displays the score. This manual will guide you through setting up your environment, installing dependencies, and running the game.

## Main Functions of the Software

1. **Player Movement**: The player character can be moved using the arrow keys (Left, Right, Up, Down).
2. **Enemy Behavior**: An enemy moves towards the player.
3. **UI Display**: A basic UI shows the score.

## Installation and Setup

### Prerequisites

- Python 3.x installed on your system.
- Godot Engine installed for translating the game into GDScript (optional).

### Step-by-Step Guide

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/cyberterminal.git
   cd cyberterminal
   ```

2. **Install Dependencies**:
   Ensure you have `pip` installed, then run:
   ```bash
   pip install -r requirements.txt
   ```
   The `requirements.txt` file should contain the following dependencies:
   ```
   pygame==2.0.1
   pydantic==1.8.2
   pyyaml==5.4.1
   ```

3. **Run the Game**:
   Execute the main script to start the game:
   ```bash
   python main.py
   ```

## Running Tests

To ensure that the game functions correctly, you can run the provided unit tests:

```bash
python -m unittest discover tests
```

This command will execute all test cases defined in the `tests` directory.

## Translating to GDScript

If you want to translate this Python code into GDScript for use in Godot, follow these steps:

1. **Install Godot Engine**: Make sure you have Godot installed on your system.
2. **Create a New Project**: Open Godot and create a new project.
3. **Import Assets**: Import any assets (e.g., images) used in the game into your Godot project.
4. **Translate Code**: Manually translate the Python code into GDScript, ensuring that you follow Godot's scripting conventions.

### Example Translation

Here is an example of how to translate a simple class from Python to GDScript:

**Python (player.py)**
```python
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
```

**GDScript (Player.gd)**
```gdscript
extends Node2D

var game: Game

func _ready():
    $Sprite.texture = preload("res://path/to/player_texture.png")
    position = Vector2(400, 300)

func _process(delta):
    var velocity = Vector2.ZERO
    if Input.is_action_pressed("ui_left"):
        velocity.x -= 5
    if Input.is_action_pressed("ui_right"):
        velocity.x += 5
    if Input.is_action_pressed("ui_up"):
        velocity.y -= 5
    if Input.is_action_pressed("ui_down"):
        velocity.y += 5
    
    position += velocity * delta

func _draw():
    draw_rect(Rect2(position - Vector2(25, 25), Vector2(50, 50)), Color(1, 0, 0))
```

### Notes on Translation
- Ensure that Godot's input actions (`ui_left`, `ui_right`, etc.) are set up in the project settings.
- Replace hardcoded paths with Godot's resource system.

## Documentation

For more detailed information about the game's architecture and codebase, please refer to the following documentation:

- **Game Class**: Manages the game loop, state, and interactions between different components.
- **Player Class**: Represents the player character, handling movement and rendering.
- **Enemy Class**: Represents enemy characters, handling behavior and rendering.
- **Level Class**: Manages level generation, progression, and rendering.
- **UIManager Class**: Handles user interface elements such as score display.

## Conclusion

This manual provides a comprehensive guide to setting up and running the CyberTerminal game. Whether you are developing in Python or translating to GDScript for Godot, this guide should help you get started. If you encounter any issues or have questions, please refer to the documentation or seek support from the community.