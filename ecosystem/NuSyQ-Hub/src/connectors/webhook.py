"""Webhook Connector - Generic webhook integration for HTTP callbacks.

Provides a flexible webhook connector that can:
- Send payloads to webhook endpoints
- Handle various HTTP methods
- Support custom headers and authentication
- Retry on failure

OmniTag: [connector, webhook, http, integration]
MegaTag: CONNECTOR⨳WEBHOOK⦾HTTP_INTEGRATION→∞
"""

import logging
from typing import Any

import requests

from src.connectors.base import BaseConnector, ConnectorConfig, ConnectorStatus
from src.core.result import Fail, Ok, Result

logger = logging.getLogger(__name__)


class WebhookConnector(BaseConnector):
    """Generic webhook connector for HTTP integrations.

    Supports sending data to any HTTP endpoint with configurable
    methods, headers, and retry behavior.

    Example:
        config = ConnectorConfig(
            name="slack_webhook",
            endpoint="https://hooks.slack.com/services/xxx",
            metadata={"method": "POST"}
        )
        webhook = WebhookConnector(config)
        webhook.connect()

        result = webhook.execute("send", {
            "payload": {"text": "Hello from NuSyQ-Hub!"}
        })
    """

    def __init__(self, config: ConnectorConfig):
        """Initialize webhook connector.

        Args:
            config: Connector configuration with endpoint URL
        """
        super().__init__(config)
        self._session: requests.Session | None = None

    def connect(self) -> Result[bool]:
        """Initialize HTTP session for webhook calls.

        Returns:
            Result[bool]: Ok(True) on success
        """
        if not self.config.endpoint:
            self._status = ConnectorStatus.ERROR
            self._last_error = "No endpoint configured"
            return Fail("No endpoint configured", code="NO_ENDPOINT")

        try:
            self._session = requests.Session()

            # Set default headers
            self._session.headers.update(
                {"Content-Type": "application/json", "User-Agent": "NuSyQ-Hub/1.0"}
            )

            # Add API key if provided
            if self.config.api_key:
                self._session.headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._status = ConnectorStatus.CONNECTED
            logger.info(f"Webhook connector '{self.name}' connected")
            return Ok(True, message="Webhook connector ready")

        except Exception as e:
            self._status = ConnectorStatus.ERROR
            self._last_error = str(e)
            return Fail(str(e), code="CONNECTION_ERROR")

    def disconnect(self) -> Result[bool]:
        """Close the HTTP session.

        Returns:
            Result[bool]: Ok(True) on success
        """
        if self._session:
            self._session.close()
            self._session = None

        self._status = ConnectorStatus.DISCONNECTED
        logger.info(f"Webhook connector '{self.name}' disconnected")
        return Ok(True)

    def health_check(self) -> Result[dict]:
        """Check webhook endpoint health.

        Performs a HEAD request to verify endpoint accessibility.

        Returns:
            Result[dict]: Health status information
        """
        if not self.config.endpoint:
            return Fail("No endpoint configured", code="NO_ENDPOINT")

        try:
            response = requests.head(
                self.config.endpoint, timeout=min(self.config.timeout, 10), allow_redirects=True
            )

            healthy = response.status_code < 500

            return Ok(
                {
                    "status": "healthy" if healthy else "degraded",
                    "status_code": response.status_code,
                    "endpoint": self.config.endpoint,
                }
            )

        except requests.Timeout:
            return Fail("Health check timeout", code="TIMEOUT")
        except requests.ConnectionError as e:
            return Fail(f"Connection error: {e}", code="CONNECTION_ERROR")
        except Exception as e:
            return Fail(str(e), code="HEALTH_CHECK_FAILED")

    def execute(self, action: str, params: dict) -> Result[Any]:
        """Execute a webhook action.

        Supported actions:
        - send: Send POST request with payload
        - get: Send GET request
        - put: Send PUT request with payload
        - delete: Send DELETE request

        Args:
            action: Action name
            params: Action parameters including 'payload', 'headers', 'url_suffix'

        Returns:
            Result[Any]: Action result
        """
        actions = {
            "send": self._send_webhook,
            "post": self._send_webhook,
            "get": self._get_request,
            "put": self._put_request,
            "delete": self._delete_request,
        }

        if action.lower() not in actions:
            return Fail(
                f"Unknown action: {action}. Supported: {list(actions.keys())}",
                code="UNKNOWN_ACTION",
            )

        return actions[action.lower()](params)

    def _send_webhook(self, params: dict) -> Result[dict]:
        """Send POST webhook with payload.

        Args:
            params: Must include 'payload', optionally 'headers', 'url_suffix'

        Returns:
            Result[dict]: Response information
        """
        if not self._session:
            return Fail("Not connected", code="NOT_CONNECTED")

        payload = params.get("payload", {})
        headers = params.get("headers", {})
        url_suffix = params.get("url_suffix", "")
        url = f"{self.config.endpoint}{url_suffix}"

        for attempt in range(self.config.retry_count):
            try:
                response = self._session.post(
                    url, json=payload, headers=headers, timeout=self.config.timeout
                )

                if response.ok:
                    return Ok(
                        {
                            "status_code": response.status_code,
                            "response": self._safe_json(response),
                            "url": url,
                        }
                    )
                elif response.status_code >= 500 and attempt < self.config.retry_count - 1:
                    # Retry on server errors
                    logger.warning(f"Webhook retry {attempt + 1}/{self.config.retry_count}")
                    continue
                else:
                    return Fail(
                        f"Webhook failed: {response.status_code}",
                        code="WEBHOOK_FAILED",
                        data={"status_code": response.status_code, "body": response.text[:500]},
                    )

            except requests.Timeout:
                if attempt < self.config.retry_count - 1:
                    continue
                return Fail("Request timeout", code="TIMEOUT")
            except Exception as e:
                return Fail(str(e), code="REQUEST_ERROR")

        return Fail("Max retries exceeded", code="MAX_RETRIES")

    def _get_request(self, params: dict) -> Result[dict]:
        """Send GET request.

        Args:
            params: Optional 'url_suffix', 'query_params'

        Returns:
            Result[dict]: Response information
        """
        if not self._session:
            return Fail("Not connected", code="NOT_CONNECTED")

        url_suffix = params.get("url_suffix", "")
        query_params = params.get("query_params", {})
        url = f"{self.config.endpoint}{url_suffix}"

        try:
            response = self._session.get(url, params=query_params, timeout=self.config.timeout)

            return Ok(
                {
                    "status_code": response.status_code,
                    "response": self._safe_json(response),
                    "url": url,
                }
            )

        except Exception as e:
            return Fail(str(e), code="REQUEST_ERROR")

    def _put_request(self, params: dict) -> Result[dict]:
        """Send PUT request with payload."""
        if not self._session:
            return Fail("Not connected", code="NOT_CONNECTED")

        payload = params.get("payload", {})
        url_suffix = params.get("url_suffix", "")
        url = f"{self.config.endpoint}{url_suffix}"

        try:
            response = self._session.put(url, json=payload, timeout=self.config.timeout)

            return Ok(
                {
                    "status_code": response.status_code,
                    "response": self._safe_json(response),
                }
            )

        except Exception as e:
            return Fail(str(e), code="REQUEST_ERROR")

    def _delete_request(self, params: dict) -> Result[dict]:
        """Send DELETE request."""
        if not self._session:
            return Fail("Not connected", code="NOT_CONNECTED")

        url_suffix = params.get("url_suffix", "")
        url = f"{self.config.endpoint}{url_suffix}"

        try:
            response = self._session.delete(url, timeout=self.config.timeout)

            return Ok(
                {
                    "status_code": response.status_code,
                    "response": self._safe_json(response),
                }
            )

        except Exception as e:
            return Fail(str(e), code="REQUEST_ERROR")

    def _safe_json(self, response: requests.Response) -> Any:
        """Safely parse JSON response, returning text if not JSON."""
        try:
            return response.json()
        except Exception:
            return response.text[:1000] if response.text else None
