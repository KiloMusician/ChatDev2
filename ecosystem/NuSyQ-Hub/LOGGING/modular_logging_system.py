"""KILO-FOOLISH Modular Logging System
Provides structured logging with tags and subprocess awareness.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Configure base logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def log_info(module_name, message):
    """Log an info message."""
    logger = logging.getLogger(module_name)
    logger.info(message)

def log_subprocess_event(module_name, message, command=None, pid=None, tags=None):
    """Log a subprocess event with metadata."""
    logger = logging.getLogger(module_name)
    metadata = {
        "command": command,
        "pid": pid,
        "tags": tags or {},
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"{message} | Metadata: {json.dumps(metadata)}")

def log_tagged_event(module_name, message, omnitag=None, megatag=None):
    """Log an event with OmniTag and MegaTag metadata."""
    logger = logging.getLogger(module_name)
    metadata = {
        "omnitag": omnitag or {},
        "megatag": megatag or {},
        "timestamp": datetime.now().isoformat()
    }
    logger.info(f"{message} | Tags: {json.dumps(metadata)}")
