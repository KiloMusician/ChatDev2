import click
from config import Config
from output import RichOutput
@click.group()
def cli():
    pass
@cli.command()
@click.option('--config', required=True, help='Path to configuration file')
def run(config):
    """Run MyTool with the specified configuration."""
    try:
        config_instance = Config.from_file(config)
        output = RichOutput()
        output.display_config(config_instance)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
if __name__ == '__main__':
    cli()