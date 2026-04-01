# 🚀 KILO-FOOLISH Quick Start — CONTINUE FROM LAST STATE

> **This guide resumes your KILO-FOOLISH journey from your current repository state.  
> All commands are idempotent and context-aware.  
> Use the Smart Command Suggester for optimal workflow.**

---

## 1️⃣ Activate Your Environment

**Windows (PowerShell):**
```powershell
.\venv_kilo\Scripts\Activate.ps1
```

**Unix/Mac:**
```bash
source venv_kilo/bin/activate
```

---

## 2️⃣ Update & Verify Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3️⃣ Ensure Ollama Service is Running

- Only one Ollama instance can run at a time.
- If you see "bind: Only one usage of each socket address...", stop other Ollama processes:

**Windows:**
```powershell
Get-Process ollama | Stop-Process -Force
ollama serve
```

**Unix/Mac:**
```bash
pkill ollama
ollama serve
```

---

## 4️⃣ Use the Smart Command Suggester

**Launch the interactive command suggester:**
```bash
python Transcendent_Spine/kilo-foolish-transcendent-spine/config/extract_commands.py
```
- This tool will suggest the next best command, track executed commands, and allow launching tools by name:
  - `launch party` (ChatDev Party System)
  - `launch wizard` (Wizard Navigator)
  - `launch navigator` (Enhanced Wizard Navigator)
  - `launch adventure` (Adventure Script)
  - `launch context` (Context Browser)

---

## 5️⃣ Launch Key Tools Directly

```bash
python Scripts/wizard_navigator.py
python Scripts/Enhanced-Interactive-Context-Browser.py
python Scripts/ChatDev-Party-System.py
```

---

## 6️⃣ Run System Health & Audit Tools

```bash
python scripts/system_audit.py
python scripts/system_dashboard.py
python tools/import_health_checker.py --fix
python tools/file_organization_auditor.py --dry-run
```

---

## 7️⃣ Start the Web Music Site

```bash
python web/foolish_music_site.py
# Then open http://localhost:5000 (password: foolish)
```

---

## 8️⃣ Master Automation (All-in-One)

```bash
python kilo_master.py --quick      # Start core services
python kilo_master.py --web        # Start web development
python kilo_master.py --full       # Full system check
```

---

## 9️⃣ Troubleshooting

- **Ollama port in use:**  
  Stop all Ollama processes, then restart `ollama serve`.

- **Permission errors:**  
  Run PowerShell as Administrator and set execution policy:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
  ```

- **Missing dependencies:**  
  Run `pip install -r requirements.txt` in your active environment.

- **Tool not launching:**  
  Ensure you’re in the correct directory and virtual environment is active.

---

## 10️⃣ Reference & Context

- All commands are tracked in `executed_commands.json` and `COMMANDS_LIST.md`.
- For advanced orchestration, see:
  - `copilot/copilot_enhancement_bridge.py`
  - `src/ai/enhanced_multi_llm_orchestra.py`
- For tagging and context, see:
  - `OTLQGL/copilot-enhancement-bridge-upgrade/docs/megatag_specifications.md`

---

## 🧠 Next Steps

- Use the Smart Command Suggester to avoid repeating completed steps.
- Explore advanced orchestration and context tools.
- Cultivate repository knowledge and propagate context using the Copilot Enhancement Bridge.

---

**KILO-FOOLISH is ready for recursive, quantum-inspired development.  
Continue your journey — every command is a step toward repository enlightenment.**
