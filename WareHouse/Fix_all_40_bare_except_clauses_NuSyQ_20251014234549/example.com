### Notes:
- The function includes specific exception handling for `requests.RequestException`.
- A timeout parameter is added to the `requests.get` call with a default value of 5 seconds.
- Proper logging is implemented using Python's built-in `logging` module.