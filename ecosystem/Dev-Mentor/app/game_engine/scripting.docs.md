# scripting.py

# Terminal Depths — In-Game Scripting Engine

## Overview
The Terminal Depths module provides a sandboxed scripting engine for in-game scripting, similar to Bitburner's `ns` API. It allows scripts to run with restricted built-in functions while providing full access to the `ns` API for game interaction.

## Public API

### Classes

#### `NS`
The `NS` class mirrors the Bitburner `ns` object and exposes various game engine functionalities to scripts running in the sandbox.

**Constructor:**
- `__init__(session: GameSession, args: List[str] | None = None)`: Initializes the NS object with a game session and optional arguments.

### Methods

#### Output Methods
- `tprint(*args) -> None`: Prints a message to the terminal, adding a line to the script output.
- `tprintRaw(line: dict) -> None`: Prints a raw output-line dictionary (advanced).
- `print(*args) -> None`: Alias for `tprint`.

#### Filesystem Methods
- `ls(path: str = ".") -> List[str]`: Lists files in a directory and returns a list of names.
- `read(filename: str) -> str`: Reads the content of a file. Raises `FileNotFoundError` if the file is missing.
- `write(filename: str, content: str, mode: str = "w") -> None`: Writes or appends content to a file.
- `fileExists(filename: str) -> bool`: Checks if a file exists.
- `rm(filename: str) -> bool`: Removes a file.
- `mv(src: str, dst: str) -> None`: Moves or renames a file.
- `getScriptName() -> str`: Returns the name of the currently running script.

#### Player / Server Info Methods
- `getPlayer() -> dict`: Returns a dictionary of player stats.
- `getHostname() -> str`: Returns the hostname of the current server.

## Usage Examples

```python
# Example of using the NS class in a script
from your_module import NS

# Initialize the NS object with a game session
ns = NS(session)

# Print a message to the terminal
ns.tprint("Hello, Terminal Depths!")

# List files in the current directory
files = ns.ls()
ns.tprint("Files in current directory:", files)

# Read a file's content
try:
    content = ns.read("example.txt")
    ns.tprint("File content:", content)
except FileNotFoundError as e:
    ns.tprint("Error:", str(e))

# Write to a file
ns.write("output.txt", "This is some output.")

# Check if a file exists
if ns.fileExists("output.txt"):
    ns.tprint("output.txt exists.")
```

## Important Notes
- The `NS` class is designed to operate within a restricted environment; only safe
