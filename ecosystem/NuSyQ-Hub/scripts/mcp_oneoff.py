import json

import requests


def main():
    url = "http://127.0.0.1:8001/api/terminals/send"
    payload = {
        "channel": "nusyq-demo",
        "level": "info",
        "message": "mcp-oneoff-test",
        "meta": {"demo": True},
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        print("STATUS", r.status_code)
        try:
            print(json.dumps(r.json(), indent=2))
        except Exception:
            print(r.text)
    except Exception as e:
        print("ERROR", e)


if __name__ == "__main__":
    main()
