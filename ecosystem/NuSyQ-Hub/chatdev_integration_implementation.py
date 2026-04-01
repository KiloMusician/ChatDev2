"""Compatibility wrapper for chatdev_integration_implementation
Delegates to src.scripts.chatdev_integration_implementation
"""

import runpy

if __name__ == "__main__":
    runpy.run_module("src.scripts.chatdev_integration_implementation", run_name="__main__")
