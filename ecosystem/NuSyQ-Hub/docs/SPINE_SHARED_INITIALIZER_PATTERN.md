# Spine Shared Initializer Pattern
**Date:** 2026-01-02
**Status:** 🎯 Design & Implementation Guide
**Related:** [SPINE_INITIALIZATION_ARCHITECTURE.md](SPINE_INITIALIZATION_ARCHITECTURE.md)

---

## 🎯 Vision: Centralized Module Initialization

Instead of maintaining 100+ redundant `__init__.py` files with scattered import/export logic, the **spine shared initializer pattern** provides a single source of truth for module interconnection and service discovery.

### Core Principle
**The spine is the central nervous system** - all modules register with it, and all cross-module dependencies flow through it.

---

## 📊 Current State vs. Spine Pattern

### **Before (Fragmented Initialization)**
```python
# In 100+ different __init__.py files:
from .module_a import ServiceA
from .module_b import ServiceB
from ..other.module_c import ServiceC

__all__ = ["ServiceA", "ServiceB", "ServiceC"]

# Problems:
# - 100+ files to maintain
# - Circular import risks
# - No centralized visibility
# - Duplicate export logic
# - Hard to track dependencies
```

### **After (Spine Pattern)**
```python
# src/spine/__init__.py - Single source of truth
"""NuSyQ-Hub Spine: Central Module Registry & Wiring"""

from src.spine.registry import SpineRegistry

# Get the singleton registry
spine = SpineRegistry()

# All services auto-discovered and available through spine
__all__ = ["spine", "get_service", "register_service"]
```

```python
# Individual module __init__.py files become minimal:
"""Agent Orchestration Module

This module is spine-wired. See src/spine/module_registry.json
for centralized configuration and public API definition.
"""

__all__ = []  # No exports needed - spine handles it
```

---

## 🏗️ Architecture Components

### **1. Spine Registry (`src/spine/registry.py`)**
Central service registry with dependency injection:

```python
from typing import Any, Callable, Optional, Type
from pathlib import Path
import importlib
import json

class SpineRegistry:
    """Central registry for all NuSyQ-Hub modules and services."""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._config_path = Path("src/spine/module_registry.json")
        self._load_config()

    def _load_config(self) -> None:
        """Load module configuration from spine registry."""
        if self._config_path.exists():
            with open(self._config_path) as f:
                self._config = json.load(f)
        else:
            self._config = {"modules": {}}

    def register(self, name: str, service: Any, *, override: bool = False) -> None:
        """Register a service with the spine.

        Args:
            name: Service identifier (e.g., "orchestration.hub")
            service: Service instance or class
            override: Allow replacing existing service
        """
        if name in self._services and not override:
            raise ValueError(f"Service '{name}' already registered")
        self._services[name] = service

    def get(self, name: str, *, default: Any = None) -> Any:
        """Get a service from the spine registry.

        Args:
            name: Service identifier
            default: Value to return if service not found

        Returns:
            Service instance or default
        """
        return self._services.get(name, default)

    def lazy_load(self, name: str) -> Any:
        """Lazily load a service based on module_registry.json configuration.

        Args:
            name: Module name from registry

        Returns:
            Loaded service instance
        """
        if name in self._services:
            return self._services[name]

        # Load from config
        module_spec = self._config["modules"].get(name, {})
        if "module_path" in module_spec:
            module = importlib.import_module(module_spec["module_path"])
            service_class = getattr(module, module_spec["class_name"])
            instance = service_class()
            self.register(name, instance)
            return instance

        raise KeyError(f"Service '{name}' not found in registry")

    def get_public_api(self, module_name: str) -> list[str]:
        """Get the public API for a module from the registry.

        Args:
            module_name: Name of the module

        Returns:
            List of public API symbols
        """
        return self._config["modules"].get(module_name, {}).get("public_api", [])

# Singleton instance
_spine = SpineRegistry()

def get_service(name: str, *, default: Any = None) -> Any:
    """Get a service from the global spine registry."""
    return _spine.get(name, default=default)

def register_service(name: str, service: Any, *, override: bool = False) -> None:
    """Register a service with the global spine registry."""
    _spine.register(name, service, override=override)
```

---

### **2. Module Registry (`src/spine/module_registry.json`)**
Declarative configuration for all modules:

```json
{
  "version": "1.0.0",
  "modules": {
    "orchestration": {
      "description": "Multi-AI orchestration and task routing",
      "module_path": "src.orchestration.unified_orchestrator",
      "class_name": "UnifiedAIOrchestrator",
      "public_api": [
        "UnifiedAIOrchestrator",
        "AgentOrchestrationHub"
      ],
      "dependencies": ["ai", "integration", "consciousness"],
      "spine_wired": true,
      "lazy_load": false
    },
    "consciousness": {
      "description": "Consciousness-aware subsystems and quantum cognition",
      "module_path": "src.consciousness.consciousness_bridge",
      "class_name": "ConsciousnessBridge",
      "public_api": [
        "ConsciousnessBridge",
        "QuantumProblemResolver"
      ],
      "submodules": {
        "house_of_leaves": {
          "module_path": "src.consciousness.house_of_leaves.maze_navigator",
          "class_name": "MazeNavigator",
          "public_api": ["Door", "MazeNavigator"]
        }
      },
      "spine_wired": true,
      "lazy_load": true
    },
    "integration": {
      "description": "External system integration bridges",
      "module_path": "src.integration",
      "public_api": [
        "ChatDevIntegration",
        "OllamaIntegration",
        "N8NIntegration"
      ],
      "dependencies": ["ai", "utils"],
      "spine_wired": true
    }
  },
  "metadata": {
    "generated_by": "spine_init_generator.py",
    "last_updated": "2026-01-02T00:00:00Z"
  }
}
```

---

### **3. Spine Initializer (`src/spine/__init__.py`)**
Main entry point for spine system:

```python
"""NuSyQ-Hub Spine: Central Module Registry & Wiring

The Spine serves as the central nervous system for all modules:
- Auto-discovers modules from module_registry.json
- Provides centralized service access
- Manages dependencies and wiring
- Validates module health
"""

from src.spine.registry import SpineRegistry, get_service, register_service

# Singleton registry instance
spine = SpineRegistry()

# Public API
__all__ = [
    "spine",
    "get_service",
    "register_service",
]
```

---

## 🔌 Usage Patterns

### **Pattern 1: Service Registration (Module Initialization)**
```python
# src/orchestration/__init__.py
"""Orchestration module - spine-wired"""

from src.spine import register_service
from src.orchestration.unified_orchestrator import UnifiedAIOrchestrator

# Register with spine on module import
orchestrator = UnifiedAIOrchestrator()
register_service("orchestration.hub", orchestrator)

__all__ = []  # Spine handles exports
```

### **Pattern 2: Service Discovery (Cross-Module Usage)**
```python
# src/agents/agent_orchestration_hub.py
from src.spine import get_service

class AgentOrchestrationHub:
    def __init__(self):
        # Get dependencies through spine (no direct imports)
        self.orchestrator = get_service("orchestration.hub")
        self.consciousness = get_service("consciousness.bridge")

        # Lazy load optional services
        self.quantum = get_service("quantum.resolver", default=None)

    def coordinate_agents(self):
        # Use services obtained from spine
        if self.orchestrator:
            self.orchestrator.dispatch_task(...)
```

### **Pattern 3: Lazy Loading (Performance Optimization)**
```python
# src/spine/registry.py extension
class SpineRegistry:
    def get_lazy(self, name: str) -> Any:
        """Get service, loading it lazily if not yet initialized."""
        if name not in self._services:
            self.lazy_load(name)
        return self._services[name]

# Usage:
from src.spine import spine

# Won't load until first use
consciousness = spine.get_lazy("consciousness.bridge")
```

### **Pattern 4: Module Health Validation**
```python
# scripts/start_nusyq.py hygiene command
from src.spine import spine

def check_spine_health():
    """Validate all spine-wired modules are healthy."""
    missing = []
    for module_name, spec in spine._config["modules"].items():
        if spec.get("spine_wired"):
            service = spine.get(module_name)
            if service is None:
                missing.append(module_name)

    if missing:
        print(f"⚠️  Missing spine services: {', '.join(missing)}")
        return False

    print("✅ All spine services registered")
    return True
```

---

## 🎯 Benefits of Spine Pattern

### **1. Centralized Configuration**
- **Before**: 100+ __init__.py files to search and update
- **After**: 1 JSON file (`module_registry.json`)

### **2. Dependency Injection**
- **Before**: Hard-coded imports create tight coupling
- **After**: Services obtained through spine registry

### **3. Circular Import Prevention**
```python
# Before (circular import risk):
from src.orchestration import OrchestrationHub  # Imports consciousness
from src.consciousness import ConsciousnessBridge  # Imports orchestration
# ❌ Circular dependency!

# After (spine pattern):
orchestrator = spine.get("orchestration.hub")  # No import needed
consciousness = spine.get("consciousness.bridge")  # No import needed
# ✅ Resolved via registry
```

### **4. Lazy Loading**
- Only initialize services when actually used
- Faster startup time
- Lower memory footprint

### **5. Health Monitoring**
```bash
# Single command to validate all modules
$ python scripts/start_nusyq.py hygiene --fast

✅ Spine integrity: 157/157 modules wired
✅ Dependencies: 0 circular imports
✅ Public APIs: 342 symbols exported
```

---

## 📋 Implementation Roadmap

### **Phase 1: Core Spine Registry** (Completed ✅)
1. ✅ Created `scripts/generate_missing_inits.py`
2. ✅ Generated 28 missing `__init__.py` files
3. ✅ Established spine concept in architecture docs

### **Phase 2: Service Registry (Next Steps)**
1. **Create `src/spine/registry.py`** with SpineRegistry class
2. **Create `src/spine/module_registry.json`** with module specs
3. **Update `src/spine/__init__.py`** to export registry
4. **Add spine validation** to hygiene command

### **Phase 3: Module Migration (Incremental)**
5. **Identify critical modules** (orchestration, consciousness, ai)
6. **Update their `__init__.py`** to register with spine
7. **Update consumers** to use `get_service()` instead of imports
8. **Validate with tests** that spine wiring works

### **Phase 4: Full Spine Integration**
9. **Migrate all 157 modules** to spine pattern
10. **Remove redundant imports** from __init__.py files
11. **Add dependency validation** in spine
12. **Generate dependency graphs** from registry

---

## 🔬 Example: Orchestration Module Migration

### **Before (Manual Wiring)**
```python
# src/orchestration/__init__.py
"""Orchestration module with manual wiring"""

from src.orchestration.unified_orchestrator import UnifiedAIOrchestrator
from src.orchestration.agent_orchestration_hub import AgentOrchestrationHub
from src.consciousness.consciousness_bridge import ConsciousnessBridge
from src.ai.ollama_integration import OllamaIntegration

__all__ = [
    "UnifiedAIOrchestrator",
    "AgentOrchestrationHub",
    "ConsciousnessBridge",  # Why exported here?
    "OllamaIntegration",    # Coupling to other modules
]
```

### **After (Spine-Wired)**
```python
# src/orchestration/__init__.py
"""Orchestration module - spine-wired

This module is spine-wired. See src/spine/module_registry.json
for centralized configuration and public API definition.
"""

from src.spine import register_service
from src.orchestration.unified_orchestrator import UnifiedAIOrchestrator

# Register primary service
orchestrator = UnifiedAIOrchestrator()
register_service("orchestration.hub", orchestrator)

__all__ = []  # Spine handles exports
```

```python
# src/orchestration/unified_orchestrator.py
from src.spine import get_service

class UnifiedAIOrchestrator:
    def __init__(self):
        # Dependencies through spine
        self.consciousness = get_service("consciousness.bridge")
        self.ollama = get_service("integration.ollama")

    def dispatch_task(self, task):
        # Use injected services
        if self.consciousness:
            self.consciousness.validate_context(task)
        return self.ollama.execute(task)
```

---

## ✅ Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| **Centralization** | 1 registry file | Count config files |
| **Coverage** | 100% of modules | `spine.validate_coverage()` |
| **Circular Imports** | 0 detected | `spine.check_circular_deps()` |
| **Lazy Loading** | <100ms startup | Time spine initialization |
| **Health Checks** | All modules pass | `hygiene --fast` exit code |

---

## 🚀 Next Steps

### **Immediate (This Session)**
1. Create `src/spine/registry.py` with SpineRegistry implementation
2. Populate `src/spine/module_registry.json` with 5-10 key modules
3. Update `src/spine/__init__.py` to export registry functions
4. Add spine health check to `hygiene` command

### **Short-term (This Week)**
5. Migrate 3-5 critical modules (orchestration, consciousness, ai)
6. Write integration tests for spine pattern
7. Document migration guide for remaining modules
8. Add `spine_sync` command to regenerate configs

### **Long-term (Future)**
9. Migrate all 157 modules to spine pattern
10. Generate dependency graphs from registry
11. Add visual spine explorer tool
12. Integrate with VSCode extension for autocomplete

---

**Created:** 2026-01-02
**Vision:** Spine as universal connector and service registry
**Impact:** 100+ init files → 1 central registry
**Status:** Ready for Phase 2 implementation
