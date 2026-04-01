"""
Request/Response Models with Enhanced Validation (Pydantic v2)
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MCPRequest(BaseModel):
    """Model Context Protocol request with validation"""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="MCP method name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters")
    id: Optional[str] = Field(None, description="Request identifier")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate method is one of the allowed MCP methods."""
        allowed_methods = ["tools/list", "tools/call"]
        if v not in allowed_methods:
            raise ValueError(f"Method must be one of {allowed_methods}")
        return v


class MCPResponse(BaseModel):
    """Model Context Protocol response"""

    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class OllamaQueryRequest(BaseModel):
    """Validated Ollama query request"""

    model: str = Field(..., description="Ollama model name")
    prompt: str = Field(..., min_length=1, max_length=10000, description="Query prompt")
    max_tokens: int = Field(100, ge=1, le=2000, description="Maximum tokens")

    @field_validator("model")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate Ollama model name length and format."""
        # Basic validation for model names
        if not v or len(v) > 100:
            raise ValueError("Model name must be between 1 and 100 characters")
        return v


class FileReadRequest(BaseModel):
    """Validated file read request"""

    path: str = Field(..., description="File path")
    encoding: str = Field("utf-8", description="Text encoding")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate file path for security (no parent directory traversal)."""
        # Basic path validation
        if not v or ".." in v:
            raise ValueError("Invalid file path")
        return v

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, v: str) -> str:
        """Validate encoding is one of the allowed text encodings."""
        allowed_encodings = ["utf-8", "ascii", "latin-1", "cp1252"]
        if v not in allowed_encodings:
            raise ValueError(f"Encoding must be one of {allowed_encodings}")
        return v


class FileWriteRequest(BaseModel):
    """Validated file write request"""

    path: str = Field(..., description="File path")
    content: str = Field(..., max_length=1000000, description="File content")
    encoding: str = Field("utf-8", description="Text encoding")

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate file path for security (no parent directory traversal)."""
        if not v or ".." in v:
            raise ValueError("Invalid file path")
        return v

    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, v: str) -> str:
        """Validate encoding is one of the allowed text encodings."""
        allowed_encodings = ["utf-8", "ascii", "latin-1", "cp1252"]
        if v not in allowed_encodings:
            raise ValueError(f"Encoding must be one of {allowed_encodings}")
        return v


class ChatDevRequest(BaseModel):
    """Validated ChatDev creation request"""

    task: str = Field(..., min_length=10, max_length=1000, description="Development task")
    model: str = Field("qwen2.5-coder:7b", description="Ollama model")
    config: str = Field("NuSyQ_Ollama", description="ChatDev configuration")
    timeout: int = Field(300, ge=30, le=1800, description="Timeout in seconds")


class JupyterRequest(BaseModel):
    """Validated Jupyter execution request"""

    code: str = Field(..., min_length=1, max_length=10000, description="Python code")
    kernel: str = Field("python3", description="Kernel type")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate Python code for dangerous patterns (security check)."""
        # Basic security checks for dangerous operations
        dangerous_patterns = ["import os", "subprocess", "__import__", "eval(", "exec("]
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"Code contains potentially dangerous pattern: {pattern}")
        return v


class SystemInfoRequest(BaseModel):
    """Validated system info request"""

    component: str = Field("all", description="Component to query")

    @field_validator("component")
    @classmethod
    def validate_component(cls, v: str) -> str:
        """Validate system component is one of the allowed types."""
        allowed_components = ["all", "ollama", "models", "config"]
        if v not in allowed_components:
            raise ValueError(f"Component must be one of {allowed_components}")
        return v


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: str
    components: Dict[str, bool]


class ToolDefinition(BaseModel):
    """MCP tool definition"""

    name: str
    description: str
    inputSchema: Dict[str, Any]
