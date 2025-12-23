import asyncio
import logging
import os
from typing import Optional
import aiohttp
from prometheus_client import start_http_server, Summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics setup
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')


class CopilotExtension:
    def __init__(self):
        self.api_client: Optional[aiohttp.ClientSession] = None

    async def activate(self):
        """
        Initialize the API client for GitHub Copilot.
        
        QUALITY FIX #2: Added timeout configuration to prevent hanging connections.
        """
        try:
            # Fix #2: Add timeout configuration (30 seconds default)
            timeout = aiohttp.ClientTimeout(total=30)
            self.api_client = aiohttp.ClientSession(timeout=timeout)
            logger.info("API client initialized successfully with 30s timeout.")
        except (aiohttp.ClientError, RuntimeError) as e:
            # Fix #4: More specific exception handling
            logger.error(f"Failed to initialize API client: {e}")
            raise

    async def send_query(self, query: str) -> Optional[dict]:
        """
        Send a query to the GitHub Copilot API and return the response.
        
        Args:
            query (str): The query string to be sent to the API.
        
        Returns:
            Optional[dict]: Parsed response from the API or None if an error occurs.
        
        QUALITY FIX #1: Uses environment variable for API token (security best practice).
        """
        if not self.api_client:
            logger.error("API client is not initialized. Please call activate() first.")
            return None

        if not isinstance(query, str) or not query.strip():
            logger.error("Invalid query provided. Query must be a non-empty string.")
            return None

        url = "https://api.github.com/copilot/endpoint"  # Replace with actual API endpoint
        
        # Fix #1: Load API token from environment variable (security improvement)
        api_token = os.getenv('GITHUB_COPILOT_API_KEY')
        if not api_token:
            logger.error("GITHUB_COPILOT_API_KEY environment variable not set.")
            return None
        
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        payload = {"query": query}

        async def fetch_with_retry(url, headers, payload, retries=3, backoff_factor=0.3):
            for attempt in range(retries + 1):
                try:
                    async with self.api_client.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            logger.error(f"API request failed with status {response.status}: {await response.text()}")
                            raise aiohttp.ClientError(f"API returned status {response.status}")
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    # Fix #4: Already uses specific exceptions - kept as-is
                    if attempt < retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Retrying in {wait_time} seconds due to error: {e}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All retry attempts failed. Last error: {e}")
                        raise

        with REQUEST_TIME.time():
            try:
                response = await fetch_with_retry(url, headers, payload)
                return self._parse_response(response)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # Fix #4: More specific exception handling
                logger.error(f"Failed to send query: {e}")
                return None

    def _parse_response(self, response: dict) -> Optional[dict]:
        """
        Validate and parse the API response.
        
        Args:
            response (dict): The raw response from the API.
        
        Returns:
            Optional[dict]: Parsed response or None if validation fails.
        """
        # Add your response validation logic here
        if "data" in response:
            return response["data"]
        else:
            logger.error("Invalid response format.")
            return None

    async def close(self):
        """
        Close the API client session.
        """
        if self.api_client:
            try:
                await self.api_client.close()
                logger.info("API client closed.")
            except (aiohttp.ClientError, RuntimeError) as e:
                # Fix #4: More specific exception handling
                logger.warning(f"Error while closing API client: {e}")


# Example usage
async def main():
    copilot = CopilotExtension()
    await copilot.activate()
    response = await copilot.send_query("example query")
    print(response)
    await copilot.close()


if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8000)
    asyncio.run(main())
