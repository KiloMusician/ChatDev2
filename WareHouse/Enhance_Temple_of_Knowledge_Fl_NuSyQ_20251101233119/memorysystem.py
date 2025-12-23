# SimulatedVerse/src/temple/memory_system.py
class MemorySystem:
    """
    A class to represent the memory system of the Temple of Knowledge Floor 1.
    """
    def __init__(self):
        """
        Initializes an empty dictionary to store knowledge data.
        """
        self.data = {}
    def add_knowledge(self, key, value):
        """
        Adds new knowledge to the memory system.
        Args:
            key (str): The key under which the knowledge is stored.
            value (any): The value of the knowledge to be stored.
        """
        self.data[key] = value
    def get_knowledge(self, key):
        """
        Retrieves knowledge from the memory system based on the given key.
        Args:
            key (str): The key under which the knowledge is stored.
        Returns:
            any: The value of the knowledge associated with the key.
        """
        return self.data.get(key)