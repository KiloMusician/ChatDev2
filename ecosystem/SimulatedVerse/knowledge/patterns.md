# ΞNuSyQ-prime⁴ Patterns Learned

## 2025-09-03 Anti-Theater Continuous Ops

### Pattern: Tier-0 Spine Recovery
- **Problem**: Ollama daemon unreachable in Replit environment
- **Solution**: Cascade approach (Ollama → Gateway → OpenAI.once → adapt)
- **Principle**: "Down" ≠ terminal for Tier-0 systems
- **Receipt**: Fallback chain with failure tracking

### Pattern: Adaptive Breath (τ′)
- **Formula**: τ′ = clamp(0.67τ, 1.25τ) with condition-based factors
- **Success + backlog_high**: τ′ = 0.85τ (speed up under load)
- **UI stale**: τ′ = 0.9τ (prevent system stagnation)
- **Receipt**: Bounded adaptation prevents runaway cycles

### Pattern: Council ACTION+RECEIPT
- **Problem**: Theater detection (claims without artifacts)
- **Solution**: Mandatory tool actions with concrete receipts
- **Format**: Agent → ACTION{tool(args)} → EXPECT{receipt_type}
- **Receipt**: Eliminates "looks good" vibes-based responses

### Pattern: Health Gates (G1-G4)
- **G1 LLM-Spine**: Sacred Tier-0, never accept terminal failure
- **G2 Queue-Live**: Completion-based liveness (not activity theater)
- **G3 UI-Fresh**: 60s drift limit with auto-repair
- **G4 Disk/Noise**: Growth rate monitoring with watchdog
- **Receipt**: Gate passage required before long work cycles

## Daemon Loop Patterns (Pass 1)

### Pattern: Differential File Scanning
- **Problem**: Need to process only NEW files to avoid redundant work
- **Solution**: Baseline + current scan with comm -13 for differential
- **Receipt**: seen_files_baseline.txt + current_scan.txt
- **Principle**: Ingest efficiency through change detection

### Pattern: Classification by Filename
- **Problem**: Mixed file types in reports/ directory
- **Solution**: Pattern matching (cycle-*.json, *receipt*.json, etc.)
- **Receipt**: Kind classification in processing logs
- **Principle**: Structural typing for automation

### Pattern: k≤3 Council Routing
- **Problem**: Avoid overwhelming council with too many simultaneous tasks
- **Solution**: Select max 3 tasks per pass, prioritize by blast_radius×tier
- **Receipt**: 3 council receipts per pass guaranteed
- **Principle**: Bounded parallelism for quality control

### Pattern: Daemon State Persistence
- **Problem**: Need to maintain state across passes for continuity
- **Solution**: daemon/state/ directory with JSON state files
- **Receipt**: pass_counter.json + watch_sets.json
- **Principle**: Stateful automation with recovery capability

## ΞNuSyQ-prime⁵ Quadpartite Patterns

### Pattern: Adaptive Breath (Both Directions)
- **Problem**: Fixed cooldowns don't respond to context
- **Solution**: τ′ = clamp(0.67τ, 1.25τ) with context factors
- **Factors**: success_rate, backlog_level, failure_burst, ui_skew, stall
- **Principle**: Speed up on progress+backlog, slow down on failures
- **Receipt**: adaptive_breath.json with rationale

### Pattern: Agent Reliability Matrix
- **Problem**: Agents need backend-aware routing
- **Solution**: Truth table (RELIABLE|LIMITED|BROKEN) × (ollama|gpt|vacuum)
- **Fallback**: Vacuum mode for tool-only operations when LLM down
- **Principle**: Choose cheapest backend that can produce needed receipt
- **Receipt**: agents_matrix.json with current modes

### Pattern: Theater Filter (Proof-Only)
- **Problem**: Vibes-based "success" without artifacts
- **Solution**: θ = 1 - min(1, Δ/K) with cascade at θ>0.2
- **Enforcement**: Ban echo-only, require file paths/diffs/tests
- **Principle**: Every "done" must have measurable artifact
- **Receipt**: theater_filter.json with enforcement status

### Pattern: Health Gates (Self-Repair)
- **Problem**: Gates that FAIL without recovery
- **Solution**: G1-G4 with mandatory receipts and auto-repair
- **Receipts**: llm_health.json, queue_metrics.json, ui_status.json, growth_watch.json
- **Principle**: PASS or actively repair, never halt on failure
- **Receipt**: Gate-specific JSON with repair actions

### Pattern: Reports as Food (Autonomous Consumption)
- **Problem**: Generate reports but don't act on them
- **Solution**: Differential scan → classify → route → act immediately
- **Flow**: audit→tasks, llm_fail→retry, sim_proof→fixes
- **Principle**: Every report becomes actionable work
- **Receipt**: routing_rules.json with immediate execution
