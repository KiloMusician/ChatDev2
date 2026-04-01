"""Small runner to ingest a set of sample files into DuckDB for smoke testing."""

import logging
from pathlib import Path

from . import ingest

logger = logging.getLogger(__name__)


def run_samples(db_path: Path = Path("./data/state.duckdb"), samples: list[Path] | None = None):
    samples = samples or [Path("SimulatedVerse/state/shared_cultivation/quest_log.jsonl")]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Call the ingester programmatically for each sample
    for s in samples:
        if s.exists():
            ingest.main(["--db-path", str(db_path), "--input", str(s)])
        else:
            logger.info("sample missing:", s)


if __name__ == "__main__":
    run_samples()
