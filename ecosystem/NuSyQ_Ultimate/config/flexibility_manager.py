"""
NuSyQ Flexible Configuration System
===================================

Purpose:
    Replace hardcoded paths and brittle configurations with a flexible,
    environment-aware system that adapts to different setups and users.

Key Features:
    1. Dynamic path resolution (Windows/Linux/macOS)
    2. GitHub user authentication integration
    3. Environment detection and adaptation
    4. Extension activation management
    5. Graceful fallback mechanisms
"""

import json
import logging
import os
import platform
import subprocess
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GitHubConfig:
    """GitHub configuration for KiloMusician account"""
    username: str = "KiloMusician"
    authenticated: bool = False
    token_available: bool = False
    repositories: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if self.repositories is None:
            self.repositories = []


@dataclass
class EnvironmentConfig:
    """System environment configuration"""
    os_type: str = ""
    python_path: str = ""
    node_path: str = ""
    git_path: str = ""
    docker_available: bool = False
    kubectl_available: bool = False
    workspace_root: str = ""

    def __post_init__(self) -> None:
        self.os_type = platform.system()
        self.workspace_root = str(Path(__file__).parent.parent.absolute())
        self._detect_tools()

    def _detect_tools(self) -> None:
        """Detect available development tools"""
        tools = {
            'python': ['python', 'python3', 'py'],
            'node': ['node', 'nodejs'],
            'git': ['git'],
            'docker': ['docker'],
            'kubectl': ['kubectl'],
            'pwsh': ['pwsh', 'powershell']
        }

        for tool_name, commands in tools.items():
            found_path: Optional[str] = None
            # Try shutil.which first for an absolute path
            for cmd in commands:
                try:
                    wp = shutil.which(cmd)
                    if wp:
                        found_path = wp
                        break
                except (OSError, TypeError):
                    continue

            # Fallback: try running --version to catch wrappers like 'py'
            if not found_path:
                for cmd in commands:
                    try:
                        result = subprocess.run(
                            [cmd, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            check=False
                        )
                        if result.returncode == 0:
                            # prefer the command name if which not found
                            found_path = cmd
                            break
                    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                        continue

            if found_path:
                # prefer absolute path when available
                setattr(self, f"{tool_name}_path", found_path)
                # For docker and kubectl, verify the daemon/cluster is responsive
                if tool_name == 'docker':
                    try:
                        # sometimes docker on Windows returns non-zero for permission reasons; still check responsiveness
                        r = subprocess.run([found_path, 'info'], capture_output=True, text=True, timeout=10)
                        if r.returncode == 0:
                            self.docker_available = True
                        else:
                            logger.debug('docker found but daemon returned non-zero: %s', r.stderr)
                    except Exception as e:
                        logger.debug('docker info check failed: %s', e)
                elif tool_name == 'kubectl':
                    try:
                        r = subprocess.run([found_path, 'version', '--client'], capture_output=True, text=True, timeout=10)
                        if r.returncode == 0:
                            self.kubectl_available = True
                        else:
                            logger.debug('kubectl found but version check failed: %s', r.stderr)
                    except Exception as e:
                        logger.debug('kubectl version check failed: %s', e)
                else:
                    # mark presence for other tools by setting the *_path
                    pass

        # write a small environment summary for easy inspection by other tools
        try:
            env_report = {
                'os_type': self.os_type,
                'python_path': getattr(self, 'python_path', ''),
                'node_path': getattr(self, 'node_path', ''),
                'git_path': getattr(self, 'git_path', ''),
                'docker_available': self.docker_available,
                'kubectl_available': self.kubectl_available,
                'pwsh_path': getattr(self, 'pwsh_path', ''),
                'workspace_root': self.workspace_root,
            }

            # Primary location: workspace config folder
            cfg_dir = Path(self.workspace_root) / 'config'
            try:
                cfg_dir.mkdir(parents=True, exist_ok=True)
                env_file = cfg_dir / 'environment.json'
                with env_file.open('w', encoding='utf8') as f:
                    json.dump(env_report, f, indent=2)
                logger.info('Wrote environment report to %s', str(env_file))
            except Exception as e:
                # Fallback: write to user home to avoid losing the report entirely
                try:
                    home_cfg = Path.home() / '.nusyq'
                    home_cfg.mkdir(parents=True, exist_ok=True)
                    env_file = home_cfg / 'environment.json'
                    with env_file.open('w', encoding='utf8') as f:
                        json.dump(env_report, f, indent=2)
                    logger.warning('Could not write to workspace config; wrote environment report to %s', str(env_file))
                except Exception as e2:
                    logger.debug('Failed to write environment report in fallback location: %s', e2)
        except Exception as e:
            logger.debug('Failed to compose/write environment report: %s', e)


class FlexiblePathManager:
    """Manages flexible path resolution across different environments"""

    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = Path(workspace_root)
        self.os_type = platform.system()

    def get_python_executable(self) -> str:
        """Get the appropriate Python executable path"""
        venv_paths = [
            self.workspace_root / ".venv" / "Scripts" / "python.exe",  # Windows
            self.workspace_root / ".venv" / "bin" / "python",  # Unix
            self.workspace_root / "venv" / "Scripts" / "python.exe",  # Windows alt
            self.workspace_root / "venv" / "bin" / "python"  # Unix alt
        ]

        for path in venv_paths:
            if path.exists():
                return str(path)

        # Fallback to system Python
        return "python"

    def get_config_path(self, config_name: str) -> Path:
        """Get flexible configuration file path"""
        config_dirs = [
            self.workspace_root / "config",
            self.workspace_root / ".config",
            self.workspace_root
        ]

        for config_dir in config_dirs:
            config_path = config_dir / config_name
            if config_path.exists():
                return config_path

        # Return default location for creation
        return self.workspace_root / "config" / config_name

    def get_data_directory(self, subdir: str = "") -> Path:
        """Get platform-appropriate data directory"""
        if self.os_type == "Windows":
            base_dir = Path(os.environ.get("APPDATA", str(self.workspace_root)))
        elif self.os_type == "Darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux
            xdg_data = os.environ.get("XDG_DATA_HOME")
            base_dir = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"

        data_dir = base_dir / "NuSyQ" / subdir if subdir else base_dir / "NuSyQ"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def resolve_template_path(self, template: str, **kwargs: str) -> str:
        """Resolve path templates with environment variables"""
        # Replace common template variables
        replacements = {
            "${workspaceFolder}": str(self.workspace_root),
            "${workspace}": str(self.workspace_root),
            "${userHome}": str(Path.home()),
            "${platform}": self.os_type.lower(),
            **kwargs
        }

        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result


class GitHubAuthManager:
    """Manages GitHub authentication for KiloMusician"""

    def __init__(self) -> None:
        self.username = "KiloMusician"
        self.config = GitHubConfig(username=self.username)

    def check_authentication(self) -> bool:
        """Check if GitHub CLI is authenticated"""
        try:
            # Increased from 10s to 30s - network latency + token verification
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )
            if result.returncode == 0 and "Logged in" in result.stderr:
                self.config.authenticated = True
                logger.info("GitHub authentication verified")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("GitHub CLI not available: %s", e)

        self.config.authenticated = False
        return False

    def setup_authentication(self) -> bool:
        """Set up GitHub authentication"""
        if self.check_authentication():
            return True

        try:
            logger.info("Starting GitHub authentication setup...")
            # Increased from 300s to 600s - interactive auth can take time
            subprocess.run(['gh', 'auth', 'login'], check=True, timeout=600)
            return self.check_authentication()
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error("Failed to set up GitHub authentication: %s", e)
            return False
        except subprocess.TimeoutExpired:
            logger.error("GitHub authentication setup timed out")
            return False

    def get_repositories(self) -> List[str]:
        """Get list of user repositories"""
        if not self.config.authenticated:
            return []

        try:
            # Increased from 30s to 60s - large orgs with many repos can be slow
            result = subprocess.run(
                ['gh', 'repo', 'list', self.username, '--json', 'name'],
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )
            if result.returncode == 0:
                repos = json.loads(result.stdout)
                self.config.repositories = [repo['name'] for repo in repos]
                return self.config.repositories
        except subprocess.TimeoutExpired:
            logger.warning("Repository fetch timed out")
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.warning("Could not fetch repositories: %s", e)

        return []


class ExtensionManager:
    """Manages VS Code extension installation and activation"""

    def __init__(self, github_user: str = "KiloMusician") -> None:
        self.github_user = github_user
        self.essential_extensions = [
            "ms-python.python",
            "ms-toolsai.jupyter",
            "GitHub.copilot",
            "GitHub.copilot-chat",
            "ms-vscode.vscode-json",
            "redhat.vscode-yaml",
            "ms-vscode.powershell",
            "continue.continue",
            "anthropic.claude-dev",
            "ms-kubernetes-tools.vscode-kubernetes-tools",
            "ms-vscode-remote.remote-containers",
            "GitKraken.gitlens",
            "ms-vscode.remote-repositories"
        ]

    def install_extensions(self) -> Dict[str, bool]:
        """Install essential extensions"""
        results: Dict[str, bool] = {}

        for extension in self.essential_extensions:
            try:
                # Increased from 60s to 180s - extension download/install varies
                result = subprocess.run(
                    ['code', '--install-extension', extension, '--force'],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False
                )
                results[extension] = result.returncode == 0

                if results[extension]:
                    logger.info("Installed %s", extension)
                else:
                    logger.warning("Failed to install %s", extension)

            except subprocess.TimeoutExpired:
                logger.error("Installation timed out for %s", extension)
                results[extension] = False
            except FileNotFoundError:
                logger.error("VS Code CLI not found, cannot install %s", extension)
                results[extension] = False

        return results

    def configure_github_extensions(self) -> bool:
        """Configure GitHub-related extensions"""
        try:
            # Configure GitHub Copilot settings
            settings_path = Path.cwd() / ".vscode" / "settings.json"

            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}

            # GitHub Copilot configuration
            settings.update({
                "github.copilot.enable": {"*": True},
                "github.username": self.github_user,
                "git.defaultRemote": "origin",
                "git.rememberCredentials": True,
                "github.copilot.advanced": {
                    "inlineSuggestEnable": True
                }
            })

            # Ensure .vscode directory exists
            settings_path.parent.mkdir(exist_ok=True)

            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)

            logger.info("GitHub extension configuration updated")
            return True

        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to configure GitHub extensions: %s", e)
            return False


class FlexibilityManager:
    """Main manager for NuSyQ flexibility enhancements"""

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        if workspace_root is None:
            workspace_root = str(Path(__file__).parent.parent.absolute())

        self.workspace_root = workspace_root
        self.path_manager = FlexiblePathManager(workspace_root)
        self.github_manager = GitHubAuthManager()
        self.extension_manager = ExtensionManager()
        self.env_config = EnvironmentConfig()

    def run_full_setup(self) -> Dict[str, Any]:
        """Run complete flexibility setup"""
        results: Dict[str, Any] = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "workspace_root": self.workspace_root,
            "github_auth": False,
            "extensions_installed": {},
            "environment": asdict(self.env_config),
            "errors": []
        }

        try:
            # 1. Set up GitHub authentication
            logger.info("Setting up GitHub authentication...")
            results["github_auth"] = self.github_manager.setup_authentication()

            # 2. Install extensions
            logger.info("Installing VS Code extensions...")
            results["extensions_installed"] = self.extension_manager.install_extensions()

            # 3. Configure GitHub extensions
            logger.info("Configuring GitHub extensions...")
            self.extension_manager.configure_github_extensions()

            # 4. Create environment configuration
            self._create_environment_config()

            # 5. Update configuration files with flexible paths
            self._update_configurations()

            logger.info("Flexibility setup complete!")

        except (OSError, subprocess.SubprocessError) as e:
            logger.error("Setup failed: %s", e)
            results["errors"].append(str(e))

        return results

    def _create_environment_config(self) -> None:
        """Create flexible environment configuration"""
        config_path = self.path_manager.get_config_path("environment.json")

        env_data = {
            "github": asdict(self.github_manager.config),
            "environment": asdict(self.env_config),
            "paths": {
                "workspace_root": self.workspace_root,
                "python_executable": self.path_manager.get_python_executable(),
                "data_directory": str(self.path_manager.get_data_directory()),
                "config_directory": str(self.path_manager.get_config_path("").parent)
            }
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(env_data, f, indent=4)

        logger.info("Environment configuration saved to %s", config_path)

    def _update_configurations(self) -> None:
        """Update existing configurations with flexible paths"""
        try:
            # Update orchestrator script with flexible paths
            orchestrator_path = Path(self.workspace_root) / "NuSyQ.Orchestrator.ps1"
            if orchestrator_path.exists():
                content = orchestrator_path.read_text(encoding='utf-8')

                # Replace hardcoded paths with flexible ones
                flexible_content = content.replace(
                    "C:/Users/keath/NuSyQ/.venv/Scripts/python.exe",
                    self.path_manager.get_python_executable()
                )

                orchestrator_path.write_text(flexible_content, encoding='utf-8')
                logger.info("Updated orchestrator script with flexible paths")

        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Could not update orchestrator script: %s", e)


def main() -> None:
    """Main entry point for flexibility setup"""
    print("NuSyQ Flexibility Enhancement")
    print("=================================")

    manager = FlexibilityManager()
    results = manager.run_full_setup()

    print("\nSetup Results:")
    print(f"GitHub Auth: {'Success' if results['github_auth'] else 'Failed'}")

    successful_extensions = sum(
        1 for installed in results['extensions_installed'].values() if installed
    )
    total_extensions = len(results['extensions_installed'])
    print(f"Extensions: {successful_extensions}/{total_extensions} installed")

    if results['errors']:
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"   - {error}")

    print("\nSetup complete! Restart VS Code to apply all changes.")


if __name__ == "__main__":
    main()
