from pydantic import BaseModel, Field
class Config(BaseModel):
    """Configuration settings for MyTool."""
    api_key: str = Field(..., description="API key for authentication")
    debug_mode: bool = Field(False, description="Enable debug mode")
    @classmethod
    def from_file(cls, file_path: str):
        """Load configuration from a JSON file."""
        with open(file_path, 'r') as f:
            data = f.read()
        return cls.parse_raw(data)