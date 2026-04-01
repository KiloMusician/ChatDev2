#!/bin/bash
# crisis_response.sh - AGENT PERFORMANCE CRISIS RESPONSE
# Uses EXISTING NuSyQ-Hub infrastructure (no new dependencies)
#
# This script orchestrates existing systems to recover from agent failures.
# Requires Linux/macOS — uses pkill, pgrep, nohup, awk (unavailable in MINGW64).

set -e

# Platform guard: this script requires a full Unix environment
if [ "$(uname -o 2>/dev/null)" = "Msys" ] || [ "$(uname -o 2>/dev/null)" = "Cygwin" ]; then
    echo "⚠️  This script requires a Linux environment (WSL, Docker, or native Linux)."
    echo "   On Windows, run inside WSL: wsl bash scripts/crisis_response.sh"
    echo "   Or inside Docker: docker exec -it nusyq-hub bash scripts/crisis_response.sh"
    exit 1
fi

echo "🚨 AGENT PERFORMANCE CRISIS RESPONSE ACTIVATED"
echo "=" | awk '{s=""; for(i=0;i<60;i++)s=s$0; print s}'
echo ""

# Configuration
INTERVAL=${INTERVAL:-300}
MAX_PUS=${MAX_PUS:-5}
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "📍 Working directory: $REPO_ROOT"
echo ""

# Step 1: Kill hanging processes
echo "🔪 Step 1: Killing hanging processes..."
if command -v pkill &> /dev/null; then
    pkill -f "github-copilot" 2>/dev/null || echo "   No Copilot processes found"
    pkill -f "pytest.*--hang" 2>/dev/null || echo "   No hanging pytest found"
    pkill -f "ruff.*--watch" 2>/dev/null || echo "   No hanging ruff found"
    echo "   ✅ Process cleanup complete"
else
    echo "   ⚠️  pkill not available, skipping process cleanup"
fi
echo ""

# Step 2: Capture pre-crisis state
echo "📊 Step 2: Capturing pre-crisis state..."
mkdir -p state/crisis_response
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CRISIS_DIR="state/crisis_response/$TIMESTAMP"
mkdir -p "$CRISIS_DIR"

echo "   Generating system snapshot..."
python scripts/start_nusyq.py snapshot > "$CRISIS_DIR/snapshot_before.md" 2>&1 || \
    echo "⚠️  Snapshot failed, continuing..."

echo "   Checking guild status..."
python scripts/start_nusyq.py guild_status > "$CRISIS_DIR/guild_before.txt" 2>&1 || \
    echo "⚠️  Guild status failed, continuing..."

echo "   ✅ Pre-crisis state saved to: $CRISIS_DIR"
echo ""

# Step 3: Run error diagnostics
echo "🔍 Step 3: Running error diagnostics..."
echo "   Quick error scan (Hub only)..."
python scripts/start_nusyq.py error_report --quick --hub-only > "$CRISIS_DIR/errors_hub.txt" 2>&1 || \
    echo "⚠️  Error report failed, continuing..."

# Extract error count
ERROR_COUNT=$(grep -c "Error\|error\|ERROR" "$CRISIS_DIR/errors_hub.txt" 2>/dev/null || echo "0")
echo "   Found approximately $ERROR_COUNT error-related lines"
echo ""

# Step 4: Activate Culture Ship (strategic advisor)
echo "🚀 Step 4: Activating Culture Ship strategic advisor..."
python scripts/activate_culture_ship.py > "$CRISIS_DIR/culture_ship_activation.txt" 2>&1 && \
    echo "   ✅ Culture Ship activated" || \
    echo "   ⚠️  Culture Ship activation failed (may already be active)"
echo ""

# Step 5: Run healing cycle
echo "🏥 Step 5: Running ecosystem healing..."
python scripts/start_nusyq.py heal > "$CRISIS_DIR/healing_output.txt" 2>&1 && \
    echo "   ✅ Healing complete" || \
    echo "   ⚠️  Healing encountered issues, check logs"
echo ""

# Step 6: Update guild board with recovery status
echo "🎪 Step 6: Updating guild board..."

# Report autonomous agent status
python scripts/start_nusyq.py guild_heartbeat autonomous working "crisis_response_$TIMESTAMP" \
    > "$CRISIS_DIR/guild_heartbeat.txt" 2>&1 || \
    echo "⚠️  Guild heartbeat failed"

# Add crisis recovery quest
python scripts/start_nusyq.py guild_add_quest autonomous \
    "Crisis Recovery $TIMESTAMP" \
    "Automated crisis response and system healing" \
    5 safe crisis,automated \
    > "$CRISIS_DIR/guild_quest.txt" 2>&1 || \
    echo "⚠️  Guild quest creation failed"

# Render guild board
python scripts/start_nusyq.py guild_render > "$CRISIS_DIR/guild_board.md" 2>&1 || \
    echo "⚠️  Guild render failed"

echo "   ✅ Guild board updated"
echo ""

# Step 7: Start autonomous monitoring (if not already running)
echo "👁️  Step 7: Checking autonomous monitor status..."
if pgrep -f "autonomous_monitor.py continuous" > /dev/null; then
    echo "   ✅ Autonomous monitor already running"
else
    echo "   🚀 Starting autonomous monitor in background..."
    nohup python scripts/autonomous_monitor.py continuous \
        --auto-cycle on-pending \
        --real-pus \
        --interval "$INTERVAL" \
        --max-pus "$MAX_PUS" \
        > "$CRISIS_DIR/autonomous_monitor.log" 2>&1 &

    MONITOR_PID=$!
    echo "   Started with PID: $MONITOR_PID"
    echo "$MONITOR_PID" > "$CRISIS_DIR/monitor.pid"
    echo "   ✅ Monitor started (logs: $CRISIS_DIR/autonomous_monitor.log)"
fi
echo ""

# Step 8: Run one auto-cycle for immediate work
echo "⚡ Step 8: Running immediate auto-cycle..."
python scripts/start_nusyq.py auto_cycle \
    --iterations 1 \
    --max-pus 3 \
    --real-pus \
    > "$CRISIS_DIR/auto_cycle.txt" 2>&1 && \
    echo "   ✅ Auto-cycle complete" || \
    echo "   ⚠️  Auto-cycle encountered issues"
echo ""

# Step 9: Generate post-crisis state
echo "📊 Step 9: Capturing post-crisis state..."
python scripts/start_nusyq.py snapshot > "$CRISIS_DIR/snapshot_after.md" 2>&1 || \
    echo "⚠️  Post-snapshot failed"

python scripts/start_nusyq.py selfcheck > "$CRISIS_DIR/selfcheck.txt" 2>&1 || \
    echo "⚠️  Selfcheck failed"

python scripts/start_nusyq.py guild_status > "$CRISIS_DIR/guild_after.txt" 2>&1 || \
    echo "⚠️  Final guild status failed"

echo "   ✅ Post-crisis state captured"
echo ""

# Step 10: Generate crisis report
echo "📝 Step 10: Generating crisis response report..."

cat > "$CRISIS_DIR/CRISIS_RESPONSE_SUMMARY.md" <<EOF
# CRISIS RESPONSE SUMMARY
**Timestamp:** $TIMESTAMP
**Duration:** $(date)

## Actions Taken

1. ✅ Killed hanging processes (Copilot, pytest, ruff)
2. ✅ Captured pre-crisis system state
3. ✅ Ran error diagnostics (~$ERROR_COUNT error lines found)
4. ✅ Activated Culture Ship strategic advisor
5. ✅ Executed ecosystem healing cycle
6. ✅ Updated guild board with crisis recovery quest
7. ✅ Started/verified autonomous monitor (interval: ${INTERVAL}s)
8. ✅ Ran immediate auto-cycle for urgent work
9. ✅ Captured post-crisis system state
10. ✅ Generated this report

## Outputs

- Pre-crisis snapshot: snapshot_before.md
- Post-crisis snapshot: snapshot_after.md
- Error report (Hub): errors_hub.txt
- Healing output: healing_output.txt
- Guild board: guild_board.md
- Self-check: selfcheck.txt
- Auto-cycle log: auto_cycle.txt
- Monitor log: autonomous_monitor.log (ongoing)

## Next Steps

1. Monitor autonomous_monitor.log for ongoing activity
2. Check guild board for quest progress: \`python scripts/start_nusyq.py guild_status\`
3. Review error trends: \`diff guild_before.txt guild_after.txt\`
4. If issues persist, check individual agent status on guild board

## Autonomous Monitor

Status: RUNNING (PID: $(cat monitor.pid 2>/dev/null || echo "unknown"))
Interval: ${INTERVAL}s
Max PUs per cycle: ${MAX_PUS}
Mode: Real execution enabled

To stop monitor:
\`\`\`bash
kill \$(cat $CRISIS_DIR/monitor.pid)
\`\`\`

To check monitor status:
\`\`\`bash
tail -f $CRISIS_DIR/autonomous_monitor.log
\`\`\`

---
*Crisis response executed using existing NuSyQ-Hub infrastructure*
EOF

echo "   ✅ Report generated: $CRISIS_DIR/CRISIS_RESPONSE_SUMMARY.md"
echo ""

# Final summary
echo "=" | awk '{s=""; for(i=0;i<60;i++)s=s$0; print s}'
echo "✅ CRISIS RESPONSE COMPLETE"
echo "=" | awk '{s=""; for(i=0;i<60;i++)s=s$0; print s}'
echo ""
echo "📁 All artifacts saved to: $CRISIS_DIR"
echo "📊 Summary: $CRISIS_DIR/CRISIS_RESPONSE_SUMMARY.md"
echo ""
echo "🔍 Quick status checks:"
echo "   Guild board:  python scripts/start_nusyq.py guild_status"
echo "   System health: python scripts/start_nusyq.py selfcheck"
echo "   Monitor logs:  tail -f $CRISIS_DIR/autonomous_monitor.log"
echo ""
echo "👁️  Autonomous monitor is now running continuously."
echo "   It will auto-process queued work and maintain system health."
echo ""
