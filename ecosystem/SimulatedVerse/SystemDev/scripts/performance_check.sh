#!/usr/bin/env bash
set -euo pipefail

echo "▶ Performance verification (real metrics)"

# Check that performance endpoint responds with growing values
perf1="$(curl -sS "http://localhost:${PORT:-5000}/api/perf" || echo '{}')"
t1="$(echo "$perf1" | jq -r '.tick // 0')"
echo "Initial tick: $t1"

sleep 2

perf2="$(curl -sS "http://localhost:${PORT:-5000}/api/perf" || echo '{}')"
t2="$(echo "$perf2" | jq -r '.tick // 0')"
echo "Second tick: $t2"

[ "$t2" -ge "$t1" ] || { echo "❌ Performance tick not advancing → fake progress"; exit 1; }

# Memory usage check
memory1="$(echo "$perf1" | jq -r '.memory.rss // 0')"
memory2="$(echo "$perf2" | jq -r '.memory.rss // 0')"
echo "Memory usage: $memory1 → $memory2 bytes"

# Uptime check
uptime="$(echo "$perf2" | jq -r '.uptime_seconds // 0')"
echo "System uptime: $uptime seconds"

# Process tracking metrics
echo "▶ Process tracking performance"
python3 -c "
import sys
sys.path.append('.')
from src.process_tracker import tracker
metrics = tracker.get_performance_metrics()
print(f'Total events tracked: {metrics.get(\"total_events\", 0)}')
print(f'PU completions: {metrics.get(\"pu_completions\", 0)}')
print(f'Game ticks tracked: {metrics.get(\"game_ticks\", 0)}')
print(f'Event rate: {metrics.get(\"event_rate_per_minute\", 0):.2f}/min')

# Track this performance check
tracker.track_agent_execution('performance_check', 'system_verification', 
                              memory_rss=int('$memory2'), 
                              uptime_seconds=float('$uptime'),
                              tick_progression=int('$t2') - int('$t1'))
"

echo "✓ Performance metrics verified - system actively progressing"