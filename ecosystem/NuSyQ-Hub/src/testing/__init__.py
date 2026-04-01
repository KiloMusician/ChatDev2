"""Test Intelligence Subsystem.

Sophisticated test orchestration with:
- Smart deduplication to prevent spam
- Result caching with configurable TTL
- Multi-agent coordination via guild board
- Rich terminal output with metasynthesis
- Failure pattern detection
- Cross-repo test awareness
"""

from .test_intelligence_terminal import (TestCache, TestIntelligenceTerminal,
                                         TestRun, TestTerminalConfig)

__all__ = [
    "TestCache",
    "TestIntelligenceTerminal",
    "TestRun",
    "TestTerminalConfig",
]
