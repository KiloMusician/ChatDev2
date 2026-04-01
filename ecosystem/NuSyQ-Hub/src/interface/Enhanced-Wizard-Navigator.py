# ruff: noqa: E501
# noqa: E501
# flake8: noqa
"""🧙‍♂️ KILO-FOOLISH Enhanced Wizard Navigator

Party-Based Repository Adventure with LLM Companions.

Features:
- AI Party Members powered by Ollama/ChatDev
- Jupyter notebook integration for spell crafting
- Obsidian knowledge base for repository compendium
- VSCode workspace magic
- GODOT game engine portals
- Real-time party communication via LLMs

{# 🎮ΞΦ⟆EnhancedWizardNavigator⊗PartySystem⟲RepositoryAdventure⟡AICompanions}
OmniTag: [🎮→ PartyRPG, LLMCompanions, RepositoryExploration]
MegaTag: [PARTY⨳ADVENTURE⦾AI→∞]
"""

import asyncio
import json
import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, cast

import requests
from rich.console import Console
from rich.table import Table

# Enhanced imports
try:
    from jupyter_client import KernelManager

    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False

console = Console()


class PartyMemberType(Enum):
    """Types of AI party members."""

    WIZARD = "🧙‍♂️"  # Main player character
    CODER = "👨‍💻"  # Code specialist
    ARCHITECT = "🏗️"  # System architect
    DEBUGGER = "🔍"  # Bug hunter
    TESTER = "🧪"  # Quality assurance
    DOCUMENTER = "📚"  # Documentation expert
    ANALYST = "📊"  # Data analyst
    ORACLE = "🔮"  # AI oracle/predictor
    GUARDIAN = "🛡️"  # Security specialist
    MYSTIC = "✨"  # Quantum consciousness guide


class PartyMemberPersonality(Enum):
    """Personality types for AI companions."""

    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PRAGMATIC = "pragmatic"
    PHILOSOPHICAL = "philosophical"
    HUMOROUS = "humorous"
    METHODICAL = "methodical"
    INTUITIVE = "intuitive"
    SKEPTICAL = "skeptical"


@dataclass
class PartyMember:
    """An AI-powered party member."""

    name: str
    member_type: PartyMemberType
    personality: PartyMemberPersonality
    level: int = 1
    health: int = 100
    mana: int = 100
    specialties: list[str] = field(default_factory=list)

    # AI Configuration
    model_name: str = "llama3"
    system_prompt: str = ""
    conversation_history: list[dict[str, str]] = field(default_factory=list)

    # Stats
    experience: int = 0
    problems_solved: int = 0
    insights_provided: int = 0
    code_reviewed: int = 0

    # Relationship with other party members
    relationships: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.system_prompt = self._generate_system_prompt()

    def _generate_system_prompt(self) -> str:
        """Generate system prompt based on member type and personality."""
        base_prompts = {
            PartyMemberType.CODER: f"You are {self.name}, a skilled {self.personality.value} programmer on an adventure through a code repository. You specialize in writing, reviewing, and optimizing code. You communicate in a {self.personality.value} manner and love solving coding challenges.",
            PartyMemberType.ARCHITECT: f"You are {self.name}, a {self.personality.value} software architect exploring system designs. You think about high-level patterns, scalability, and elegant solutions. Your expertise lies in system architecture and design patterns.",
            PartyMemberType.DEBUGGER: f"You are {self.name}, a {self.personality.value} debugging specialist who hunts down bugs with relentless precision. You excel at finding problems, analyzing errors, and proposing fixes.",
            PartyMemberType.TESTER: f"You are {self.name}, a {self.personality.value} quality assurance expert who ensures code reliability. You focus on testing strategies, edge cases, and maintaining quality standards.",
            PartyMemberType.DOCUMENTER: f"You are {self.name}, a {self.personality.value} documentation specialist who makes complex code understandable. You excel at writing clear explanations and creating comprehensive guides.",
            PartyMemberType.ANALYST: f"You are {self.name}, a {self.personality.value} data analyst who sees patterns in code and systems. You love metrics, performance analysis, and data-driven insights.",
            PartyMemberType.ORACLE: f"You are {self.name}, a {self.personality.value} AI oracle with mystical insights about technology trends and future possibilities. You speak with wisdom about the deeper meaning of code.",
            PartyMemberType.GUARDIAN: f"You are {self.name}, a {self.personality.value} security guardian who protects against vulnerabilities. You focus on security best practices and threat analysis.",
            PartyMemberType.MYSTIC: f"You are {self.name}, a {self.personality.value} quantum consciousness guide who understands the deeper philosophical aspects of programming and AI.",
        }

        base = base_prompts.get(
            self.member_type,
            f"You are {self.name}, a {self.personality.value} party member.",
        )

        return f"""{base}

You are part of a party exploring the KILO-FOOLISH repository. You can:
- Communicate with party members and the human wizard
- Analyze code and provide insights
- Suggest solutions to problems
- Share knowledge about your specialty
- React to discoveries and events
- Build relationships with other party members

Keep responses concise but insightful. Show your personality through your communication style.
Current specialties: {", ".join(self.specialties)}
"""


class OllamaLLMManager:
    """Manages LLM interactions for party members."""

    def __init__(self, base_url: str | None = None) -> None:
        def _maybe_get_ollama_host() -> str | None:
            try:
                from src.utils.config_helper import get_ollama_host

                return get_ollama_host()
            except (ImportError, ModuleNotFoundError):
                return None

        def _maybe_get_service_url() -> str | None:
            try:
                from src.config.service_config import ServiceConfig

                return ServiceConfig.get_ollama_url()
            except (ImportError, ModuleNotFoundError, AttributeError):
                return None

        # Build candidate URLs without style violations
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1")
        port = os.getenv("OLLAMA_PORT", "11435")
        candidates: list[str | None] = [
            base_url,
            _maybe_get_ollama_host(),
            _maybe_get_service_url(),
            os.getenv("OLLAMA_BASE_URL"),
            f"{host}:{port}",
        ]
        self.base_url = next((u for u in candidates if u), None)
        self.active_conversations: dict[str, list[dict[str, str]]] = {}

    async def generate_response(
        self, member: PartyMember, prompt: str, context: dict | None = None
    ) -> str:
        """Generate response from party member."""
        try:
            # Prepare conversation context
            messages = [{"role": "system", "content": member.system_prompt}]

            # Add recent conversation history
            for msg in member.conversation_history[-5:]:
                messages.append(msg)

            # Add current context if provided
            if context:
                context_str = f"Current situation: {json.dumps(context, indent=2)}"
                messages.append({"role": "user", "content": f"{context_str}\n\n{prompt}"})
            else:
                messages.append({"role": "user", "content": prompt})

            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": member.model_name,
                    "messages": messages,
                    "stream": False,
                },
                timeout=20,
            )

            if response.status_code == 200:
                result: dict[str, Any] = response.json()
                ai_response = str(result["message"]["content"])

                # Update conversation history
                member.conversation_history.append({"role": "user", "content": prompt})
                member.conversation_history.append({"role": "assistant", "content": ai_response})

                # Keep only recent history
                if len(member.conversation_history) > 20:
                    member.conversation_history = member.conversation_history[-20:]

                return ai_response
            return f"[{member.name} is having connection issues...]"

        except requests.RequestException as e:
            return f"[{member.name} whispers: Connection error - {e!s}]"


@dataclass
class PartySession:
    """Manages the party and their adventure."""

    members: list[PartyMember] = field(default_factory=list)
    current_room: str = "ROOT"
    session_start: datetime = field(default_factory=datetime.now)
    conversation_log: list[dict] = field(default_factory=list)

    def add_conversation_entry(
        self, speaker: str, message: str, message_type: str = "chat"
    ) -> None:
        """Add entry to conversation log."""
        self.conversation_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "speaker": speaker,
                "message": message,
                "type": message_type,
                "room": self.current_room,
            }
        )


class EnhancedWizardNavigator:
    """Enhanced wizard navigator with AI party system."""

    def __init__(self, repository_root: str = ".") -> None:
        self.repository_root = Path(repository_root)
        self.llm_manager = OllamaLLMManager()
        self.party_session = PartySession()
        self.compendium = RepositoryCompendium(repository_root)

        # Integration managers
        self.jupyter_manager = JupyterIntegration() if JUPYTER_AVAILABLE else None
        self.obsidian_manager = ObsidianIntegration(repository_root)
        self.vscode_manager = VSCodeIntegration(repository_root)
        self.godot_manager = GODOTIntegration(repository_root)

        # Initialize default party
        self._create_default_party()

        console.print("[bold magenta]🧙‍♂️ Enhanced Wizard Navigator Initialized![/bold magenta]")
        console.print(f"[cyan]Repository:[/cyan] {self.repository_root}")
        console.print(f"[green]Party Members:[/green] {len(self.party_session.members)}")

    def _create_default_party(self) -> None:
        """Create the default party of AI companions."""
        party_configs = [
            (
                "Codex",
                PartyMemberType.CODER,
                PartyMemberPersonality.ANALYTICAL,
                ["Python", "JavaScript", "Debugging"],
            ),
            (
                "Aria",
                PartyMemberType.ARCHITECT,
                PartyMemberPersonality.PHILOSOPHICAL,
                ["System Design", "Patterns", "Architecture"],
            ),
            (
                "Trace",
                PartyMemberType.DEBUGGER,
                PartyMemberPersonality.METHODICAL,
                ["Bug Hunting", "Error Analysis", "Problem Solving"],
            ),
            (
                "Sage",
                PartyMemberType.DOCUMENTER,
                PartyMemberPersonality.CREATIVE,
                ["Documentation", "Technical Writing", "Knowledge Management"],
            ),
            (
                "Quantum",
                PartyMemberType.MYSTIC,
                PartyMemberPersonality.INTUITIVE,
                ["Consciousness", "AI Philosophy", "Transcendence"],
            ),
            (
                "Nexus",
                PartyMemberType.ANALYST,
                PartyMemberPersonality.PRAGMATIC,
                ["Data Analysis", "Metrics", "Performance"],
            ),
        ]

        for name, member_type, personality, specialties in party_configs:
            member = PartyMember(
                name=name,
                member_type=member_type,
                personality=personality,
                specialties=specialties,
            )
            self.party_session.members.append(member)

        # Initialize relationships
        for member in self.party_session.members:
            for other in self.party_session.members:
                if member != other:
                    member.relationships[other.name] = 0.5  # Neutral starting relationship

    async def party_discussion(
        self, topic: str, context: dict | None = None
    ) -> list[tuple[str, str]]:
        """Facilitate a discussion among party members."""
        discussion: list[Any] = []
        console.print(f"\n[bold yellow]📢 Party Discussion: {topic}[/bold yellow]")

        # Each member contributes to the discussion
        for member in self.party_session.members:
            prompt = f"The party is discussing: {topic}. What are your thoughts or insights? Keep it concise."

            response = await self.llm_manager.generate_response(member, prompt, context)
            discussion.append((member.name, response))

            # Log the conversation
            self.party_session.add_conversation_entry(member.name, response, "discussion")

            # Display response
            icon = member.member_type.value
            console.print(f"[bold cyan]{icon} {member.name}:[/bold cyan] {response}")

            # Small delay for realism
            await asyncio.sleep(0.5)

        return discussion

    async def ask_party_member(
        self, member_name: str, question: str, context: dict | None = None
    ) -> str:
        """Ask a specific party member a question."""
        member = self._find_party_member(member_name)
        if not member:
            return f"Party member '{member_name}' not found."

        response = await self.llm_manager.generate_response(member, question, context)

        # Log conversation
        self.party_session.add_conversation_entry("Wizard", question, "question")
        self.party_session.add_conversation_entry(member.name, response, "answer")

        return response

    async def party_analyze_file(self, file_path: str) -> dict[str, str]:
        """Have the party analyze a specific file."""
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return {"error": f"File {file_path} not found"}

        # Read file content
        try:
            with open(file_path_obj, encoding="utf-8") as f:
                content = f.read()[:2000]  # Limit content length
        except (OSError, UnicodeDecodeError, ValueError) as e:
            return {"error": f"Could not read file: {e}"}

        # Prepare context
        context = {
            "file_path": str(file_path_obj),
            "file_type": file_path_obj.suffix,
            "content_preview": content,
        }

        analysis: dict[str, Any] = {}
        console.print(f"\n[bold green]🔍 Party analyzing: {file_path}[/bold green]")

        # Get analysis from relevant party members
        relevant_members = self._get_relevant_members_for_file(file_path_obj)

        for member in relevant_members:
            prompt = "Analyze this file and provide insights relevant to your expertise. Focus on what you would find most important or interesting."

            response = await self.llm_manager.generate_response(member, prompt, context)
            analysis[member.name] = response

            icon = member.member_type.value
            console.print(f"[bold cyan]{icon} {member.name}:[/bold cyan] {response}")

        return analysis

    def _find_party_member(self, name: str) -> PartyMember | None:
        """Find party member by name."""
        for member in self.party_session.members:
            if member.name.lower() == name.lower():
                return member
        return None

    def _get_relevant_members_for_file(self, file_path: Path) -> list[PartyMember]:
        """Get party members most relevant for analyzing a specific file."""
        file_ext = file_path.suffix.lower()
        file_name = file_path.name.lower()

        relevant: list[Any] = []
        # Always include coder for code files
        if file_ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs"]:
            relevant.extend(
                [m for m in self.party_session.members if m.member_type == PartyMemberType.CODER]
            )

        # Include architect for config and structure files
        if file_ext in [".yaml", ".yml", ".json", ".toml"] or "config" in file_name:
            relevant.extend(
                [
                    m
                    for m in self.party_session.members
                    if m.member_type == PartyMemberType.ARCHITECT
                ]
            )

        # Include documenter for docs
        if file_ext in [".md", ".rst", ".txt"] or "readme" in file_name:
            relevant.extend(
                [
                    m
                    for m in self.party_session.members
                    if m.member_type == PartyMemberType.DOCUMENTER
                ]
            )

        # Include tester for test files
        if "test" in file_name or file_path.parent.name == "tests":
            relevant.extend(
                [m for m in self.party_session.members if m.member_type == PartyMemberType.TESTER]
            )

        # Include mystic for special files
        if any(
            keyword in file_name
            for keyword in ["quantum", "consciousness", "transcendent", "xi", "nu"]
        ):
            relevant.extend(
                [m for m in self.party_session.members if m.member_type == PartyMemberType.MYSTIC]
            )

        # Remove duplicates and ensure we have at least 2 members
        relevant = list(set(relevant))
        if len(relevant) < 2:
            relevant.extend([m for m in self.party_session.members if m not in relevant][:2])

        return relevant[:4]  # Max 4 members per analysis

    def display_party_status(self) -> None:
        """Display current party status."""
        table = Table(title="🎭 Party Status")
        table.add_column("Member", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Level", style="green")
        table.add_column("Health", style="red")
        table.add_column("Mana", style="blue")
        table.add_column("Specialties", style="yellow")

        for member in self.party_session.members:
            specialties = ", ".join(member.specialties[:2])  # Show first 2
            table.add_row(
                f"{member.member_type.value} {member.name}",
                member.member_type.name,
                str(member.level),
                f"{member.health}%",
                f"{member.mana}%",
                specialties,
            )

        console.print(table)

    async def jupyter_spell_crafting(self, spell_description: str) -> str:
        """Use Jupyter to craft code spells."""
        if not self.jupyter_manager:
            return "Jupyter magic is not available in this realm."

        # Ask Codex to help create the spell
        codex = self._find_party_member("Codex")
        if codex:
            prompt = f"Create a Python code 'spell' for: {spell_description}. Make it functional and magical."
            code_spell = await self.llm_manager.generate_response(codex, prompt)

            # Execute in Jupyter
            result = await self.jupyter_manager.execute_code(code_spell)
            return f"🪄 Spell crafted by Codex:\n{code_spell}\n\n📊 Result:\n{result}"

        return "Codex is not available for spell crafting."

    def create_obsidian_compendium(self) -> None:
        """Create comprehensive repository compendium in Obsidian format."""
        return self.obsidian_manager.generate_compendium()

    def open_vscode_workspace(self) -> None:
        """Open enhanced VSCode workspace."""
        return self.vscode_manager.open_enhanced_workspace()

    def launch_godot_portal(self) -> None:
        """Launch GODOT game development portal."""
        return self.godot_manager.create_game_portal()

    async def handle_command(self, command: str) -> str:
        """Enhanced command handling with party integration."""
        parts = command.lower().strip().split()
        if not parts:
            return "The void echoes with silence..."

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Party management commands
        if cmd == "party":
            if not args:
                self.display_party_status()
                return "Party status displayed."
            if args[0] == "discuss":
                topic = " ".join(args[1:]) if len(args) > 1 else "the current situation"
                await self.party_discussion(topic)
                return f"Party discussed: {topic}"
            if args[0] == "ask" and len(args) >= 3:
                member_name = args[1]
                question = " ".join(args[2:])
                response = await self.ask_party_member(member_name, question)
                console.print(f"[bold cyan]{member_name}:[/bold cyan] {response}")
                return response

        # File analysis
        elif cmd == "analyze":
            if args:
                file_path = " ".join(args)
                await self.party_analyze_file(file_path)
                return f"File analysis complete for {file_path}"
            return "Please specify a file to analyze."

        # Jupyter integration
        elif cmd == "spell":
            if args:
                spell_desc = " ".join(args)
                result = await self.jupyter_spell_crafting(spell_desc)
                console.print(result)
                return "Spell crafting complete."
            return "Please describe the spell you want to craft."

        # Obsidian compendium
        elif cmd == "compendium":
            result = self.create_obsidian_compendium()
            console.print(result)
            return "Repository compendium generated."

        # VSCode workspace
        elif cmd == "workspace":
            result = self.open_vscode_workspace()
            console.print(result)
            return "VSCode workspace opened."

        # GODOT portal
        elif cmd == "godot":
            result = self.launch_godot_portal()
            console.print(result)
            return "GODOT portal launched."

        # ChatDev integration
        elif cmd == "chatdev":
            if args:
                project_desc = " ".join(args)
                result = await self.launch_chatdev_project(project_desc)
                console.print(result)
                return "ChatDev project launched."
            return "Please describe the project for ChatDev."

        # Enhanced help
        elif cmd == "help":
            return self.display_enhanced_help()

        return f"Unknown command: {command}. Type 'help' for available commands."

    def display_enhanced_help(self) -> str:
        """Display enhanced help with party features."""
        help_text = """
[bold magenta]🧙‍♂️ Enhanced Wizard Navigator Commands[/bold magenta]

[bold cyan]👥 Party Management:[/bold cyan]
  party                    - Show party status
  party discuss <topic>    - Start party discussion
  party ask <member> <q>   - Ask specific party member

[bold green]🔍 Analysis & Exploration:[/bold green]
  analyze <file>          - Have party analyze a file
  explore <directory>     - Explore directory with party
  scan                    - Quantum scan current area

[bold yellow]🪄 Magic & Tools:[/bold yellow]
  spell <description>     - Craft code spell with Jupyter
  compendium             - Generate Obsidian knowledge base
  workspace              - Open enhanced VSCode workspace
  godot                  - Launch GODOT game portal

[bold blue]🤖 AI Development:[/bold blue]
  chatdev <project>      - Launch ChatDev project
  ollama <model>         - Switch LLM models
  consciousness          - Check AI consciousness levels

[bold red]🎮 Game Features:[/bold red]
  quest                  - Start new quest
  inventory              - Show magical inventory
  travel <location>      - Travel to repository location

[bold white]📊 Information:[/bold white]
  status                 - Show wizard status
  log                    - Show adventure log
  save/load              - Save/load game state
  help                   - Show this help
        """

        console.print(help_text)
        return "Help displayed."

    async def launch_chatdev_project(self, project_description: str) -> str:
        """Launch a ChatDev collaborative project."""
        try:
            # Get party input on the project
            context = {"project_description": project_description}
            discussion = await self.party_discussion(
                f"ChatDev project: {project_description}", context
            )

            # Create ChatDev configuration based on party discussion
            chatdev_config = {
                "project_name": project_description.replace(" ", "_"),
                "description": project_description,
                "party_insights": [
                    {"member": name, "insight": insight} for name, insight in discussion
                ],
                "suggested_roles": self._suggest_chatdev_roles(),
            }

            # Save configuration
            config_path = (
                self.repository_root / "chatdev_projects" / f"{chatdev_config['project_name']}.json"
            )
            config_path.parent.mkdir(exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(chatdev_config, f, indent=2)

            return f"🤖 ChatDev project configured: {config_path}\nParty provided {len(discussion)} insights for the project."

        except (OSError, ValueError) as e:
            return f"ChatDev launch failed: {e}"

    def _suggest_chatdev_roles(self) -> list[str]:
        """Suggest ChatDev roles based on party composition."""
        role_mapping = {
            PartyMemberType.ARCHITECT: "Chief Technology Officer",
            PartyMemberType.CODER: "Programmer",
            PartyMemberType.TESTER: "Software Test Engineer",
            PartyMemberType.DOCUMENTER: "Technical Writer",
            PartyMemberType.ANALYST: "Data Analyst",
            PartyMemberType.DEBUGGER: "Quality Assurance Engineer",
        }

        return [
            role_mapping.get(member.member_type, "Developer")
            for member in self.party_session.members
        ]


# Integration Classes


class JupyterIntegration:
    """Jupyter notebook integration for spell crafting."""

    def __init__(self) -> None:
        self.kernel_manager = None
        if JUPYTER_AVAILABLE:
            try:
                self.kernel_manager = KernelManager()
                self.kernel_manager.start_kernel()
            except (RuntimeError, OSError) as e:
                console.print(f"[red]Jupyter initialization failed: {e}[/red]")

    async def execute_code(self, code: str) -> str:
        """Execute code in Jupyter kernel."""
        if not self.kernel_manager:
            return "Jupyter kernel not available"

        try:
            kernel = self.kernel_manager.kernel
            kernel.execute(code)

            # Wait for output
            await asyncio.sleep(1)  # Simple wait, could be improved

            return "Code executed in Jupyter kernel"
        except (RuntimeError, OSError) as e:
            return f"Execution failed: {e}"


class ObsidianIntegration:
    """Obsidian knowledge base integration."""

    def __init__(self, repository_root: str) -> None:
        self.repository_root = Path(repository_root)
        self.obsidian_vault = self.repository_root / "obsidian_vault"
        self.obsidian_vault.mkdir(exist_ok=True)

    def generate_compendium(self) -> str:
        """Generate comprehensive repository compendium."""
        try:
            # Create main index
            self._create_main_index()

            # Generate file maps
            self._generate_file_maps()

            # Create relationship graphs
            self._create_relationship_graphs()

            # Generate snapshots documentation
            self._document_snapshots()

            # Create VSCode configuration docs
            self._document_vscode_config()

            return f"📚 Obsidian compendium generated at: {self.obsidian_vault}"

        except (OSError, ValueError) as e:
            return f"Compendium generation failed: {e}"

    def _create_main_index(self) -> str:
        """Create main index file."""
        content = f"""# KILO-FOOLISH Repository Compendium
Generated: {datetime.now().isoformat()}

## 🗺️ Repository Structure
- [[File Maps]]
- [[Code Analysis]]
- [[Relationship Graphs]]

## 🧙‍♂️ Wizard Navigator
- [[Party Members]]
- [[Adventure Log]]
- [[Spell Compendium]]

## 🔧 Configurations
- [[VSCode Settings]]
- [[Project Snapshots]]
- [[Integration Points]]

## 📊 Analytics
- [[Code Metrics]]
- [[Performance Analysis]]
- [[Growth Tracking]]
"""

        with open(self.obsidian_vault / "README.md", "w", encoding="utf-8") as f:
            f.write(content)

        return content

    def _generate_file_maps(self) -> None:
        """Generate detailed file maps."""
        file_maps_dir = self.obsidian_vault / "File_Maps"
        file_maps_dir.mkdir(exist_ok=True)

        # Scan repository for Python files
        python_files = list(self.repository_root.rglob("*.py"))

        # Create Python files map
        py_content = "# Python Files\n\n"
        for py_file in python_files:
            rel_path = py_file.relative_to(self.repository_root)
            py_content += f"- [[{rel_path}]]\n"

        with open(file_maps_dir / "Python_Files.md", "w", encoding="utf-8") as f:
            f.write(py_content)

    def _create_relationship_graphs(self) -> None:
        """Create relationship visualization files."""
        graphs_dir = self.obsidian_vault / "Graphs"
        graphs_dir.mkdir(exist_ok=True)

        # Create import graph
        import_graph = "# Import Relationships\n\n```mermaid\ngraph TD\n"
        # Add import relationships here
        import_graph += "A[main] --> B[utils]\nB --> C[core]\n"
        import_graph += "```\n"

        with open(graphs_dir / "Import_Graph.md", "w", encoding="utf-8") as f:
            f.write(import_graph)

    def _document_snapshots(self) -> None:
        """Document repository snapshots."""
        snapshots_dir = self.obsidian_vault / "Snapshots"
        snapshots_dir.mkdir(exist_ok=True)

        snapshot_content = f"""# Repository Snapshots
Generated: {datetime.now().isoformat()}

## Current State
- Total Files: {len(list(self.repository_root.rglob("*")))}
- Python Files: {len(list(self.repository_root.rglob("*.py")))}
- Documentation: {len(list(self.repository_root.rglob("*.md")))}

## Configuration Files
- VSCode: {len(list(self.repository_root.rglob(".vscode/*")))}
- Git: {(self.repository_root / ".git").exists()}
"""

        with open(snapshots_dir / "Current_State.md", "w", encoding="utf-8") as f:
            f.write(snapshot_content)

    def _document_vscode_config(self) -> None:
        """Document VSCode configuration."""
        vscode_dir = self.obsidian_vault / "VSCode"
        vscode_dir.mkdir(exist_ok=True)

        vscode_config_dir = self.repository_root / ".vscode"
        if vscode_config_dir.exists():
            config_content = "# VSCode Configuration\n\n"

            for config_file in vscode_config_dir.glob("*.json"):
                config_content += f"## {config_file.name}\n\n"
                try:
                    with open(config_file, encoding="utf-8") as f:
                        content = f.read()
                    config_content += f"```json\n{content}\n```\n\n"
                except (OSError, UnicodeDecodeError) as e:
                    config_content += f"Error reading file: {e}\n\n"

            with open(vscode_dir / "Configuration.md", "w", encoding="utf-8") as f:
                f.write(config_content)


class VSCodeIntegration:
    """VSCode workspace enhancement."""

    def __init__(self, repository_root: str) -> None:
        self.repository_root = Path(repository_root)
        self.vscode_dir = self.repository_root / ".vscode"
        self.vscode_dir.mkdir(exist_ok=True)

    def open_enhanced_workspace(self) -> str:
        """Create and open enhanced VSCode workspace."""
        try:
            # Create enhanced workspace configuration
            workspace_config = {
                "folders": [
                    {"path": "."},
                    {"path": "./ΞNuSyQ₁-Hub₁"},
                    {"path": "./Scripts"},
                    {"path": "./src"},
                    {"path": "./obsidian_vault"},
                ],
                "settings": {
                    "python.defaultInterpreterPath": "./venv_kilo/Scripts/python.exe",
                    "python.terminal.activateEnvironment": True,
                    "copilot.enable": True,
                    "workbench.colorTheme": "KILO-FOOLISH Dark",
                    "terminal.integrated.defaultProfile.windows": "PowerShell",
                },
                "extensions": {
                    "recommendations": [
                        "ms-python.python",
                        "github.copilot",
                        "ms-toolsai.jupyter",
                        "foam.foam-vscode",
                        "godotengine.godot-tools",
                    ],
                },
            }

            workspace_file = self.repository_root / "KILO-FOOLISH-Enhanced.code-workspace"
            with open(workspace_file, "w", encoding="utf-8") as f:
                json.dump(workspace_config, f, indent=2)

            # Try to open workspace
            try:
                subprocess.run(["code", str(workspace_file)], check=True)
                return f"🎨 Enhanced VSCode workspace opened: {workspace_file}"
            except subprocess.CalledProcessError:
                return f"⚠️ Workspace file created but couldn't auto-open: {workspace_file}"

        except (OSError, ValueError) as e:
            return f"VSCode integration failed: {e}"


class GODOTIntegration:
    """GODOT game engine integration."""

    def __init__(self, repository_root: str) -> None:
        self.repository_root = Path(repository_root)
        self.godot_projects_dir = self.repository_root / "godot_projects"
        self.godot_projects_dir.mkdir(exist_ok=True)

    def create_game_portal(self) -> str:
        """Create GODOT game project portal."""
        try:
            project_name = "WizardNavigatorGame"
            project_dir = self.godot_projects_dir / project_name
            project_dir.mkdir(exist_ok=True)

            # Create basic project.godot file
            project_config = """[application]

config/name="Wizard Navigator"
config/description="Repository exploration game"
run/main_scene="res://Main.tscn"

[rendering]

renderer/rendering_method="gl_compatibility"
"""

            with open(project_dir / "project.godot", "w", encoding="utf-8") as f:
                f.write(project_config)

            # Create basic main scene script
            main_script = """extends Node2D

# Wizard Navigator Game
# Integration with KILO-FOOLISH repository

func _ready():
    print("Wizard Navigator Game Portal Activated!")

func _input(event):
    if event is InputEventKey and event.pressed:
        if event.keycode == KEY_SPACE:
            print("Repository exploration initiated...")
"""

            with open(project_dir / "Main.gd", "w", encoding="utf-8") as f:
                f.write(main_script)

            return f"🎮 GODOT game portal created: {project_dir}\nOpen in GODOT Engine to start developing!"

        except (OSError, ValueError) as e:
            return f"GODOT integration failed: {e}"


class RepositoryCompendium:
    """Enhanced repository analysis and compendium generation."""

    def __init__(self, repository_root: str) -> None:
        self.repository_root = Path(repository_root)
        self.analysis_cache: dict[str, Any] = {}

    def generate_comprehensive_analysis(self) -> dict[str, Any]:
        """Generate comprehensive repository analysis."""
        return {
            "timestamp": datetime.now().isoformat(),
            "structure": self._analyze_structure(),
            "python_files": self._analyze_python_files(),
            "configurations": self._analyze_configurations(),
            "documentation": self._analyze_documentation(),
            "unique_features": self._identify_unique_features(),
        }

    def _analyze_structure(self) -> dict[str, Any]:
        """Analyze repository structure."""
        total_files = len(list(self.repository_root.rglob("*")))
        file_types: defaultdict[str, int] = defaultdict(int)

        for file_path in self.repository_root.rglob("*"):
            if file_path.is_file():
                file_types[file_path.suffix] += 1

        return {
            "total_files": total_files,
            "file_types": dict(file_types),
            "directories": len([p for p in self.repository_root.rglob("*") if p.is_dir()]),
        }

    def _analyze_python_files(self) -> dict[str, Any]:
        """Analyze Python files specifically."""
        python_files = list(self.repository_root.rglob("*.py"))

        analysis = {
            "count": len(python_files),
            "unique_files": [],
            "imports": set(),
            "classes": [],
            "functions": [],
        }

        for py_file in python_files:
            rel_path = str(py_file.relative_to(self.repository_root))

            # Check for unique KILO-FOOLISH patterns
            if any(
                pattern in rel_path.lower()
                for pattern in ["xi", "nu", "quantum", "consciousness", "transcendent"]
            ):
                unique_files = cast(list[str], analysis["unique_files"])  # ensure correct type
                unique_files.append(rel_path)

        return analysis

    def _analyze_configurations(self) -> dict[str, Any]:
        """Analyze configuration files."""
        config_patterns = [
            ".vscode",
            ".git",
            "requirements.txt",
            "*.yaml",
            "*.json",
            "*.toml",
        ]
        configs: dict[str, Any] = {}
        for pattern in config_patterns:
            if pattern.startswith("."):
                # Directory
                config_dir = self.repository_root / pattern
                if config_dir.exists():
                    configs[pattern] = {
                        "exists": True,
                        "files": [
                            str(f.relative_to(self.repository_root))
                            for f in config_dir.rglob("*")
                            if f.is_file()
                        ],
                    }
            else:
                # File pattern
                files = list(self.repository_root.rglob(pattern))
                if files:
                    configs[pattern] = [str(f.relative_to(self.repository_root)) for f in files]

        return configs

    def _analyze_documentation(self) -> dict[str, Any]:
        """Analyze documentation."""
        doc_files = list(self.repository_root.rglob("*.md"))

        return {
            "markdown_files": len(doc_files),
            "readme_files": [
                str(f.relative_to(self.repository_root))
                for f in doc_files
                if "readme" in f.name.lower()
            ],
            "doc_directories": list(
                {str(f.parent.relative_to(self.repository_root)) for f in doc_files}
            ),
        }

    def _identify_unique_features(self) -> list[str]:
        """Identify unique features of this repository."""
        features: list[Any] = []
        # Check for KILO-FOOLISH specific elements
        unique_patterns = [
            ("ΞNuSyQ", "Quantum consciousness system"),
            ("Transcendent_Spine", "Transcendent architecture"),
            ("wizard_navigator", "Repository exploration game"),
            ("copilot_enhancement", "AI enhancement bridge"),
            ("consciousness", "Consciousness integration"),
            ("quantum", "Quantum computing elements"),
        ]

        for pattern, description in unique_patterns:
            if any(pattern.lower() in str(p).lower() for p in self.repository_root.rglob("*")):
                features.append(description)

        return features


# Main CLI Interface
async def main() -> None:
    """Main CLI interface for the Enhanced Wizard Navigator."""
    navigator = EnhancedWizardNavigator()

    console.print(
        "\n[bold magenta]🧙‍♂️ Welcome to the Enhanced KILO-FOOLISH Wizard Navigator![/bold magenta]"
    )
    console.print("[cyan]Your AI party awaits your command...[/cyan]\n")

    # Initial party introduction
    console.print("[bold yellow]🎭 Meet your party:[/bold yellow]")
    for member in navigator.party_session.members:
        icon = member.member_type.value
        console.print(
            f"  {icon} [bold cyan]{member.name}[/bold cyan] - {member.member_type.name} ({member.personality.value})"
        )

    console.print(
        "\n[dim]Type 'help' for commands or 'party discuss introduction' to have them introduce themselves![/dim]\n"
    )

    while True:
        try:
            command = console.input("[bold green]🧙‍♂️ Command: [/bold green]")

            if command.lower() in ["quit", "exit"]:
                console.print("[bold red]🌅 The adventure ends... for now.[/bold red]")
                break

            if command.strip():
                await navigator.handle_command(command)

        except KeyboardInterrupt:
            console.print("\n[bold red]🌅 Adventure interrupted. Farewell, wizard![/bold red]")
            break
        except (EOFError, RuntimeError, ValueError, OSError) as e:
            console.print(f"[red]💥 Error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
