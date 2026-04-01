# 🛠️ Tools Directory Context

## 📋 Directory Purpose
**Primary Function**: Development tools, utilities, launchers, and helper scripts that support the KILO-FOOLISH development workflow and system operations.

## ✅ Files That BELONG Here

- **Development Launchers**: System and tool launch scripts (`chatdev_launcher.py`, `kilo_dev_launcher.py`)
- **Testing Chambers**: Development testing environments (`chatdev_testing_chamber.py`)
- **Command Extractors**: Development workflow tools (`extract_commands.py`)
- **Build Tools**: Compilation, packaging, and deployment utilities
- **Development Utilities**: Code generation, scaffolding, and automation tools  
- **Helper Scripts**: General development assistance and workflow automation
- **CLI Tools**: Command-line interfaces for development operations

## ❌ Files That Do NOT Belong Here

- **Core System Logic**: Belongs in `src/core/`
- **AI Orchestration**: Belongs in `src/ai/` or `src/orchestration/`
- **Testing Files**: Belong in `tests/` (except testing chambers/environments)
- **Production Code**: Business logic belongs in appropriate domain directories
- **Configuration**: Belongs in `config/` or `src/setup/`

## 🔗 Integration Points

- **Core Systems**: Launches and manages `src/core/` components
- **AI Systems**: Provides tools for `src/ai/` development
- **ChatDev**: Integration tools for ChatDev workflow
- **Development Workflow**: Supports entire development pipeline

## 🏷️ Required Tags

All files must include OmniTag/MegaTag headers with:
- **#DEVELOPMENT_TOOL** - Primary classification
- **#LAUNCHER** - If launching other systems
- **#UTILITY** - If providing helper functionality
- **#WORKFLOW** - If supporting development workflow

## 📊 Current Contents

- `ChatDev-Party-System.py` - AI agents party orchestrator
- `chatdev_testing_chamber.py` - Development testing environment
- `consolidation_planner.py` - Safe consolidation utilities
- `extract_commands.py` - Development command extraction utility
- `health_restorer.py` - System health restoration tool
- `kilo_dev_launcher.py` - KILO-FOOLISH development launcher
- `kilo_discovery_system.py` - Component discovery and indexing
- `launch-adventure.py` - Adventure launcher script
- `safe_consolidator.py` - Helper for safe file consolidations
- `structure_organizer.py` - Repository structure organizer


---

## 🔄 Workflow Integration

- ### **Infrastructure Integration Status**

- **Chatdev Launcher**: ❌ Not Available
  **Testing Chamber**: ❌ Not Available
  **Quantum Automator**: ❌ Not Available
  **Ollama Integrator**: ❌ Not Available
  **Kilo Secrets**: ❌ Not Available
- **Testing Chamber**: ❌ Not Available
- **Quantum Automator**: ❌ Not Available
- **Ollama Integrator**: ❌ Not Available
- **Kilo Secrets**: ❌ Not Available

### **Workflow Capabilities**

ChatDev Launcher, Testing Chamber, Development utilities

### **Subprocess Management**

Tool launching, environment setup, workflow automation

### Subprocess Integration Guide

**Standard Tools Integration:**

```python
from tools.tools_coordinator import ToolsCoordinator

# Initialize coordinator
coordinator = ToolsCoordinator()

# Execute tools operations
coordinator.execute_operations(parameters)
```  


### **Rube Goldbergian Integration**

This directory integrates seamlessly with the modular KILO-FOOLISH workflow:
This directory integrates seamlessly with the modular KILO-FOOLISH workflow:

1. **ChatDev Integration**: Automated development task orchestration
2. **Ollama Bridge**: Local AI model integration with API fallback
3. **Testing Chamber**: Isolated development and testing environments
4. **Quantum Workflows**: Advanced workflow automation and optimization
5. **Consciousness Sync**: Repository awareness and memory integration

---

*This directory centralizes all development tools and utilities. Production code should not be placed here - only development support tools.*
