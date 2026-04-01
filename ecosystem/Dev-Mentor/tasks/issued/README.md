# Task Surfaces

- `queue.json`: canonical live swarm queue
- `legacy_runtime/`: legacy file-based task lane kept for backward compatibility
- `archive/`: historical task snapshots and stale task records

Top-level task JSON files should not be created anymore. New file-based legacy
tasks belong under `legacy_runtime/`, and new swarm work belongs in
`queue.json`.
