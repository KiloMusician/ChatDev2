# Dashboard & Interface Consolidation Plan
**Date:** 2026-02-28  
**Status:** 🚧 In Progress  
**Goal:** Consolidate 19 dashboard files + 4+ browser variants into unified professional desktop application

## Executive Summary

**Problem:** Dashboard ecosystem is fragmented (19 files, 6 health monitors, 3 API layers, 4+ browser variants)  
**Solution:** Apply wizard navigator consolidation pattern - create canonical implementations with compatibility shims  
**Timeline:** 4-6 weeks  
**Impact:** -58% file reduction, improved UX, professional native Windows app

## Current State Inventory

### Dashboard Files (19 Total)

#### Backend/Data Collection
- ✅ **autonomy_dashboard.py** (435 lines) - Phase 3 real-time monitoring [KEEP]
- ✅ **metrics_dashboard_api.py** (422 lines) - FastAPI backend [KEEP]
- ⚠️ system_dashboard.py - System status [EVALUATE]

#### Health Monitors (6 variants - CONSOLIDATE)
- health_dashboard.py
- healing_dashboard.py
- ecosystem_health_dashboard.py
- launch_health_dashboard.py
- testing_dashboard.py (src/diagnostics/)
- test_dashboard_healing_integration.py (tests/)

#### API Layers (3 variants - CLARIFY or MERGE)
- dashboard_api.py (src/web/)
- metrics_dashboard_api.py (src/observability/) [CANONICAL]
- token_metrics_dashboard.py (src/tools/)

#### Utilities
- dashboard.py (scripts/)
- tool_dashboard.py (scripts/)
- start_metrics_dashboard.py (scripts/)
- monitoring_dashboard.json (data/)

#### Frontend
- dashboard-viewer.js (web/modular-window-server/)

#### SimulatedVerse Extensions (3 files)
- quantum-dashboard.ts
- chatdev-dashboard-enhancement.js
- comparative-kpi-dashboard.js

### Interactive Browser Variants (4+ versions - UNIFY)

| File | Framework | Lines | Status | Notes |
|------|-----------|-------|--------|-------|
| **Interactive-Context-Browser.py** | PyQt5 | 311 | ✅ Operational | Clean, well-structured |
| **ContextBrowser_DesktopApp.py** | tkinter | 627 | ✅ Operational | Dark theme, Streamlit integration |
| Enhanced-Interactive-Context-Browser.py | Streamlit | ? | ⚠️ Unknown | Multiple versions |
| Enhanced-Interactive-Context-Browser-v2.py | Streamlit | ? | ⚠️ Unknown | V2 iteration |
| Enhanced-Interactive-Context-Browser-Fixed.py | Streamlit | ? | ⚠️ Unknown | Bug fix version |
| Enhanced_Interactive_Context_Browser.py | ? | ? | ⚠️ Unknown | Underscore variant |

**Recommendation:** Choose **PyQt5** as canonical (more professional, better features, smaller footprint than Streamlit)

## Consolidation Strategy

### Phase 1: Health Monitor Unification (Week 1)
**Goal:** 6 health monitors → 1 canonical `health_dashboard_consolidated.py`

**Architecture:**
```python
# src/observability/health_dashboard_consolidated.py
class HealthDashboard:
    """Unified health monitoring for all NuSyQ ecosystem components."""
    
    def __init__(self):
        self.monitors = {
            'system': SystemHealthMonitor(),
            'healing': HealingStatusMonitor(),
            'ecosystem': EcosystemHealthMonitor(),
            'testing': TestingStatusMonitor(),
        }
    
    def get_unified_health(self) -> HealthSnapshot:
        """Aggregate all health metrics into single snapshot."""
        pass
    
    def get_health_by_category(self, category: str) -> CategoryHealth:
        """Get specific health category (system/healing/ecosystem/testing)."""
        pass
```

**Compatibility Shims:**
```python
# scripts/health_dashboard.py (shim)
from src.observability.health_dashboard_consolidated import HealthDashboard
# Redirect to consolidated version with deprecation warning
```

**Deprecation Timeline:**
- Week 1: Create consolidated version + shims
- Week 2: Update all imports across codebase
- Week 3-4: 30-day deprecation notice in logs
- Week 5: Remove old files

### Phase 2: Browser Unification (Week 2)
**Goal:** 4+ browser variants → 1 canonical `unified_context_browser.py`

**Framework Choice:** **PyQt5** (Rationale: Professional look, native performance, cross-platform)

**Architecture:**
```python
# src/interface/unified_context_browser.py
class UnifiedContextBrowser(QtWidgets.QMainWindow):
    """
    Professional desktop context browser combining best features from all variants.
    
    Features:
    - PyQt5 native widgets (fast, professional)
    - Dark theme with Material Design influence
    - Real-time metrics from autonomy_dashboard
    - AI party system from Enhanced-Wizard-Navigator
    - Repository analysis from RepositoryCompendium
    - Plotly/matplotlib visualizations
    - Electron packaging support
    """
    
    def __init__(self):
        super().__init__()
        self.metrics_client = MetricsDashboardClient()  # Connect to API
        self.wizard_navigator = EnhancedWizardNavigator()  # AI party system
        self.repo_analyzer = RepositoryCompendium()
        self._init_modern_ui()
    
    def _init_modern_ui(self):
        """Initialize professional UI with tabs, metrics, visualizations."""
        # Status bar with real-time metrics
        # Tab system: Overview, Files, Functions, Classes, Metrics, AI Party
        # Dark theme with accent colors
        # Native dialogs and file pickers
        pass
```

**Feature Migration Matrix:**

| Feature | Source File | Status |
|---------|-------------|--------|
| PyQt5 widgets | Interactive-Context-Browser.py | ✅ Keep |
| Dark theme | ContextBrowser_DesktopApp.py | ✅ Enhance |
| Streamlit integration | launch_context_browser_app.py | ⚠️ Remove (replace with native) |
| AI party system | Enhanced-Wizard-Navigator.py | ✅ Integrate |
| Metrics visualization | autonomy_dashboard.py | ✅ Add new feature |

### Phase 3: Integrated Dashboard App (Week 3)
**Goal:** Create unified desktop app combining browser + dashboard + AI navigator

**Architecture:**
```python
# src/interface/nusyq_unified_desktop.py
class NuSyQDesktopApp(QtWidgets.QMainWindow):
    """
    Unified NuSyQ Desktop Application
    
    Combines:
    - Context Browser (repo analysis)
    - Metrics Dashboard (real-time monitoring)
    - Wizard Navigator (AI party exploration)
    - Health Monitor (system status)
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NuSyQ Desktop — Quantum Development Environment")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Core components
        self.browser = UnifiedContextBrowser()
        self.dashboard = HealthDashboard()
        self.metrics_api = MetricsDashboardClient()
        self.wizard = EnhancedWizardNavigator()
        
        self._init_unified_ui()
```

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 NuSyQ Desktop — Quantum Development Environment          ⚙️🔔│
├─────────────────────────────────────────────────────────────────┤
│ 📂 Browser | 📊 Dashboard | 🧙 Navigator | ⚕️ Health | 🤖 AI   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Main Content Area - Tabbed Interface]                        │
│                                                                 │
│  Tab: Dashboard                                                │
│  ┌─────────────────┬─────────────────┬─────────────────┐      │
│  │ Task Queue: 42  │ PR Success: 85% │ Model Usage     │      │
│  │ ✅ Ready: 12    │ Auto-merge: 34  │ Ollama: 45%     │      │
│  │ ⏳ Pending: 30  │ Rejected: 3     │ ChatDev: 30%    │      │
│  └─────────────────┴─────────────────┴─────────────────┘      │
│                                                                 │
│  [Real-time metrics chart with plotly]                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Status: ✅ All systems operational | Consciousness: Level 7.2  │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 4: Modern UI Enhancements (Week 4)
**Features to Add:**

#### Visual Improvements
- **Material Design Dark Theme** - Modern color palette (#212121 base, #00BCD4 accent)
- **Fluent Design Elements** - Subtle shadows, acrylic effects, rounded corners
- **Status Indicators** - Real-time health badges (🟢🟡🔴) with animations
- **Chart Library** - Plotly for interactive metrics visualization
- **System Tray** - Minimize to tray with notifications

#### Functional Enhancements
- **Real-time Metrics Stream** - WebSocket connection to metrics_dashboard_api
- **AI Party Integration** - Chat with AI companions directly in app
- **Quick Actions** - Keyboard shortcuts (Ctrl+/, Ctrl+K for command palette)
- **Search Everything** - Fuzzy search across files, functions, classes, metrics
- **Context Menus** - Right-click actions for files, functions, etc.

#### Data Visualization
```python
# Add to unified app
def _create_metrics_charts(self):
    """Create interactive Plotly charts for metrics."""
    
    # Task queue trend (line chart)
    self.task_queue_chart = self._plotly_line_chart(
        x=timestamps, y=queue_sizes, title="Task Queue Over Time"
    )
    
    # Risk distribution (pie chart)
    self.risk_chart = self._plotly_pie_chart(
        values=[auto, review, proposal, blocked],
        labels=["Auto (<0.3)", "Review (0.3-0.6)", "Proposal (0.6-0.8)", "Blocked (>0.8)"],
        title="Risk Distribution"
    )
    
    # Model utilization (bar chart)
    self.model_chart = self._plotly_bar_chart(
        x=["Ollama", "ChatDev", "LM Studio", "Copilot"],
        y=[ollama_count, chatdev_count, lmstudio_count, copilot_count],
        title="Model Invocations (Last 24h)"
    )
```

### Phase 5: Electron Packaging (Week 5)
**Goal:** Professional Windows installer for distribution

**Build Process:**
```bash
# 1. Build PyQt5 app as standalone
python -m PyInstaller src/interface/nusyq_unified_desktop.py \
  --windowed \
  --onefile \
  --icon=assets/nusyq_icon.ico \
  --name="NuSyQ Desktop"

# 2. Package with Electron (optional - for auto-updates)
cd SimulatedVerse/templates/desktop/electron
npm install
npm run build
npm run dist:electron  # Creates NuSyQ-Desktop-Setup-1.0.0.exe
```

**Installer Features:**
- ✅ Native Windows installer (.exe)
- ✅ Desktop shortcut
- ✅ Start menu entry
- ✅ Uninstaller
- ⚠️ Code signing (requires certificate)
- ⚠️ Auto-updates (optional - requires update server)

### Phase 6: Testing & Documentation (Week 6)
**Deliverables:**

#### Testing
- [ ] Unit tests for consolidated modules
- [ ] Integration tests for unified app
- [ ] UI tests with pytest-qt
- [ ] Performance benchmarks (startup time, memory usage)

#### Documentation
- [ ] USER_GUIDE.md - End-user documentation
- [ ] DEVELOPER_GUIDE.md - Extension/customization guide
- [ ] MIGRATION_GUIDE.md - How to update imports from old files
- [ ] ARCHITECTURE.md - Technical documentation

## File Reduction Target

### Before Consolidation (19 files)
- 16 files in NuSyQ-Hub
- 3 files in SimulatedVerse

### After Consolidation (8 files) — 58% reduction
1. **src/observability/health_dashboard_consolidated.py** - Unified health monitoring
2. **src/observability/autonomy_dashboard.py** - Real-time metrics [KEEP]
3. **src/observability/metrics_dashboard_api.py** - FastAPI backend [KEEP]
4. **src/interface/unified_context_browser.py** - Canonical browser
5. **src/interface/nusyq_unified_desktop.py** - Integrated desktop app
6. **scripts/launch_nusyq_desktop.py** - Launcher script
7. **data/monitoring_dashboard.json** - Configuration [KEEP]
8. **web/modular-window-server/public/js/dashboard-viewer.js** - Optional web viewer [KEEP]

**Compatibility shims** (8 files - deprecation warnings only):
- scripts/health_dashboard.py → health_dashboard_consolidated
- scripts/healing_dashboard.py → health_dashboard_consolidated
- scripts/ecosystem_health_dashboard.py → health_dashboard_consolidated
- scripts/launch_health_dashboard.py → health_dashboard_consolidated
- src/interface/Interactive-Context-Browser.py → unified_context_browser
- src/interface/ContextBrowser_DesktopApp.py → unified_context_browser
- src/interface/Enhanced-Interactive-Context-Browser*.py → unified_context_browser
- scripts/start_metrics_dashboard.py → launch_nusyq_desktop

## Technology Stack

### Core Technologies
- **GUI Framework:** PyQt5 6.7+ (native widgets, cross-platform)
- **Visualization:** Plotly 5.x (interactive charts)
- **API Client:** httpx (async metrics fetching)
- **AI Integration:** Ollama SDK, ChatDev bridge
- **Packaging:** PyInstaller + Electron Builder (optional)

### UI Theme
- **Base:** Material Design Dark Theme
- **Primary:** #212121 (dark gray)
- **Accent:** #00BCD4 (cyan)
- **Success:** #4CAF50 (green)
- **Warning:** #FF9800 (orange)
- **Error:** #F44336 (red)
- **Typography:** Segoe UI (Windows), San Francisco (macOS)

### Dependencies to Add
```txt
PyQt5>=6.7.0
plotly>=5.18.0
httpx>=0.27.0
pandas>=2.2.0
numpy>=1.26.0
```

## Migration Path

### Week 1: Create Core Consolidated Modules
- [x] Create health_dashboard_consolidated.py
- [ ] Migrate all 6 health monitors into unified module
- [ ] Create compatibility shims with deprecation warnings
- [ ] Add tests for consolidated module

### Week 2: Browser Unification
- [ ] Create unified_context_browser.py (PyQt5 base)
- [ ] Migrate features from all 4+ browser variants
- [ ] Add dark theme with Material Design
- [ ] Create compatibility shims for old browsers
- [ ] Add tests for unified browser

### Week 3: Integrated Desktop App
- [ ] Create nusyq_unified_desktop.py
- [ ] Integrate browser + dashboard + metrics
- [ ] Add tabbed interface with 5 main sections
- [ ] Implement status bar with real-time updates
- [ ] Add system tray integration

### Week 4: UI/UX Enhancements
- [ ] Add Plotly charts for metrics visualization
- [ ] Implement command palette (Ctrl+K)
- [ ] Add keyboard shortcuts
- [ ] Create context menus
- [ ] Add fuzzy search across all content
- [ ] Polish theme and animations

### Week 5: Packaging & Distribution
- [ ] Configure PyInstaller for standalone build
- [ ] Test on clean Windows VM
- [ ] Configure Electron packaging (optional)
- [ ] Create installer with electron-builder
- [ ] Test installer on multiple Windows versions

### Week 6: Documentation & Testing
- [ ] Write USER_GUIDE.md
- [ ] Write DEVELOPER_GUIDE.md
- [ ] Write MIGRATION_GUIDE.md
- [ ] Add UI tests with pytest-qt
- [ ] Performance benchmarks
- [ ] Update all imports across codebase

## Success Metrics

- ✅ 58% file reduction (19 → 8 canonical files)
- ✅ Single native desktop app replacing 4+ browser variants
- ✅ Unified health monitoring (6 monitors → 1)
- ✅ Professional UI with dark theme
- ✅ Real-time metrics visualization
- ✅ <3s startup time
- ✅ <200MB memory footprint
- ✅ Windows installer ready for distribution
- ✅ 100% test coverage for new modules
- ✅ All old imports redirected with deprecation warnings

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes for existing code | HIGH | Use compatibility shims, 30-day deprecation |
| PyQt5 learning curve | MEDIUM | Start with existing PyQt5 code, reuse patterns |
| Performance issues with metrics | MEDIUM | Use async updates, caching, throttling |
| Electron packaging complexity | LOW | Optional - PyInstaller is primary method |
| User resistance to change | MEDIUM | Keep old launchers working via shims |

## Next Steps

**Immediate (Today):**
1. ✅ Create this consolidation plan
2. Create health_dashboard_consolidated.py skeleton
3. Start migrating first health monitor

**This Week:**
1. Complete health monitor consolidation
2. Create all compatibility shims
3. Run full test suite

**Next Week:**
1. Start browser unification
2. Prototype integrated desktop app
3. Design UI mockups

---

**Status:** 🟢 Ready to Execute  
**Owner:** Claude + User  
**Review Date:** 2026-03-07 (weekly check-ins)
