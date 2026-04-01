# Knowledge Base — Terminal Depths

This directory contains persistent knowledge accumulated by the agent framework.

## Files

- `last_playtest.json` — Results of the most recent playtest.py run
- `tester_results.json` — Results from agents/tester.py
- `coverage_report.json` — Engine coverage from agents/implementer.py
- `content_manifest.json` — Generated content catalog
- `player_report_*.json` — Play session reports from agents/player.py

## Patterns

### Running a quick health check
```bash
python3 agents/tester.py --quick
```

### Full playtest
```bash
python3 playtest.py
```

### Generate new content
```bash
python3 agents/content_generator.py --batch 5
```

### Orchestrator status
```bash
python3 agents/orchestrator.py --status
```

### Implementation gaps
```bash
python3 agents/implementer.py --gaps --verbose
```
