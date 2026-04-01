# UI Rescue Pack - Strong Shell & HUD

**Infrastructure-First UI system** for CoreLink Foundation's Culture-Ship ecosystem.

## 🚀 Quick Start

### Manual Setup (Required)
Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "devshell": "node tools/devshell/server.mjs",
    "open:rescue": "node -e \"console.log('Open http://localhost:3030 after devshell starts')\"",
    "hud:rescue": "npm run devshell & sleep 1 && npm run open:rescue",
    "cascade": "node scripts/cascade.mjs",
    "scan:todos": "node scripts/scan-todos.mjs",
    "scan:dupes": "node scripts/scan-dupes.mjs", 
    "scan:imports": "node scripts/scan-imports.mjs",
    "fix:imports": "node scripts/fix-imports.mjs",
    "fix:dupes": "node scripts/fix-dupes.mjs",
    "smoke:game": "node scripts/smoke-game.mjs"
  }
}
```

### Run the Rescue HUD
```bash
npm run devshell  # Start strong shell on port 3030
```

Open http://localhost:3030 in your browser.

## 📱 Features

### **Strong Shell API** (`tools/devshell/server.mjs`)
- Zero-dependency API server
- Task queue management (JSON files in `/tasks/`)
- Cascade & smoke test integration
- CORS-enabled for frontend consumption

### **Responsive Rescue HUD** (`ui/rescue/`)
- **Mobile-first** responsive design
- **Live ASCII Viewport** with 4 themes (matrix, amber, classic, cogmind)
- **Big Red Button** → triggers existing `cascade.mjs`
- **Task Queue Panel** shows Culture-Ship operations
- **Sound feedback** & fullscreen support

### **Key Controls**
- **BIG RED BUTTON**: Runs `npm run cascade`
- **Smoke**: Runs `npm run smoke:game`
- **+ Task**: Add items to Culture-Ship queue
- **🔈**: Audio feedback toggle
- **⛶**: Fullscreen mode

## 🎮 Game Integration

### **Title/Boot Sequence**
- **New Game**: Boot sequence with progressive unlocks
- **Load**: Save slot management (ready for implementation)
- **Settings**: Mobile/desktop toggles, themes
- **Temple**: Links to Culture-Ship Temple system

### **ASCII Viewport Themes**
- **matrix**: Green digital rain aesthetic
- **amber**: Classic terminal amber glow
- **classic**: Clean monochrome
- **cogmind**: Blue-green sci-fi styling

## 🏗️ Architecture

### **API Endpoints**
```
GET  /api/health     - System status
GET  /api/tasks      - Task queue contents  
POST /api/enqueue    - Add task to queue
POST /api/run/cascade - Trigger cascade
POST /api/run/smoke  - Run smoke tests
GET  /api/hud        - HUD configuration
```

### **File Structure**
```
ui/rescue/
├── index.html      # Main HUD interface
├── styles.css      # Mobile-first responsive CSS
├── app.js          # ASCII renderer + API integration
└── README.md       # This file

tools/devshell/
└── server.mjs      # Strong shell API server

tasks/
└── seed.json       # Initial task queue
```

## 🔧 Next Steps

1. **Wire to Main App**: Mount rescue HUD in existing router
2. **Health Monitoring**: Read `/reports/` for system status
3. **ASCII Scenes**: Map game state → viewport scenes  
4. **Progressive Unlocks**: Hide UI elements until unlocked
5. **Save/Load**: JSON save slots under `/saves/`
6. **Live Logs**: Stream `/reports/` into logs panel

## 🚢 Culture-Ship Integration

The Rescue Pack integrates with your existing Culture-Ship systems:

- **Task Queue**: Feeds Culture-Ship mega-queue operations
- **Cascade**: Uses your existing `scripts/cascade.mjs`
- **Reports**: Reads from your `/reports/` directory
- **Zero-Token**: Operates entirely locally
- **Mobile-First**: Matches your responsive design philosophy

**The UI Rescue Pack provides a strong backbone for your sophisticated autonomous development ecosystem!**