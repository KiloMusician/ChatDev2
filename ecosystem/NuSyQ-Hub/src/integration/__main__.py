"""NuSyQ-Hub Integration Package Entrypoint.

This allows running the integration package as a module:
    python -m integration
"""

from .chatdev_launcher import main

if __name__ == "__main__":
    main()
