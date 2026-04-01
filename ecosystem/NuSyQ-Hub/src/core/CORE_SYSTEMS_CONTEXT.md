# 🧠 Core Systems Directory Context

## 📋 Directory Purpose
**Primary Function**: Core system components that form the foundation of the KILO-FOOLISH ecosystem, including AI Coordinator, Architecture Scanner, main entry points, and essential system services.

## ✅ Files That BELONG Here

- **Main Entry Points**: Application launchers and primary execution files (`main.py`)
- **System Coordinators**: Central coordination systems (`ai_coordinator.py`)
- **Architecture Components**: System architecture scanning and analysis (`ArchitectureScanner.py`, `ArchitectureWatcher.py`)
- **Context Generators**: AI context generation and management (`AIContextGenerator.py`, `AIContextGenerator.ps1`)
- **Core Bridges**: Essential integration bridges and connectors
- **System Managers**: Core system management and lifecycle components
- **Foundation Classes**: Base classes and core abstractions

## ❌ Files That Do NOT Belong Here

- **AI Orchestration**: Belongs in `src/ai/` or `src/orchestration/`
- **Testing Files**: Belong in `tests/`
- **Development Tools**: Belong in `src/tools/`
- **Logging Systems**: Belong in `LOGGING/infrastructure/`
- **User Interfaces**: Belong in `src/interface/`
- **Specialized Systems**: ML, blockchain, cloud belong in their respective directories

## 🔗 Integration Points

- **AI Systems**: Provides foundation for `src/ai/` modules
- **Consciousness**: Core awareness systems in `src/consciousness/`
- **Architecture**: System structure analysis and monitoring
- **Context**: Central context management for all subsystems

## 🏷️ Required Tags

All files must include OmniTag/MegaTag headers with:
- **#CORE_SYSTEM** - Primary classification
- **#FOUNDATION** - If providing base functionality
- **#COORDINATOR** - If managing system coordination
- **#ARCHITECTURE** - If handling system structure

## 📊 Current Contents

- `main.py` - Primary application entry point
- `ai_coordinator.py` - Central AI coordination system
- `ArchitectureScanner.py` - System architecture analysis
- `ArchitectureWatcher.py` - Real-time architecture monitoring
- `AIContextGenerator.py` - AI context generation system
- `AIContextGenerator.ps1` - PowerShell context generator


---

## 🔄 Workflow Integration

### **Infrastructure Integration Status**
- **Chatdev Launcher**: ❌ Not Available
- **Testing Chamber**: ❌ Not Available
- **Quantum Automator**: ❌ Not Available
- **Ollama Integrator**: ❌ Not Available
- **Kilo Secrets**: ❌ Not Available

### **Workflow Capabilities**
Core system integration

### **Subprocess Management**
Core process management


### Subprocess Integration Guide

**Standard Core Integration:**
```python
# Import relevant modules
from core.core_coordinator import CoreCoordinator

# Initialize coordinator
coordinator = CoreCoordinator()

# Execute core operations
coordinator.execute_operations(parameters)
```


### **Rube Goldbergian Integration**
This directory integrates seamlessly with the modular KILO-FOOLISH workflow:
1. **ChatDev Integration**: Automated development task orchestration
2. **Ollama Bridge**: Local AI model integration with API fallback
3. **Testing Chamber**: Isolated development and testing environments
4. **Quantum Workflows**: Advanced workflow automation and optimization
5. **Consciousness Sync**: Repository awareness and memory integration

---

*This directory contains the foundational components that enable all other systems. All core, essential functionality should be centralized here.*
