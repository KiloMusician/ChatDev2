"""KILO-FOOLISH Ollama Integration
Provides Ollama LLM integration capabilities.
"""

import requests

try:
    from src.utils import config_helper
except ImportError:
    config_helper = None


class OllamaIntegration:
    def __init__(self, host=None):
        try:
            from src.config.service_config import ServiceConfig

            if host:
                self.host = host.rstrip("/")
            elif ServiceConfig:
                self.host = ServiceConfig.get_ollama_url().rstrip("/")
            elif config_helper:
                self.host = config_helper.get_ollama_host().rstrip("/")
            else:
                import os
                from urllib.parse import urlparse

                base = os.environ.get("OLLAMA_BASE_URL") or os.environ.get(
                    "OLLAMA_HOST", "http://127.0.0.1"
                )
                port = os.environ.get("OLLAMA_PORT", "11434")
                parsed = urlparse(base if "://" in base else f"http://{base}")
                netloc = (
                    f"{parsed.hostname}:{parsed.port}"
                    if parsed.port
                    else f"{parsed.hostname}:{port}"
                )
                self.host = f"{parsed.scheme}://{netloc}".rstrip("/")
        except ImportError:
            import os
            from urllib.parse import urlparse

            base = os.environ.get("OLLAMA_BASE_URL") or os.environ.get(
                "OLLAMA_HOST", "http://127.0.0.1"
            )
            port = os.environ.get("OLLAMA_PORT", "11434")
            parsed = urlparse(base if "://" in base else f"http://{base}")
            netloc = (
                f"{parsed.hostname}:{parsed.port}" if parsed.port else f"{parsed.hostname}:{port}"
            )
            self.host = host or f"{parsed.scheme}://{netloc}"

    def generate(self, model, prompt, **kwargs):
        """Generate text using Ollama."""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, **kwargs},
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Ollama integration error: {e}")
        return None


# Global instance
ollama = OllamaIntegration()
