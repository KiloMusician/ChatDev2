from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class DevMentorState(BaseModel):
    schema_version: str = "2.0"
    first_open_completed: bool = False
    active_track: str = "vscode"
    active_tutorial: str = "tutorials/00-vscode-basics/01-command-palette.md"
    active_challenge: Optional[str] = None
    skill_xp: Dict[str, int] = Field(default_factory=lambda: {"vscode":0,"git":0,"ai":0,"debugging":0,"godot":0})
    achievements: List[str] = Field(default_factory=list)
    last_platform: str = "unknown"
