import requests
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
def test_fetch_data_failure():
    try:
        fetch_data('http://example.com')
    except Exception as e:
        print(f"An error occurred: {e}")