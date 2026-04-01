import importlib
import sys

sys.path.insert(0, ".")
mods = [
    "src.integrations.ollama_stub",
    "src.integrations.chatdev_stub",
    "src.integrations.mcp_stub",
]

for m in mods:
    try:
        mod = importlib.import_module(m)
        ok = getattr(mod, "get_client", None) is not None
        print(f"{m}: OK - has get_client={ok}")
    except Exception as e:
        print(f"{m}: FAIL - {e}")
