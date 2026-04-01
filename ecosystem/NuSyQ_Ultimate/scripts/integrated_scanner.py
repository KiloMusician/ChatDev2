"""
Shim to expose integrated scanner from src/tools when imported as scripts.integrated_scanner.
"""

from src.tools.integrated_scanner import IntegratedScanner

__all__ = ["IntegratedScanner"]
