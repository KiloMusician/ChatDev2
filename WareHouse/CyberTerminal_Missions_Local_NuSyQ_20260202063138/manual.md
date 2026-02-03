# CyberTerminal Training Missions

Welcome to CyberTerminal Training Missions! This application allows you to create and manage training missions for the CyberTerminal game. Each mission includes a goal, required commands, success criteria, and flavor text to provide an immersive experience.

## Table of Contents

1. [Quick Install](#quick-install)
2. [Main Functions](#main-functions)
3. [How to Use/Play](#how-to-useplay)

## Quick Install

To get started with CyberTerminal Training Missions, you need to install the required dependencies. Follow these steps:

### Using pip

```sh
pip install -r requirements.txt
```

### Using conda

```sh
conda create -n cyberterminal python=3.8
conda activate cyberterminal
conda install -c conda-forge -f requirements.txt
```

## Main Functions

The main functions of CyberTerminal Training Missions include:

- **Creating Missions**: Add new missions with a title, goal, required commands, success criteria, and flavor text.
- **Executing Commands**: Execute commands in the context of each mission to determine if they are successful or not.
- **Managing Missions**: View all missions, update existing ones, and delete them as needed.

## How to Use/Play

### Adding a New Mission

1. Open the CyberTerminal Training Missions application.
2. Click on the "Add Mission" button.
3. Fill in the following fields:
   - **Title**: The name of the mission.
   - **Goal**: The objective of the mission.
   - **Required Commands (comma-separated)**: A list of commands that must be executed to complete the mission.
   - **Success Criteria**: The condition that must be met for the mission to be considered successful.
   - **Flavor**: Additional text to enhance the immersive experience.
4. Click "Add Mission" to save the new mission.

### Executing Commands

1. Open the CyberTerminal Training Missions application.
2. Select a mission from the listbox.
3. Click on the "Execute Command" button.
4. Enter the command you want to execute in the dialog box.
5. Click "OK" to execute the command.
6. The application will display the result of the command execution, indicating whether it was successful or not.

### Managing Missions

1. Open the CyberTerminal Training Missions application.
2. Select a mission from the listbox.
3. You can update the mission details by clicking on "Add Mission" again and editing the fields.
4. To delete a mission, select it and click on the appropriate button in the GUI.

## Example Usage

Here's an example of how to create a new mission and execute commands:

1. **Create a New Mission**:
   - Title: Retrieve Data
   - Goal: Collect all data from the server.
   - Required Commands: login, fetch_data
   - Success Criteria: Data retrieved successfully.
   - Flavor: You are a cyber operative tasked with retrieving sensitive information.

2. **Execute Commands**:
   - Enter "login" and click "OK".
   - Enter "fetch_data" and click "OK".

The application will display the result of each command execution, indicating whether it was successful or not.

That's it! With CyberTerminal Training Missions, you can create engaging training missions for the CyberTerminal game. Enjoy your coding journey!