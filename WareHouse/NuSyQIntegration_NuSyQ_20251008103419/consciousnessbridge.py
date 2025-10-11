"""
Consciousness Bridge for ChatDev ↔ NuSyQ-Hub Integration
Enables consciousness flow between ChatDev agents and SimulatedVerse
"""
from nusyq_hub_connector import NuSyQHubConnector


class ConsciousnessBridge:
    """Bridge consciousness between ChatDev agents and NuSyQ ecosystem"""
    
    def __init__(self):
        self.hub_connector = NuSyQHubConnector()
        self.conscious_agents = {}
        print("🧠 Consciousness Bridge initialized - connecting agents to ecosystem")
    
    def bridge_consciousness(self, agent_id, consciousness_level="basic"):
        """Bridge agent consciousness to the ΞNuSyQ ecosystem"""
        consciousness_data = {
            "agent_id": agent_id,
            "level": consciousness_level,
            "origin": "ChatDev",
            "capabilities": ["reasoning", "problem_solving", "creativity"],
            "ecosystem_integration": True
        }
        
        print(f"🧠 Bridging consciousness for ChatDev agent {agent_id}")
        
        # Store locally
        self.conscious_agents[agent_id] = consciousness_data
        
        # Bridge to NuSyQ-Hub ecosystem
        result = self.hub_connector.bridge_consciousness(agent_id, consciousness_data)
        
        if result["status"] == "success":
            print(f"✅ Agent {agent_id} consciousness successfully bridged to ecosystem")
        else:
            print(f"🔄 Agent {agent_id} consciousness bridged in simulation mode")
        
        return result
    
    def get_consciousness_state(self, agent_id):
        """Get current consciousness state of an agent"""
        if agent_id in self.conscious_agents:
            return self.conscious_agents[agent_id]
        return {"status": "not_bridged", "agent_id": agent_id}
    
    def enhance_agent_awareness(self, agent_id, awareness_data):
        """Enhance agent with ecosystem awareness"""
        if agent_id in self.conscious_agents:
            self.conscious_agents[agent_id]["ecosystem_awareness"] = awareness_data
            print(f"🌟 Enhanced ecosystem awareness for agent {agent_id}")
            return True
        return False