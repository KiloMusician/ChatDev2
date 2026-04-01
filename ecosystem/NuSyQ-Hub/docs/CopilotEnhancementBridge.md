# Copilot Enhancement Bridge

The VS Code extension integrates with the `CopilotEnhancementBridge` to enrich GitHub Copilot suggestions using project context.

## Usage
1. Open a file in VS Code within this repository.
2. Run the **Enhance Copilot Context** command from the command palette.
3. Suggestions from the bridge appear in the *Copilot Enhancement* output channel.

## Debugging
A launch configuration named **Debug Copilot Enhancement Bridge** is available. It runs `src/integration/advanced_chatdev_copilot_integration.py` for step‑through debugging of the bridge logic.
