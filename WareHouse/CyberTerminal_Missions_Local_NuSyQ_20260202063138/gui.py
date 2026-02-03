'''
Class providing the graphical user interface for managing missions.
'''
import tkinter as tk
from tkinter import messagebox, simpledialog
from mission_manager import MissionManager
class MissionManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CyberTerminal Training Missions")
        self.mission_manager = MissionManager()
        self.create_widgets()
    def create_widgets(self):
        # Create widgets for adding a new mission
        tk.Label(self.root, text="Title:").grid(row=0, column=0)
        self.title_entry = tk.Entry(self.root)
        self.title_entry.grid(row=0, column=1)
        tk.Label(self.root, text="Goal:").grid(row=1, column=0)
        self.goal_entry = tk.Entry(self.root)
        self.goal_entry.grid(row=1, column=1)
        tk.Label(self.root, text="Required Commands (comma-separated):").grid(row=2, column=0)
        self.commands_entry = tk.Entry(self.root)
        self.commands_entry.grid(row=2, column=1)
        tk.Label(self.root, text="Success Criteria:").grid(row=3, column=0)
        self.criteria_entry = tk.Entry(self.root)
        self.criteria_entry.grid(row=3, column=1)
        tk.Label(self.root, text="Flavor:").grid(row=4, column=0)
        self.flavor_entry = tk.Entry(self.root)
        self.flavor_entry.grid(row=4, column=1)
        add_button = tk.Button(self.root, text="Add Mission", command=self.add_mission)
        add_button.grid(row=5, columnspan=2)
        # Create a listbox to display missions
        self.missions_listbox = tk.Listbox(self.root)
        self.missions_listbox.grid(row=6, columnspan=2)
        execute_button = tk.Button(self.root, text="Execute Command", command=self.execute_command)
        execute_button.grid(row=7, columnspan=2)
    def add_mission(self):
        title = self.title_entry.get()
        goal = self.goal_entry.get()
        commands = [cmd.strip() for cmd in self.commands_entry.get().split(',')]
        criteria = self.criteria_entry.get()
        flavor = self.flavor_entry.get()
        if not all([title, goal, commands, criteria, flavor]):
            messagebox.showerror("Error", "All fields are required")
            return
        mission = Mission(len(self.mission_manager.missions) + 1, title, goal, commands, criteria, flavor)
        self.mission_manager.add_mission(mission)
        self.update_missions_listbox()
    def update_missions_listbox(self):
        self.missions_listbox.delete(0, tk.END)
        for mission in self.mission_manager.missions:
            self.missions_listbox.insert(tk.END, f"{mission.id}: {mission.title}")
    def execute_command(self):
        selected_index = self.missions_listbox.curselection()
        if not selected_index:
            messagebox.showerror("Error", "Select a mission first")
            return
        mission_id = int(self.missions_listbox.get(selected_index)[0])
        mission = self.mission_manager.get_mission_by_id(mission_id)
        command = simpledialog.askstring("Command", "Enter command to execute:")
        if not command:
            return
        result = self.mission_manager.execute_command(command)
        success_count = sum(1 for res in result if res[1])
        failure_count = len(result) - success_count
        messagebox.showinfo(
            "Result",
            f"Mission {mission.title}: {'Success' if all(res[1] for res in result) else 'Failure'}\n"
            f"Commands Executed: {len(result)}\n"
            f"Successes: {success_count}\n"
            f"Failures: {failure_count}"
        )