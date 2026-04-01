#!/usr/bin/env bash
# install_td.sh — Install the 'td' command system-wide (Unix/macOS/WSL/Git Bash)
# ─────────────────────────────────────────────────────────────────────────────
# Installs 'td' into ~/.local/bin/td and writes a .td_repo sentinel file
# so the wrapper can always find the DevMentor repo regardless of CWD.
#
# Usage:
#   bash scripts/install_td.sh          # standard install
#   bash scripts/install_td.sh --uninstall
#   bash scripts/install_td.sh --check
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT_FILE="$REPO_ROOT/.td_repo"

# ── Colour helpers ────────────────────────────────────────────────────────────
_ok()   { echo -e "\033[32m  ✓ $*\033[0m"; }
_warn() { echo -e "\033[33m  ⚠ $*\033[0m"; }
_err()  { echo -e "\033[1;31m  ✗ $*\033[0m"; }
_info() { echo -e "\033[36m  · $*\033[0m"; }
_hr()   { printf '\033[2m  %s\033[0m\n' '────────────────────────────────────────────────────'; }

echo ""
echo -e "\033[1;35m  ◈ TERMINAL DEPTHS — Launcher Installer\033[0m"
_hr

# ── Arguments ─────────────────────────────────────────────────────────────────
MODE="install"
for arg in "$@"; do
    case "$arg" in
        --uninstall) MODE="uninstall" ;;
        --check)     MODE="check" ;;
    esac
done

# ── Determine install dirs ────────────────────────────────────────────────────
LOCAL_BIN="$HOME/.local/bin"
HOME_BIN="$HOME/bin"

# Pick the first dir that is (or can be created) on PATH
INSTALL_DIR=""
for candidate in "$LOCAL_BIN" "$HOME_BIN" "/usr/local/bin"; do
    if echo "$PATH" | grep -q "$candidate"; then
        INSTALL_DIR="$candidate"
        break
    fi
done

# Fallback: create ~/.local/bin and add to PATH
if [ -z "$INSTALL_DIR" ]; then
    INSTALL_DIR="$LOCAL_BIN"
    _warn "~/.local/bin is not on PATH. Add this to ~/.bashrc / ~/.zshrc:"
    echo '    export PATH="$HOME/.local/bin:$PATH"'
fi

DEST="$INSTALL_DIR/td"

# ── Check mode ────────────────────────────────────────────────────────────────
if [ "$MODE" = "check" ]; then
    if [ -x "$DEST" ]; then
        _ok "'td' is installed at $DEST"
        _info "td version: $(python3 "$REPO_ROOT/scripts/td.py" --help 2>&1 | head -1)"
    else
        _warn "'td' is NOT installed (checked $DEST)"
        _info "Run: bash scripts/install_td.sh"
    fi
    echo ""
    exit 0
fi

# ── Uninstall mode ────────────────────────────────────────────────────────────
if [ "$MODE" = "uninstall" ]; then
    for path in "$LOCAL_BIN/td" "$HOME_BIN/td" "/usr/local/bin/td"; do
        if [ -f "$path" ]; then
            rm "$path"
            _ok "Removed: $path"
        fi
    done
    [ -f "$REPO_ROOT_FILE" ] && rm "$REPO_ROOT_FILE" && _ok "Removed: $REPO_ROOT_FILE"
    _info "Uninstall complete."
    echo ""
    exit 0
fi

# ── Install ───────────────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR"

# Write repo sentinel
echo "$REPO_ROOT" > "$REPO_ROOT_FILE"
_ok "Repo sentinel: $REPO_ROOT_FILE → $REPO_ROOT"

# Copy repo-root wrapper scripts (always fresh)
cp "$REPO_ROOT/td"     "$REPO_ROOT/td"     2>/dev/null || true
chmod +x "$REPO_ROOT/td"

# Write the global wrapper
cat > "$DEST" << 'WRAPPER'
#!/usr/bin/env bash
# td — Terminal Depths Universal Launcher (installed by install_td.sh)
# REPO_ROOT is read from TD_REPO env var or from ~/.td_repo sentinel
if [ -n "${TD_REPO:-}" ]; then
    _td_repo="$TD_REPO"
elif [ -f "$(dirname "$0")/.td_repo" ]; then
    _td_repo="$(cat "$(dirname "$0")/.td_repo")"
else
    # Try common locations
    for candidate in \
        "$HOME/.local/share/devmentor" \
        "$HOME/Dev-Mentor" \
        "$HOME/dev-mentor" \
        "$HOME/DevMentor"
    do
        [ -f "$candidate/scripts/td.py" ] && { _td_repo="$candidate"; break; }
    done
fi

# Last resort: search for .td_repo sentinels in known dirs
if [ -z "${_td_repo:-}" ]; then
    for loc in \
        "$HOME/.local/bin/.td_repo" \
        "$HOME/bin/.td_repo" \
        "/usr/local/bin/.td_repo"
    do
        [ -f "$loc" ] && { _td_repo="$(cat "$loc")"; break; }
    done
fi

if [ -z "${_td_repo:-}" ] || [ ! -f "$_td_repo/scripts/td.py" ]; then
    echo "[td] ERROR: Cannot locate DevMentor repo." >&2
    echo "     Set: export TD_REPO=/path/to/Dev-Mentor" >&2
    exit 1
fi

exec python3 "$_td_repo/scripts/td.py" "$@"
WRAPPER

chmod +x "$DEST"
_ok "Installed: $DEST"

# Write .td_repo sentinel next to the wrapper too (for the wrapper to find it)
echo "$REPO_ROOT" > "$INSTALL_DIR/.td_repo"
_ok "Sentinel: $INSTALL_DIR/.td_repo"

# Also write to ~/bin if it exists and is different
if [ -d "$HOME_BIN" ] && [ "$HOME_BIN" != "$INSTALL_DIR" ]; then
    cp "$DEST" "$HOME_BIN/td" && echo "$REPO_ROOT" > "$HOME_BIN/.td_repo"
    _ok "Also installed: $HOME_BIN/td"
fi

# PowerShell Core (cross-platform) wrapper
if command -v pwsh &>/dev/null; then
    PWSH_DIR="$HOME/.config/powershell"
    mkdir -p "$PWSH_DIR"
    cat > "$PWSH_DIR/td.ps1" << PSEOF
# td.ps1 — auto-installed by install_td.sh
\$TDRepo = "$REPO_ROOT"
& python3 "\$TDRepo/scripts/td.py" @Args
PSEOF
    _ok "PowerShell Core: $PWSH_DIR/td.ps1"
fi

_hr
echo ""
echo -e "\033[32m  Installation complete!\033[0m"
echo ""
echo "  Usage anywhere on this system:"
echo "    td                 — enter Terminal Depths"
echo "    td play            — terminal REPL (no browser)"
echo "    td status          — server health"
echo "    td open            — open in browser"
echo "    td surfaces        — map all surfaces"
echo "    td install         — re-run this installer via Python"
echo ""
echo -e "\033[2m  If 'td' is not found after install, reload your shell:\033[0m"
echo '    source ~/.bashrc   or   exec zsh'
echo ""
