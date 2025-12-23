# House of Leaves Debugging Labyrinth System User Manual

## Introduction

Welcome to the House of Leaves Debugging Labyrinth System, designed to streamline your debugging process by transforming error logs into an engaging and interactive experience. This system comprises four core modules: `maze_navigator.py`, `minotaur_tracker.py`, `environment_scanner.py`, and `debugging_labyrinth.py`. Each module plays a crucial role in navigating through complex issues efficiently.

## 1. Usage Instructions

### 1.1 Installation
1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/ChatDev/house-of-leaves.git
   ```

2. **Install Dependencies**:
   Navigate to the cloned directory and install the required Python packages.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory with necessary configurations such as API keys or paths.

### 1.2 Running the Application
To start the application, run the main orchestrator script.
```bash
python debugging_labyrinth.py
```
This will initialize all modules and begin processing your error logs and tests.

## 2. Examples of Key Features

### 2.1 Maze Navigator (`maze_navigator.py`)
- **Parsing Error Logs**: The system parses error logs to create a navigable maze.
- **A* Pathfinding**: Utilizes A* algorithm for efficient pathfinding through the maze.
- **XP Rewards**: Provides XP rewards for successful navigation, encouraging continuous improvement.

### 2.2 Minotaur Tracker (`minotaur_tracker.py`)
- **Bug Hunting**: Identifies complex issues and presents them as boss battles.
- **Interactive Challenges**: Engages users in solving intricate bugs to progress through the system.

### 2.3 Environment Scanner (`environment_scanner.py`)
- **Repo Scanning**: Analyzes your repository for complexity metrics.
- **Complexity Metrics**: Provides insights into code complexity, aiding in prioritization of debugging efforts.

### 2.4 Debugging Labyrinth (`debugging_labyrinth.py`)
- **Quest Generation**: Generates quests from failed tests, guiding users through the debugging process.
- **Orchestration**: Manages interactions between all modules to ensure a seamless experience.

## 3. Setup and Configuration Steps

1. **Environment Variables**:
   - `API_KEY`: Your API key for accessing external services.
   - `LOG_PATH`: Path to your error logs.
   - `REPO_PATH`: Path to your repository.

2. **Configuration File**:
   Edit the `config.yaml` file located in the root directory with specific settings tailored to your environment.

## 4. Important Limitations and Considerations

- **Error Log Format**: Ensure that your error logs are in a compatible format for parsing.
- **Repository Size**: Large repositories may require additional processing time.
- **External Dependencies**: Some features rely on external APIs; ensure they are accessible and configured correctly.

## 5. Contact Information for Support

For any issues or questions, please contact our support team at:
- Email: support@chatdev.com
- Phone: +1-800-CHATDEV

We are committed to providing timely assistance and ensuring your debugging experience is as smooth as possible.

---

Thank you for choosing the House of Leaves Debugging Labyrinth System. We hope this manual helps you navigate through complex issues with ease. Happy debugging!