class FixPrioritizer:
    def __init__(self, error_detector):
        self.error_detector = error_detector
    def prioritize(self):
        errors = self.error_detector.get_errors()
        for error in errors:
            print(f"Prioritizing fix for {error}...")
            # Simulate prioritization based on impact
            if "module1" == error:
                print("Priority: High")
            elif "module2" == error:
                print("Priority: Medium")
    def get_prioritized_fixes(self):
        return self.error_detector.get_errors()