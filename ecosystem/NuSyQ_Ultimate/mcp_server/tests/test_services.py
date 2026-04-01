"""
Test suite for modular MCP server components
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from mcp_server.src.config import ConfigManager, OllamaConfig, ServiceConfig
from mcp_server.src.file_ops import FileOperationsService

# Import our modules (fixed import paths for pytest)
from mcp_server.src.models import (
    FileReadRequest,
    FileWriteRequest,
    MCPRequest,
    OllamaQueryRequest,
)
from mcp_server.src.ollama import OllamaService
from mcp_server.src.security import SecurityValidator


class TestModels:
    """Test Pydantic models and validation"""

    def test_mcp_request_validation(self):
        """Test MCP request validation"""
        # Valid request
        request = MCPRequest(method="tools/list", params={}, id="req-1")
        assert request.method == "tools/list"

        # Invalid method
        with pytest.raises(ValueError):
            MCPRequest(method="invalid/method", params={}, id="req-2")

    def test_ollama_query_validation(self):
        """Test Ollama query request validation"""
        # Valid request
        request = OllamaQueryRequest(
            model="qwen2.5-coder:7b",
            prompt="Hello, world!",
            max_tokens=50,
        )
        assert request.model == "qwen2.5-coder:7b"
        assert request.max_tokens == 50

        # Invalid model name (too long)
        with pytest.raises(ValueError):
            OllamaQueryRequest(
                model="a" * 101,
                prompt="test",
                max_tokens=50,
            )

    def test_file_request_validation(self):
        """Test file operation request validation"""
        # Valid read request
        read_req = FileReadRequest(path="test.txt", encoding="utf-8")
        assert read_req.encoding == "utf-8"

        # Invalid path with traversal
        with pytest.raises(ValueError):
            FileReadRequest(path="../../../etc/passwd", encoding="utf-8")


class TestConfigManager:
    """Test configuration management"""

    def test_default_config_creation(self):
        """Test default configuration creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            config_manager = ConfigManager(str(config_path))

            # Should create default config
            assert config_path.exists()

            # Test service config
            service_config = config_manager.get_service_config()
            assert isinstance(service_config, ServiceConfig)
            assert service_config.host == "localhost"
            assert service_config.port == 8000

            # Test Ollama config
            ollama_config = config_manager.get_ollama_config()
            assert isinstance(ollama_config, OllamaConfig)
            assert ollama_config.host == "localhost"
            assert ollama_config.port == 11434

    def test_config_get_set(self):
        """Test configuration get/set operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.yaml"
            config_manager = ConfigManager(str(config_path))

            # Test get with default
            value = config_manager.get("nonexistent.key", "default")
            assert value == "default"

            # Test set and get
            config_manager.set("test.value", "hello")
            assert config_manager.get("test.value") == "hello"


class TestSecurityValidator:
    """Test security validation utilities"""

    def test_path_validation(self):
        """Test file path validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            validator = SecurityValidator([temp_dir])

            # Valid path within allowed directory
            valid_path = Path(temp_dir) / "test.txt"
            assert validator.validate_file_path(valid_path)

            # Invalid path with traversal
            invalid_path = Path(temp_dir) / ".." / "etc" / "passwd"
            assert not validator.validate_file_path(invalid_path)

            # Path outside allowed directories
            outside_path = Path("/tmp/outside.txt")
            assert not validator.validate_file_path(outside_path)

    def test_input_sanitization(self):
        """Test input sanitization"""
        validator = SecurityValidator()

        # Normal text
        clean_text = validator.sanitize_input("Hello, world!")
        assert clean_text == "Hello, world!"

        # Text with dangerous characters
        dirty = "Hello <script>alert('xss')</script>"
        dirty_text = validator.sanitize_input(dirty)
        assert "<script>" not in dirty_text
        assert "alert" in dirty_text

        # Text too long
        long_text = "a" * 2000
        sanitized = validator.sanitize_input(long_text, max_length=100)
        assert len(sanitized) == 100

    def test_model_name_validation(self):
        """Test model name validation"""
        validator = SecurityValidator()

        # Valid model names
        assert validator.validate_model_name("qwen2.5-coder:7b")
        assert validator.validate_model_name("llama3.1:8b")
        assert validator.validate_model_name("phi3.5")

        # Invalid model names
        assert not validator.validate_model_name("model with spaces")
        assert not validator.validate_model_name("model@with!special")
        assert not validator.validate_model_name("")
        assert not validator.validate_model_name("a" * 101)

    def test_code_safety_check(self):
        """Test code safety validation"""
        validator = SecurityValidator()

        # Safe code
        safe_code = "print('Hello, world!')\nx = 1 + 2"
        assert validator.is_safe_code(safe_code)

        # Dangerous code
        dangerous_code = "import os\nos.system('rm -rf /')"
        assert not validator.is_safe_code(dangerous_code)

        eval_code = "eval('malicious_code')"
        assert not validator.is_safe_code(eval_code)


@pytest.mark.asyncio
class TestOllamaService:
    """Test Ollama service"""

    def test_ollama_service_init(self):
        """Test Ollama service initialization"""
        config = OllamaConfig(host="localhost", port=11434)
        service = OllamaService(config)

        assert service.config.host == "localhost"
        assert service.config.port == 11434
        assert service.base_url == "http://localhost:11434"

    @patch("aiohttp.ClientSession.post")
    async def test_query_model_success(self, mock_post):
        """Test successful model query"""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "response": "Hello, how can I help you?",
            "done": True,
        }
        mock_post.return_value.__aenter__.return_value = mock_response

        config = OllamaConfig(host="localhost", port=11434)
        service = OllamaService(config)

        request = OllamaQueryRequest(
            model="qwen2.5-coder:7b",
            prompt="Hello",
            max_tokens=50,
        )

        result = await service.query_model(request)

        assert result["status"] == "success"
        assert "response" in result
        assert result["model"] == "qwen2.5-coder:7b"

        await service.close()

    @patch("aiohttp.ClientSession.post")
    async def test_query_model_error(self, mock_post):
        """Test model query error handling"""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text.return_value = "Model not found"
        mock_post.return_value.__aenter__.return_value = mock_response

        config = OllamaConfig(host="localhost", port=11434)
        service = OllamaService(config)

        request = OllamaQueryRequest(
            model="nonexistent:model",
            prompt="Hello",
            max_tokens=50,
        )

        result = await service.query_model(request)

        assert result["status"] == "error"
        assert "HTTP 404" in result["error"]

        await service.close()


@pytest.mark.asyncio
class TestFileOperationsService:
    """Test file operations service"""

    def test_file_operations_init(self):
        """Test file operations service initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            security_config = SecurityValidator(allowed_paths=[temp_dir])
            service = FileOperationsService(security_config)

            assert service.security_config.allowed_paths == [temp_dir]

    def test_read_file_success(self):
        """Test successful file read"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_content = "Hello, world!"
            test_file.write_text(test_content, encoding="utf-8")

            security_config = SecurityValidator(allowed_paths=[temp_dir])
            service = FileOperationsService(security_config)

            request = FileReadRequest(path=str(test_file), encoding="utf-8")
            result = service.read_file(request)

            assert result["status"] == "success"
            assert result["content"] == test_content

    def test_read_file_security_error(self):
        """Test file read security validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            security_config = SecurityValidator(allowed_paths=[temp_dir])
            service = FileOperationsService(security_config)

            # Try to read file outside allowed paths
            request = FileReadRequest(path="/etc/passwd", encoding="utf-8")
            result = service.read_file(request)

            assert result["status"] == "error"
            assert "security" in result["error"].lower()

    def test_write_file_success(self):
        """Test successful file write"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "output.txt"
            test_content = "Hello, world!"

            security_config = SecurityValidator(allowed_paths=[temp_dir])
            service = FileOperationsService(security_config)

            request = FileWriteRequest(
                path=str(test_file),
                content=test_content,
                encoding="utf-8",
            )
            result = service.write_file(request)

            assert result["status"] == "success"
            assert test_file.exists()
            assert test_file.read_text(encoding="utf-8") == test_content


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
