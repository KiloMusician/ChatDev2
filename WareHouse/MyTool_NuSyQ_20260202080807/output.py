from rich.console import Console
class RichOutput:
    """Provides rich console output for MyTool."""
    def __init__(self):
        self.console = Console()
    def display_config(self, config):
        """Display the configuration settings."""
        self.console.print(f"API Key: {config.api_key}")
        self.console.print(f"Debug Mode: {'Enabled' if config.debug_mode else 'Disabled'}")