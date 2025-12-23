"""
╔══════════════════════════════════════════════════════════════════════════╗
║ NuSyQ Modular Agent Model Manager                                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║ PURPOSE: Per-agent Ollama model assignment and tracking                 ║
║ ENABLES: Agent-specific model selection for optimized workflows         ║
║ TRACKS: Which model was used by each agent for performance analysis     ║
╚══════════════════════════════════════════════════════════════════════════╝

Integrates with ChatDev's multi-agent system to assign different Ollama models
to different agent roles based on their task requirements.

Example:
    - CEO uses qwen2.5-coder:14b for strategic thinking
    - Programmer uses qwen2.5-coder:14b for code generation
    - Code Reviewer uses starcoder2:15b for code analysis
    - Tester uses codellama:7b for test generation
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentModelAssignment:
    """Represents a model assignment for a specific agent role"""
    role: str
    model: str
    reasoning: str
    usage_count: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0


class ModularAgentModelManager:
    """
    Manages per-agent model assignments for ChatDev multi-agent workflows
    
    Features:
    - Load role-specific model assignments from RoleConfig
    - Track which model each agent uses
    - Collect performance metrics per agent/model combination
    - Enable A/B testing and optimization
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the manager
        
        Args:
            config_path: Path to RoleConfig_Modular.json (auto-detected if None)
        """
        if config_path is None:
            # Auto-detect config in NuSyQ_Ollama directory
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "CompanyConfig" / "NuSyQ_Ollama" / "RoleConfig_Modular.json"
        
        self.config_path = Path(config_path)
        self.role_models: Dict[str, AgentModelAssignment] = {}
        self.session_log: List[Dict] = []
        self.load_config()
    
    def load_config(self):
        """Load role-to-model assignments from config file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Parse role configurations
            for role_name, role_config in config.items():
                if role_name.startswith('_'):
                    # Skip metadata
                    continue
                
                if isinstance(role_config, dict) and 'model' in role_config:
                    assignment = AgentModelAssignment(
                        role=role_name,
                        model=role_config['model'],
                        reasoning=role_config.get('model_reasoning', 'No reasoning provided')
                    )
                    self.role_models[role_name] = assignment
                    logger.info(f"Loaded model for {role_name}: {assignment.model}")
            
            logger.info(f"Loaded {len(self.role_models)} agent-model assignments")
            
        except FileNotFoundError:
            logger.warning(f"Modular config not found at {self.config_path}, using defaults")
            self._load_defaults()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self._load_defaults()
    
    def _load_defaults(self):
        """Load default model assignments if config file not found"""
        default_model = os.environ.get('CHATDEV_MODEL', 'qwen2.5-coder:14b')
        
        default_roles = [
            "Chief Executive Officer",
            "Chief Product Officer",
            "Counselor",
            "Chief Technology Officer",
            "Chief Human Resource Officer",
            "Programmer",
            "Code Reviewer",
            "Software Test Engineer",
            "Chief Creative Officer"
        ]
        
        for role in default_roles:
            self.role_models[role] = AgentModelAssignment(
                role=role,
                model=default_model,
                reasoning="Default fallback model"
            )
    
    def get_model_for_role(self, role: str, fallback: str = "qwen2.5-coder:14b") -> str:
        """
        Get the assigned Ollama model for a specific agent role
        
        Args:
            role: Agent role name (e.g., "Programmer", "Chief Executive Officer")
            fallback: Model to use if role not found
        
        Returns:
            Ollama model name (e.g., "qwen2.5-coder:14b")
        """
        assignment = self.role_models.get(role)
        if assignment:
            return assignment.model
        else:
            logger.warning(f"No model assignment for role '{role}', using fallback: {fallback}")
            return fallback
    
    def log_agent_interaction(self, role: str, model: str, tokens: int, response_time: float):
        """
        Log an agent interaction for tracking and analysis
        
        Args:
            role: Agent role name
            model: Model used
            tokens: Number of tokens consumed
            response_time: Response time in seconds
        """
        self.session_log.append({
            "role": role,
            "model": model,
            "tokens": tokens,
            "response_time": response_time
        })
        
        # Update assignment metrics
        if role in self.role_models:
            assignment = self.role_models[role]
            assignment.usage_count += 1
            assignment.total_tokens += tokens
            
            # Update rolling average response time
            prev_avg = assignment.avg_response_time
            count = assignment.usage_count
            assignment.avg_response_time = (prev_avg * (count - 1) + response_time) / count
    
    def get_performance_summary(self) -> Dict:
        """
        Get performance summary for all agents
        
        Returns:
            Dictionary with performance metrics per role
        """
        summary = {}
        
        for role, assignment in self.role_models.items():
            summary[role] = {
                "model": assignment.model,
                "usage_count": assignment.usage_count,
                "total_tokens": assignment.total_tokens,
                "avg_response_time": round(assignment.avg_response_time, 2),
                "reasoning": assignment.reasoning
            }
        
        return summary
    
    def save_session_log(self, output_path: Path):
        """Save session interaction log to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "session_log": self.session_log,
                "performance_summary": self.get_performance_summary()
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Session log saved to {output_path}")
    
    def get_model_usage_stats(self) -> Dict[str, Dict]:
        """
        Get aggregated statistics per model (across all agents)
        
        Returns:
            Dictionary mapping model names to usage statistics
        """
        model_stats = {}
        
        for role, assignment in self.role_models.items():
            model = assignment.model
            
            if model not in model_stats:
                model_stats[model] = {
                    "roles": [],
                    "total_usage_count": 0,
                    "total_tokens": 0,
                    "avg_response_time": 0.0
                }
            
            model_stats[model]["roles"].append(role)
            model_stats[model]["total_usage_count"] += assignment.usage_count
            model_stats[model]["total_tokens"] += assignment.total_tokens
        
        # Calculate weighted average response times per model
        for model, stats in model_stats.items():
            total_time = 0
            total_count = 0
            
            for role in stats["roles"]:
                assignment = self.role_models[role]
                total_time += assignment.avg_response_time * assignment.usage_count
                total_count += assignment.usage_count
            
            if total_count > 0:
                stats["avg_response_time"] = round(total_time / total_count, 2)
        
        return model_stats
    
    def print_model_assignments(self):
        """Print current role-to-model assignments"""
        print("\n" + "="*70)
        print("🤖 NuSyQ Modular Agent-Model Assignments")
        print("="*70)
        
        for role, assignment in sorted(self.role_models.items()):
            print(f"\n{role}:")
            print(f"  Model: {assignment.model}")
            print(f"  Reasoning: {assignment.reasoning}")
            
            if assignment.usage_count > 0:
                print(f"  Usage: {assignment.usage_count} interactions")
                print(f"  Tokens: {assignment.total_tokens:,}")
                print(f"  Avg Response Time: {assignment.avg_response_time:.2f}s")
        
        print("\n" + "="*70)


# Singleton instance for easy import
_manager_instance: Optional[ModularAgentModelManager] = None


def get_manager() -> ModularAgentModelManager:
    """Get or create the singleton ModularAgentModelManager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ModularAgentModelManager()
    return _manager_instance


def get_model_for_role(role: str, fallback: str = "qwen2.5-coder:14b") -> str:
    """
    Convenience function to get model for a role
    
    Args:
        role: Agent role name
        fallback: Fallback model if role not found
    
    Returns:
        Ollama model name
    """
    return get_manager().get_model_for_role(role, fallback)


if __name__ == "__main__":
    # Demo/test the manager
    manager = ModularAgentModelManager()
    manager.print_model_assignments()
    
    # Simulate some interactions
    manager.log_agent_interaction("Programmer", "qwen2.5-coder:14b", 500, 2.5)
    manager.log_agent_interaction("Code Reviewer", "starcoder2:15b", 300, 1.8)
    manager.log_agent_interaction("Programmer", "qwen2.5-coder:14b", 450, 2.3)
    
    # Print performance summary
    print("\n📊 Performance Summary:")
    print(json.dumps(manager.get_performance_summary(), indent=2))
    
    print("\n📈 Model Usage Statistics:")
    print(json.dumps(manager.get_model_usage_stats(), indent=2))
