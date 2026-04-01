"""KILO-FOOLISH Conversation Manager
Manages conversation state and context.
"""


class ConversationManager:
    def __init__(self):
        self.conversations = {}

    def create_conversation(self, conversation_id):
        """Create a new conversation."""
        self.conversations[conversation_id] = {"messages": [], "context": {}}

    def add_message(self, conversation_id, role, content):
        """Add a message to a conversation."""
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)

        self.conversations[conversation_id]["messages"].append({"role": role, "content": content})


# Global instance
conversation_manager = ConversationManager()
