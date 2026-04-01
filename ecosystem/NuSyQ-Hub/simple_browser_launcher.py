# Compatibility wrapper for simple_browser_launcher
# Delegates to src.scripts.simple_browser_launcher
import runpy

if __name__ == "__main__":
    runpy.run_module("src.scripts.simple_browser_launcher", run_name="__main__")

# original simple browser launcher script
