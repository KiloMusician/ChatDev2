#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════════
# RimWorld VNC Container Entrypoint
# Starts X11, VNC, noVNC, and RimWorld (headless or visual mode).
# ════════════════════════════════════════════════════════════════════════════════

set -euo pipefail

DISPLAY_NUM=1
DISPLAY=":${DISPLAY_NUM}"
VNC_PORT=5900
NOVNC_PORT=6080
VNC_PASSWORD="${VNC_PASSWORD:-lattice}"
RIMWORLD_MODE="${RIMWORLD_MODE:-visual}"   # headless | visual
GAME_DIR="/rimworld/game"
SAVES_DIR="/rimworld/saves"
CONFIG_DIR="/rimworld/config"

echo "╔════════════════════════════════════════════════╗"
echo "║   RimWorld VNC Container — Terminal Keeper     ║"
echo "╠════════════════════════════════════════════════╣"
echo "║  Mode:   ${RIMWORLD_MODE}"
echo "║  VNC:    :${VNC_PORT} (password: ${VNC_PASSWORD})"
echo "║  noVNC:  http://0.0.0.0:${NOVNC_PORT}"
echo "╚════════════════════════════════════════════════╝"

# Update VNC password from env
mkdir -p ~/.vnc
x11vnc -storepasswd "$VNC_PASSWORD" ~/.vnc/passwd

# Start virtual display
Xvfb "$DISPLAY" -screen 0 1920x1080x24 -ac +extension GLX &
XVFB_PID=$!
export DISPLAY

sleep 2

# Start VNC server
x11vnc -display "$DISPLAY" \
       -rfbauth ~/.vnc/passwd \
       -rfbport "$VNC_PORT" \
       -forever \
       -noxdamage \
       -noxrecord \
       -quiet &
VNC_PID=$!

# Start noVNC web interface
websockify --web=/usr/share/novnc \
           "$NOVNC_PORT" \
           "localhost:${VNC_PORT}" &
NOVNC_PID=$!

sleep 1
echo "[RW] X11 + VNC + noVNC started"

# Check if game files exist
if [ ! -f "${GAME_DIR}/RimWorldLinux" ] && [ ! -f "${GAME_DIR}/RimWorldWin64.exe" ]; then
    echo "[RW] WARNING: RimWorld game files not found in ${GAME_DIR}"
    echo "[RW] Mount your RimWorld installation or run SteamCMD to install."
    echo "[RW] Container will stay alive for VNC access."
    tail -f /dev/null
fi

# Write Terminal Keeper container marker
touch /.terminal-keeper-container

# Write ModsConfig to enable Terminal Keeper
mkdir -p "${CONFIG_DIR}"
cat > "${CONFIG_DIR}/ModsConfig.xml" << 'MODSXML'
<?xml version="1.0" encoding="utf-8"?>
<ModsConfigData>
  <version>1.5</version>
  <activeMods>
    <li>brrainz.harmony</li>
    <li>com.devmentor.terminalkeeper</li>
  </activeMods>
  <knownExpansions />
</ModsConfigData>
MODSXML

echo "[RW] ModsConfig written with Terminal Keeper enabled"

# Launch RimWorld
if [ -f "${GAME_DIR}/RimWorldLinux" ]; then
    GAME_EXE="${GAME_DIR}/RimWorldLinux"
else
    GAME_EXE="wine ${GAME_DIR}/RimWorldWin64.exe"
fi

if [ "$RIMWORLD_MODE" = "headless" ]; then
    echo "[RW] Starting RimWorld in headless/quicktest mode..."
    DISPLAY="$DISPLAY" $GAME_EXE \
        -savedatafolder "${SAVES_DIR}" \
        -logfile /rimworld/rimworld.log \
        -quicktest &
else
    echo "[RW] Starting RimWorld in visual mode (VNC)..."
    DISPLAY="$DISPLAY" $GAME_EXE \
        -savedatafolder "${SAVES_DIR}" \
        -logfile /rimworld/rimworld.log &
fi

RIMWORLD_PID=$!
echo "[RW] RimWorld started (PID=${RIMWORLD_PID})"

# Monitor loop: detect crashes and notify Terminal Depths
while kill -0 $RIMWORLD_PID 2>/dev/null; do
    sleep 5
done

EXIT_CODE=$?
echo "[RW] RimWorld exited with code ${EXIT_CODE}"

# Notify Terminal Depths of crash
if [ "$EXIT_CODE" -ne 0 ]; then
    echo "[RW] Crash detected — notifying Lattice..."
    curl -s -X POST "${TERMINAL_DEPTHS_URL:-http://dev-mentor:5000}/api/game/command" \
         -H "Content-Type: application/json" \
         -H "X-NuSyQ-Passkey: ${NUSYQ_PASSKEY:-}" \
         -d "{\"command\":\"crash_event\",\"source\":\"rimworld_entrypoint\",\"exit_code\":${EXIT_CODE}}" \
         || true
fi

# Keep VNC alive even after game exits
echo "[RW] Keeping VNC alive. Reconnect to investigate or restart."
wait $NOVNC_PID
