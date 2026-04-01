#!/usr/bin/env python3
"""Code Generator - AI-powered code generation using Ollama models.

Generates complete, functional code files using specialized AI models.
Integrates with autonomous development agent for project generation.
"""

import logging
import time

from src.agents.adaptive_timeout_manager import get_timeout_manager
from src.ai.ollama_integration import KILOOllamaIntegration

logger = logging.getLogger(__name__)

# Model constants for flexible configuration
MODEL_QWEN_CODER_7B = "qwen2.5-coder:7b"
MODEL_QWEN_CODER_14B = "qwen2.5-coder:14b"
MODEL_CODELLAMA_7B = "codellama:7b"
MODEL_LLAMA3_8B = "llama3.1:8b"
MODEL_PHI3_5 = "phi3.5:latest"
MODEL_DEEPSEEK_16B = "deepseek-coder-v2:16b"


class CodeGenerator:
    """AI-powered code generator using Ollama models with adaptive timeouts."""

    def __init__(self, ollama_host: str | None = None) -> None:
        """Initialize code generator.

        Args:
            ollama_host: Optional Ollama API host URL
        """
        self.ollama = KILOOllamaIntegration(host=ollama_host)
        self.timeout_manager = get_timeout_manager()
        self.max_retries = 2  # Try alternative models if needed

        # Auto-select best available model based on system capabilities
        self.default_model = self._select_optimal_model()
        logger.info(f"🎯 Selected optimal model: {self.default_model}")

        # Model preferences per task type (can be configured)
        self.model_preferences = {
            "game_code": self.default_model,
            "webapp_backend": self.default_model,
            "webapp_frontend": self.default_model,
            "package_code": self.default_model,
            "requirements": self.default_model,
            "documentation": self.default_model,
            "tests": self.default_model,
        }

    def _select_optimal_model(self) -> str:
        """Auto-select best model based on available models and system RAM.

        Returns:
            Optimal model name
        """
        # Preferred models in priority order (code-focused, balanced size/performance)
        preferred_models = [
            MODEL_QWEN_CODER_7B,  # Best balance: code-focused, 4.4GB, modern
            MODEL_CODELLAMA_7B,  # Fallback: proven stable, 3.6GB
            MODEL_QWEN_CODER_14B,  # Powerful option if RAM allows, 8.4GB
            MODEL_LLAMA3_8B,  # General purpose fallback, 4.6GB
            MODEL_PHI3_5,  # Last resort (has memory issues)
        ]

        try:
            # Get available models from Ollama
            available = self.ollama.list_models()
            available_names = {
                str(m.get("name")) for m in available if isinstance(m, dict) and m.get("name")
            }

            # Find first available preferred model
            for model in preferred_models:
                if model in available_names:
                    logger.info(f"✅ Found optimal model: {model}")
                    return model

            # If none found, use first available model
            if available_names:
                fallback = next(iter(available_names))
                logger.warning(f"⚠️ Using fallback model: {fallback}")
                return fallback

        except (RuntimeError, ImportError) as e:
            logger.warning(f"Failed to query models: {e}")

        # Ultimate fallback
        return MODEL_CODELLAMA_7B

    def configure_model_preference(self, task_type: str, model: str) -> None:
        """Configure preferred model for a specific task type.

        Args:
            task_type: Type of task (game_code, webapp_backend, etc.)
            model: Model name to use for this task type
        """
        self.model_preferences[task_type] = model
        logger.info(f"Set {task_type} model preference to {model}")

    def get_model_for_task(self, task_type: str) -> str:
        """Get the best model for a task type.

        Args:
            task_type: Type of task

        Returns:
            Model name to use
        """
        # Use configured preference if available
        if task_type in self.model_preferences:
            return self.model_preferences[task_type]

        # Fall back to adaptive timeout manager recommendation
        try:
            model = self.timeout_manager.get_recommended_model(task_type)
            return model if isinstance(model, str) else self.default_model
        except RuntimeError:
            # Ultimate fallback to default model
            return self.default_model

    def generate_game(self, concept: str, complexity: str = "simple") -> dict[str, str]:
        """Generate complete game code files.

        Args:
            concept: Game concept description
            complexity: "simple", "medium", or "complex"

        Returns:
            Dictionary of filename -> code content
        """
        logger.info(f"🎮 Generating {complexity} game: {concept}")

        files: dict[str, str] = {}

        # Generate main game file
        main_prompt = f"""Generate a complete Python game: {concept}

Complexity: {complexity}
Requirements:
- Complete, runnable game
- Use pygame or built-in modules
- Include game loop, controls, scoring
- Add comments explaining code
- Handle window close event
- Keep it {complexity} but functional

Generate ONLY the Python code for main.py, no explanations."""

        main_code = self._generate_code(
            main_prompt, self.get_model_for_task("game_code"), complexity, "game_code"
        )
        if main_code:
            files["main.py"] = main_code

        # Generate requirements.txt
        requirements_prompt = f"""List Python package requirements for this game: {concept}

Game uses pygame or similar libraries.
Generate ONLY requirements.txt content, one package per line with versions."""

        requirements = self._generate_code(
            requirements_prompt,
            self.get_model_for_task("requirements"),
            "simple",
            "requirements",
        )
        if requirements:
            files["requirements.txt"] = requirements

        # Generate README
        readme_prompt = f"""Write a README.md for this game: {concept}

Include:
- Game description
- How to install
- How to run
- Controls
- Features

Keep it concise and clear."""

        readme = self._generate_code(
            readme_prompt,
            self.get_model_for_task("documentation"),
            "simple",
            "documentation",
        )
        if readme:
            files["README.md"] = readme

        # Generate Dockerfile
        dockerfile_content = self._generate_dockerfile_game()
        files["Dockerfile"] = dockerfile_content

        logger.info(f"✅ Generated {len(files)} files for game")
        return files

    def generate_webapp(self, description: str, framework: str = "fastapi") -> dict[str, str]:
        """Generate complete web application code.

        Args:
            description: Web app description
            framework: "fastapi", "flask", or "django"

        Returns:
            Dictionary of filename -> code content
        """
        logger.info(f"🌐 Generating {framework} web app: {description}")

        files: dict[str, str] = {}

        # Backend main file
        backend_prompt = f"""Generate a complete {framework} web application: {description}

Requirements:
- REST API with proper endpoints
- Error handling
- CORS enabled
- Database models (SQLite)
- Complete, runnable code
- Add comments

Generate ONLY the Python code for backend/main.py, no explanations."""

        backend_code = self._generate_code(
            backend_prompt, MODEL_QWEN_CODER_14B, "medium", "webapp_backend"
        )
        if backend_code:
            files["backend/main.py"] = backend_code

        # Frontend HTML
        frontend_prompt = f"""Generate an HTML frontend for: {description}

Requirements:
- Modern, responsive design
- JavaScript for API calls
- CSS styling
- Complete, working HTML file

Generate ONLY the HTML code for frontend/index.html."""

        frontend_code = self._generate_code(
            frontend_prompt, MODEL_QWEN_CODER_14B, "medium", "webapp_frontend"
        )
        if frontend_code:
            files["frontend/index.html"] = frontend_code

        # Requirements
        requirements_prompt = (
            f"List Python package requirements for {framework} app: {description}\n\n"
            f"Include {framework}, database, CORS, etc.\n"
            "Generate ONLY requirements.txt content."
        )

        requirements = self._generate_code(
            requirements_prompt, MODEL_QWEN_CODER_7B, "simple", "requirements"
        )
        if requirements:
            files["requirements.txt"] = requirements

        # README
        readme_prompt = f"""Write README.md for {framework} web app: {description}

Include installation, running, API endpoints, usage.
Keep it practical and clear."""

        readme = self._generate_code(
            readme_prompt,
            self.get_model_for_task("documentation"),
            "simple",
            "documentation",
        )
        if readme:
            files["README.md"] = readme

        # Docker setup
        files["Dockerfile"] = self._generate_dockerfile_webapp(framework)
        files["docker-compose.yml"] = self._generate_docker_compose_webapp()

        logger.info(f"✅ Generated {len(files)} files for web app")
        return files

    def generate_package(self, package_name: str, functionality: str) -> dict[str, str]:
        """Generate complete Python package.

        Args:
            package_name: Name of the package
            functionality: Description of package functionality

        Returns:
            Dictionary of filename -> code content
        """
        logger.info(f"📦 Generating package: {package_name}")

        files: dict[str, str] = {}

        # Main module
        module_prompt = f"""Generate a complete Python package: {package_name}

Functionality: {functionality}

Requirements:
- Clean, documented API
- Type hints
- Error handling
- Docstrings
- Complete implementation

Generate ONLY the Python code for {package_name}/__init__.py."""

        module_code = self._generate_code(
            module_prompt, MODEL_QWEN_CODER_14B, "medium", "package_code"
        )
        if module_code:
            files[f"{package_name}/__init__.py"] = module_code

        # Tests
        test_prompt = f"""Generate pytest tests for package: {package_name}

Functionality: {functionality}

Requirements:
- Comprehensive test coverage
- Unit tests
- Edge cases
- Clear test names

Generate ONLY the Python code for tests/test_{package_name}.py."""

        test_code = self._generate_code(
            test_prompt, MODEL_CODELLAMA_7B, "simple", "test_generation"
        )
        if test_code:
            files[f"tests/test_{package_name}.py"] = test_code

        # Setup.py
        setup_prompt = f"""Generate setup.py for Python package: {package_name}

Description: {functionality}

Include proper metadata, dependencies, classifiers.
Generate ONLY setup.py code."""

        setup_code = self._generate_code(
            setup_prompt, MODEL_QWEN_CODER_7B, "simple", "package_setup"
        )
        if setup_code:
            files["setup.py"] = setup_code

        # README
        readme_prompt = f"""Write README.md for Python package: {package_name}

Functionality: {functionality}

Include:
- Installation
- Usage examples
- API documentation
- License info"""

        readme = self._generate_code(
            readme_prompt,
            self.get_model_for_task("documentation"),
            "simple",
            "documentation",
        )
        if readme:
            files["README.md"] = readme

        # Requirements
        files["requirements.txt"] = "# Package requirements\npytest>=7.0.0\n"

        logger.info(f"✅ Generated {len(files)} files for package")
        return files

    def _generate_code(
        self,
        prompt: str,
        model: str,
        complexity: str = "simple",
        task_type: str = "code_generation",
    ) -> str | None:
        """Generate code using Ollama model with adaptive timeouts and retries.

        Args:
            prompt: Code generation prompt
            model: Ollama model to use
            complexity: Task complexity for timeout calculation
            task_type: Type of task for metrics tracking

        Returns:
            Generated code or None if failed
        """
        if not self.ollama.is_available():
            logger.warning("Ollama not available, using fallback")
            return self._generate_fallback(prompt)

        # Try with primary model first, then alternatives
        current_model = model
        for attempt in range(self.max_retries + 1):
            try:
                # Get adaptive timeout
                timeout_seconds = self.timeout_manager.get_timeout(
                    current_model, task_type, complexity
                )

                logger.info(
                    f"Attempt {attempt + 1}/{self.max_retries + 1}: "
                    f"Using {current_model} with {timeout_seconds:.0f}s timeout"
                )

                start_time = time.time()

                # Generate code
                import requests

                response = requests.post(
                    f"{self.ollama.host}/api/generate",
                    json={
                        "model": current_model,
                        "prompt": prompt,
                        "temperature": 0.2,
                        "stream": False,
                    },
                    timeout=timeout_seconds,
                ).json()

                duration = time.time() - start_time

                # Check for Ollama runner errors (common with large models)
                if response and "error" in response:
                    error_msg = response["error"]
                    logger.warning(f"Ollama error with {current_model}: {error_msg}")

                    # Record failed attempt
                    self.timeout_manager.record_attempt(current_model, task_type, duration, False)

                    # If runner crashed, don't retry this model
                    if "exit status" in error_msg or "terminated" in error_msg:
                        logger.warning(f"Model {current_model} unstable, skipping retries")
                        # Try smaller, more stable model immediately
                        if current_model != MODEL_PHI3_5:
                            logger.info(f"Falling back to {MODEL_PHI3_5} (stable model)")
                            current_model = MODEL_PHI3_5
                            continue

                    # Continue to next attempt or fallback
                    continue

                if response and "response" in response:
                    code = response["response"]

                    # Check if response is actually empty
                    if not code or code.strip() == "":
                        logger.warning(f"Empty response from {current_model}")
                        self.timeout_manager.record_attempt(
                            current_model, task_type, duration, False
                        )
                        continue

                    cleaned = self._clean_code(code)

                    # Record successful attempt
                    self.timeout_manager.record_attempt(current_model, task_type, duration, True)

                    logger.info(f"✅ Generated code with {current_model} in {duration:.1f}s")
                    return cleaned

                # Response but no content
                self.timeout_manager.record_attempt(current_model, task_type, duration, False)

                logger.warning(f"No valid response from {current_model}")

            except (RuntimeError, ConnectionError, OSError) as e:
                duration = time.time() - start_time if "start_time" in locals() else 0
                self.timeout_manager.record_attempt(current_model, task_type, duration, False)

                logger.warning(f"Error with {current_model} (attempt {attempt + 1}): {e}")

                # Check if we should retry with different model
                should_retry, alternative = self.timeout_manager.should_retry(
                    current_model, task_type, attempt
                )

                if should_retry and alternative and attempt < self.max_retries:
                    logger.info(f"Switching to alternative model: {alternative}")
                    current_model = alternative
                    continue

                # No more retries or no alternative
                if attempt >= self.max_retries:
                    logger.error(f"All {self.max_retries + 1} attempts failed")
                    return self._generate_fallback(prompt)

        return self._generate_fallback(prompt)

    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown code blocks.

        Args:
            code: Raw generated code

        Returns:
            Cleaned code
        """
        # Remove markdown code blocks
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            parts = code.split("```")
            if len(parts) >= 3:
                code = parts[1]

        return code.strip()

    def _generate_fallback(self, prompt: str) -> str:
        """Generate fallback code when AI is unavailable.

        Args:
            prompt: Original prompt

        Returns:
            Placeholder code
        """
        if "game" in prompt.lower():
            return '''#!/usr/bin/env python3
"""Simple Snake Game - Generated by NuSyQ-Hub AI System."""

import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Game Constants
WIDTH, HEIGHT = 640, 480
CELL_SIZE = 20
FPS = 10

# Colors
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

class SnakeGame:
    """Simple Snake game implementation."""

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Game - NuSyQ-Hub")
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self) -> None:
        """Reset game state."""
        self.snake = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = (CELL_SIZE, 0)
        self.food = self.spawn_food()
        self.score = 0
        self.game_over = False

    def spawn_food(self) -> None:
        """Spawn food at random position."""
        while True:
            food = (
                random.randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE,
                random.randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
            )
            if food not in self.snake:
                return food

    def handle_input(self) -> None:
        """Handle keyboard input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.direction != (0, CELL_SIZE):
                    self.direction = (0, -CELL_SIZE)
                elif event.key == pygame.K_DOWN and self.direction != (0, -CELL_SIZE):
                    self.direction = (0, CELL_SIZE)
                elif event.key == pygame.K_LEFT and self.direction != (CELL_SIZE, 0):
                    self.direction = (-CELL_SIZE, 0)
                elif event.key == pygame.K_RIGHT and self.direction != (-CELL_SIZE, 0):
                    self.direction = (CELL_SIZE, 0)
                elif event.key == pygame.K_SPACE and self.game_over:
                    self.reset()
        return True

    def update(self) -> None:
        """Update game state."""
        if self.game_over:
            return

        # Move snake
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        # Check collisions
        if (new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT or
            new_head in self.snake):
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        # Check food
        if new_head == self.food:
            self.score += 10
            self.food = self.spawn_food()
        else:
            self.snake.pop()

    def draw(self) -> None:
        """Draw game state."""
        self.screen.fill(BLACK)

        # Draw snake
        for segment in self.snake:
            pygame.draw.rect(self.screen, GREEN, (*segment, CELL_SIZE, CELL_SIZE))

        # Draw food
        pygame.draw.rect(self.screen, RED, (*self.food, CELL_SIZE, CELL_SIZE))

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Draw game over
        if self.game_over:
            game_over_text = font.render("GAME OVER! Press SPACE", True, RED)
            text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(game_over_text, text_rect)

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop."""
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()
'''
        elif "flask" in prompt.lower() or "fastapi" in prompt.lower():
            return '''#!/usr/bin/env python3
"""RESTful API Server - Generated by NuSyQ-Hub AI System."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Optional
import uvicorn

app = FastAPI(
    title="NuSyQ-Hub API",
    description="Generated API server with CRUD operations",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    quantity: int = 0

# In-memory storage
items_db: dict[int, Item] = {}
next_id = 1

@app.get("/")
def read_root() -> None:
    """Root endpoint with API information."""
    return {
        "message": "NuSyQ-Hub API Server",
        "version": "1.0.0",
        "endpoints": {
            "GET /items": "List all items",
            "GET /items/{id}": "Get item by ID",
            "POST /items": "Create new item",
            "PUT /items/{id}": "Update item",
            "DELETE /items/{id}": "Delete item"
        }
    }

@app.get("/health")
def health_check() -> None:
    """Health check endpoint."""
    return {"status": "healthy", "items_count": len(items_db)}

@app.get("/items")
def list_items() -> None:
    """Get all items."""
    return {"items": list(items_db.values()), "count": len(items_db)}

@app.get("/items/{item_id}")
def get_item(item_id: int) -> None:
    """Get item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.post("/items")
def create_item(item: Item) -> None:
    """Create new item."""
    global next_id
    item.id = next_id
    items_db[next_id] = item
    next_id += 1
    return {"message": "Item created", "item": item}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item) -> None:
    """Update existing item."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    item.id = item_id
    items_db[item_id] = item
    return {"message": "Item updated", "item": item}

@app.delete("/items/{item_id}")
def delete_item(item_id: int) -> None:
    """Delete item by ID."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    deleted_item = items_db.pop(item_id)
    return {"message": "Item deleted", "item": deleted_item}

if __name__ == "__main__":
    print("Starting NuSyQ-Hub API Server...")
    print("API docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
'''
        elif "test" in prompt.lower():
            return '''#!/usr/bin/env python3
"""Comprehensive Test Suite - Generated by NuSyQ-Hub AI System."""

import pytest
import sys
from typing import Any
from unittest.mock import Mock, patch, MagicMock


class TestBasicFunctionality:
    """Test basic functionality."""

    def test_sanity_check(self) -> None:
        """Verify test framework is working."""
        assert True
        assert 1 + 1 == 2

    def test_string_operations(self) -> None:
        """Test string operations."""
        test_str = "NuSyQ-Hub"
        assert test_str.lower() == "nusyq-hub"
        assert test_str.upper() == "NUSYQ-HUB"
        assert len(test_str) == 9

    def test_list_operations(self) -> None:
        """Test list operations."""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert sum(test_list) == 15
        assert max(test_list) == 5
        assert min(test_list) == 1


class TestDataStructures:
    """Test data structures."""

    def test_dict_operations(self) -> None:
        """Test dictionary operations."""
        test_dict = {"name": "NuSyQ", "version": "1.0"}
        assert test_dict["name"] == "NuSyQ"
        assert "version" in test_dict
        assert len(test_dict) == 2

    def test_set_operations(self) -> None:
        """Test set operations."""
        set1 = {1, 2, 3}
        set2 = {3, 4, 5}
        assert set1.union(set2) == {1, 2, 3, 4, 5}
        assert set1.intersection(set2) == {3}
        assert set1.difference(set2) == {1, 2}


class TestExceptionHandling:
    """Test exception handling."""

    def test_value_error(self) -> None:
        """Test ValueError is raised correctly."""
        with pytest.raises(ValueError):
            int("not a number")

    def test_key_error(self) -> None:
        """Test KeyError is raised correctly."""
        test_dict = {"key": "value"}
        with pytest.raises(KeyError):
            _ = test_dict["nonexistent"]

    def test_zero_division(self) -> None:
        """Test ZeroDivisionError is raised correctly."""
        with pytest.raises(ZeroDivisionError):
            _ = 1 / 0


class TestMocking:
    """Test mocking capabilities."""

    def test_mock_function(self) -> None:
        """Test function mocking."""
        mock_func = Mock(return_value=42)
        assert mock_func() == 42
        mock_func.assert_called_once()

    def test_mock_object(self) -> None:
        """Test object mocking."""
        mock_obj = MagicMock()
        mock_obj.method.return_value = "mocked"
        assert mock_obj.method() == "mocked"
        mock_obj.method.assert_called_once()

    @patch('sys.platform')
    def test_patch_decorator(self, mock_platform) -> None:
        """Test patching with decorator."""
        mock_platform.return_value = "test_platform"
        # Decorator patches sys.platform for this test


class TestParametrization:
    """Test parametrized tests."""

    @pytest.mark.parametrize("input_val,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
        (4, 8),
    ])
    def test_doubling(self, input_val: int, expected: int) -> None:
        """Test doubling function."""
        assert input_val * 2 == expected

    @pytest.mark.parametrize("value", [0, 1, 2, 5, 10])
    def test_positive_numbers(self, value: int) -> None:
        """Test positive number validation."""
        assert value >= 0


class TestFixtures:
    """Test fixtures."""

    @pytest.fixture
    def sample_data(self) -> None:
        """Provide sample data for tests."""
        return {"key1": "value1", "key2": "value2"}

    def test_fixture_usage(self, sample_data: dict[str, str]) -> None:
        """Test using fixture."""
        assert "key1" in sample_data
        assert sample_data["key2"] == "value2"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
'''
        else:
            return '''#!/usr/bin/env python3
"""Utility Library - Generated by NuSyQ-Hub AI System."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileHandler:
    """Handle file operations safely."""

    @staticmethod
    def read_json(filepath: str | Path) -> dict[str, Any]:
        """Read JSON file safely."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            return {}

    @staticmethod
    def write_json(filepath: str | Path, data: dict[str, Any], indent: int = 2) -> bool:
        """Write JSON file safely."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"Successfully wrote to {filepath}")
            return True
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return False

    @staticmethod
    def read_text(filepath: str | Path) -> Optional[str]:
        """Read text file safely."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            return None
        except OSError as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None

    @staticmethod
    def write_text(filepath: str | Path, content: str) -> bool:
        """Write text file safely."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Successfully wrote to {filepath}")
            return True
        except OSError as e:
            logger.error(f"Failed to write {filepath}: {e}")
            return False


class DataValidator:
    """Validate data structures."""

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email format is valid."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL format is valid."""
        import re
        pattern = r'^https?://[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}(/.*)?$'
        return bool(re.match(pattern, url))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        import re
        # Remove invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip('. ')
        return sanitized or 'unnamed'


class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str = "Operation") -> None:
        self.name = name
        self.start_time: Optional[float] = None

    def __enter__(self) -> None:
        self.start_time = datetime.now().timestamp()
        logger.info(f"{self.name} started")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time:
            elapsed = datetime.now().timestamp() - self.start_time
            logger.info(f"{self.name} completed in {elapsed:.3f}s")


# Example usage
if __name__ == "__main__":
    # File operations
    handler = FileHandler()

    # Write sample data
    sample_data = {
        "name": "NuSyQ-Hub",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
    handler.write_json("output/sample.json", sample_data)

    # Read data back
    loaded_data = handler.read_json("output/sample.json")
    print(f"Loaded: {loaded_data}")

    # Validation
    validator = DataValidator()
    print(f"Valid email: {validator.is_valid_email('test@example.com')}")
    print(f"Valid URL: {validator.is_valid_url('https://example.com')}")

    # Timing
    with Timer("Sample operation"):
        import time
        time.sleep(1)

    print("Utility library ready!")
'''

    def _generate_dockerfile_game(self) -> str:
        """Generate Dockerfile for game."""
        return """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    libsdl2-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
"""

    def _generate_dockerfile_webapp(self, framework: str) -> str:
        """Generate Dockerfile for web app."""
        cmd = (
            "uvicorn main:app --host 0.0.0.0 --port 5000"
            if framework == "fastapi"
            else "python main.py"
        )
        return f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 5000

CMD ["{cmd.split()[0]}", "{" ".join(cmd.split()[1:])}"]
"""

    def _generate_docker_compose_webapp(self) -> str:
        """Generate docker-compose.yml for web app."""
        return """version: "3.9"

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - ./data:/app/data
"""
