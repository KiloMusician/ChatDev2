import importlib
import sys

print("python", sys.version)

for name in ("fastapi", "uvicorn", "aiohttp"):
    try:
        importlib.import_module(name)
        print(name, "OK")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(name, "MISSING", type(e).__name__, e)
