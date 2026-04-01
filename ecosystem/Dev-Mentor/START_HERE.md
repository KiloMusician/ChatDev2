# START HERE — DevMentor boots inside VS Code

## 0) Confirm you are in VS Code
You should see:
- Explorer sidebar
- Terminal panel
- Source Control (SCM) view

## 1) Install recommended extensions
VS Code should prompt: **Install recommended extensions?**  
Click **Install** (or **Install All**).

## 2) Boot the mentor runtime (this is the “it just works” moment)
Open the Command Palette:
- Windows/Linux: **Ctrl+Shift+P**
- macOS: **Cmd+Shift+P**

Run:
**Tasks: Run Task** → ✅ **DevMentor: Start/Resume**

You’ll see output in the terminal panel.

## 2.5) Use the built-in operator tasks instead of rediscovering scripts
The primary VS Code task surface is:
- `DevMentor: Start/Resume`
- `DevMentor: Next Step`
- `DevMentor: Diagnose Environment`
- `DevMentor: Validate Current Challenge`
- `🔍 DevMentor: Boot Status`
- `🔗 DevMentor: Integration Matrix`

## 3) Do the first lesson (5–10 min)
Open:
`tutorials/00-vscode-basics/01-command-palette.md`

Follow the steps, then run:
✅ **DevMentor: Next Step**

## 4) Save-game + portability
Progress is stored locally in `.devmentor/state.json` (gitignored).

To carry progress from Replit → VS Code:
✅ **DevMentor: Export Portable ZIP**
Then unzip + open in VS Code and run:
✅ **DevMentor: Import Portable ZIP**

