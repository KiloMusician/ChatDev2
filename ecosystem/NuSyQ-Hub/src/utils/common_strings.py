"""Common String Constants.

Centralized string constants to reduce duplication across the codebase.
These constants are extracted from frequently used strings identified
by static analysis.

Usage:
    from src.utils.common_strings import CONSCIOUSNESS_LEVEL, QUANTUM_COHERENCE

Author: Automated extraction via string duplication analyzer
Date: December 12, 2025
"""

# Consciousness-related constants (highest frequency)
CONSCIOUSNESS_LEVEL = "consciousness_level"
CONSCIOUSNESS_INTEGRATION = "consciousness_integration"
CONSCIOUSNESS_STATE = "consciousness_state"
CONSCIOUSNESS_RESONANCE = "consciousness_resonance"
CONSCIOUSNESS_EVOLUTION = "consciousness_evolution"
CONSCIOUSNESS_BRIDGE = "consciousness_bridge"
CONSCIOUSNESS_ENHANCED = "consciousness_enhanced"

# Quantum-related constants
QUANTUM_COHERENCE = "quantum_coherence"
QUANTUM_ENHANCEMENT = "quantum_enhancement"
QUANTUM_PROBLEMS = "quantum_problems"
REALITY_COHERENCE = "reality_coherence"

# Integration constants
INTEGRATION_POINTS = "integration_points"
INTEGRATION_STATUS = "integration_status"
CHATDEV_INTEGRATION = "chatdev_integration"

# Analysis constants
RECOMMENDATIONS = "recommendations"
PROBLEMS_DETECTED = "problems_detected"
PATTERNS_MATCHED = "patterns_matched"
LAUNCH_PAD_FILES = "launch_pad_files"

# Class name constants
QUANTUM_PROBLEM_RESOLVER = "QuantumProblemResolver"

# Date/time formats
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

# File paths and directories
DATA_DIR = "data"
LOGS_DIR = "logs"
CONFIG_DIR = "config"
TEMP_DIR = ".tmp"

# Configuration keys
CONFIG_OLLAMA = "ollama"
CONFIG_CHATDEV = "chatdev"
CONFIG_QUANTUM = "quantum"
CONFIG_TEMPLE = "temple"

# Status constants
STATUS_ACTIVE = "active"
STATUS_PENDING = "pending"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"
STATUS_RUNNING = "running"
STATUS_QUEUED = "queued"

# Common field names
FIELD_ID = "id"
FIELD_NAME = "name"
FIELD_TYPE = "type"
FIELD_STATUS = "status"
FIELD_CREATED_AT = "created_at"
FIELD_UPDATED_AT = "updated_at"
FIELD_METADATA = "metadata"
FIELD_DESCRIPTION = "description"
FIELD_PRIORITY = "priority"

# Error messages
ERROR_FILE_NOT_FOUND = "File not found"
ERROR_INVALID_CONFIG = "Invalid configuration"
ERROR_CONNECTION_FAILED = "Connection failed"
ERROR_TIMEOUT = "Operation timed out"
ERROR_PERMISSION_DENIED = "Permission denied"

# Success messages
SUCCESS_OPERATION_COMPLETE = "Operation completed successfully"
SUCCESS_FILE_SAVED = "File saved successfully"
SUCCESS_CONNECTION_ESTABLISHED = "Connection established"
