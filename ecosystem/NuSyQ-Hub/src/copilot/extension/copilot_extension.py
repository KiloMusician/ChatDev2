import asyncio
import logging
import os

import aiohttp

# Fallback: try to load token from the project's SecureConfig if environment missing
try:
    from src.setup.secrets import config as secure_config
except (ImportError, ModuleNotFoundError, OSError):
    secure_config = None
from prometheus_client import Summary, start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics setup
REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing request")


class CopilotExtension:
    def __init__(self) -> None:
        """Initialize CopilotExtension."""
        self.api_client: aiohttp.ClientSession | None = None
        self.api_endpoint = self._resolve_api_endpoint()
        self.bridge_mode = (os.getenv("NUSYQ_COPILOT_BRIDGE_MODE") or "").strip().lower()

    def _resolve_api_endpoint(self) -> str | None:
        """Resolve live Copilot bridge endpoint from environment configuration."""
        candidates = [
            os.getenv("NUSYQ_COPILOT_BRIDGE_ENDPOINT"),
            os.getenv("GITHUB_COPILOT_API_ENDPOINT"),
            os.getenv("NUSYQ_COPILOT_API_ENDPOINT"),
        ]
        for value in candidates:
            endpoint = (value or "").strip()
            if endpoint:
                return endpoint
        return None

    async def _probe_endpoint(self, endpoint: str) -> bool:
        """Best-effort endpoint probe to fail fast on dead/placeholder URLs."""
        if not self.api_client:
            return False

        health_url = os.getenv("NUSYQ_COPILOT_BRIDGE_HEALTH_URL", "").strip() or endpoint
        try:
            async with self.api_client.get(health_url) as response:
                if response.status < 500:
                    return True
                logger.warning("Copilot endpoint probe returned status %s", response.status)
                return False
        except (TimeoutError, aiohttp.ClientError) as exc:
            logger.warning("Copilot endpoint probe failed: %s", exc)
            return False

    def _get_api_token(self) -> str | None:
        """Get API token from env first, then from secure config as fallback."""
        token = os.getenv("GITHUB_COPILOT_API_KEY")
        if token:
            return token
        try:
            if secure_config:
                # Use the github.token field from secrets if present
                val = secure_config.get_secret("github", "token", None)
                if val:
                    return val
        except (AttributeError, KeyError, RuntimeError):
            logger.debug("Secure config unavailable or failed to return github.token")
        return None

    async def activate(self) -> None:
        """Initialize the API client for GitHub Copilot.

        QUALITY FIX #2: Added timeout configuration to prevent hanging connections.
        """
        try:
            # If no API key is present, skip client initialization and allow caller to fallback
            api_token = self._get_api_token()
            if not api_token:
                logger.error(
                    "GITHUB_COPILOT_API_KEY not found in environment or config. Skipping API client initialization.",
                )
                self.api_client = None
                return
            # Fix #2: Add timeout configuration (30 seconds default)
            timeout = aiohttp.ClientTimeout(total=30)
            self.api_client = aiohttp.ClientSession(timeout=timeout)
            if self.api_endpoint:
                if not await self._probe_endpoint(self.api_endpoint):
                    logger.warning(
                        "Copilot live endpoint probe failed for %s",
                        self.api_endpoint,
                    )
            else:
                logger.warning(
                    "No Copilot endpoint configured. Set NUSYQ_COPILOT_BRIDGE_ENDPOINT to enable live bridge mode.",
                )
            logger.info("API client initialized successfully with 30s timeout.")
        except (aiohttp.ClientError, RuntimeError) as e:
            # Fix #4: More specific exception handling
            logger.exception("Failed to initialize API client: %s", e)
            raise

    async def send_query(self, query: str) -> dict | None:
        """Send a query to the GitHub Copilot API and return the response.

        Args:
            query (str): The query string to be sent to the API.

        Returns:
            Optional[dict]: Parsed response from the API or None if an error occurs.

        QUALITY FIX #1: Uses environment variable for API token (security best practice).

        """
        if not self.api_client:
            # No client (likely due to missing API key) - indicate gracefully
            logger.warning(
                "API client is not initialized (likely missing API key). Skipping API call.",
            )
            return None

        if not isinstance(query, str) or not query.strip():
            logger.error("Invalid query provided. Query must be a non-empty string.")
            return None

        url = self.api_endpoint
        if not url:
            logger.error(
                "Copilot endpoint is not configured. Set NUSYQ_COPILOT_BRIDGE_ENDPOINT or GITHUB_COPILOT_API_ENDPOINT.",
            )
            return None

        # Fix #1: Load API token from environment variable (security improvement)
        api_token = self._get_api_token()
        if not api_token:
            logger.error("GITHUB_COPILOT_API_KEY not found in environment or config.")
            return None

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {"query": query}
        if self.bridge_mode == "intermediary" or "/api/intermediary" in url:
            payload = {
                "text": query,
                "paradigm": "code_analysis",
                "module": "code_analysis_helper",
                "context": {"source": "copilot_extension"},
            }

        async def fetch_with_retry(url, headers, payload, retries=3, backoff_factor=0.3):
            for attempt in range(retries + 1):
                try:
                    async with self.api_client.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            return await response.json()
                        logger.error(
                            f"API request failed with status {response.status}: {await response.text()}",
                        )
                        msg = f"API returned status {response.status}"
                        raise aiohttp.ClientError(msg)
                except (TimeoutError, aiohttp.ClientError) as e:
                    # Fix #4: Already uses specific exceptions - kept as-is
                    if attempt < retries:
                        wait_time = backoff_factor * (2**attempt)
                        logger.warning("Retrying in %s seconds due to error: %s", wait_time, e)
                        await asyncio.sleep(wait_time)
                    else:
                        logger.exception("All retry attempts failed. Last error: %s", e)
                        raise
            return None

        with REQUEST_TIME.time():
            try:
                response = await fetch_with_retry(url, headers, payload)
                return self._parse_response(response)
            except (TimeoutError, aiohttp.ClientError) as e:
                # Fix #4: More specific exception handling
                logger.exception("Failed to send query: %s", e)
                return None

    def _parse_response(self, response: dict | None) -> dict | None:
        """Validate and parse the API response.

        Args:
            response (dict): The raw response from the API.

        Returns:
            Optional[dict]: Parsed response or None if validation fails.

        """
        if not isinstance(response, dict):
            logger.error("Invalid response type.")
            return None
        # Legacy Copilot bridge format
        if "data" in response and isinstance(response["data"], dict):
            return response["data"]
        # Intermediary bridge format
        if response.get("status") == "ok":
            payload = response.get("payload")
            if isinstance(payload, dict):
                return payload
            if isinstance(payload, str):
                return {"text": payload}
        logger.error("Invalid response format.")
        return None

    async def close(self) -> None:
        """Close the API client session."""
        if self.api_client:
            try:
                await self.api_client.close()
                logger.info("API client closed.")
            except (aiohttp.ClientError, RuntimeError) as e:
                # Fix #4: More specific exception handling
                logger.warning("Error while closing API client: %s", e)


# Example usage
async def main() -> None:
    copilot = CopilotExtension()
    await copilot.activate()
    await copilot.send_query("example query")
    await copilot.close()


if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8000)
    asyncio.run(main())
