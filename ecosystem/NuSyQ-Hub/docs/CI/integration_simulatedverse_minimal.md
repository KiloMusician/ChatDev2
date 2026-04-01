# Integration: SimulatedVerse Minimal CI

This workflow runs a source-of-truth integration test for the SimulatedVerse minimal server
and a simulated "Culture Ship" agent to validate the file-based async bridge and
local start scripts.

What it does:
- Installs Python and Node dependencies
- Starts a minimal SimulatedVerse server via `scripts/start_simulatedverse_minimal.py`
- Starts the simulated Culture Ship agent via `scripts/simulate_culture_ship_agent.py`
- Waits for the health endpoint to return
- Runs the test suite (`pytest`) and uploads logs

How to run locally for debugging:

1. Ensure the SimulatedVerse directory exists under the workspace: `SimulatedVerse/SimulatedVerse`
2. Install Python deps and Node deps:
```bash
python -m pip install -r requirements-dev.txt
cd SimulatedVerse/SimulatedVerse
npm ci
```

3. Start the simulate agent in the background:
```bash
export SIMULATEDVERSE_ROOT=$(pwd)/SimulatedVerse/SimulatedVerse # adjust path accordingly
nohup python scripts/simulate_culture_ship_agent.py > simulate_agent.log 2>&1 &
```

4. Start the minimal server (runs in background on linux):
```bash
export SIMULATEDVERSE_PATH=$(pwd)/SimulatedVerse/SimulatedVerse
nohup python scripts/start_simulatedverse_minimal.py --force --timeout 60 > simmin.log 2>&1 &
```

5. Confirm the server responds:
```bash
curl -sf http://localhost:${SIMULATEDVERSE_PORT:-5002}/api/health
```

6. Run the test(s):
```bash
python -m pytest -q
```

If you want CI to cover more, consider building a devcontainer-based integration job that mirrors developer environment.

Notes:
- This workflow intentionally attempts to run quickly and is an optional integration gate for PRs.
- On Windows or specialized developer machines, set `SIMULATEDVERSE_ROOT` or `SIMULATEDVERSE_PATH` env variables if the path layout differs.
