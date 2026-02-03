# ChatDev Consolidation Guide
## Overview
This guide provides instructions for migrating from the previous modular structure to the new consolidated `unified_chatdev_bridge.py` module.
## Deprecated Modules
The following modules have been deprecated and will be removed in future releases:
- chatdev_integration
- chatdev_launcher
- chatdev_service
- chatdev_llm_adapter
- copilot_chatdev_bridge
- advanced_chatdev_copilot_integration
## New Module Structure
All functionalities are now encapsulated within the `ChatDevOrchestrator` class. You should use this class to interact with the various modules.
## Migration Steps
### 1. Update Imports
Replace direct imports of individual modules with the `ChatDevOrchestrator`.
**Before:**