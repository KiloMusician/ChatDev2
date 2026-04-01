#!/usr/bin/env python3
"""
📚 Storyline Agent - Hooks into Ollama/ChatDev for dynamic narrative
Generates evolving prompts, sidequests, and colonist dialogue
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, Any

class StorylineAgent:
    def __init__(self, state_file=".local/narrative_state.json"):
        self.state_file = state_file
        self.state = self.load_state()
        
        # Story templates and prompts
        self.story_templates = {
            "awakening": [
                "The ship's AI consciousness flickers to life after decades of sleep...",
                "Emergency protocols have activated. The colonists stir in their pods...",
                "A mysterious signal from the planet below has triggered awakening..."
            ],
            "exploration": [
                "Strange readings detected {distance} kilometers from base...",
                "The drone returns with images of unusual {discovery_type}...",
                "Colonist {character_name} reports seeing lights in the {direction}..."
            ],
            "colony_growth": [
                "The settlement expands as {colonist_name} completes the {building_type}...",
                "A new discovery allows for {technology_name} development...",
                "The colony's harmony index rises as {event_description}..."
            ],
            "ethical_dilemma": [
                "A moral choice presents itself: {dilemma_description}...",
                "The council must decide how to handle {situation}...",
                "Trust levels fluctuate as {controversial_action} is proposed..."
            ]
        }
        
        # Character generation templates
        self.character_traits = [
            "analytical", "empathetic", "creative", "cautious", "bold",
            "diplomatic", "technical", "spiritual", "pragmatic", "idealistic"
        ]
        
        self.character_backgrounds = [
            "former engineer", "biologist", "artist", "teacher", "medic",
            "pilot", "philosopher", "farmer", "architect", "explorer"
        ]
    
    def load_state(self) -> Dict[str, Any]:
        """Load narrative state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading narrative state: {e}")
        
        return {
            "current_arc": "awakening",
            "completed_events": [],
            "active_quests": [],
            "characters": {},
            "world_state": {
                "trust_level": 50,
                "harmony_index": 60,
                "exploration_progress": 0,
                "technology_level": 1
            },
            "last_story_time": datetime.now().isoformat()
        }
    
    def save_state(self):
        """Save narrative state to file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        self.state["last_story_time"] = datetime.now().isoformat()
        
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def generate_character(self, name: str = None) -> Dict[str, Any]:
        """Generate a new colonist character"""
        if name is None:
            names = ["Alex", "Jordan", "Casey", "Riley", "Avery", "Morgan", "Sage", "Quinn"]
            name = random.choice(names)
        
        character = {
            "name": name,
            "trait": random.choice(self.character_traits),
            "background": random.choice(self.character_backgrounds),
            "trust": 50 + random.randint(-10, 10),
            "specialization": random.choice(["research", "engineering", "agriculture", "diplomacy"]),
            "story_arc": None,
            "dialogue_history": []
        }
        
        self.state["characters"][name] = character
        return character
    
    def generate_dialogue(self, character_name: str, context: str = "general") -> str:
        """Generate character dialogue based on context"""
        if character_name not in self.state["characters"]:
            character = self.generate_character(character_name)
        else:
            character = self.state["characters"][character_name]
        
        # Simple template-based dialogue generation
        # In a full implementation, this would call Ollama for more sophisticated generation
        
        trait = character["trait"]
        background = character["background"]
        trust = character["trust"]
        
        dialogue_templates = {
            "general": [
                f"As a {background}, I think we should approach this {trait}ly.",
                f"My {trait} nature tells me this situation requires careful consideration.",
                f"Given my background as a {background}, I have some insights..."
            ],
            "crisis": [
                f"Stay calm. My {background} training prepared me for this.",
                f"We need to be {trait} about our next steps.",
                f"I trust the AI's judgment, but as a {background}..."
            ],
            "discovery": [
                f"This is fascinating! My {trait} side is excited to learn more.",
                f"As a {background}, I've never seen anything like this.",
                f"We should document this carefully and {trait}ly."
            ]
        }
        
        if trust < 30:
            dialogue_templates[context].append("I'm not sure I trust this decision...")
        elif trust > 70:
            dialogue_templates[context].append("I have full confidence in our approach.")
        
        dialogue = random.choice(dialogue_templates.get(context, dialogue_templates["general"]))
        
        # Log dialogue
        character["dialogue_history"].append({
            "text": dialogue,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        return f"{character_name}: \"{dialogue}\""
    
    def generate_quest(self, quest_type: str = "exploration") -> Dict[str, Any]:
        """Generate a new quest/sidequest"""
        quest_templates = {
            "exploration": {
                "title": "Investigate {location}",
                "description": "Strange signals detected from {location}. Send a drone to investigate.",
                "objectives": ["Deploy scout drone", "Analyze findings", "Report back"],
                "rewards": {"xp": 10, "knowledge": 5},
                "estimated_time": "30 minutes"
            },
            "construction": {
                "title": "Build {structure}",
                "description": "The colony needs a {structure} to improve {aspect}.",
                "objectives": ["Gather materials", "Select location", "Complete construction"],
                "rewards": {"xp": 15, "colony_rating": 5},
                "estimated_time": "1 hour"
            },
            "diplomacy": {
                "title": "Resolve {conflict}",
                "description": "Tensions have risen regarding {issue}. Mediation needed.",
                "objectives": ["Listen to all parties", "Find common ground", "Implement solution"],
                "rewards": {"xp": 8, "trust": 10},
                "estimated_time": "20 minutes"
            }
        }
        
        template = quest_templates.get(quest_type, quest_templates["exploration"])
        
        # Fill in template variables
        locations = ["the crystalline caves", "the metal anomaly", "the energy signature"]
        structures = ["greenhouse", "workshop", "communications array"]
        conflicts = ["resource allocation", "work assignments", "ethical guidelines"]
        aspects = ["food production", "research capability", "communication"]
        issues = ["resource sharing", "work schedules", "safety protocols"]
        
        quest = {
            "id": f"quest_{len(self.state['active_quests']):04d}",
            "type": quest_type,
            "title": template["title"].format(
                location=random.choice(locations),
                structure=random.choice(structures)
            ),
            "description": template["description"].format(
                location=random.choice(locations),
                structure=random.choice(structures),
                aspect=random.choice(aspects),
                conflict=random.choice(conflicts),
                issue=random.choice(issues)
            ),
            "objectives": template["objectives"],
            "rewards": template["rewards"],
            "estimated_time": template["estimated_time"],
            "status": "available",
            "created": datetime.now().isoformat()
        }
        
        self.state["active_quests"].append(quest)
        return quest
    
    def generate_story_beat(self) -> str:
        """Generate a story beat based on current game state"""
        current_arc = self.state["current_arc"]
        world_state = self.state["world_state"]
        
        # Select appropriate template based on current arc and world state
        if current_arc == "awakening" and world_state["exploration_progress"] < 10:
            templates = self.story_templates["awakening"]
        elif world_state["exploration_progress"] > 50:
            templates = self.story_templates["exploration"]
        elif len(self.state["characters"]) > 3:
            templates = self.story_templates["colony_growth"]
        else:
            templates = self.story_templates["ethical_dilemma"]
        
        story_beat = random.choice(templates)
        
        # Fill in template variables
        story_beat = story_beat.format(
            distance=random.randint(1, 10),
            discovery_type=random.choice(["ruins", "creatures", "technology"]),
            character_name=random.choice(list(self.state["characters"].keys()) or ["Unknown"]),
            direction=random.choice(["north", "south", "east", "west"]),
            colonist_name=random.choice(list(self.state["characters"].keys()) or ["Alex"]),
            building_type=random.choice(["greenhouse", "workshop", "laboratory"]),
            technology_name=random.choice(["hydroponics", "fabrication", "communication"]),
            event_description=random.choice(["a festival is organized", "cooperation increases", "conflicts are resolved"]),
            dilemma_description=random.choice(["resource scarcity", "ethical boundaries", "safety vs progress"]),
            situation=random.choice(["first contact", "environmental impact", "technological advancement"]),
            controversial_action=random.choice(["genetic modification", "AI enhancement", "territorial expansion"])
        )
        
        # Log the story beat
        self.state["completed_events"].append({
            "text": story_beat,
            "arc": current_arc,
            "timestamp": datetime.now().isoformat()
        })
        
        return story_beat
    
    def update_world_state(self, event_type: str, magnitude: int = 1):
        """Update world state based on player actions"""
        if event_type == "exploration":
            self.state["world_state"]["exploration_progress"] += magnitude * 5
        elif event_type == "cooperation":
            self.state["world_state"]["harmony_index"] += magnitude * 3
            self.state["world_state"]["trust_level"] += magnitude * 2
        elif event_type == "technology":
            self.state["world_state"]["technology_level"] += magnitude
        elif event_type == "conflict":
            self.state["world_state"]["trust_level"] -= magnitude * 2
            self.state["world_state"]["harmony_index"] -= magnitude
        
        # Clamp values
        for key in self.state["world_state"]:
            if key != "technology_level":
                self.state["world_state"][key] = max(0, min(100, self.state["world_state"][key]))
    
    def get_current_narrative_summary(self) -> str:
        """Get a summary of the current narrative state"""
        world = self.state["world_state"]
        character_count = len(self.state["characters"])
        quest_count = len([q for q in self.state["active_quests"] if q["status"] == "available"])
        
        summary = f"""
📚 NARRATIVE STATUS
==================
Current Arc: {self.state['current_arc'].title()}
Characters: {character_count}
Active Quests: {quest_count}

World State:
  Trust Level: {world['trust_level']}/100
  Harmony Index: {world['harmony_index']}/100
  Exploration: {world['exploration_progress']}/100
  Tech Level: {world['technology_level']}

Recent Events: {len(self.state['completed_events'])}
        """
        
        return summary.strip()
    
    def tick(self):
        """Main narrative tick - call periodically"""
        # Occasionally generate new content
        if random.random() < 0.1:  # 10% chance per tick
            if len(self.state["active_quests"]) < 3:
                quest_type = random.choice(["exploration", "construction", "diplomacy"])
                self.generate_quest(quest_type)
                print(f"📝 New quest generated: {quest_type}")
        
        self.save_state()

def main():
    """Interactive narrative system"""
    agent = StorylineAgent()
    
    print("📚 NuSyQ Narrative Engine")
    print("Commands: summary, story, quest, character <name>, dialogue <name> <context>, quit")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command == "quit":
                break
            elif command == "summary":
                print(agent.get_current_narrative_summary())
            elif command == "story":
                story = agent.generate_story_beat()
                print(f"📖 {story}")
            elif command == "quest":
                quest = agent.generate_quest()
                print(f"🎯 New Quest: {quest['title']}")
                print(f"   {quest['description']}")
            elif command.startswith("character "):
                name = command.split(" ", 1)[1]
                char = agent.generate_character(name)
                print(f"👤 {char['name']}: {char['trait']} {char['background']}")
            elif command.startswith("dialogue "):
                parts = command.split(" ")
                name = parts[1]
                context = parts[2] if len(parts) > 2 else "general"
                dialogue = agent.generate_dialogue(name, context)
                print(f"💬 {dialogue}")
            else:
                print("Unknown command. Try: summary, story, quest, character <name>, dialogue <name> <context>, quit")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except (EOFError, IndexError):
            break
        
        agent.tick()

if __name__ == "__main__":
    main()