'''
Class managing all missions and providing methods to interact with them.
'''
from mission import Mission
class MissionManager:
    def __init__(self):
        self.missions = []
    def add_mission(self, mission):
        self.missions.append(mission)
    def get_mission_by_id(self, id):
        for mission in self.missions:
            if mission.id == id:
                return mission
        return None
    def execute_command(self, command):
        # Execute a command across all missions
        results = []
        for mission in self.missions:
            result = mission.execute_command(command)
            results.append((mission.title, result))
        return results