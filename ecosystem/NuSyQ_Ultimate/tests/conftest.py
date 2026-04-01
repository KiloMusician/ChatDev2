"""
Pytest Configuration - NuSyQ Test Suite

Configures test environment and Python path.
"""

import os
import sys
from pathlib import Path

# Disable OpenTelemetry during tests to prevent I/O cleanup issues
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["TRACING_ENABLED"] = "false"

# Add project root and src/ to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))
