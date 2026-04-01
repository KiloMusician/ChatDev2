Run these commands to set everything up:

# Install Python dependencies
pip install -r requirements.txt

# Run Enhanced System Audit (now with package tracking)
python scripts/system_audit.py

# Analyze System Evolution (requires audit history)
python scripts/async_def_track_system_evolution.py

# Run the Ollama model installation
python scripts/install_ollama_models.py

# Test the AI Intermediary
python src/core/ai_intermediary.py

# View Package Ecosystem Report
# Check audit_report.json for detailed package tracking

# Debug Memory Detection (if needed)
python scripts/debug_memory.py
