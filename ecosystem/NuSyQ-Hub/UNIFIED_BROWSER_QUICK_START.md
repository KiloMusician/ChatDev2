# 🧠 Unified Browser — Quick Reference

## 🚀 Launch (30 seconds)

**Step 1: Ensure dependencies installed**
```bash
pip install PyQt5 plotly httpx
```

**Step 2: Launch**
```bash
python src/interface/unified_context_browser.py
```

**Result:** Professional desktop app with 5 tabs

---

## 🎯 What Can You Do?

### 📊 Dashboard Tab
**See system metrics in real-time**
- Task queue size (updated every 5 seconds)
- PR success rate
- Model usage distribution
- Overall system health indicator

**Try:** Just open the app, metrics auto-populate!

---

### 📂 Browser Tab  
**Analyze any Python repository**
1. Enter repository path (use `.` for current)
2. Click "Analyze"
3. See: files, functions, classes, imports count

**Try These:**
- `.` - Analyze NuSyQ-Hub
- `../NuSyQ` - Analyze NuSyQ root
- `../../SimulatedVerse` - Analyze SimulatedVerse

---

### 🧙 AI Navigator Tab
**Chat with AI party members**

**Ask questions like:**
- "Generate tests for this function"
- "Review my code for bugs"
- "Optimize this algorithm"
- "Document this class"
- "Find security issues"

**Or:** Click "🧙 Launch Full Wizard Navigator Experience" for the complete RPG environment

---

### ⚕️ Health Tab
**Check system health in one click**

1. Click "🔄 Refresh Health Status"
2. See health by category:
   - 🟢 **System** - Python version, disk space, services
   - 🟢 **Healing** - Self-healing activity (last 7 days)
   - 🟢 **Ecosystem** - 3 repos status
   - 🟢 **Testing** - pytest coverage

**Interpretation:**
- 🟢 Green = All good
- 🟡 Yellow = Minor issue, watch
- 🔴 Red = Needs attention

---

### 📈 Metrics Tab
**View detailed charts and statistics**

**Charts:**
1. **Task Queue Trend** - 24 hours of task activity
2. **Risk Distribution** - Low/Medium/High/Critical breakdown
3. **Model Utilization** - Ollama vs ChatDev vs Claude vs Copilot

**Note:** Charts save to `~/.nusyq_temp/metrics_chart.html` (open in browser)

---

## ⌨️ Pro Tips

### Keyboard Shortcuts
```
Ctrl+1      → Dashboard tab (quick metrics)
Ctrl+2      → Browser tab (code analysis)
Ctrl+3      → AI Navigator (ask questions)
Ctrl+4      → Health tab (system check)
Ctrl+5      → Metrics tab (visualizations)

Ctrl+K      → Command palette (search actions)
Ctrl+W      → Launch full Wizard Navigator
Ctrl+O      → Open repository dialog
Ctrl+Q      → Exit
F5          → Refresh all data
```

### Common Workflows

**🔍 Quick Code Analysis**
1. `Ctrl+2` (Browser tab)
2. Type repo path
3. Click Analyze
4. See stats in seconds

**🏥 Health Check**
1. `Ctrl+4` (Health tab)
2. Click refresh
3. Review status by category

**🤖 Ask AI Party**
1. `Ctrl+3` (AI Navigator)
2. Type question in chat box
3. Get instant response
4. Or click wizard for full experience

**📊 View Metrics**
1. `Ctrl+5` (Metrics tab)
2. Auto-updates every 5 seconds
3. Click charts to open in browser

---

## ❓ Troubleshooting

### Browser won't start
**Error:** `⚠️ PyQt5 not available`

**Fix:**
```bash
pip install --upgrade PyQt5
python src/interface/unified_context_browser.py
```

### Health check says "Not available"
**Fix:** Make sure you're in the right directory
```bash
cd C:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python src/interface/unified_context_browser.py
```

### Metrics not showing
**Fix:** Start the metrics API
```bash
# In another terminal:
python src/observability/metrics_dashboard_api.py
```

### Repository analysis fails
**Check:**
1. Path exists: `ls <path>`
2. Is a Python project (has .py files)
3. Not too large (performance)

---

## 🎨 Features At A Glance

| Feature | Tab | Shortcut | Action |
|---------|-----|----------|--------|
| **Real-time metrics** | Dashboard | Ctrl+1 | Auto-updates |
| **Code analysis** | Browser | Ctrl+2 | Analyze any repo |
| **AI chat** | Navigator | Ctrl+3 | Ask questions |
| **Health check** | Health | Ctrl+4 | Check system status |
| **Charts & stats** | Metrics | Ctrl+5 | View visualizations |
| **Command palette** | Any | Ctrl+K | Search & execute |
| **Wizard launcher** | Any | Ctrl+W | Full RPG experience |

---

## 🎯 Your First 2 Minutes

1. **Launch** (15 sec)
   ```bash
   python src/interface/unified_context_browser.py
   ```

2. **Check Health** (30 sec)
   - Press `Ctrl+4`
   - Click "🔄 Refresh Health Status"
   - See overall system status

3. **Analyze Code** (45 sec)
   - Press `Ctrl+2`
   - Type `.` and click "Analyze"
   - See project statistics

4. **Talk to AI** (30 sec)
   - Press `Ctrl+3`
   - Ask "Generate tests"
   - Get party response

**Total:** ~2 minutes ✅

---

## 💡 Power User Tips

### Combine Shortcuts
- **Quick workflow:** `Ctrl+2` → `Ctrl+3` → `Ctrl+4` (analyze, ask AI, check health)
- **System check:** `Ctrl+4` → `Ctrl+5` (health + metrics)
- **Full deep dive:** `Ctrl+W` then use wizard (launches Enhanced-Wizard-Navigator)

### Use Command Palette
- Press `Ctrl+K` for fuzzy search
- Quick access to any action
- Better than menu diving

### Metrics In Real-Time
- Metrics auto-update every 5 seconds
- Top bar shows: Tasks, PR Success, Consciousness
- Watch it react to system changes

### AI Party Interaction
- Simple questions: Use chat in tab
- Complex tasks: Launch full wizard
- Get second opinions: Ask different members

---

## 📚 Learn More

- **Full documentation:** [UNIFIED_BROWSER_IMPLEMENTATION_2026-02-28.md](UNIFIED_BROWSER_IMPLEMENTATION_2026-02-28.md)
- **Consolidation strategy:** [DASHBOARD_CONSOLIDATION_PLAN_2026-02-28.md](docs/DASHBOARD_CONSOLIDATION_PLAN_2026-02-28.md)
- **Health system:** [health_dashboard_consolidated.py](src/observability/health_dashboard_consolidated.py)
- **AI party:** [Enhanced-Wizard-Navigator.py](src/interface/Enhanced-Wizard-Navigator.py)

---

**Ready? Launch it now:**
```bash
python src/interface/unified_context_browser.py
```

Enjoy your unified development environment! 🚀
