#!/usr/bin/env python3
"""Publish Project - CLI tool for publishing projects to registries

Usage:
    publish-project publish <project_id> <version> --registries pypi npm
    publish-project status <project_id>
    publish-project history <project_id> [--limit 10]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.publishing.orchestrator import (
    PublishConfig,
    PublishingOrchestrator,
    PublishTarget,
    RegistryType,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def format_result(data: dict, indent: int = 2) -> str:
    """Format result as pretty JSON."""
    return json.dumps(data, indent=indent, default=str)


def publish_command(args) -> int:
    """Execute publish command."""
    try:
        logger.info(f"Publishing {args.project_id} v{args.version}")

        orchestrator = PublishingOrchestrator()

        # Determine PublishTarget from registries
        registries = args.registries.split(",") if args.registries else ["pypi"]
        registries = [r.strip().lower() for r in registries]

        if len(registries) == 1:
            if registries[0] == "pypi":
                publish_target = PublishTarget.PYPI_ONLY
            elif registries[0] == "npm":
                publish_target = PublishTarget.NPM_ONLY
            elif registries[0] == "vscode":
                publish_target = PublishTarget.VSCODE_ONLY
            elif registries[0] == "docker":
                publish_target = PublishTarget.DOCKER_ONLY
            else:
                publish_target = PublishTarget.PYPI_ONLY
        else:
            publish_target = PublishTarget.MULTI

        # Create config
        config = PublishConfig(
            project_id=args.project_id,
            project_name=args.project_name or args.project_id,
            version=args.version,
            description=args.description or "",
            author=args.author or "Unknown",
            author_email=args.author_email or "",
            license_type=args.license or "MIT",
            targets=[RegistryType(r) for r in registries],
            publish_target=publish_target,
            repository_url=args.repository_url,
            documentation_url=args.documentation_url,
        )

        # Execute
        project_path = Path(args.project_path) if args.project_path else Path(".")
        result = orchestrator.publish(config, project_path=project_path)

        # Display result
        print("\n✅ Publishing Complete")
        print(f"Status: {result.status}")
        print(f"Project: {config.project_name} v{config.version}")
        print(f"Registries: {', '.join(registries)}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        if result.status == "success":
            print("\n📦 Per-Registry Results:")

            if hasattr(result, "pypi_result") and result.pypi_result:
                print(f"  PyPI: {result.pypi_result.get('status', 'unknown')}")
                if result.pypi_result.get("url"):
                    print(f"    → {result.pypi_result['url']}")

            if hasattr(result, "npm_result") and result.npm_result:
                print(f"  NPM: {result.npm_result.get('status', 'unknown')}")
                if result.npm_result.get("url"):
                    print(f"    → {result.npm_result['url']}")

            if hasattr(result, "vscode_result") and result.vscode_result:
                print(f"  VSCode: {result.vscode_result.get('status', 'unknown')}")
                if result.vscode_result.get("url"):
                    print(f"    → {result.vscode_result['url']}")

            if hasattr(result, "docker_result") and result.docker_result:
                print(f"  Docker: {result.docker_result.get('status', 'unknown')}")
                if result.docker_result.get("url"):
                    print(f"    → {result.docker_result['url']}")

            return 0
        else:
            print("\n❌ Publishing failed")
            if hasattr(result, "error") and result.error:
                print(f"Error: {result.error}")
            return 1

    except Exception as e:
        logger.error(f"Publishing failed: {e!s}")
        print(f"\n❌ Error: {e!s}")
        return 1


def status_command(args) -> int:
    """Execute status command."""
    try:
        logger.info(f"Checking status for {args.project_id}")

        orchestrator = PublishingOrchestrator()
        status = orchestrator.get_publish_status(args.project_id)

        print("\n📊 Publish Status")
        print(f"Project ID: {args.project_id}")
        print(f"Project Name: {status.get('project_name', 'Unknown')}")
        print(f"Latest Version: {status.get('latest_version', 'N/A')}")
        print(f"Latest Status: {status.get('latest_status', 'unknown')}")

        if status.get("last_publish_time"):
            print(f"Last Published: {status['last_publish_time']}")

        if status.get("registry_status"):
            print("\nRegistry Status:")
            for registry, reg_status in status["registry_status"].items():
                print(f"  {registry}: {reg_status}")

        return 0

    except Exception as e:
        logger.error(f"Status check failed: {e!s}")
        print(f"\n❌ Error: {e!s}")
        return 1


def history_command(args) -> int:
    """Execute history command."""
    try:
        logger.info(f"Retrieving history for {args.project_id}")

        orchestrator = PublishingOrchestrator()
        history = orchestrator.get_publish_history(args.project_id, limit=args.limit)

        if not history:
            print(f"\n📋 No publish history found for {args.project_id}")
            return 0

        print(f"\n📋 Publish History ({len(history)} entries)")
        print("-" * 70)

        for i, entry in enumerate(history, 1):
            timestamp = entry.get("timestamp", "Unknown")
            status = entry.get("status", "unknown")
            version = entry.get("version", "N/A")
            registries = entry.get("registries", [])

            status_icon = "✅" if status == "success" else "❌"

            print(f"\n{i}. {status_icon} {timestamp}")
            print(f"   Version: {version}")
            print(f"   Registries: {', '.join(registries)}")

            if entry.get("error"):
                print(f"   Error: {entry['error']}")

        return 0

    except Exception as e:
        logger.error(f"History retrieval failed: {e!s}")
        print(f"\n❌ Error: {e!s}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="📦 Publish projects to registries (PyPI, NPM, VSCode, Docker, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish to PyPI
  python publish_project.py publish my-project 0.1.0 --registries pypi

  # Publish to multiple registries
  python publish_project.py publish my-project 0.1.0 --registries pypi,npm,docker

  # Check publish status
  python publish_project.py status my-project

  # View publish history
  python publish_project.py history my-project --limit 20

  # Publish with full metadata
  python publish_project.py publish my-project 0.2.0 \\
    --author "John Doe" \\
    --description "My awesome project" \\
    --registries pypi,npm \\
    --license MIT
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Publish command
    publish_parser = subparsers.add_parser("publish", help="Publish project to registries")
    publish_parser.add_argument("project_id", help="Project identifier")
    publish_parser.add_argument("version", help="Semantic version (e.g., 0.1.0)")
    publish_parser.add_argument("--project-name", dest="project_name", default=None, help="Human-readable project name")
    publish_parser.add_argument(
        "--registries",
        default="pypi",
        help="Registries to publish to (comma-separated: pypi,npm,vscode,docker)",
    )
    publish_parser.add_argument("--author", default="Unknown", help="Author name")
    publish_parser.add_argument("--author-email", dest="author_email", default="", help="Author email")
    publish_parser.add_argument("--description", default="", help="Project description")
    publish_parser.add_argument("--license", default="MIT", help="License type (MIT, Apache-2.0, GPL-3.0, etc.)")
    publish_parser.add_argument("--repository-url", dest="repository_url", default=None, help="Git repository URL")
    publish_parser.add_argument(
        "--documentation-url",
        dest="documentation_url",
        default=None,
        help="Documentation website URL",
    )
    publish_parser.add_argument("--project-path", dest="project_path", default=".", help="Path to project directory")
    publish_parser.set_defaults(func=publish_command)

    # Status command
    status_parser = subparsers.add_parser("status", help="Check publish status for a project")
    status_parser.add_argument("project_id", help="Project identifier")
    status_parser.set_defaults(func=status_command)

    # History command
    history_parser = subparsers.add_parser("history", help="View publish history for a project")
    history_parser.add_argument("project_id", help="Project identifier")
    history_parser.add_argument("--limit", type=int, default=10, help="Maximum number of history entries to show")
    history_parser.set_defaults(func=history_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
