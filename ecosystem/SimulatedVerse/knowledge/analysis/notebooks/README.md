# KPulse Analytics

This directory contains Jupyter notebooks for analyzing gameplay data and informing development decisions.

## Notebooks

- `balance-analysis.ipynb` - Resource production and consumption balance
- `narrative-effectiveness.ipynb` - Story engagement and player response metrics  
- `tier-progression.ipynb` - Advancement pacing and difficulty curves
- `colonist-behavior.ipynb` - Personality system effectiveness analysis
- `event-patterns.ipynb` - Player interaction patterns and optimization opportunities

## Data Sources

- `/analysis/datasets/events.ndjson` - Real-time event stream from game
- `/analysis/datasets/metrics.ndjson` - Resource and progression metrics
- `/analysis/datasets/narrative.ndjson` - Story events and player choices
- `/analysis/datasets/directives.ndjson` - Self-spawned content effectiveness

## Usage

```bash
# Start Jupyter Lab
make analyze

# Or directly:
jupyter lab --notebook-dir=analysis
```

## Integration

Results from these analyses automatically feed into:
- Knowledge base insights (`/kb/insights/`)
- RepoPilot training data for better suggestions
- Automatic balance adjustments in directive spawning
- Storyteller personality tuning

## Cultivation Loop

1. **Play** → Events logged to datasets
2. **Analyze** → Notebooks identify patterns and issues  
3. **Insights** → Findings documented in knowledge base
4. **Suggestions** → RepoPilot proposes code improvements
5. **Implementation** → Changes deployed and cycle repeats

This creates a self-improving game that evolves based on actual player behavior and data-driven decisions.