import requests
import logging
# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)  # Add timeout parameter
        response.raise_for_status()
    except requests.exceptions.RequestException as e:  # Replace bare except with specific exception type
        logging.error(f"An error occurred while fetching data from {url}: {e}")
        raise  # Re-raise the exception to propagate it further
def test_fetch_data_failure():
    try:
        fetch_data('http://example.com')
    except requests.exceptions.RequestException as e:  # Replace bare except with specific exception type
        logging.error(f"Test failed: {e}")