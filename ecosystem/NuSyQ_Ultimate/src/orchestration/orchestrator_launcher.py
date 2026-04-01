import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'src' imports resolve when started as a detached process
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# Also add the NuSyQ-Hub src path where the orchestrator implementation lives
hub_root = Path(os.getenv("NUSYQ_HUB_ROOT", "/mnt/c/Users/keath/Desktop/Legacy/NuSyQ-Hub")).resolve()
if hub_root.exists() and str(hub_root) not in sys.path:
    # Insert the parent directory so the 'src' package inside NuSyQ-Hub is importable as 'src'
    sys.path.insert(0, str(hub_root))

log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'orchestrator.log'

logging.basicConfig(filename=str(log_file), level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
# mirror to stdout as well
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logging.info('Starting MultiAIOrchestrator from orchestrator_launcher.py')

try:
    # Diagnostic: dump sys.path and hub_root contents to help debug import issues
    logging.info('--- Debug: sys.path start ---')
    for p in sys.path:
        logging.info('sys.path entry: %s', p)
    logging.info('--- Debug: sys.path end ---')
    logging.info('Checking NuSyQ-Hub path: %s', hub_root)
    try:
        exists = hub_root.exists()
        logging.info('Hub root exists: %s', exists)
        if exists:
            # List a few entries in the hub_root to confirm 'src' presence
            entries = [p.name for p in hub_root.iterdir()][:50]
            logging.info('Hub root entries (first 50): %s', entries)
            src_path = hub_root / 'src'
            logging.info('hub_root/src exists: %s', src_path.exists())
            if src_path.exists():
                sample = [p.name for p in src_path.iterdir()][:50]
                logging.info('src dir entries (first 50): %s', sample)
    except (OSError, AttributeError, TypeError):
        logging.exception('Failed to inspect hub_root for diagnostics')

    from src.orchestration.multi_ai_orchestrator import MultiAIOrchestrator
    orchestrator = MultiAIOrchestrator()
    orchestrator.start_orchestration()
except Exception as e:
    logging.exception('Failed to start orchestrator: %s', e)
    raise

# keep process alive if orchestrator uses background threads
try:
    import time
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    logging.info('Orchestrator launcher received KeyboardInterrupt, exiting')
