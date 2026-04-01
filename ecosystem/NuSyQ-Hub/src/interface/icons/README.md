# NuSyQ Icon Library 🎨

**Version:** 1.0.0  
**Created:** 2026-02-28  
**Total Icons:** 22 SVG files

---

## Overview

Professional SVG icon library for the NuSyQ unified desktop application. All icons are:

- **Material Design inspired** - Clean, modern, recognizable
- **Scalable** - SVG format, no quality loss at any size
- **Theme-aware** - Use `currentColor` for easy theming
- **Lightweight** - Average 300-500 bytes per icon

---

## Icon Catalog

### Tab Icons (8)

| Icon | Filename | Usage |
|------|----------|-------|
| 📊 | `dashboard.svg` | Dashboard tab (4-grid layout) |
| 📁 | `repository.svg` | Repository analysis tab (folder with code) |
| ❤️ | `health.svg` | Health monitoring tab (heart with pulse) |
| 🧭 | `navigator.svg` | Navigator/explorer tab (compass) |
| ✅ | `tasks.svg` | Task management tab (checklist) |
| 📈 | `metrics.svg` | Metrics/charts tab (bar chart) |
| ⚙️ | `settings.svg` | Settings tab (gear) |
| 🐛 | `debug.svg` | Debug console tab (bug) |

### Action Icons (6)

| Icon | Filename | Usage |
|------|----------|-------|
| 💾 | `save.svg` | Save button (floppy disk) |
| 📤 | `export.svg` | Export button (upload arrow) |
| 🔄 | `refresh.svg` | Refresh button (circular arrow) |
| ❌ | `close.svg` | Close button (X) |
| ❓ | `about.svg` | About dialog (question mark in circle) |
| 🔍 | `search.svg` | Search functionality (magnifying glass) |

### Status Icons (4)

| Icon | Filename | Usage |
|------|----------|-------|
| ✅ | `success.svg` | Success/healthy status (checkmark in circle) |
| ⚠️ | `warning.svg` | Warning status (triangle with exclamation) |
| ❌ | `error.svg` | Error/critical status (X in circle) |
| ℹ️ | `info.svg` | Info messages (i in circle) |

### Sidebar Icons (2)

| Icon | Filename | Usage |
|------|----------|-------|
| 🕐 | `history.svg` | History panel (clock) |
| 🔖 | `bookmark.svg` | Bookmarks panel (ribbon) |

### Special Icons (2)

| Icon | Filename | Usage |
|------|----------|-------|
| 📊 | `charts.svg` | Chart/visualization (line chart with trend) |
| 🌗 | `theme.svg` | Theme toggle (sun/moon) |

---

## Usage

### Option 1: Icon Manager (Recommended)

```python
from src.interface.icon_manager import get_icon, Icons

# Get icon by name
dashboard_icon = get_icon(Icons.DASHBOARD, size=24)
self.tab_widget.setTabIcon(0, dashboard_icon)

# Custom color
blue_health_icon = get_icon(Icons.HEALTH, size=32, color='#2196F3')
self.health_button.setIcon(blue_health_icon)

# List all available icons
from src.interface.icon_manager import get_icon_manager
manager = get_icon_manager()
print(manager.list_icons())  # ['dashboard', 'repository', ...]
```

### Option 2: Direct QIcon Loading

```python
from PyQt5.QtGui import QIcon
from pathlib import Path

icon_dir = Path('src/interface/icons')
icon = QIcon(str(icon_dir / 'dashboard.svg'))
```

### Option 3: SVG in HTML/CSS

```html
<img src="src/interface/icons/dashboard.svg" width="24" height="24" />

<!-- Or inline -->
<svg ... fill="currentColor" stroke="#2196F3" ... />
```

---

## Icon Manager Features

The `icon_manager.py` utility provides:

1. **Caching** - Icons loaded once, cached for performance
2. **Color Overrides** - Change `currentColor` on-the-fly
3. **Scalability** - Render at any size (16px, 24px, 32px, 64px, etc.)
4. **Fallback** - Gray placeholder for missing icons
5. **Preloading** - Preload all icons for instant access

```python
from src.interface.icon_manager import get_icon_manager

manager = get_icon_manager()

# Preload all icons at 24px
manager.preload_all(size=24)

# Check if icon exists
if manager.has_icon('dashboard'):
    icon = manager.get_icon('dashboard')

# Clear cache to free memory
manager.clear_cache()
```

---

## Integration with Desktop App

### Phase 3 Desktop App (nusyq_unified_desktop.py)

Replace placeholder emojis with icons:

```python
# Before (Phase 3 - emoji placeholders)
self.tab_widget.addTab(self.dashboard_tab, "📊 Dashboard")

# After (Phase 4 - SVG icons)
from src.interface.icon_manager import get_icon, Icons

dashboard_icon = get_icon(Icons.DASHBOARD, size=24)
self.tab_widget.addTab(self.dashboard_tab, dashboard_icon, "Dashboard")
```

### System Tray Integration (Phase 4.4)

```python
from src.interface.icon_manager import get_icon, Icons

# System tray with health status
tray_icon = self.get_health_status_icon()  # success/warning/error
self.system_tray.setIcon(tray_icon)

def get_health_status_icon(self):
    health = self.get_system_health()
    if health == 'healthy':
        return get_icon(Icons.SUCCESS, size=16, color='#4CAF50')  # Green
    elif health == 'warning':
        return get_icon(Icons.WARNING, size=16, color='#FF9800')  # Orange
    else:
        return get_icon(Icons.ERROR, size=16, color='#F44336')  # Red
```

### Menu Actions (Phase 4)

```python
# File menu
save_action = QAction(get_icon(Icons.SAVE, size=16), '&Save', self)
export_action = QAction(get_icon(Icons.EXPORT, size=16), '&Export', self)

# View menu
refresh_action = QAction(get_icon(Icons.REFRESH, size=16), '&Refresh', self)
theme_action = QAction(get_icon(Icons.THEME, size=16), 'Toggle &Theme', self)
```

---

## Testing

Run the icon manager test:

```bash
cd src/interface
python icon_manager.py

# Expected output:
# 🎨 Icon Manager Test
# Icon directory: src/interface/icons
# Available icons: 22
# Icons: about, bookmark, charts, close, ...
# ✅ Loaded 'dashboard' icon: True
# ✅ Loaded 'health' icon with blue color: True
# ✅ Placeholder for missing icon: True
```

---

## Future Enhancements (Phase 5+)

1. **Animated Icons** - Add SMIL animations to SVGs (spinning refresh, pulsing notifications)
2. **Icon Variants** - Filled vs outlined versions
3. **Dark/Light Presets** - Pre-colored icon sets for each theme
4. **Icon Font** - Convert SVGs to icon font for even easier usage
5. **Electron Integration** - Package icons in Electron app resources

---

## Technical Details

### SVG Structure

```xml
<svg xmlns="http://www.w3.org/2000/svg" 
     width="24" 
     height="24" 
     viewBox="0 0 24 24" 
     fill="none" 
     stroke="currentColor"  <!-- Theme-aware color -->
     stroke-width="2" 
     stroke-linecap="round" 
     stroke-linejoin="round">
  <!-- Icon path data -->
</svg>
```

### Key Attributes

- `viewBox="0 0 24 24"` - Scalable coordinate system
- `stroke="currentColor"` - Inherits text color from theme
- `stroke-width="2"` - Line thickness (consistent across all icons)
- `fill="none"` - Outline style (Material Design)

---

## License

Part of the NuSyQ-Hub project. All icons are original creations or Material Design inspired (Apache 2.0 compatible).

---

**Icon Library Complete** ✅  
**Phase 4.1 Status:** COMPLETE (22/22 icons)  
**Next:** Phase 4.2 (Animation Framework)
