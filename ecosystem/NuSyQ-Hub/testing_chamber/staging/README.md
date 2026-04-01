# Task Manager CLI Tool

## Introduction

Task Manager is a Python Command Line Interface (CLI) tool designed to help you manage your tasks efficiently. It allows you to add, list, and delete tasks using simple commands in the terminal. The tool uses a JSON file for persistent storage of tasks.

## Installation

### Prerequisites
- Python 3.x installed on your system.
- pip (Python package installer).

### Installation Steps
1. Clone this repository or download the files.
2. Navigate to the project directory.
3. Install the required dependencies by running:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Adding a New Task
To add a new task, run the following command:
```bash
python main.py add "Task description"
```
Replace `"Task description"` with your actual task description.

### Listing All Tasks
To list all tasks, run the following command:
```bash
python main.py list
```

### Deleting a Task
To delete a task, run the following command:
```bash
python main.py delete <task_id>
```
Replace `<task_id>` with the ID of the task you want to delete.

## Example Usage

1. **Adding Tasks**
   ```bash
   python main.py add "Complete Python project"
   python main.py add "Read a book on data structures"
   ```

2. **Listing Tasks**
   ```bash
   python main.py list
   ```
   Output:
   ```
   1: Complete Python project
   2: Read a book on data structures
   ```

3. **Deleting a Task**
   ```bash
   python main.py delete 1
   ```
   Output:
   ```
   Task 1 deleted.
   ```

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Thank you for using Task Manager CLI Tool!