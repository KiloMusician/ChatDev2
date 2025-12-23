import requests
import logging
from requests.exceptions import RequestException, ConnectionError, TimeoutError, HTTPError
# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
def fetch_data(url, timeout=5):
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except ConnectionError as e:
        logging.error(f"Connection error: {e}")
        raise
    except TimeoutError as e:
        logging.error(f"Timeout error: {e}")
        raise
    except HTTPError as e:
        logging.error(f"HTTP error: {e}")
        raise
    except RequestException as e:
        logging.error(f"Request exception: {e}")
        raise
def test_fetch_data_failure():
    try:
        fetch_data('http://example.com')
    except requests.exceptions.RequestException as e:
        print(f"Test failed with exception: {e}")
if __name__ == "__main__":
    test_fetch_data_failure()