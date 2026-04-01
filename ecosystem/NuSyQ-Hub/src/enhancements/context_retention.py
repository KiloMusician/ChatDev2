from datetime import datetime
from typing import Any, cast


class ContextRetention:
    """Manages the retention of contextual information across sessions."""

    def __init__(self) -> None:
        """Initialize ContextRetention with empty contextual memory and session history."""
        self.contextual_memory: dict[str, dict[str, Any]] = {}
        self.session_history: list[dict[str, Any]] = []
        self.last_updated: datetime = datetime.now()

    def store_context(self, session_id: str, context_data: dict[str, Any]) -> None:
        """Store contextual information for a given session.

        Args:
            session_id (str): The session identifier.
            context_data (dict[str, Any]): Contextual data to store.

        """
        self.contextual_memory[session_id] = context_data
        self.last_updated = datetime.now()

    def retrieve_context(self, session_id: str) -> dict[str, Any]:
        """Retrieve contextual information for a given session.

        Args:
            session_id (str): The session identifier.

        Returns:
            dict[str, Any]: The contextual data for the session, or empty dict if not found.

        """
        return cast(dict[str, Any], self.contextual_memory.get(session_id, {}))

    def update_session_history(self, session_data: dict[str, Any]) -> None:
        """Update the history of sessions with new data.

        Args:
            session_data (dict[str, Any]): Data to append to session history.

        """
        self.session_history.append(session_data)
        self.last_updated = datetime.now()

    def clear_context(self, session_id: str) -> None:
        """Clear contextual information for a given session.

        Args:
            session_id (str): The session identifier to clear.

        """
        if session_id in self.contextual_memory:
            del self.contextual_memory[session_id]
            self.last_updated = datetime.now()

    def get_all_contexts(self) -> dict[str, Any]:
        """Retrieve all stored contextual information.

        Returns:
            dict[str, Any]: All contextual memory.

        """
        return self.contextual_memory

    def get_session_history(self) -> list[dict[str, Any]]:
        """Retrieve the history of all sessions.

        Returns:
            list[dict[str, Any]]: list of session history entries.

        """
        return self.session_history

    def get_last_updated(self) -> datetime:
        """Get the last updated timestamp for the context retention system.

        Returns:
            datetime: The last updated datetime.

        """
        return self.last_updated
