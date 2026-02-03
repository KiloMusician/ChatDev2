'''
Main entry point for the CyberTerminal training missions application.
'''
from gui import MissionManagerGUI
import mission_data
def load_missions():
    for mission in mission_data.missions:
        m = Mission(mission["id"], mission["title"], mission["goal"], mission["required_commands"], mission["success_criteria"], mission["flavor"])
        mission_manager.add_mission(m)
def main():
    root = tk.Tk()
    app = MissionManagerGUI(root)
    load_missions()
    root.mainloop()
if __name__ == "__main__":
    mission_manager = MissionManager()
    main()