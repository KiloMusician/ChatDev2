"""
File Operations Service with Security
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from .config import SecurityConfig
    from .models import FileReadRequest, FileWriteRequest
    from .security import SecurityValidator
except ImportError:
    # Handle case when running as standalone script
    from models import FileReadRequest, FileWriteRequest
    from security import SecurityValidator

    from config import SecurityConfig


logger = logging.getLogger(__name__)


class FileOperationsService:
    """Secure file operations service with async support"""

    def __init__(self, security_config: Optional[SecurityConfig] = None):
        if security_config is None:
            # Create default security config
            security_config = SecurityConfig()

        self.security_config = security_config
        self.validator = SecurityValidator(security_config.allowed_paths)

    def read_file(self, request: FileReadRequest) -> Dict[str, Any]:
        """
        Read file with security validation

        Args:
            request: Validated file read request

        Returns:
            Dict with status and content or error
        """
        try:
            # Validate path security
            if not self.validator.validate_file_path(request.path):
                return {"status": "error", "error": "Path security validation failed"}

            file_path = Path(request.path)

            # Check if file exists
            if not file_path.exists():
                return {"status": "error", "error": f"File not found: {request.path}"}

            # Check file size
            if not self.validator.validate_file_size(file_path, self.security_config.max_file_size):
                return {"status": "error", "error": "File too large"}

            # Read file content
            content = file_path.read_text(encoding=request.encoding)

            return {
                "status": "success",
                "content": content,
                "path": str(file_path),
                "size": file_path.stat().st_size,
            }

        except UnicodeDecodeError as e:
            logger.error("Encoding error reading file: %s", str(e))
            return {"status": "error", "error": f"Encoding error: {str(e)}"}
        except PermissionError as e:
            logger.error("Permission error reading file: %s", str(e))
            return {"status": "error", "error": "Permission denied"}
        except Exception as e:
            logger.error("Error reading file: %s", str(e))
            return {"status": "error", "error": f"Read error: {str(e)}"}

    def write_file(self, request: FileWriteRequest) -> Dict[str, Any]:
        """
        Write file with security validation

        Args:
            request: Validated file write request

        Returns:
            Dict with status and result info
        """
        try:
            # Validate path security
            if not self.validator.validate_file_path(request.path):
                return {"status": "error", "error": "Path security validation failed"}

            file_path = Path(request.path)

            # Check content size
            content_size = len(request.content.encode(request.encoding))
            if content_size > self.security_config.max_file_size:
                return {"status": "error", "error": "Content too large"}

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            file_path.write_text(request.content, encoding=request.encoding)

            return {
                "status": "success",
                "path": str(file_path),
                "size": content_size,
                "message": "File written successfully",
            }

        except UnicodeEncodeError as e:
            logger.error("Encoding error writing file: %s", str(e))
            return {"status": "error", "error": f"Encoding error: {str(e)}"}
        except PermissionError as e:
            logger.error("Permission error writing file: %s", str(e))
            return {"status": "error", "error": "Permission denied"}
        except Exception as e:
            logger.error("Error writing file: %s", str(e))
            return {"status": "error", "error": f"Write error: {str(e)}"}
