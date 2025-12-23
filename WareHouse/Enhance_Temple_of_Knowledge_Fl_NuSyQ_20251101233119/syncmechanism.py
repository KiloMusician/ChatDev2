# SimulatedVerse/src/temple/memory_system.py
class MemorySystem:
    def __init__(self):
        self.data = {}
    def add_knowledge(self, key, value):
        self.data[key] = value
    def get_knowledge(self, key):
        return self.data.get(key)
# SimulatedVerse/modules/culture_ship/ship_state.py
class ShipState:
    def __init__(self):
        self.health_metrics = {}
    def update_health(self, metric, value):
        self.health_metrics[metric] = value
    def get_health(self, metric):
        return self.health_metrics.get(metric)
# SimulatedVerse/src/temple/sync_mechanism.py
from .memory_system import MemorySystem
from ..modules.culture_ship.ship_state import ShipState
class SyncMechanism:
    def __init__(self):
        self.memory_system = MemorySystem()
        self.ship_state = ShipState()
    def sync_knowledge(self, key, value):
        if isinstance(value, dict) and 'health' in value:
            self.ship_state.update_health(key, value['health'])
        else:
            self.memory_system.add_knowledge(key, value)
    def get_synced_data(self, key):
        if isinstance(key, str) and key.startswith('health'):
            return {'health': self.ship_state.get_health(key)}
        else:
            return self.memory_system.get_knowledge(key)