# MyTool CLI User Manual

## Introduction

MyTool is a command-line interface tool built with Python. It uses `click` for handling command-line arguments, `pydantic` for configuration management, and `rich` for rich console output. This manual will guide you through the installation of dependencies, usage of the CLI, and provide examples to help you get started.

## Installation

### Prerequisites

- **Python**: Ensure that Python 3.7 or higher is installed on your system.
- **pip**: Make sure `pip` is installed as it is required for installing Python packages.

### Steps

1. **Install Dependencies**:
   You can install the required dependencies using `pip`. It's recommended to use a virtual environment to manage your project's dependencies.

   ```bash
   # Create and activate a virtual environment (optional but recommended)
   python -m venv mytool-env
   source mytool-env/bin/activate  # On Windows use `mytool-env\Scripts\activate`

   # Install the required packages from requirements.txt
   pip install -r requirements.txt
   ```

2. **Download the Code**:
   You can download the code for MyTool from our repository or clone it using Git.

   ```bash
   git clone https://github.com/ChatDev/mytool.git
   cd mytool
   ```

3. **Install the CLI**:
   If you want to install MyTool as a command-line tool, you can use `pip`.

   ```bash
   pip install .
   ```

## Usage

### Main Command

The main command of MyTool is `mytool`. You can run it using the following syntax:

```bash
mytool <command> [options]
```

### Commands

#### `run`

This command runs MyTool with a specified configuration file.

**Syntax:**

```bash
mytool run --config <path_to_config_file>
```

**Options:**

- `--config`: Path to the configuration file (required).

**Example:**

```bash
mytool run --config config.json
```

### Configuration File

MyTool uses a JSON configuration file to store settings. Here is an example of what the configuration file might look like:

```json
{
    "api_key": "your_api_key_here",
    "debug_mode": true
}
```

- **`api_key`**: Your API key for authentication.
- **`debug_mode`**: A boolean indicating whether debug mode should be enabled.

## Testing

MyTool includes unit tests to ensure the functionality of its components. You can run these tests using `pytest`.

```bash
pytest
```

This will execute all test files in the project and provide a report on the results.

## Documentation

For more detailed information about MyTool, including advanced usage and API documentation, please refer to the [full documentation](https://github.com/ChatDev/mytool/docs).

## Contributing

We welcome contributions from the community! If you have any ideas for improvements or bug fixes, please fork the repository and submit a pull request.

## Support

If you encounter any issues or have questions about MyTool, please feel free to reach out to our support team via email at [support@chatdev.com](mailto:support@chatdev.com).

---

Thank you for using MyTool! We hope this manual helps you get the most out of our tool. If you have any feedback or suggestions, we'd love to hear from you.

Best regards,

The ChatDev Team