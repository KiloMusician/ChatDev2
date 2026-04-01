import asyncio
import os

# Ensure project path is on PYTHONPATH if needed
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.copilot.extension.copilot_extension import CopilotExtension


async def main():
    c = CopilotExtension()
    await c.activate()
    print("api_client is", "initialized" if c.api_client else "NOT initialized")
    await c.close()


if __name__ == "__main__":
    asyncio.run(main())
