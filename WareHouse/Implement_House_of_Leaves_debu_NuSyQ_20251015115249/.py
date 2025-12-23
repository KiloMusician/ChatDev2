# House of Leaves Debugging Labyrinth System
## Overview
The House of Leaves debugging labyrinth system is designed to help developers navigate through complex issues in their codebase. It consists of four core modules: `maze_navigator.py`, `minotaur_tracker.py`, `environment_scanner.py`, and `debugging_labyrinth.py`.
## Modules
### 1. maze_navigator.py
- **Description**: Parses error logs to create a navigable maze using A* pathfinding and provides XP rewards.
- **Functions**:
  - `parse_error_logs(logs: str)`: Parses logs to define the maze.
  - `a_star_search()`: Finds the shortest path using A* algorithm.
  - `get_path()`: Returns the path and XP reward.
### 2. minotaur_tracker.py
- **Description**: Handles bug hunting with boss battles for complex issues.
- **Functions**:
  - `add_boss_battle(issue: str)`: Adds a boss battle for a specific issue.
  - `hunt_bugs()`: Simulates bug hunting with boss battles.
### 3. environment_scanner.py
- **Description**: Scans the repository for complexity metrics.
- **Functions**:
  - `scan_repo()`: Scans the repository and returns complexity metrics.
### 4. debugging_labyrinth.py
- **Description**: Main orchestrator that generates quests from failed tests.
- **Functions**:
  - `generate_quests()`: Generates quests based on failed tests.
  - `main()`: Orchestrates the entire process.
## Usage
1. Run the `debugging_labyrinth.py` script to start the debugging labyrinth system.
2. The system will parse error logs, scan the repository, and generate quests for bug hunting.
3. The path through the maze and XP rewards will be displayed.