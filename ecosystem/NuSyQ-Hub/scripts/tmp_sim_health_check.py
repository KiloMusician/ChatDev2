import json
import os

import requests

try:
    from src.config.service_config import ServiceConfig
except ImportError:
    ServiceConfig = None


def _get_simulatedverse_url() -> str:
    """Resolve SimulatedVerse URL from config/env."""
    if ServiceConfig:
        try:
            return ServiceConfig.get_simulatedverse_url()
        except (AttributeError, RuntimeError, ValueError):
            pass

    base = os.getenv("SIMULATEDVERSE_BASE_URL")
    if base:
        return base if "://" in base else f"http://{base}"

    host = os.getenv("SIMULATEDVERSE_HOST", "http://127.0.0.1")
    port = os.getenv("SIMULATEDVERSE_PORT", "5002")
    if "://" not in host:
        host = f"http://{host}"
    if ":" not in host.split("://")[1]:
        host = f"{host}:{port}"
    return host


try:
    sim_url = _get_simulatedverse_url()
    r = requests.get(f"{sim_url}/api/health", timeout=3)
    print("STATUS:", r.status_code)
    try:
        print("BODY:", r.json())
    except (ValueError, json.JSONDecodeError):
        print("BODY_TEXT:", r.text)
except Exception as e:
    print("Error contacting simulatedverse minimal health:", e)
