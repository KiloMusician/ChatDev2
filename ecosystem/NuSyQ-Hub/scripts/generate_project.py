#!/usr/bin/env python3
"""generate_project.py - CLI tool for Universal Project Generator

Usage:
    python generate_project.py [template] [name] [options]

Examples:
    python generate_project.py game_godot_3d my_game
    python generate_project.py webapp_nextjs my_app --with-auth
    python generate_project.py package_python my_package --author "John Doe"
"""

import argparse
import json
import sys
from pathlib import Path

from src.generators.template_definitions import ProjectType, get_template
from src.generators.universal_project_generator import UniversalProjectGenerator


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_template_list(upg: UniversalProjectGenerator, project_type: str | None = None) -> None:
    """Print list of available templates."""
    templates = upg.list_templates()
    if project_type:
        try:
            ptype = ProjectType[project_type.upper()]
            templates = [t for t in templates if t.type == ptype]
        except KeyError:
            print(f"❌ Unknown project type: {project_type}")
            return

    print_header(f"Available Templates ({len(templates)})")

    # Group by type
    by_type: dict[str, list] = {}
    for t in templates:
        if t.type.value not in by_type:
            by_type[t.type.value] = []
        by_type[t.type.value].append(t)

    for ptype in sorted(by_type.keys()):
        print(f"\n  {ptype.upper()}")
        print(f"  {'-' * 60}")
        for t in by_type[ptype]:
            ai_provider = t.primary_ai_provider.value
            complexity = "🔥" * min(3, (t.complexity // 3) + 1)
            print(f"    📋 {t.template_id:<30} Complexity: {t.complexity}/10 {complexity}")
            print(f"       {t.description}")
            print(f"       Language: {t.language.value} | AI: {ai_provider}")
            print()


def cmd_list(args: argparse.Namespace) -> None:
    """List available templates."""
    upg = UniversalProjectGenerator()
    print_template_list(upg, args.type)


def cmd_info(args: argparse.Namespace) -> None:
    """Show detailed template information."""
    template_id = args.template
    template = get_template(template_id)

    if not template:
        print(f"❌ Template not found: {template_id}")
        return

    print_header(f"Template: {template.name}")

    print(f"  ID:                 {template.template_id}")
    print(f"  Name:               {template.name}")
    print(f"  Type:               {template.type.value.upper()}")
    print(f"  Language:           {template.language.value}")
    print(f"  Description:        {template.description}")
    print()

    print(f"  Complexity:         {template.complexity}/10")
    print(f"  Est. Generation:    {template.estimated_generation_time}")
    print(f"  AI Provider:        {template.primary_ai_provider.value}")
    print(f"  AI Enhancement:     {'✅ Yes' if template.ai_enhancement_available else '❌ No'}")
    print()

    if template.starter_files:
        print(f"  Starter Files:      {len(template.starter_files)}")
        for fname in template.starter_files:
            print(f"    - {fname}")
        print()

    if template.tags:
        print(f"  Tags:               {', '.join(template.tags)}")

    if template.prerequisites:
        print(f"  Prerequisites:      {', '.join(template.prerequisites)}")
        print()


def cmd_generate(args: argparse.Namespace) -> int:
    """Generate a new project."""
    template_id = args.template
    project_name = args.name

    # Verify template exists
    template = get_template(template_id)
    if not template:
        print(f"❌ Template not found: {template_id}")
        print("\nUse 'python generate_project.py list' to see available templates")
        return 1

    print_header(f"Generating Project: {project_name}")
    print(f"  Template:   {template.name}")
    print(f"  Language:   {template.language.value}")
    print(f"  Type:       {template.type.value}")
    print()

    # Initialize generator
    upg = UniversalProjectGenerator()

    # Parse options
    options = {}
    if args.options:
        try:
            options = json.loads(args.options)
        except json.JSONDecodeError:
            print(f"❌ Invalid options JSON: {args.options}")
            return 1

    # Generate project
    print("⏳ Generating project...")
    result = upg.generate(template_id, project_name, options=options)

    if result.status != "success":
        print(f"\n❌ Generation failed: {result.error_message}")
        return 1

    # Success
    print("\n✅ Project generated successfully!")
    print()
    print(f"  Project ID:     {result.project_id}")
    print(f"  Name:           {result.project_name}")
    print(f"  Location:       {result.output_path}")
    print(f"  AI Provider:    {result.ai_provider}")
    print(f"  Time:           {result.generation_time:.2f}s")
    print()

    # Next steps
    project_path = Path(result.output_path)
    print("📋 Next Steps:")
    print(f"  1. cd {project_path.name}")
    print("  2. Review the generated project structure")

    if template.prerequisites:
        print(f"  3. Install prerequisites: {', '.join(template.prerequisites)}")
        if "python" in template.language.value.lower():
            print("     pip install -r requirements.txt")
        elif "node" in template.language.value.lower() or "javascript" in template.language.value.lower():
            print("     npm install")

    print()
    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Project Generator - Create projects from templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_project.py list
  python generate_project.py list game
  python generate_project.py info game_godot_3d
  python generate_project.py generate game_godot_3d my_awesome_game
  python generate_project.py generate webapp_nextjs my_app --options '{"with_auth": true}'
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List available templates")
    list_parser.add_argument(
        "type",
        nargs="?",
        choices=["game", "webapp", "package", "extension", "cli", "library"],
        help="Filter by project type",
    )
    list_parser.set_defaults(func=cmd_list)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show template details")
    info_parser.add_argument("template", help="Template ID")
    info_parser.set_defaults(func=cmd_info)

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a new project")
    gen_parser.add_argument("template", help="Template ID to use")
    gen_parser.add_argument("name", help="Project name")
    gen_parser.add_argument("--options", help="JSON string of options (e.g., '{\"with_auth\": true}')")
    gen_parser.set_defaults(func=cmd_generate)

    # Parse args
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    # Execute command
    try:
        if hasattr(args, "func"):
            if args.command == "generate":
                return args.func(args)
            else:
                args.func(args)
                return 0
    except (ValueError, KeyError, OSError) as e:
        print(f"\n❌ Error: {e!s}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
