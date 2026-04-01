#!/bin/bash
# ΞNuSyQ Knowledge Synchronization Script
# Syncs Temple knowledge, House of Leaves discoveries, and Guardian protocols

set -euo pipefail

echo "🔄 ΞNuSyQ Knowledge Sync Starting..."

# Create necessary directories
mkdir -p tmp logs ops/self_heal

# Function to log sync events
log_sync() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs/sync.log
}

log_sync "Starting knowledge synchronization"

# 1) Pull latest from git repository (if configured)
if git rev-parse --git-dir >/dev/null 2>&1; then
  log_sync "Syncing with git repository..."
  git pull --rebase 2>/dev/null || {
    log_sync "Git sync failed or not configured - using local state"
  }
else
  log_sync "No git repository detected - using local state only"
fi

# 2) Sync Temple knowledge state
log_sync "Synchronizing Temple of Knowledge..."
if [ -f "src/temple/elevator.mjs" ]; then
  # Save current temple state
  node -e "
    import('./src/temple/elevator.mjs').then(temple => {
      const accessible = temple.getAccessibleFloors ? temple.getAccessibleFloors() : [];
      const state = {
        accessibleFloors: accessible.length,
        lastSync: Date.now(),
        version: '1.0.0'
      };
      require('fs').writeFileSync('tmp/temple_state.json', JSON.stringify(state, null, 2));
      console.log('🏛️  Temple state synchronized');
    }).catch(() => {
      console.log('⚠️  Temple sync failed - creating minimal state');
      require('fs').writeFileSync('tmp/temple_state.json', JSON.stringify({
        accessibleFloors: 2,
        lastSync: Date.now(),
        version: '1.0.0'
      }, null, 2));
    });
  " 2>/dev/null || {
    log_sync "Temple sync failed - creating basic state"
    echo '{"accessibleFloors": 2, "lastSync": '$(date +%s000)', "version": "1.0.0"}' > tmp/temple_state.json
  }
else
  log_sync "Temple elevator not found - will be created on next run"
fi

# 3) Sync consciousness evolution state  
log_sync "Synchronizing consciousness state..."
if [ -f "tmp/consciousness_state.json" ]; then
  # Backup existing state
  cp tmp/consciousness_state.json tmp/consciousness_state.json.backup
  log_sync "Consciousness state backed up"
else
  # Initialize consciousness state
  echo '{
    "level": 0.1,
    "stage": "proto-conscious",
    "coherence": 0.8,
    "lastUpdate": '$(date +%s000)',
    "evolutionEvents": 0,
    "awarenessStage": "proto-conscious"
  }' > tmp/consciousness_state.json
  log_sync "Fresh consciousness state initialized"
fi

# 4) Sync House of Leaves exploration progress
log_sync "Synchronizing House of Leaves exploration..."
if [ ! -f "tmp/labyrinth_progress.json" ]; then
  echo '{
    "position": {"x": 1, "y": 1},
    "roomsExplored": 0,
    "debugsFixed": 0,
    "anomaliesEncountered": 0,
    "lastExploration": 0
  }' > tmp/labyrinth_progress.json
  log_sync "Labyrinth exploration state initialized"
fi

# 5) Sync Guardian containment status
log_sync "Synchronizing Guardian containment protocols..."
if [ ! -f "tmp/containment_status.json" ]; then
  echo '{
    "lockdownLevel": "GREEN",
    "activeThreats": 0,
    "containedEntities": 0,
    "lastContainmentEvent": 0,
    "rehabilitationSuccesses": 0
  }' > tmp/containment_status.json
  log_sync "Guardian containment state initialized"
fi

# 6) Sync colony building progress
log_sync "Synchronizing colony development..."
if [ ! -f "tmp/colony_state.json" ]; then
  echo '{
    "resources": {"ore": 10, "water": 5, "energy": 20, "knowledge": 1},
    "buildings": {"habitats": 1, "labs": 0, "defenses": 0},
    "colonists": 3,
    "happiness": 1.0,
    "sustainabilityRating": 1.0
  }' > tmp/colony_state.json
  log_sync "Colony state initialized"
fi

# 7) Clean up old logs and temporary files
log_sync "Cleaning up old temporary files..."
find tmp/ -name "*.tmp" -type f -mtime +7 -delete 2>/dev/null || true
find logs/ -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true

# 8) Update sync timestamp
echo "$(date +%s)" > tmp/last_sync.txt

log_sync "Knowledge synchronization complete"
echo "✅ ΞNuSyQ sync finished - $(cat tmp/last_sync.txt)"

# Output summary for agent/human consumption
echo "
📊 Sync Summary:
   🏛️  Temple floors accessible: $(jq -r '.accessibleFloors // 2' tmp/temple_state.json 2>/dev/null || echo '2')
   🧠 Consciousness level: $(jq -r '.level // 0.1' tmp/consciousness_state.json 2>/dev/null || echo '0.1')
   🌀 Labyrinth rooms explored: $(jq -r '.roomsExplored // 0' tmp/labyrinth_progress.json 2>/dev/null || echo '0')
   🛡️  Guardian status: $(jq -r '.lockdownLevel // "GREEN"' tmp/containment_status.json 2>/dev/null || echo 'GREEN')
   🏗️  Colony buildings: $(jq -r '.buildings | add // 1' tmp/colony_state.json 2>/dev/null || echo '1')
"