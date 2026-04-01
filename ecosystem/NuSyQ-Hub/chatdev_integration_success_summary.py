"""Compatibility wrapper for chatdev_integration_success_summary
Delegates to src.scripts.chatdev_integration_success_summary
"""

import runpy

if __name__ == "__main__":
    runpy.run_module("src.scripts.chatdev_integration_success_summary", run_name="__main__")
