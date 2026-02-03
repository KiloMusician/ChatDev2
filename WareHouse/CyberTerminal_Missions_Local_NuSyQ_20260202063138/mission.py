'''
Class representing a single mission with attributes and methods.
'''
class Mission:
    def __init__(self, id, title, goal, required_commands, success_criteria, flavor):
        self.id = id
        self.title = title
        self.goal = goal
        self.required_commands = required_commands
        self.success_criteria = success_criteria
        self.flavor = flavor
    def execute_command(self, command):
        # Simulate command execution
        if command in self.required_commands:
            return True
        else:
            return False