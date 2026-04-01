# ChatDev VS Code Extension Quick Start

This extension exposes commands that run ChatDev tools from inside VS Code and shows their logs in a dedicated panel.

## Setup
1. Open this repository in VS Code.
2. Install the extension dependencies:
   ```bash
   cd src/integration/vscode-extension
   npm install
   ```
3. Press `F5` to launch the extension in a new Extension Development Host window.

## Commands
- **Start ChatDev Party** (`startChatDevParty`) – launches `src/tools/ChatDev-Party-System.py` in an integrated terminal.
- **Launch ChatDev Task** (`launchChatDevTask`) – runs `src/integration/chatdev_launcher.py` in an integrated terminal.

Running either command opens the **ChatDev Logs** webview which streams updates from `logs/chatdev.log`.
