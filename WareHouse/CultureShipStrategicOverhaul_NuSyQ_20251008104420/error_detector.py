class ErrorDetector:
    def __init__(self, system_status):
        self.system_status = system_status
    def scan(self):
        status = self.system_status.get_status()
        for module in status["ImportErrors"]:
            print(f"Scanning {module} for errors...")
            # Simulate error detection
            if "module1" == module:
                print("Error found in module1: Dependency issue")
            elif "module2" == module:
                print("Error found in module2: Syntax error")
    def get_errors(self):
        return self.system_status.get_status()["ImportErrors"]