Repository maze scanner utilities

Files:
- `maze_solver.py` - DFS-style scanner that finds TODO/FIXME/BUG markers across the repo.
- `run_and_capture.py` - Utility to run commands, stream output to terminal, and write full logs to `logs/`.

Quick usage:

Run scanner and stream output while capturing logs:

```powershell
python -m src.tools.run_and_capture python -m src.tools.maze_solver . --max-depth 8
```

Programmatic usage from Python:

```python
from src.tools.maze_solver import MazeRepoScanner
s = MazeRepoScanner(Path('.'))
findings = s.scan()
```

Recommended VS Code task (add to `.vscode/tasks.json`):

```json
{
  "label": "Scan repo for treasures",
  "type": "shell",
  "command": "python -m src.tools.run_and_capture python -m src.tools.maze_solver . --max-depth 8",
  "group": "build"
}
```
