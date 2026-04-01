"""
Security utilities and validation
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Security validation utilities"""

    def __init__(self, allowed_paths: Optional[List[str]] = None):
        self.allowed_paths = allowed_paths or [
            str(Path.cwd()),
            str(Path.home() / "Documents"),
            str(Path.home() / "Desktop"),
        ]
        # Normalize paths for comparison
        self.allowed_paths = [str(Path(p).resolve()) for p in self.allowed_paths]

    def validate_file_path(self, file_path: Union[str, Path]) -> bool:
        """
        Validate file path against path traversal and allowed directories

        Args:
            file_path: Path to validate

        Returns:
            bool: True if path is safe and allowed
        """
        try:
            # Convert to Path object and resolve
            path = Path(file_path).resolve()

            # Check for path traversal attempts
            if ".." in str(file_path):
                logger.warning(f"Path traversal attempt detected: {file_path}")
                return False

            # Check if path is within allowed directories
            path_str = str(path)
            for allowed_path in self.allowed_paths:
                if path_str.startswith(allowed_path):
                    return True

            logger.warning(f"Path outside allowed directories: {file_path}")
            return False

        except (OSError, ValueError) as e:
            logger.error(f"Invalid path format: {file_path}, error: {e}")
            return False

    def validate_file_size(self, file_path: Union[str, Path], max_size: int = 10485760) -> bool:
        """
        Validate file size is within limits

        Args:
            file_path: Path to file
            max_size: Maximum allowed size in bytes (default 10MB)

        Returns:
            bool: True if file size is acceptable
        """
        try:
            size = Path(file_path).stat().st_size
            if size > max_size:
                logger.warning(f"File too large: {file_path} ({size} bytes > {max_size})")
                return False
            return True
        except (OSError, ValueError) as e:
            logger.error(f"Error checking file size: {file_path}, error: {e}")
            return False

    def sanitize_input(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input by removing dangerous characters

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            str: Sanitized text
        """
        if not isinstance(text, str):
            return ""

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]

        # Remove null bytes and control characters
        text = text.replace("\x00", "")

        # Remove potentially dangerous patterns for file operations
        dangerous_chars = ["<", ">", "|", "&", ";", "`"]
        for char in dangerous_chars:
            text = text.replace(char, "")

        return text.strip()

    def validate_model_name(self, model_name: str) -> bool:
        """
        Validate Ollama model name format

        Args:
            model_name: Model name to validate

        Returns:
            bool: True if model name is valid
        """
        if not isinstance(model_name, str):
            return False

        # Basic validation: alphanumeric, dots, hyphens, underscores, colons
        import re

        pattern = r"^[a-zA-Z0-9._:-]+$"
        if not re.match(pattern, model_name):
            logger.warning(f"Invalid model name format: {model_name}")
            return False

        # Length check
        if len(model_name) > 100 or len(model_name) < 1:
            logger.warning(f"Invalid model name length: {model_name}")
            return False

        return True

    def compute_file_hash(self, file_path: Union[str, Path]) -> Optional[str]:
        """
        Compute SHA256 hash of file for integrity checking

        Args:
            file_path: Path to file

        Returns:
            str or None: SHA256 hash of file, None if error
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb", encoding="utf-8") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, ValueError) as e:
            logger.error(f"Error computing file hash: {file_path}, error: {e}")
            return None

    def is_safe_code(self, code: str) -> bool:
        """
        Check if code contains potentially dangerous operations

        Args:
            code: Python code to check

        Returns:
            bool: True if code appears safe
        """
        dangerous_patterns = [
            "import os",
            "subprocess",
            "__import__",
            "eval(",
            "exec(",
            "open(",
            "file(",
            "compile(",
            "globals(",
            "locals(",
            "setattr(",
            "getattr(",
            "hasattr(",
            "delattr(",
            "__builtins__",
        ]

        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                logger.warning(f"Potentially dangerous code pattern: {pattern}")
                return False

        return True

    def create_secure_temp_file(
        self, content: str, suffix: str = ".tmp", prefix: str = "nusyq_"
    ) -> Optional[str]:
        """
        Create a secure temporary file with restricted permissions

        Args:
            content: Content to write to file
            suffix: File suffix
            prefix: File prefix

        Returns:
            str or None: Path to created file, None if error
        """
        import tempfile

        try:
            # Create temporary file with restricted permissions (600)
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, text=True)

            # Set restrictive permissions
            os.chmod(temp_path, 0o600)

            # Write content
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)

            return temp_path

        except (OSError, ValueError) as e:
            logger.error(f"Error creating secure temp file: {e}")
            return None
