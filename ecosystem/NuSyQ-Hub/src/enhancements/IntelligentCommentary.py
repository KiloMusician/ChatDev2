"""KILO-FOOLISH Intelligent Code Commentary System.

Systematically enhances code with meaningful, insightful comments that improve
understanding, maintainability, and AI integration effectiveness.
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class KILOIntelligentCommentary:
    def __init__(self, repo_root: str | None = None) -> None:
        """Initialize KILOIntelligentCommentary with repo_root."""
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent.parent
        self.comment_history: dict[str, Any] = {}
        self.analysis_cache: dict[str, Any] = {}
        self.commentary_rules: dict[str, Any] = {}
        self.enhancement_targets: list[str] = []
        self.ai_integration_insights: list[str] = []

        # Commentary configuration
        self.config = {
            "interval_minutes": 5,
            "comments_per_session": 3,
            "min_line_length": 20,
            "max_comment_length": 120,
            "enhancement_focus": [
                "functionality",
                "architecture",
                "ai_integration",
                "best_practices",
            ],
            "comment_styles": {
                "python": "#",
                "powershell": "#",
                "javascript": "//",
                "markdown": "<!--",
            },
            "skip_patterns": [
                r"^\s*#.*",  # Already commented
                r"^\s*$",  # Empty lines
                r"^\s*import\s+",  # Simple imports
                r"^\s*from\s+.*import",  # Simple imports
            ],
        }

        self.load_commentary_intelligence()
        self.setup_logging()

    def setup_logging(self) -> None:
        """Setup logging for commentary system."""
        log_file = self.repo_root / "data" / "logs" / "commentary.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def load_commentary_intelligence(self) -> None:
        """Load existing commentary intelligence and history."""
        intel_file = self.repo_root / "src" / "core" / "commentary_intelligence.json"

        if intel_file.exists():
            try:
                with open(intel_file) as f:
                    data = json.load(f)
                    self.comment_history = data.get("comment_history", {})
                    self.analysis_cache = data.get("analysis_cache", {})
                    self.commentary_rules = data.get("commentary_rules", {})
            except Exception as e:
                self.logger.warning(f"Could not load commentary intelligence: {e}")

        # Initialize default rules if empty
        if not self.commentary_rules:
            self.initialize_default_rules()

    def save_commentary_intelligence(self) -> None:
        """Save commentary intelligence data."""
        intel_file = self.repo_root / "src" / "core" / "commentary_intelligence.json"
        intel_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "timestamp": datetime.now().isoformat(),
            "comment_history": self.comment_history,
            "analysis_cache": self.analysis_cache,
            "commentary_rules": self.commentary_rules,
            "config": self.config,
        }

        with open(intel_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def initialize_default_rules(self) -> None:
        """Initialize default commentary rules."""
        self.commentary_rules = {
            "function_patterns": {
                r"def\s+(\w+)\s*\(.*\):": {
                    "templates": [
                        "# {function_name}: Orchestrates {purpose} with intelligent {technique}",
                        "# Strategic {function_name} implementation for enhanced {benefit}",
                        "# {function_name} leverages {pattern} to optimize {outcome}",
                    ],
                    "focus": "architectural_insight",
                },
                r"class\s+(\w+).*:": {
                    "templates": [
                        "# {class_name}: Core intelligence engine for {domain} management",
                        "# Advanced {class_name} framework enabling {capability}",
                        "# {class_name} represents {abstraction} in the KILO ecosystem",
                    ],
                    "focus": "design_pattern",
                },
            },
            "code_patterns": {
                r"for\s+\w+\s+in\s+.*:": {
                    "templates": [
                        "# Iterative processing optimizes {data_structure} traversal efficiency",
                        "# Systematic enumeration ensures comprehensive {operation} coverage",
                        "# Parallel-ready iteration pattern for scalable {process} execution",
                    ],
                    "focus": "algorithmic_insight",
                },
                r"if\s+.*:\s*$": {
                    "templates": [
                        "# Conditional branching implements intelligent decision logic",
                        "# Strategic condition evaluation for optimal {outcome}",
                        "# Guard clause ensures robust {behavior} under {scenario} conditions",
                    ],
                    "focus": "logic_flow",
                },
                r"try:\s*$": {
                    "templates": [
                        "# Resilient error handling maintains system stability",
                        "# Defensive programming ensures graceful {operation} degradation",
                        "# Exception management preserves data integrity during {process}",
                    ],
                    "focus": "reliability",
                },
            },
            "ai_integration_patterns": {
                r"openai|gpt|llm|ai|intelligence": {
                    "templates": [
                        "# AI integration point: Enhances human-machine collaboration",
                        "# LLM bridge: Transforms natural language into actionable intelligence",
                        "# Cognitive augmentation layer for enhanced decision-making",
                    ],
                    "focus": "ai_enhancement",
                },
                r"config|secret|key": {
                    "templates": [
                        "# Secure configuration management prevents credential exposure",
                        "# Environment-aware settings enable flexible deployment strategies",
                        "# Configuration abstraction supports multi-environment operations",
                    ],
                    "focus": "security_architecture",
                },
            },
            "architecture_patterns": {
                r"coordinator|manager|controller|handler": {
                    "templates": [
                        "# Orchestration layer: Coordinates distributed system components",
                        "# Central command pattern enables unified {system} management",
                        "# Strategic coordination hub for {domain} intelligence",
                    ],
                    "focus": "system_design",
                },
                r"scanner|analyzer|processor|parser": {
                    "templates": [
                        "# Analysis engine: Extracts actionable insights from {data_type}",
                        "# Intelligent parsing transforms raw {input} into structured knowledge",
                        "# Pattern recognition system for {domain} understanding",
                    ],
                    "focus": "data_processing",
                },
            },
        }

    def analyze_code_line(self, line: str, file_path: Path, line_number: int) -> dict[str, Any]:
        """Analyze a line of code for commentary potential."""
        analysis = {
            "line": line.strip(),
            "file_path": str(file_path),
            "line_number": line_number,
            "complexity_score": 0,
            "insight_potential": 0,
            "ai_relevance": 0,
            "patterns_matched": [],
            "suggested_comments": [],
            "enhancement_opportunities": [],
        }

        # Skip if line matches skip patterns
        for pattern in self.config["skip_patterns"]:
            if re.match(pattern, line):
                return analysis

        # Calculate complexity score
        analysis["complexity_score"] = self.calculate_complexity_score(line)

        # Check for pattern matches
        analysis["patterns_matched"] = self.find_pattern_matches(line)

        # Calculate insight potential
        analysis["insight_potential"] = self.calculate_insight_potential(
            line, analysis["patterns_matched"]
        )

        # Calculate AI relevance
        analysis["ai_relevance"] = self.calculate_ai_relevance(line, file_path)

        # Generate suggested comments
        analysis["suggested_comments"] = self.generate_intelligent_comments(line, analysis)

        # Identify enhancement opportunities
        analysis["enhancement_opportunities"] = self.identify_enhancements(line, file_path)

        return analysis

    def calculate_complexity_score(self, line: str) -> int:
        """Calculate complexity score for a line of code."""
        score = 0

        # Base score on line length and content
        score += min(len(line) // 20, 5)

        # Boost for complex constructs
        complex_patterns = [
            r"lambda\s+.*:",  # Lambda functions
            r".*\[.*for.*in.*\]",  # List comprehensions
            r".*\{.*:.*for.*in.*\}",  # Dict comprehensions
            r".*\.join\(",  # String joining
            r".*\.format\(",  # String formatting
            r".*\*\*\w+",  # Kwargs unpacking
            r".*\*\w+",  # Args unpacking
            r"with\s+.*as.*:",  # Context managers
            r"@\w+",  # Decorators
        ]

        for pattern in complex_patterns:
            if re.search(pattern, line):
                score += 2

        # Boost for method chaining
        if line.count(".") > 2:
            score += 1

        # Boost for multiple operators
        operators = ["+", "-", "*", "/", "%", "==", "!=", "<=", ">=", "&&", "||"]
        operator_count = sum(line.count(op) for op in operators)
        score += min(operator_count, 3)

        return min(score, 10)

    def find_pattern_matches(self, line: str) -> list[dict[str, str]]:
        """Find patterns that match the line."""
        matches: list[Any] = []
        for category, patterns in self.commentary_rules.items():
            for pattern, rule_info in patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append(
                        {
                            "category": category,
                            "pattern": pattern,
                            "focus": rule_info["focus"],
                            "templates": rule_info["templates"],
                        }
                    )

        return matches

    def calculate_insight_potential(self, line: str, patterns: list[dict]) -> int:
        """Calculate potential for generating insightful comments."""
        score = 0

        # Base score on pattern matches
        score += len(patterns) * 3

        # Boost for architectural keywords
        arch_keywords = [
            "coordinator",
            "manager",
            "intelligence",
            "strategy",
            "optimization",
            "framework",
            "orchestration",
            "abstraction",
            "pattern",
            "engine",
        ]

        for keyword in arch_keywords:
            if keyword in line.lower():
                score += 2

        # Boost for AI/ML related content
        ai_keywords = [
            "ai",
            "llm",
            "gpt",
            "openai",
            "anthropic",
            "model",
            "client",
            "prompt",
            "completion",
            "embedding",
            "semantic",
        ]

        for keyword in ai_keywords:
            if keyword in line.lower():
                score += 3

        # Boost for complex logic
        logic_indicators = ["and", "or", "not", "if", "else", "elif", "while", "for"]
        logic_count = sum(1 for indicator in logic_indicators if indicator in line.lower())
        score += min(logic_count, 4)

        return min(score, 15)

    def calculate_ai_relevance(self, line: str, file_path: Path) -> int:
        """Calculate relevance for AI systems and Copilot."""
        score = 0

        # Boost for files with AI-related names
        ai_file_patterns = [
            "ai",
            "gpt",
            "llm",
            "intelligence",
            "smart",
            "cognitive",
            "semantic",
            "model",
            "client",
            "prompt",
        ]

        file_name = file_path.name.lower()
        for pattern in ai_file_patterns:
            if pattern in file_name:
                score += 3

        # Boost for API integration points
        api_patterns = [
            r"api_key",
            r"client\.",
            r"\.chat\.",
            r"\.completion",
            r"openai",
            r"anthropic",
            r"ollama",
            r"request",
            r"response",
        ]

        for pattern in api_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                score += 2

        # Boost for configuration and security
        config_patterns = [
            r"config",
            r"secret",
            r"token",
            r"auth",
            r"credential",
            r"environment",
            r"setting",
            r"parameter",
        ]

        for pattern in config_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                score += 2

        return min(score, 10)

    def generate_intelligent_comments(self, line: str, analysis: dict) -> list[str]:
        """Generate intelligent, insightful comments for the line."""
        comments: list[Any] = []
        # Use pattern-based templates
        for pattern_match in analysis["patterns_matched"]:
            templates = pattern_match["templates"]
            for template in templates[:2]:  # Limit to 2 per pattern
                comment = self.populate_comment_template(template, line, analysis)
                if comment and comment not in comments:
                    comments.append(comment)

        # Generate context-aware comments
        context_comments = self.generate_context_aware_comments(line, analysis)
        comments.extend(context_comments)

        # Generate AI-enhancement comments
        if analysis["ai_relevance"] > 5:
            ai_comments = self.generate_ai_enhancement_comments(line, analysis)
            comments.extend(ai_comments)

        # Ensure uniqueness and reasonable length
        unique_comments: list[Any] = []
        for comment in comments:
            if len(comment) <= self.config["max_comment_length"] and comment not in unique_comments:
                unique_comments.append(comment)

        return unique_comments[:3]  # Limit to top 3 suggestions

    def populate_comment_template(self, template: str, line: str, _analysis: dict) -> str:
        """Populate comment template with intelligent values."""
        try:
            # Extract meaningful terms from the line
            context = self.extract_line_context(line)

            # Default replacements
            replacements = {
                "function_name": context.get("function_name", "operation"),
                "class_name": context.get("class_name", "component"),
                "purpose": context.get("purpose", "system coordination"),
                "technique": context.get("technique", "strategic processing"),
                "benefit": context.get("benefit", "operational efficiency"),
                "pattern": context.get("pattern", "architectural design"),
                "outcome": context.get("outcome", "optimized performance"),
                "domain": context.get("domain", "system"),
                "capability": context.get("capability", "intelligent automation"),
                "abstraction": context.get("abstraction", "strategic coordination"),
                "data_structure": context.get("data_structure", "information"),
                "operation": context.get("operation", "processing"),
                "process": context.get("process", "workflow"),
                "behavior": context.get("behavior", "functionality"),
                "scenario": context.get("scenario", "operational"),
                "system": context.get("system", "KILO"),
                "data_type": context.get("data_type", "structured data"),
                "input": context.get("input", "information"),
            }

            # Populate template
            populated = template
            for key, value in replacements.items():
                populated = populated.replace(f"{{{key}}}", value)

            return populated

        except Exception as e:
            self.logger.debug(f"Template population error: {e}")
            return ""

    def extract_line_context(self, line: str) -> dict[str, str]:
        """Extract contextual information from a line of code."""
        context: dict[str, Any] = {}
        # Extract function names
        func_match = re.search(r"def\s+(\w+)", line)
        if func_match:
            context["function_name"] = func_match.group(1)

        # Extract class names
        class_match = re.search(r"class\s+(\w+)", line)
        if class_match:
            context["class_name"] = class_match.group(1)

        # Infer purpose from keywords
        if any(word in line.lower() for word in ["config", "setting", "secret"]):
            context["purpose"] = "configuration management"
            context["domain"] = "security"
        elif any(word in line.lower() for word in ["ai", "gpt", "llm"]):
            context["purpose"] = "AI integration"
            context["domain"] = "artificial intelligence"
        elif any(word in line.lower() for word in ["scan", "analyze", "parse"]):
            context["purpose"] = "data analysis"
            context["domain"] = "information processing"
        elif any(word in line.lower() for word in ["coordinate", "manage", "control"]):
            context["purpose"] = "system orchestration"
            context["domain"] = "architecture"

        # Infer techniques from patterns
        if "for" in line and "in" in line:
            context["technique"] = "iterative processing"
        elif "if" in line:
            context["technique"] = "conditional logic"
        elif "try:" in line:
            context["technique"] = "resilient error handling"
        elif "import" in line:
            context["technique"] = "modular integration"

        return context

    def generate_context_aware_comments(self, _line: str, analysis: dict) -> list[str]:
        """Generate comments based on broader context."""
        comments: list[Any] = []
        # Comments based on complexity
        if analysis["complexity_score"] > 7:
            comments.append("# Complex operation requiring careful attention to edge cases")
        elif analysis["complexity_score"] > 4:
            comments.append(
                "# Strategic implementation balances functionality with maintainability"
            )

        # Comments based on AI relevance
        if analysis["ai_relevance"] > 7:
            comments.append("# Critical AI integration point: Enhances system intelligence")
        elif analysis["ai_relevance"] > 4:
            comments.append("# AI-enhanced functionality for improved user experience")

        # Comments based on file context
        file_path = Path(analysis["file_path"])
        if "config" in file_path.name.lower():
            comments.append("# Configuration layer: Enables flexible system adaptation")
        elif "core" in str(file_path):
            comments.append("# Core system component: Essential for KILO architecture")
        elif "intelligence" in file_path.name.lower():
            comments.append("# Intelligence module: Transforms data into actionable insights")

        return comments

    def generate_ai_enhancement_comments(self, line: str, _analysis: dict) -> list[str]:
        """Generate comments that enhance AI understanding and Copilot effectiveness."""
        comments: list[Any] = []
        # API integration comments
        if any(keyword in line.lower() for keyword in ["api", "client", "key"]):
            comments.append("# API bridge: Connects KILO intelligence with external AI services")

        # Configuration comments
        if any(keyword in line.lower() for keyword in ["config", "secret"]):
            comments.append(
                "# Secure config: Maintains AI service credentials with enterprise-grade security"
            )

        # Processing comments
        if any(keyword in line.lower() for keyword in ["process", "analyze", "parse"]):
            comments.append(
                "# Data transformation: Converts raw input into AI-ready structured format"
            )

        # Error handling comments
        if "try:" in line or "except" in line:
            comments.append("# Resilient AI operation: Ensures continuous service availability")

        return comments

    def identify_enhancements(self, line: str, _file_path: Path) -> list[str]:
        """Identify opportunities for code enhancement."""
        enhancements: list[Any] = []
        # Suggest type hints
        if "def " in line and ":" in line and "->" not in line:
            enhancements.append("Consider adding type hints for improved AI code understanding")

        # Suggest docstrings
        if ("def " in line or "class " in line) and '"""' not in line:
            enhancements.append("Docstring addition would enhance AI-assisted development")

        # Suggest error handling
        if (
            any(risky in line.lower() for risky in ["open(", "requests.", "json.load"])
            and "try:" not in line
        ):
            enhancements.append("Consider adding error handling for improved reliability")

        return enhancements

    def select_enhancement_target(self) -> tuple[Path, int, str] | None:
        """Select the next line to enhance with comments."""
        candidates: list[Any] = []
        # Scan repository for enhancement targets
        for file_path in self.get_target_files():
            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    # Skip if already commented recently
                    line_id = f"{file_path}:{line_num}"
                    if self.was_recently_commented(line_id):
                        continue

                    # Analyze line
                    analysis = self.analyze_code_line(line, file_path, line_num)

                    # Calculate overall score
                    score = (
                        analysis["complexity_score"] * 0.3
                        + analysis["insight_potential"] * 0.4
                        + analysis["ai_relevance"] * 0.3
                    )

                    if score > 5:  # Threshold for enhancement
                        candidates.append((file_path, line_num, line.strip(), score, analysis))

            except Exception as e:
                self.logger.debug(f"Error analyzing {file_path}: {e}")

        # Sort by score and select best candidate
        if candidates:
            candidates.sort(key=lambda x: x[3], reverse=True)
            best_candidate = candidates[0]
            return (
                best_candidate[:3],
                best_candidate[4],
            )  # Return file, line_num, line, analysis

        return None

    def get_target_files(self) -> list[Path]:
        """Get list of files to target for enhancement."""
        target_files: list[Any] = []
        # Target patterns
        patterns = ["*.py", "*.ps1", "*.js", "*.ts"]

        for pattern in patterns:
            target_files.extend(self.repo_root.rglob(pattern))

        # Filter out unwanted files
        filtered_files: list[Any] = []
        for file_path in target_files:
            if (
                not any(skip in str(file_path) for skip in [".git", "__pycache__", "node_modules"])
                and file_path.stat().st_size < 1024 * 1024
            ):  # Skip files > 1MB
                filtered_files.append(file_path)

        return filtered_files

    def was_recently_commented(self, line_id: str) -> bool:
        """Check if line was commented recently."""
        if line_id in self.comment_history:
            last_commented = datetime.fromisoformat(self.comment_history[line_id]["timestamp"])
            time_diff = datetime.now() - last_commented
            return time_diff < timedelta(hours=24)  # Don't comment same line within 24h
        return False

    def add_intelligent_comment(self, file_path: Path, line_number: int, comment: str) -> bool:
        """Add intelligent comment to the specified line."""
        try:
            # Read file
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Determine comment style
            ext = file_path.suffix.lower()
            comment_char = self.config["comment_styles"].get(ext.lstrip("."), "#")

            # Format comment
            formatted_comment = f"{comment_char} {comment}\n"

            # Insert comment before the target line
            lines.insert(line_number - 1, formatted_comment)

            # Write file back
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            # Record in history
            line_id = f"{file_path}:{line_number}"
            self.comment_history[line_id] = {
                "timestamp": datetime.now().isoformat(),
                "comment": comment,
                "file_path": str(file_path),
            }

            self.logger.info(f"Added comment to {file_path}:{line_number}: {comment}")
            return True

        except Exception as e:
            self.logger.exception(f"Error adding comment to {file_path}:{line_number}: {e}")
            return False

    def run_commentary_session(self) -> dict[str, Any]:
        """Run a single commentary enhancement session."""
        session_results = {
            "timestamp": datetime.now().isoformat(),
            "comments_added": 0,
            "files_enhanced": set(),
            "insights_generated": [],
            "errors": [],
        }

        self.logger.info("🧠 Starting intelligent commentary session...")

        for i in range(self.config["comments_per_session"]):
            try:
                # Select enhancement target
                target_result = self.select_enhancement_target()
                if not target_result:
                    self.logger.info("No suitable enhancement targets found")
                    break

                target_info, analysis = target_result
                file_path, line_number, _line = target_info

                # Select best comment
                if analysis["suggested_comments"]:
                    comment = analysis["suggested_comments"][0]  # Use top suggestion

                    # Add comment
                    if self.add_intelligent_comment(file_path, line_number, comment):
                        session_results["comments_added"] += 1
                        session_results["files_enhanced"].add(str(file_path))
                        session_results["insights_generated"].append(
                            {
                                "file": str(file_path),
                                "line": line_number,
                                "comment": comment,
                                "complexity": analysis["complexity_score"],
                                "insight_potential": analysis["insight_potential"],
                                "ai_relevance": analysis["ai_relevance"],
                            }
                        )

            except Exception as e:
                error_msg = f"Error in commentary session iteration {i}: {e}"
                self.logger.exception(error_msg)
                session_results["errors"].append(error_msg)

        # Save updated intelligence
        self.save_commentary_intelligence()

        self.logger.info(
            f"Commentary session complete: {session_results['comments_added']} comments added"
        )
        return session_results

    def start_continuous_commentary(self) -> None:
        """Start continuous commentary enhancement."""
        self.logger.info("🧠 Starting KILO-FOOLISH Continuous Intelligent Commentary")

        while True:
            try:
                # Run commentary session
                session_results = self.run_commentary_session()

                # Log session summary
                if session_results["comments_added"] > 0:
                    self.logger.info(
                        f"✨ Enhanced {len(session_results['files_enhanced'])} files "
                        f"with {session_results['comments_added']} intelligent comments",
                    )

                # Wait for next session
                wait_time = self.config["interval_minutes"] * 60
                self.logger.debug(
                    f"Waiting {self.config['interval_minutes']} minutes for next session..."
                )
                time.sleep(wait_time)

            except KeyboardInterrupt:
                self.logger.info("🛑 Continuous commentary stopped by user")
                break
            except Exception as e:
                self.logger.exception(f"Error in continuous commentary: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KILO-FOOLISH Intelligent Commentary")
    parser.add_argument("--continuous", action="store_true", help="Start continuous commentary")
    parser.add_argument("--session", action="store_true", help="Run single commentary session")
    parser.add_argument("--analyze", help="Analyze specific file")
    parser.add_argument("--target", help="Target specific line (file:line_number)")

    args = parser.parse_args()

    commentary = KILOIntelligentCommentary()

    if args.continuous:
        commentary.start_continuous_commentary()
    elif args.session:
        results = commentary.run_commentary_session()
    elif args.analyze:
        # Analyze specific file logic here
        pass
    elif args.target:
        # Target specific line logic here
        pass
    else:
        # Run single session by default
        results = commentary.run_commentary_session()
