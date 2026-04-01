# KILO-FOOLISH: Dynamic Repository Context Index (Auto-Generated)

> This file is auto-generated and updated in real-time by a background subprocess using pandas.  
> It provides a living, structured map of the repository’s files, their roles, tags, and relationships for Copilot, LLMs, and developers.  
> Use this as a “context injection” source for any session, prompt, or code review.

---

## 🗂️ Repository Structure Overview

| File/Folder | Type | Description | Tags | Last Modified |
| ----------- | ---- | ----------- | ---- | ------------- |
<!-- This table is auto-populated by the context subprocess. -->

---

## 🧠 Contextual File Summaries

### Core Modules (`src/`)
- **src/core/**: Quantum problem resolvers, core logic, and recursive AI orchestration.
- **src/ai/**: Multi-LLM orchestration, enhanced bridge integration, and consciousness evolution.
- **src/config/**: All configuration files (YAML, TOML, JSON) for system, AI, and orchestration.

### Enhancement Bridges
- **.copilot/copilot_enhancement_bridge.py**:  
  - Memory palace for Copilot, OmniTag/MegaTag integration, musical lexeme generation, context synthesis.
- **OTLQGL/copilot-enhancement-bridge-upgrade/**:  
  - MegaTag specifications, context enhancement, and symbolic cognition modules.

### Logging & Audit
- **LOGGING/modular_logging_system.py**: Modular, tag-aware logging.
- **scripts/system_audit.py**: System health and capability audit.
- **scripts/async_def_track_system_evolution.py**: Tracks system evolution and changes over time.

### Automation & Command Extraction
- **Transcendent_Spine/kilo-foolish-transcendent-spine/config/extract_commands.py**:  
  - Smart command suggester, tracks executed commands, suggests next optimal actions, integrates with LLMs.
- **executed_commands.json**: Persistent record of completed commands.

### Game & AI Integration
- **godot-integration-project/**: GODOT engine integration, ChatDev and Ollama bridges.
- **Scripts/ChatDev-Party-System.py**: Launches and tests party system.
- **Scripts/wizard_navigator.py**: Wizard navigation tool.
- **Scripts/launch-adventure.py**: Adventure system launcher.
- **Scripts/Interactive-Context-Browser.py**: Context browser for repository analysis.

### Documentation & Guidance
- **docs/Archive/COMMANDS_LIST.md**: Chronological, dependency-based command checklist.
- **docs/guidance/123-step-development-checklist.md**: Recursive, modular development lifecycle.
- **docs/guidance/code_cultivation.md**: 123 principles of code cultivation.
- **OTLQGL/copilot-enhancement-bridge-upgrade/docs/megatag_specifications.md**: MegaTag structure and usage.

### Tagging & Symbolic Systems
- **ΞNuSyQ₁-Hub₁/txt_Files/OmniTag.txt**: OmniTag syntax and examples.
- **ΞNuSyQ₁-Hub₁/txt_Files/NuSyQRosettaStone.txt**: Rosetta Stone for symbolic translation.

---

## 🔗 File Relationships & Integration Points

- **Copilot Enhancement Bridge** links with all core modules, logging, and orchestration scripts.
- **Multi-LLM Orchestra** imports and extends the bridge, enabling collaborative LLM workflows.
- **extract_commands.py** references `COMMANDS_LIST.md` and updates `executed_commands.json` for stateful command suggestion.
- **MegaTagProcessor** and **SymbolicCognition** (see `megatag_specifications.md`) are used by both Copilot and orchestration modules for advanced tagging and context linking.

---

## 🏷️ Tagging & Semantic Layering

- **OmniTag/MegaTag**: Used throughout for tagging, memory, and context propagation.
- **Semantic tags**: Purpose, dependencies, context, evolution stage.
- **Musical lexeme generation**: ZetaSetLexemeGenerator in `.copilot/copilot_enhancement_bridge.py`.

---

## 🛠️ Real-Time Context Update (Subprocess)

A background Python subprocess (see below) uses pandas to:
- Scan the repository for all files and folders.
- Extract file type, last modified time, and summary from docstrings/comments.
- Parse tags (OmniTag/MegaTag/RSHTS) and relationships.
- Update this `instructions.md` file in real time.

### Example subprocess logic (Python/pandas):

```python
import os
import pandas as pd
from pathlib import Path
import time

def scan_repo(root="."):
    file_data = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.startswith(".") or fname.endswith((".pyc", ".pkl")):
                continue
            fpath = Path(dirpath) / fname
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    doc = ""
                    for line in lines[:10]:
                        if line.strip().startswith(("#", "\"\"\"", "//", "'''")):
                            doc += line.strip().lstrip("#/\"' ") + " "
                    tags = [w for w in doc.split() if "Tag" in w or "Ξ" in w or "Φ" in w]
                file_data.append({
                    "File/Folder": str(fpath.relative_to(root)),
                    "Type": fpath.suffix or "folder",
                    "Description": doc[:120],
                    "Tags": ", ".join(tags),
                    "Last Modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(fpath.stat().st_mtime))
                })
            except Exception:
                continue
    df = pd.DataFrame(file_data)
    df.sort_values("File/Folder", inplace=True)
    return df

def update_instructions_md(df, md_path):
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# KILO-FOOLISH: Dynamic Repository Context Index (Auto-Generated)\n\n")
        f.write("| File/Folder | Type | Description | Tags | Last Modified |\n")
        f.write("|-------------|------|-------------|------|--------------|\n")
        for _, row in df.iterrows():
            f.write(f"| {row['File/Folder']} | {row['Type']} | {row['Description']} | {row['Tags']} | {row['Last Modified']} |\n")

if __name__ == "__main__":
    repo_root = "."
    md_path = ".github/instructions/instructions.md"
    while True:
        df = scan_repo(repo_root)
        update_instructions_md(df, md_path)
        time.sleep(60)  # Update every 60 seconds
```

---

## 🧩 Usage

- **For Copilot/LLM sessions**:  
  - Reference this file for up-to-date context about any file/module.
  - Use as a prompt supplement: “Refer to `.github/instructions/instructions.md` for repository context.”
- **For developers**:  
  - Quickly locate files, understand their purpose, and see integration points.
  - Add or update tags and docstrings to improve context extraction.

---

## 🚦 Maintenance

- This file is maintained by the context subprocess.  
- To add more context, update docstrings, tags, or comments in your source files.
- For new modules, ensure they are documented and tagged for maximum discoverability.

---

*This dynamic instructions file is the living map of KILO-FOOLISH. Use it to cultivate, navigate, and evolve the system with maximal context
