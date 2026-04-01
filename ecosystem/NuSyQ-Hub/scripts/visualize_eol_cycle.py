"""Epistemic-Operational Lattice (EOL) Decision Cycle Visualizer

Generates ASCII + SVG diagrams of the 5-plane sense→propose→critique→act cycle.
Run standalone to display visualizations in terminal.

Usage:
    python visualize_eol_cycle.py [--svg] [--detailed]

Example output:
```
━┓  SENSE  ┏━ Build world state (git, agents, quests)
 ┃         ┃ Reconcile: 3 contradictions detected
 ┃         ┣━ "error_count" (tool: 28 vs UI: 209)
 ┃         ┗━ SIGNAL_DRIFT detected
 ┃
━┓  PROPOSE ┏━ Generated 7 action candidates
 ┃          ┃ Top: "Run linter" (cost: 10s, priority: critical)
 ┃          ┣━ "Fix imports" (cost: 5s, priority: high)
 ┃          ┗━ "Generate tests" (cost: 45s, priority: medium)
 ┃
━┓  CRITIQUE ┏━ Evaluate policies + budgets
 ┃           ┃ Action: "Run linter" → APPROVED
 ┃           ┃ Status: High priority + available budget
 ┃           ┗━ Proceed to ACT
 ┃
━┓  ACT  ┏━ Execute action "Run linter"
 ┃       ┣━ Pre: ruff available? YES
 ┃       ┃ Duration: 8.3s (within budget)
 ┃       ┃ Exit code: 0 (success)
 ┃       ┣━ Post: violations should decrease below 200
 ┃       ┃ Result: 195 violations (PASS)
 ┃       ┗━ RECEIPT: action_receipt_ledger.jsonl
 ┃
━┓  PERSIST  ┏━ Write to ledgers
 ┃           ┣━ state/world_state_snapshot_N.json
 ┃           ┣━ action_receipt_ledger.jsonl (append)
 ┃           ┗━ quest_receipt_link.jsonl (connect to quest)
 ┃
```
"""

from pathlib import Path


# Color codes for terminal
class _Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    DIM = "\033[2m"


def ascii_diagram():
    """Print the 5-plane EOL cycle in ASCII."""
    diagram = f"""{_Colors.BOLD}╔═══════════════════════════════════════════════════════════╗{_Colors.END}
{_Colors.BOLD}║  Epistemic-Operational Lattice (EOL) Decision Cycle v0.1  ║{_Colors.END}
{_Colors.BOLD}╚═══════════════════════════════════════════════════════════╝{_Colors.END}

{_Colors.CYAN}
    ┌─────────────────────────────────────┐
    │   EPOCH N (Agent Reconstituted)     │
    └─────────────────────────────────────┘
              ↓
{_Colors.GREEN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{_Colors.END}
{_Colors.GREEN}┃ 1️⃣  OBSERVATION PLANE (sense)                       ┃{_Colors.END}
{_Colors.GREEN}┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩{_Colors.END}
│                                                 │
│  Input sources:                               │
│  • git status                                 │
│  • agent probes (Ollama, LM Studio, etc.)    │
│  • quest system (active quests, history)     │
│  • diagnostics (errors, warnings, metrics)   │
│                                              │
│  Operation:                                  │
│  → Signal(timestamp, source, value, confidence)
│  → List of 20-50 signals aggregated         │
│                                              │
│  Output: ObservationSignals[]                │
│          timestamp, source_type, value, confidence
│
{_Colors.GREEN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{_Colors.END}
              ↓
{_Colors.YELLOW}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{_Colors.END}
{_Colors.YELLOW}┃ 2️⃣  COHERENCE PLANE (reconcile)                     ┃{_Colors.END}
{_Colors.YELLOW}┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩{_Colors.END}
│                                                 │
│  Signal precedence (resolve contradictions):  │
│  1. user_input (confidence 10)               │
│  2. diagnostic_tool (confidence 9)           │
│  3. agent_probe (confidence 8)               │
│  4. quest_log (confidence 7)                 │
│  5. git_status (confidence 6)                │
│  6. config_file (confidence 5)               │
│                                              │
│  Example contradiction found:                │
│  • tool says "28 errors"                    │
│  • UI shows "209 errors"                    │
│  • Precedence: tool (9) > git (6)           │
│  • Resolution: "28 errors (diagnostic)"      │
│                                              │
│  Output: Contradictions[], SignalDrift[]    │
│          (metadata + reconciliation reason)  │
│
{_Colors.YELLOW}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{_Colors.END}
              ↓
{_Colors.CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{_Colors.END}
{_Colors.CYAN}┃ 3️⃣  PLANNING PLANE (propose)                         ┃{_Colors.END}
{_Colors.CYAN}┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩{_Colors.END}
│                                                 │
│  Input: WorldState + user objective           │
│  (e.g., "Analyze errors")                    │
│                                              │
│  Step 1: Intent parser                       │
│  • Extract TaskType: ANALYSIS, CODE_GEN, etc │
│  • Extract constraints: {{priority, budget}}   │
│  • Extract keywords: "analyze", "errors"     │
│                                              │
│  Step 2: Capability registry lookup           │
│  • Ollama (success_rate: 0.78, cost: 15s)    │
│  • LM Studio (0.72, 8s)                      │
│  • ChatDev (0.65, 120s)                      │
│  • Can handle ANALYSIS? YES for all 3        │
│                                              │
│  Step 3: Generate candidates                 │
│  → Action 1: Ollama + qwen model (15s)       │
│  → Action 2: LM Studio + codeup (8s)         │
│  → Action 3: ChatDev review (120s)           │
│                                              │
│  Step 4: Rank by priority + cost             │
│  • Sort by: (policy_priority, time_sensitivity,
│              cost, success_rate_desc)        │
│                                              │
│  Output: list[Action] (ranked)               │
│          {{agent, task, params, cost, eta}}    │
│
{_Colors.CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{_Colors.END}
              ↓
{_Colors.BLUE}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{_Colors.END}
{_Colors.BLUE}┃ 4️⃣  POLICY PLANE (critique)                          ┃{_Colors.END}
{_Colors.BLUE}┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩{_Colors.END}
│                                                 │
│  Input: Action candidate + WorldState         │
│                                              │
│  Evaluation gates:                            │
│  ✓ Budget check: cost (15s) < budget (60s)? │
│  ✓ Risk assessment: priority=HIGH, ok       │
│  ✓ Precondition: Ollama available? YES      │
│  ✓ Policy: Action in approved_list? YES     │
│                                              │
│  If SECURITY category:                       │
│  → Forward to Culture Ship for approval      │
│  → (future: advanced policy compiler)        │
│                                              │
│  Output: bool                                │
│          (approved=true or rejected + reason)│
│
{_Colors.BLUE}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{_Colors.END}
              ↓
{_Colors.RED}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{_Colors.END}
{_Colors.RED}┃ 5️⃣  EXECUTION PLANE (act)                            ┃{_Colors.END}
{_Colors.RED}┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩{_Colors.END}
│                                                 │
│  Input: Action + WorldState + dry_run flag   │
│                                              │
│  Step 1: Validate preconditions              │
│  • Is Ollama running? YES                    │
│  • Is model qwen available? YES              │
│  • Is network accessible? YES                │
│                                              │
│  Step 2: Dispatch to background orchestrator │
│  • Task: BackgroundTask(action_id, metadata) │
│  • Queue: FIFO with priority sorting         │
│  • Started: "task_xyz" (timestamp)           │
│                                              │
│  Step 3: Run with timeout                    │
│  real_time: 13.2 seconds (within budget)    │
│ exit_code: 0 (success)                       │
│  stdout: [analysis output]                   │
│                                              │
│  Step 4: Validate postconditions             │
│  • Did error count decrease? YES (28→21)     │
│  • Did execution complete? YES               │
│  • Was output valid? YES (format ok)         │
│                                              │
│  Step 5: Emit ActionReceipt                  │
│  • Immutable JSON record                     │
│  • Append to ledger (atomically)             │
│  • Timestamp: 2026-02-28T14:32:05.123+00     │
│  • Duration: 13.2s                           │
│  • Status: success                           │
│  • Postcondition results: ["error_count": 21]│
│                                              │
│  Output: ActionReceipt                       │
│          {{id, agent, task, status, duration, │
│           stdout, stderr, postconditions}}    │
│
{_Colors.RED}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{_Colors.END}
              ↓
{_Colors.GREEN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{_Colors.END}
{_Colors.GREEN}┃ 6️⃣  MEMORY PLANE (persist)                          ┃{_Colors.END}
{_Colors.GREEN}┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩{_Colors.END}
│                                                 │
│  Output files written (immutable):            │
│                                              │
│  1. state/world_state_snapshot_N.json         │
│     └─ Full observation + coherence state    │
│        (used for drift analysis + recovery)   │
│                                              │
│  2. action_receipt_ledger.jsonl (append)      │
│     └─ One JSON per line = one receipt       │
│        (immutable audit trail)                │
│                                              │
│  3. quest_receipt_links.jsonl (append)        │
│     └─ Link action to quest for tracing      │
│        (enables "which actions completed Q?")│
│                                              │
│  4. state/eol_stats.json (RW)                │
│     └─ Aggregate stats (success rate, etc.)   │
│        (updated per epoch)                    │
│                                              │
│  Result: All state preserved; Agent ready    │
│          for next epoch reconstitution.       │
│
{_Colors.GREEN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{_Colors.END}
              ↓
{_Colors.BOLD}┌─────────────────────────────────────┐{_Colors.END}
{_Colors.BOLD}│  Epoch N+1 (Agent Reconstituted)    │{_Colors.END}
{_Colors.BOLD}│  (Reads same substrate; fresh view) │{_Colors.END}
{_Colors.BOLD}└─────────────────────────────────────┘{_Colors.END}

{_Colors.DIM}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KEY INSIGHT: Agent is STATELESS (no memory during epochs).
            Continuity comes from SUBSTRATE (quest_log, receipts, snapshots).
            Each epoch: Fresh agent, same substrate → Same reasoning + learning.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{_Colors.END}
"""
    print(diagram)


def svg_diagram():
    """Generate SVG version of EOL cycle."""
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 1000 1400" xmlns="http://www.w3.org/2000/svg" font-family="monospace">
  <defs>
    <style>
      .box { fill: #f0f0f0; stroke: #333; stroke-width: 2; }
      .box-observe { fill: #d4edda; stroke: #28a745; stroke-width: 2; }
      .box-coherence { fill: #fff3cd; stroke: #ffc107; stroke-width: 2; }
      .box-plan { fill: #d1ecf1; stroke: #17a2b8; stroke-width: 2; }
      .box-critique { fill: #cce5ff; stroke: #004085; stroke-width: 2; }
      .box-act { fill: #f8d7da; stroke: #dc3545; stroke-width: 2; }
      .box-persist { fill: #d4edda; stroke: #28a745; stroke-width: 2; }
      .title { font-size: 18px; font-weight: bold; fill: #333; }
      .label { font-size: 12px; fill: #555; }
      .arrow { fill: none; stroke: #333; stroke-width: 2; marker-end: url(#arrowhead); }
      .line { stroke: #999; stroke-width: 1; fill: none; }
    </style>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#333" />
    </marker>
  </defs>

  <text x="500" y="30" text-anchor="middle" class="title">
    Epistemic-Operational Lattice (EOL) - Decision Cycle v0.1
  </text>

  <!-- Epoch N -->
  <rect x="350" y="50" width="300" height="40" class="box" rx="5"/>
  <text x="500" y="75" text-anchor="middle" class="label">Epoch N: Agent Reconstituted</text>

  <!-- Arrow down -->
  <path d="M 500 90 L 500 120" class="arrow"/>

  <!-- 1. OBSERVATION -->
  <rect x="100" y="120" width="800" height="180" class="box-observe" rx="10"/>
  <text x="110" y="145" class="title">1️⃣  OBSERVATION PLANE (sense)</text>
  <text x="120" y="170" class="label">Input sources: git, agents, quests, diagnostics</text>
  <text x="120" y="190" class="label">→ Signal(timestamp, source, value, confidence)</text>
  <text x="120" y="210" class="label">→ Aggregate 20-50 signals</text>
  <text x="120" y="250" class="label">Output: ObservationSignals[]</text>

  <path d="M 500 300 L 500 340" class="arrow"/>

  <!-- 2. COHERENCE -->
  <rect x="100" y="340" width="800" height="180" class="box-coherence" rx="10"/>
  <text x="110" y="365" class="title">2️⃣  COHERENCE PLANE (reconcile)</text>
  <text x="120" y="390" class="label">Signal precedence: user_input(10) > diagnostic(9) > agent(8) > quest(7) > git(6) > config(5)</text>
  <text x="120" y="410" class="label">Example: "error_count" tool(28) vs UI(209) → Resolve to 28</text>
  <text x="120" y="450" class="label">Output: Contradictions[], SignalDrift[]</text>

  <path d="M 500 520 L 500 560" class="arrow"/>

  <!-- 3. PLANNING -->
  <rect x="100" y="560" width="800" height="200" class="box-plan" rx="10"/>
  <text x="110" y="585" class="title">3️⃣  PLANNING PLANE (propose)</text>
  <text x="120" y="610" class="label">Input: WorldState + objective (e.g., "Analyze errors")</text>
  <text x="120" y="630" class="label">1. Intent parser → TaskType, constraints, keywords</text>
  <text x="120" y="650" class="label">2. Capability registry → Ollama(0.78, 15s), LM Studio(0.72, 8s), ChatDev(0.65, 120s)</text>
  <text x="120" y="670" class="label">3. Generate candidates → Rank by priority + cost</text>
  <text x="120" y="710" class="label">Output: list[Action] {agent, task, params, cost, eta}</text>

  <path d="M 500 760 L 500 800" class="arrow"/>

  <!-- 4. CRITIQUE -->
  <rect x="100" y="800" width="800" height="160" class="box-critique" rx="10"/>
  <text x="110" y="825" class="title">4️⃣  POLICY PLANE (critique)</text>
  <text x="120" y="850" class="label">Input: Action candidate + WorldState</text>
  <text x="120" y="870" class="label">Evaluation: Budget ✓ | Risk ✓ | Preconditions ✓ | Policy ✓</text>
  <text x="120" y="890" class="label">If SECURITY → Culture Ship approval (future)</text>
  <text x="120" y="930" class="label">Output: bool (approved / rejected + reason)</text>

  <path d="M 500 960 L 500 1000" class="arrow"/>

  <!-- 5. EXECUTION -->
  <rect x="100" y="1000" width="800" height="220" class="box-act" rx="10"/>
  <text x="110" y="1025" class="title">5️⃣  EXECUTION PLANE (act)</text>
  <text x="120" y="1050" class="label">Step 1: Validate preconditions (Ollama running? Model available?)</text>
  <text x="120" y="1070" class="label">Step 2: Dispatch to background orchestrator</text>
  <text x="120" y="1090" class="label">Step 3: Run with timeout + capture output</text>
  <text x="120" y="1110" class="label">Step 4: Validate postconditions (error_count decreased?)</text>
  <text x="120" y="1130" class="label">Step 5: Emit ActionReceipt (immutable) → ledger</text>
  <text x="120" y="1170" class="label">Output: ActionReceipt {id, agent, status, duration, postconditions}</text>

  <path d="M 500 1220 L 500 1260" class="arrow"/>

  <!-- 6. PERSIST -->
  <rect x="100" y="1260" width="800" height="100" class="box-persist" rx="10"/>
  <text x="110" y="1285" class="title">6️⃣  MEMORY PLANE (persist)</text>
  <text x="120" y="1310" class="label">Write: world_state_snapshot_N.json | action_receipt_ledger.jsonl | quest_receipt_links.jsonl</text>
  <text x="120" y="1330" class="label">Result: Agent ready for next epoch (stateless design)</text>

  <!-- Epoch N+1 -->
  <rect x="350" y="1370" width="300" height="40" class="box" rx="5"/>
  <text x="500" y="1395" text-anchor="middle" class="label">Epoch N+1 (reads same substrate)</text>
</svg>
"""
    return svg


def table_summary():
    """Print summary table of planes."""
    table = f"""
{_Colors.BOLD}Summary Table: 5 EOL Planes{_Colors.END}

┌──────────┬──────────────┬────────────────────────────┬──────────────────┐
│ Plane    │ Operation    │ Input                      │ Output           │
├──────────┼──────────────┼────────────────────────────┼──────────────────┤
│ 1. Obs   │ sense()      │ Signals (git, agents, etc) │ ObservationSet[] │
│ 2. Coh   │ reconcile()  │ ObservationSet[] + rules   │ Contradictions[] │
│ 3. Plan  │ propose()    │ WorldState + objective     │ Action[] (ranked)│
│ 4. Crit. │ critique()   │ Action + WorldState        │ bool (approved)  │
│ 5. Exec  │ act()        │ Action (approved)          │ ActionReceipt    │
│ 6. Mem   │ persist()    │ All of above               │ Ledger files     │
└──────────┴──────────────┴────────────────────────────┴──────────────────┘

{_Colors.DIM}
Files (v0.1 implementation):
  • build_world_state.py (450L) - Planes 1 & 2
  • plan_from_world_state.py (550L) - Plane 3
  • [critique logic built into eol_integration.py] - Plane 4
  • action_receipt_ledger.py (550L) - Plane 5
  • quest_receipt_linkage.py (300L) - Plane 6 (memory bridge)
{_Colors.END}
"""
    print(table)


if __name__ == "__main__":
    import sys

    print_svg = "--svg" in sys.argv
    print_detailed = "--detailed" in sys.argv

    if print_detailed:
        ascii_diagram()
    else:
        ascii_diagram()

    table_summary()

    if print_svg:
        svg_data = svg_diagram()
        svg_path = Path(__file__).parent / "eol_cycle_diagram.svg"
        svg_path.write_text(svg_data)
        print(f"\n{_Colors.GREEN}✓ SVG diagram saved to {svg_path}{_Colors.END}\n")
