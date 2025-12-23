# conftest.py
import pytest
import httpx
@pytest.fixture(scope="module")
async def client():
    async with httpx.AsyncClient(base_url="http://localhost:11434") as client:
        yield client
@pytest.fixture(scope="module")
def model_name():
    return "qwen2.5-coder:7b"