# 🚀 Phase 3 Quick Start Card

## Launch Phase 3 Desktop App

```bash
python src/interface/nusyq_unified_desktop.py
```

---

## Interface Overview

### 8 Tabs (Left to Right)
1. **📊 Dashboard** - System metrics & health at a glance
2. **🔍 Repository** - Code analysis & metrics
3. **💚 Health** - System status (🟢🟡🔴)
4. **🧙 Navigator** - AI party members & chat
5. **📋 Tasks** - Queue monitoring & progress
6. **📈 Metrics** - Detailed analytics & charts
7. **⚙️ Settings** - Preferences & configuration
8. **🐛 Debug** - Console & command execution

### Left Sidebar (3 Panels)
- **History** - Recent actions
- **Bookmarks** - Favorite repos
- **Workspaces** - Multi-repo management

---

## Essential Keyboard Shortcuts

```
Tab Navigation:
  Ctrl+1 through Ctrl+8    Switch to tabs 1-8

Common Actions:
  Ctrl+O                   Open repository
  Ctrl+R                   Refresh all tabs
  Ctrl+E                   Export report
  Ctrl+W                   Launch AI Wizard
  Ctrl+K                   Command palette
  Ctrl+,                   Settings

Interface:
  Ctrl+\                   Toggle sidebar
  F11                      Fullscreen mode
  Ctrl+H                   Show history
  Ctrl+B                   Show bookmarks
  Ctrl+D                   Debug console
  Ctrl+Q                   Quit
```

---

## 5-Minute Workflow

### 1. Open & Analyze a Repository
```
1. Click 🔍 Repository tab
2. Click 📂 Browse or paste path
3. Click ▶️ Analyze
→ See: Files, functions, classes, imports
```

### 2. Check System Health
```
1. Click 💚 Health tab
2. Click 🔄 Refresh Health Status
→ See: 25+ health checks with status
```

### 3. Save for Later
```
1. Click ➕ Add Bookmark in sidebar
2. Name your bookmark
→ Quick access next time
```

### 4. Monitor Tasks
```
1. Click 📋 Tasks tab
2. See running/queued/completed tasks
3. Pause ⏸️ or Resume ▶️ as needed
```

### 5. Export Results
```
1. File menu → Export Report
2. Choose PDF or JSON
3. Select save location
→ Share results with team
```

---

## Status Bar (Bottom)

```
[Status Message]              [Metrics]             [Health 🟢]
Status updates               Queue: 0 | CPU: 2%    Overall status
                             Health: healthy
```

---

## Menu Bar

### File Menu 📁
- Open Repository (Ctrl+O)
- Open Recent
- Export Report (Ctrl+E)
- Export Metrics
- Exit (Ctrl+Q)

### View Menu 👁️
- Refresh All (Ctrl+R)
- Settings (Ctrl+,)
- History (Ctrl+H)
- Bookmarks (Ctrl+B)
- Toggle Sidebar (Ctrl+\)
- Fullscreen (F11)

### Tools Menu 🔧
- Launch Wizard (Ctrl+W)
- Terminal (Ctrl+`)
- Debug Console (Ctrl+D)
- Plugin Manager

### Help Menu ❓
- Command Palette (Ctrl+K)
- Keyboard Shortcuts
- About

---

## Settings You Can Configure

```
Theme             Dark mode (Light in Phase 4)
Auto-Refresh      Enable/disable auto updates
Refresh Interval  5, 10, 30, 60 seconds
API Endpoint      http://127.0.0.1:8000 (default)
Language          English (others in Phase 4)
Notifications     On/off
History Retention 7, 30, 90, 365 days
```

---

## State Persistence

The app **automatically remembers**:
- ✅ Window size & position
- ✅ Last repository opened
- ✅ Current tab when you closed it
- ✅ User preferences
- ✅ Action history (30 days)

Location: `C:\Users\{user}\.nusyq_state\` (Windows)

---

## Troubleshooting Quick Links

| Problem | Solution |
|---------|----------|
| Window blank | Check PyQt5 installed: `pip install PyQt5` |
| Metrics blank | Verify metrics_dashboard_api.py running (port 8000) |
| Analysis fails | Check repo path is valid and readable |
| Settings won't save | Verify ~/.nusyq_state/ is writable |
| Wizard won't launch | Ensure Enhanced-Wizard-Navigator.py exists in src/interface/ |

---

## Power User Tips

### 💡 Command Palette (Ctrl+K)
Quickly access any command:
- Opens search dropdown
- Start typing command name
- Hit Enter to execute

### 💡 Multi-Window
Run Phase 2 and Phase 3 simultaneously:
```bash
# Terminal 1: Phase 2 (Browser)
python src/interface/unified_context_browser.py

# Terminal 2: Phase 3 (Desktop)
python src/interface/nusyq_unified_desktop.py
```

### 💡 Quick Repository Switch
1. Add multiple workspaces in sidebar
2. Click workspace to switch instantly
3. Repo path auto-restores

### 💡 History Tracking
- All actions logged automatically
- Export history as JSON for audit trail
- Clear old entries in Settings if needed

### 💡 Debug Commands
In Debug tab, try:
```
python --version
pip list
git status
dir (Windows) or ls (Linux)
pip show PyQt5
```

---

## What's Different from Phase 2

| Aspect | Phase 2 | Phase 3 |
|--------|---------|---------|
| Window | Shared | Separate app |
| Tabs | 5 basic | 8 advanced |
| Sidebar | None | Extensive |
| Persistence | None | Full |
| Tasks | No | Yes |
| Settings | No | Yes |
| Settings Tab | No | Yes |
| Debug Console | No | Yes |
| Shortcuts | 9 | 40+ |

**Result**: Phase 3 = Professional desktop app status

---

## Phase 3 vs Alternatives

```
Phase 3 (NuSyQ)          VS          VS Code Copilot
✅ Native desktop app              Browser-based
✅ 100% offline capable            Cloud-dependent  
✅ Multi-workspace support          Single file focus
✅ Task monitoring                  No queue visibility
✅ Export reports                   Screenshot only
✅ Free & open source              Proprietary
✅ Customizable theme               Fixed UI
```

---

## Coming in Phase 4

- 🎨 Icon library (SVG icons for all tabs)
- ✨ UI animations
- 🎭 Light theme variant
- 🖱️ Drag-and-drop support
- 🔌 Plugin system (full)
- 🖥️ System tray icon
- 📊 Advanced charts

---

## Getting Help

1. **Command Palette**: Ctrl+K → search for help
2. **Shortcuts Panel**: Help → Keyboard Shortcuts
3. **About Dialog**: Help → About
4. **Debug Console**: Ctrl+D for system inspection
5. **Settings**: Ctrl+, to tweak behavior

---

## Session State Recovery

If app crashes:
```
1. Relaunch: python src/interface/nusyq_unified_desktop.py
2. State automatically restores:
   ✓ Window size & position
   ✓ Open tabs
   ✓ Last repository
   ✓ Preferences
3. History preserved (query it from sidebar)
```

---

**Phase 3 Status**: ✅ **READY TO USE**

**Launch command:**
```bash
python src/interface/nusyq_unified_desktop.py
```

Enjoy your new native desktop development environment! 🚀
