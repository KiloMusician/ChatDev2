# Proxy module so `python -m copilot.bridge_cli` works when tests spawn a subprocess
# Delegates to the implementation at `src/copilot/bridge_cli.py`.

from importlib import import_module

_impl = import_module("src.copilot.bridge_cli")

# Re-export main so `python -m copilot.bridge_cli` executes the same entrypoint
main = getattr(_impl, "main", None)

if __name__ == "__main__":
    if main is None:
        raise SystemExit("bridge_cli implementation not found")
    main()
