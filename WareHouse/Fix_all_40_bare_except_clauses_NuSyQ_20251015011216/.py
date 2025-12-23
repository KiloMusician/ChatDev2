import logging
import requests
logger = logging.getLogger(__name__)
def safe_request(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        return response
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
# Usage in module1.py
try:
    response = safe_request('https://api.example.com/data')
except Exception as e:
    print("An error occurred")