"""
Ollama Service with async HTTP client and adaptive timeout management
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from .config import ConfigManager, OllamaConfig
    from .models import OllamaQueryRequest
except ImportError:
    # Handle case when running as standalone script
    from models import OllamaQueryRequest

    from config import ConfigManager, OllamaConfig

logger = logging.getLogger(__name__)

try:
    from config.adaptive_timeout_manager import (
        AgentType,
        TaskComplexity,
        get_timeout_manager,
    )

    ADAPTIVE_TIMEOUT_AVAILABLE = True
except ImportError:
    ADAPTIVE_TIMEOUT_AVAILABLE = False

    # Create dummy classes for type hints when not available
    class TaskComplexity:
        MODERATE = "moderate"

    class AgentType:
        LOCAL_QUALITY = "local_quality"

    logger.warning("AdaptiveTimeoutManager not available, using static timeouts")


class OllamaService:
    """Async Ollama service with improved error handling"""

    def __init__(self, config: Optional[OllamaConfig] = None):
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.get_ollama_config()

        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(
        self, task_complexity: TaskComplexity = TaskComplexity.MODERATE
    ) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session with adaptive timeout

        Args:
            task_complexity: Expected task complexity for timeout calculation
        """
        if self._session is None or self._session.closed:
            # Use adaptive timeout if available
            if ADAPTIVE_TIMEOUT_AVAILABLE and self.config.use_adaptive_timeout:
                timeout_manager = get_timeout_manager()
                recommendation = timeout_manager.get_timeout(
                    AgentType.LOCAL_QUALITY,  # Ollama models
                    task_complexity,
                )
                timeout_seconds = recommendation.timeout_seconds
                logger.info(
                    "Using adaptive timeout: %.1fs (confidence: %.1f%%, %s)",
                    timeout_seconds,
                    recommendation.confidence * 100,
                    recommendation.reasoning,
                )
            else:
                # Fall back to static config timeout
                timeout_seconds = self.config.timeout
                logger.debug("Using static timeout: %ds", timeout_seconds)

            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def query(self, request: OllamaQueryRequest) -> Dict[str, Any]:
        """
        Query Ollama model asynchronously

        Args:
            request: Validated query request

        Returns:
            Dict containing the response
        """
        return await self.query_model(request)

    async def query_model(
        self,
        request: OllamaQueryRequest,
        task_complexity: TaskComplexity = TaskComplexity.MODERATE,
    ) -> Dict[str, Any]:
        """
        Query Ollama model asynchronously with performance tracking

        Args:
            request: Validated query request
            task_complexity: Expected task complexity (for adaptive timeout)

        Returns:
            Dict containing the response
        """
        # Start timing for adaptive learning
        start_time = time.time()
        succeeded = False

        session = await self._get_session(task_complexity)

        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {"num_predict": request.max_tokens},
        }

        try:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    succeeded = True
                    result = {
                        "status": "success",
                        "response": data.get("response", ""),
                        "model": request.model,
                        "done": data.get("done", True),
                    }
                else:
                    error_text = await response.text()
                    logger.error(
                        "Ollama API error: status=%d, response=%s",
                        response.status,
                        error_text,
                    )
                    result = {
                        "status": "error",
                        "error": f"HTTP {response.status}: {error_text}",
                    }

        except asyncio.TimeoutError:
            logger.error("Ollama query timeout")
            result = {"status": "error", "error": "Query timeout"}
        except aiohttp.ClientError as e:
            logger.error("Ollama client error: %s", str(e))
            result = {"status": "error", "error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error querying Ollama: %s", str(e))
            result = {"status": "error", "error": f"Unexpected error: {str(e)}"}
        finally:
            # Record execution metrics for adaptive learning
            duration = time.time() - start_time
            if ADAPTIVE_TIMEOUT_AVAILABLE:
                timeout_manager = get_timeout_manager()
                timeout_manager.record_execution(
                    agent_type=AgentType.LOCAL_QUALITY,
                    task_complexity=task_complexity,
                    duration=duration,
                    succeeded=succeeded,
                    context={
                        "model": request.model,
                        "prompt_length": len(request.prompt),
                        "max_tokens": request.max_tokens,
                    },
                )

        return result

    async def list_models(self) -> Dict[str, Any]:
        """List available Ollama models"""
        session = await self._get_session()

        try:
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    return {"status": "success", "models": models}
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "error": f"HTTP {response.status}: {error_text}",
                    }

        except Exception as e:
            logger.error("Error listing Ollama models: %s", str(e))
            return {"status": "error", "error": str(e)}

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        session = await self._get_session()

        try:
            async with session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200

        except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError):
            return False

    async def close(self) -> None:
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
