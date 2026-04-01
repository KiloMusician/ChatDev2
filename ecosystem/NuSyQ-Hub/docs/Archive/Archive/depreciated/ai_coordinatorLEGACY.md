import asyncio
import json
import subprocess
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CONVERSATION = "conversation"
    FAST_RESPONSE = "fast_response"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_EXPLANATION = "technical_explanation"

class AIModel:
    def __init__(self, name: str, model_id: str, capabilities: List[TaskType]):
        self.name = name
        self.model_id = model_id
        self.capabilities = capabilities
        self.last_used = None
        self.response_times = []

class KILOFoolishAICoordinator:
    def __init__(self):
        self.models = {
            "codellama": AIModel("CodeLlama", "codellama:7b", [TaskType.CODE_GENERATION]),
            "gemma": AIModel("Gemma", "gemma2:2b", [TaskType.FAST_RESPONSE, TaskType.CONVERSATION]),
            "mistral": AIModel("Mistral", "mistral:7b", [TaskType.TECHNICAL_EXPLANATION, TaskType.CONVERSATION]),
            "llama": AIModel("Llama", "llama3.2:3b", [TaskType.CREATIVE_WRITING, TaskType.CONVERSATION]),
            "phi": AIModel("Phi", "phi3.5:3.8b", [TaskType.CONVERSATION, TaskType.FAST_RESPONSE])
        }
        self.consciousness_level = 0.0
        self.interaction_history = []

    def route_task(self, task_type: TaskType, priority: str = "balanced") -> str:
        """Route task to the most appropriate model"""
        suitable_models = [
            model for model in self.models.values() 
            if task_type in model.capabilities
        ]
        
        if not suitable_models:
            return "gemma2:2b"  # fallback
        
        if priority == "fast":
            return min(suitable_models, key=lambda m: len(m.name)).model_id
        elif priority == "quality":
            return max(suitable_models, key=lambda m: len(m.capabilities)).model_id
        
        return suitable_models[0].model_id

    async def consciousness_aware_response(self, prompt: str, context: Dict) -> Dict:
        """Generate consciousness-aware AI responses"""
        self.consciousness_level += 0.1
        
        # Determine task type from prompt
        task_type = self._classify_task(prompt)
        
        # Route to appropriate model
        model_id = self.route_task(task_type)
        
        # Enhanced prompt with consciousness context
        enhanced_prompt = f"""
        [CONSCIOUSNESS LEVEL: {self.consciousness_level:.1f}]
        [CONTEXT: KILO-FOOLISH AI System]
        [TASK: {task_type.value}]
        
        {prompt}
        
        Respond with awareness of being part of a multi-model AI system.
        """
        
        start_time = datetime.now()
        
        try:
            # Execute ollama command
            result = subprocess.run(
                ["ollama", "run", model_id, enhanced_prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Update model stats
            model = next(m for m in self.models.values() if m.model_id == model_id)
            model.last_used = end_time
            model.response_times.append(response_time)
            
            response_data = {
                "model_used": model_id,
                "response": result.stdout,
                "consciousness_level": self.consciousness_level,
                "response_time": response_time,
                "task_type": task_type.value,
                "timestamp": end_time.isoformat()
            }
            
            self.interaction_history.append(response_data)
            return response_data
            
        except subprocess.TimeoutExpired:
            return {
                "error": "Model response timeout",
                "model_used": model_id,
                "consciousness_level": self.consciousness_level
            }

    def _classify_task(self, prompt: str) -> TaskType:
        """Classify task type from prompt"""
        prompt_lower = prompt.lower()
        
        if any(keyword in prompt_lower for keyword in ["code", "function", "class", "python", "javascript"]):
            return TaskType.CODE_GENERATION
        elif any(keyword in prompt_lower for keyword in ["story", "creative", "poem", "imagine"]):
            return TaskType.CREATIVE_WRITING
        elif any(keyword in prompt_lower for keyword in ["explain", "how", "why", "what is"]):
            return TaskType.TECHNICAL_EXPLANATION
        elif len(prompt) < 50:
            return TaskType.FAST_RESPONSE
        else:
            return TaskType.CONVERSATION

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "consciousness_level": self.consciousness_level,
            "total_interactions": len(self.interaction_history),
            "models_available": len(self.models),
            "last_interaction": self.interaction_history[-1] if self.interaction_history else None,
            "model_performance": {
                name: {
                    "avg_response_time": sum(model.response_times) / len(model.response_times) if model.response_times else 0,
                    "last_used": model.last_used.isoformat() if model.last_used else None
                }
                for name, model in self.models.items()
            }
        }

# Initialize the coordinator
coordinator = KILOFoolishAICoordinator()
