import requests
import logging
logger = logging.getLogger(__name__)
def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Data fetch error: {e}")
        return None