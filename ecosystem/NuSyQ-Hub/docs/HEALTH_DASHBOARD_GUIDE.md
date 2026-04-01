# 🏥 Self-Diagnostic Health Dashboard - User Guide

**Enhanced Context Browser v2 with Integrated Diagnostics**

---

## 🚀 Quick Start

### Option 1: Python Launcher (Recommended)
```bash
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python scripts/launch_health_dashboard.py
```

### Option 2: Direct Streamlit Launch
```bash
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
streamlit run src/interface/Enhanced-Interactive-Context-Browser-v2.py
```

### Option 3: PowerShell Launcher
```powershell
cd c:\Users\keath\Desktop\Legacy\NuSyQ-Hub
python src/interface/Launch-ContextBrowserApp.ps1
```

**Dashboard URL**: http://localhost:8501

---

## 📊 Features Overview

### 🩺 Health Monitoring Page

Navigate to: **Navigation Menu → Health**

#### 1. **Real-Time Diagnostic Suite**
- Click **"Run Full Diagnostic Suite"** button
- Executes all self-diagnostic systems:
  - System Integration Checker
  - Health Verification
  - Repository Health

#### 2. **System Integration Status** 🔗
**What it shows:**
- Overall health score (0-100%)
- Ollama service status
- ChatDev integration status
- Copilot enhancement status
- Number of operational systems
- Issues detected count

**How to use:**
1. Click "Run Full Diagnostic Suite"
2. Expand "System Integration Status" section
3. View health score and metrics
4. Click "Detailed Report" to see full output

**Example Output:**
```
✅ Last check: 14:30:45
Overall Health: 70%
Systems Operational: 3
Issues Found: 2
```

#### 3. **Dependency Health Verification** ✅
**What it shows:**
- Import success rates
- Third-party package status
- AI integration status
- Standard library checks

**How to use:**
1. Expand "Dependency Health Verification"
2. View success rate metrics
3. Check color-coded status indicators:
   - 🟢 Green: ≥80% success
   - 🟡 Yellow: 50-79% success
   - 🔴 Red: <50% success

**Example Metrics:**
- Check 1: 50.0% (1/2 imports)
- Check 2: 60.0% (9/15 third-party)
- Check 3: 100.0% (14/14 standard library)

#### 4. **Repository Health** 🔧
**What it checks:**
- ✅ src/ directory
- ✅ config/ directory
- ✅ tests/ directory
- ✅ docs/ directory
- ✅ requirements.txt
- ✅ .git directory

**Health Score:**
- 100%: All components present
- 80-99%: Minor missing components
- <80%: Critical components missing

#### 5. **Auto-Refresh Mode** 🔄
- Toggle "Auto-refresh (30s)" checkbox
- Dashboard automatically re-runs diagnostics every 30 seconds
- Perfect for continuous monitoring during development

---

## 🎯 Use Cases

### Use Case 1: Quick Health Check
**When:** Starting work session
**Steps:**
1. Launch dashboard: `python scripts/launch_health_dashboard.py`
2. Navigate to "Health" page
3. Click "Run Full Diagnostic Suite"
4. Review overall health score
5. Address any issues with <70% health

---

### Use Case 2: Continuous Monitoring
**When:** Running long development sessions or CI/CD
**Steps:**
1. Launch dashboard with auto-refresh
2. Enable "Auto-refresh (30s)" toggle
3. Keep dashboard open in separate monitor/window
4. Monitor health metrics in real-time

---

### Use Case 3: Troubleshooting Integration Issues
**When:** Ollama/ChatDev/Copilot not working
**Steps:**
1. Navigate to Health page
2. Run diagnostic suite
3. Expand "System Integration Status"
4. Check "Detailed Report" for specific errors
5. Fix issues based on recommendations
6. Re-run diagnostics to verify fixes

---

### Use Case 4: Dependency Validation
**When:** After pip install or environment changes
**Steps:**
1. Run diagnostic suite
2. Expand "Dependency Health Verification"
3. Check success rates
4. View full report for missing packages
5. Install missing dependencies
6. Re-verify

---

## 📈 Other Dashboard Pages

### Dashboard (Home)
- Repository statistics
- File type distribution
- Recent activity

### Analytics
- Code complexity metrics
- Dependency analysis
- Growth trends

### Architecture
- Module relationship graphs
- Import network visualization
- Dependency tree

### AI Insights
- AI-powered code analysis
- Consciousness bridge integration
- Quantum problem resolver insights

### Settings
- Theme selection (Light/Dark/Auto)
- Performance settings
- Integration configuration

---

## 🔧 Troubleshooting

### Issue: Dashboard won't start
**Solution:**
```bash
# Check Streamlit installation
pip install streamlit plotly pandas networkx streamlit-agraph

# Try alternative launch method
streamlit run src/interface/Enhanced-Interactive-Context-Browser-v2.py --server.port 8502
```

---

### Issue: Diagnostic suite hangs
**Solution:**
- Check if diagnostic scripts are executable
- Verify Python path is correct
- Try running diagnostics manually:
  ```bash
  python -m src.diagnostics.system_integration_checker
  python -m src.diagnostics.health_verification
  ```

---

### Issue: "No diagnostic results" message
**Solution:**
1. Click "Run Full Diagnostic Suite" button first
2. Wait for spinner to complete (up to 60 seconds)
3. Results are cached in session state

---

### Issue: Port already in use
**Solution:**
```bash
# Use different port
python scripts/launch_health_dashboard.py --port 8502

# Or kill existing Streamlit process
# Windows PowerShell:
Get-Process -Name "streamlit" | Stop-Process -Force
```

---

## 🎨 Dashboard Customization

### Change Port
```bash
python scripts/launch_health_dashboard.py --port 8080
```

### Enable Browser Auto-Open
```bash
python scripts/launch_health_dashboard.py --browser
```

### Run in Background
```bash
# PowerShell
Start-Process python -ArgumentList "scripts/launch_health_dashboard.py" -WindowStyle Hidden
```

---

## 📊 Health Score Interpretation

| Score | Status | Meaning | Action |
|-------|--------|---------|--------|
| 90-100% | 🟢 EXCELLENT | All systems operational | Continue development |
| 70-89% | 🟡 GOOD | Minor issues present | Address warnings when convenient |
| 50-69% | 🟠 FAIR | Some systems degraded | Fix issues before major changes |
| <50% | 🔴 POOR | Critical issues | Stop and repair immediately |

---

## 🔗 Integration with Other Tools

### With Quantum Workflow Automator
The dashboard can be monitored by the automated orchestration system:
```python
# In quantum_workflow_automation.py
def monitor_dashboard_health():
    result = subprocess.run(["python", "-m", "src.diagnostics.system_integration_checker"])
    if health_score < 70:
        trigger_quantum_healing()
```

### With VS Code
Keep dashboard open in VS Code simple browser:
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Simple Browser: Show"
3. Enter: http://localhost:8501

### With CI/CD
Run diagnostics in GitHub Actions:
```yaml
- name: Health Check
  run: |
    python -m src.diagnostics.system_integration_checker
    python -m src.diagnostics.health_verification
```

---

## 🚀 Advanced Features (Coming Soon)

- [ ] Export health reports to PDF
- [ ] Email alerts on health degradation
- [ ] Historical health trend charts
- [ ] Cross-repository health sync
- [ ] Predictive health analytics
- [ ] One-click automated healing

---

## 📚 Related Documentation

- [SELF_DIAGNOSTIC_SYSTEMS_INVENTORY.md](SELF_DIAGNOSTIC_SYSTEMS_INVENTORY.md) - Full system catalog
- [DIAGNOSTIC_SYSTEMS_STATUS_REPORT.md](DIAGNOSTIC_SYSTEMS_STATUS_REPORT.md) - Current status
- [DIAGNOSTIC_SYSTEMS_ANALYSIS.md](DIAGNOSTIC_SYSTEMS_ANALYSIS.md) - How systems work
- [EXISTING_INFRASTRUCTURE_AUDIT.md](EXISTING_INFRASTRUCTURE_AUDIT.md) - Infrastructure overview

---

**Version**: 1.0  
**Last Updated**: October 13, 2025  
**Integration Status**: ✅ Phase 1 Complete (2 hours)
