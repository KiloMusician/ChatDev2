import requests
import logging
logger = logging.getLogger(__name__)
def fetch_data(url):
    try:
        response = requests.get(url, timeout=5)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return None