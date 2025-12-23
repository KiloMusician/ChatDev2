class ShipState:
    def __init__(self):
        self.health = None
    def update_health(self, health):
        if not isinstance(health, (int, float)):
            raise ValueError("Health metrics must be numeric.")
        if health < 0 or health > 100:
            raise ValueError("Health metrics out of acceptable range (0-100).")
        self.health = health