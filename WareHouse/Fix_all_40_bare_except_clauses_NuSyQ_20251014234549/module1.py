import logging
from requests.exceptions import RequestException, ConnectionError, TimeoutError, IOError
# Set up logging configuration
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
def fetch_data(url):
    try:
        response = requests.get(url, timeout=5)
    except RequestException as e:
        logger.error(f"Request failed: {e}", exc_info=True)
    return response.json()