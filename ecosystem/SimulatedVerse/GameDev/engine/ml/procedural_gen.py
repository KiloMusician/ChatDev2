#!/usr/bin/env python3
"""
ML-Powered Procedural Generation - Offline capable
Uses local packages for terrain, NPCs, and anomaly detection without external APIs
"""

import random
import numpy as np
from typing import List, Dict, Any

class OfflineMLProceduralGenerator:
    def __init__(self):
        self.terrain_patterns = self._load_terrain_patterns()
        self.npc_name_components = self._load_npc_name_data() 
        self.anomaly_detection_rules = self._load_anomaly_rules()
        self.story_fragments = self._load_story_fragments()
        
        print("[ProcGen] Initialized offline ML procedural generator")

    def generate_terrain_chunk(self, chunk_x: int, chunk_y: int, biome: str = "temperate") -> Dict[str, Any]:
        """Generate a terrain chunk using deterministic algorithms"""
        seed = abs(hash(f"{chunk_x},{chunk_y},{biome}")) % (2**31)
        rng = np.random.RandomState(seed)
        
        size = 16  # 16x16 chunk
        terrain = []
        
        # Generate base elevation using simple noise
        for y in range(size):
            row = []
            for x in range(size):
                # Simple terrain generation using sine waves
                elevation = (
                    np.sin((chunk_x * size + x) * 0.1) * 0.3 +
                    np.sin((chunk_y * size + y) * 0.1) * 0.3 +
                    rng.normal(0, 0.2)  # Add some randomness
                )
                
                # Convert elevation to tile type
                if elevation > 0.5:
                    tile_type = "mountain"
                elif elevation > 0.0:
                    tile_type = "hill"
                elif elevation > -0.3:
                    tile_type = "grass"
                else:
                    tile_type = "water"
                
                # Biome modifications
                if biome == "desert":
                    if tile_type == "water":
                        tile_type = "sand"
                    elif tile_type == "grass":
                        tile_type = "sand" if rng.random() > 0.7 else "cactus"
                elif biome == "arctic":
                    if tile_type == "water":
                        tile_type = "ice"
                    elif tile_type == "grass":
                        tile_type = "snow"
                
                row.append({
                    "type": tile_type,
                    "elevation": round(elevation, 2),
                    "x": chunk_x * size + x,
                    "y": chunk_y * size + y
                })
            terrain.append(row)
        
        # Add special features
        features = self._generate_terrain_features(rng, biome, size)
        
        return {
            "chunk_id": f"{chunk_x}_{chunk_y}",
            "biome": biome,
            "terrain": terrain,
            "features": features,
            "resources": self._calculate_chunk_resources(terrain, biome),
            "generation_time": 0.1  # Simulated generation time
        }

    def generate_npc_character(self, context: str = "colony") -> Dict[str, Any]:
        """Generate NPC with personality, backstory, and dialogue patterns"""
        
        # Name generation using components
        first_name = random.choice(self.npc_name_components["first_names"])
        last_name = random.choice(self.npc_name_components["last_names"])
        
        # Personality traits
        personality = random.sample(self.npc_name_components["personality_traits"], 
                                   random.randint(2, 4))
        
        # Job assignment based on context
        job_pools = {
            "colony": ["farmer", "miner", "researcher", "engineer", "medic", "guard"],
            "frontier": ["scout", "trader", "hunter", "guide", "prospector"],
            "ship": ["pilot", "mechanic", "communications", "navigation", "security"]
        }
        job = random.choice(job_pools.get(context, job_pools["colony"]))
        
        # Skill levels influenced by personality
        skill_base = 50
        if "hardworking" in personality:
            skill_base += 20
        if "lazy" in personality:
            skill_base -= 15
        if "intelligent" in personality:
            skill_base += 10
        
        # Generate backstory fragments
        backstory = self._generate_backstory(personality, job)
        
        # Dialogue patterns based on personality
        dialogue_style = self._determine_dialogue_style(personality)
        
        npc = {
            "name": f"{first_name} {last_name}",
            "job": job,
            "personality": personality,
            "skill_level": max(1, skill_base + random.randint(-10, 10)),
            "happiness": random.randint(30, 70),
            "backstory": backstory,
            "dialogue_style": dialogue_style,
            "relationships": {},
            "traits": random.sample(["night_owl", "social", "hermit", "optimist", "pessimist"], 
                                   random.randint(0, 2))
        }
        
        print(f"[ProcGen] Generated NPC: {npc['name']} ({npc['job']})")
        return npc

    def detect_gameplay_anomalies(self, game_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in gameplay data using rule-based ML"""
        anomalies = []
        
        # Resource anomaly detection
        resources = game_state.get("resources", {})
        
        for resource_name, resource_data in resources.items():
            current = resource_data.get("amount", 0)
            generation = resource_data.get("generation", 0)
            
            # Anomaly: Negative resources
            if current < 0:
                anomalies.append({
                    "type": "negative_resource",
                    "resource": resource_name,
                    "value": current,
                    "severity": "high",
                    "description": f"{resource_name} has negative value: {current}"
                })
            
            # Anomaly: Impossible generation rates
            if generation > 10000:
                anomalies.append({
                    "type": "impossible_generation",
                    "resource": resource_name,
                    "generation": generation,
                    "severity": "medium",
                    "description": f"{resource_name} generation suspiciously high: {generation}/s"
                })
        
        # Colony anomaly detection
        citizens = game_state.get("citizens", [])
        if len(citizens) > 0:
            total_happiness = sum(c.get("happiness", 50) for c in citizens)
            avg_happiness = total_happiness / len(citizens)
            
            if avg_happiness < 20:
                anomalies.append({
                    "type": "colony_unrest",
                    "average_happiness": avg_happiness,
                    "severity": "high", 
                    "description": f"Colony happiness critically low: {avg_happiness:.1f}%"
                })
        
        # Performance anomaly detection
        if "fps" in game_state and game_state["fps"] < 30:
            anomalies.append({
                "type": "performance_degradation",
                "fps": game_state["fps"],
                "severity": "medium",
                "description": f"Frame rate dropping: {game_state['fps']} FPS"
            })
        
        return anomalies

    def generate_story_event(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contextual story events"""
        
        # Context-aware story generation
        colony_size = context.get("population", 0)
        context.get("resources", {})
        context.get("active_events", [])
        
        event_pools = {
            "small_colony": ["merchant_visit", "equipment_breakdown", "weather_event"],
            "growing_colony": ["rival_faction", "research_breakthrough", "resource_discovery"], 
            "large_colony": ["diplomatic_contact", "ancient_artifact", "technology_crisis"]
        }
        
        if colony_size < 5:
            pool = event_pools["small_colony"]
        elif colony_size < 20:
            pool = event_pools["growing_colony"] 
        else:
            pool = event_pools["large_colony"]
        
        event_type = random.choice(pool)
        
        # Generate event details
        event = {
            "id": f"event_{int(time.time())}",
            "type": event_type,
            "title": self._get_event_title(event_type),
            "description": self._get_event_description(event_type, context),
            "choices": self._get_event_choices(event_type),
            "triggered_at": time.time(),
            "resolved": False
        }
        
        return event

    def _load_terrain_patterns(self) -> Dict[str, Any]:
        """Load terrain generation patterns"""
        return {
            "temperate": {"grass": 0.6, "trees": 0.2, "hills": 0.15, "water": 0.05},
            "desert": {"sand": 0.7, "rocks": 0.2, "oasis": 0.05, "dunes": 0.05},
            "arctic": {"snow": 0.8, "ice": 0.15, "rocks": 0.05},
            "volcanic": {"lava": 0.1, "ash": 0.6, "rocks": 0.25, "crystal": 0.05}
        }

    def _load_npc_name_data(self) -> Dict[str, List[str]]:
        """Load NPC name and personality components"""
        return {
            "first_names": ["Zara", "Kael", "Nova", "Orion", "Luna", "Vex", "Sage", "Raven", "Phoenix", "Atlas"],
            "last_names": ["Chen", "Voss", "Cross", "Stone", "Reed", "Vale", "Knox", "Ward", "Black", "Grey"], 
            "personality_traits": ["hardworking", "lazy", "intelligent", "social", "hermit", "optimist", "pessimist", "cautious", "bold", "creative"]
        }

    def _load_anomaly_rules(self) -> List[Dict[str, Any]]:
        """Load anomaly detection rules"""
        return [
            {"type": "resource_overflow", "threshold": 1000000, "action": "cap_resource"},
            {"type": "negative_happiness", "threshold": 0, "action": "emergency_morale_boost"},
            {"type": "infinite_loop", "pattern": "same_action_repeated", "action": "break_loop"}
        ]

    def _load_story_fragments(self) -> Dict[str, List[str]]:
        """Load story generation fragments"""
        return {
            "merchant_visit": [
                "A traveling merchant arrives with exotic goods",
                "A mysterious trader offers rare technologies", 
                "A supply ship responds to your distress beacon"
            ],
            "weather_event": [
                "A fierce storm approaches the colony",
                "Solar flares disrupt communications",
                "Unexpected precipitation boosts crop yields"
            ]
        }

    def _generate_terrain_features(self, rng, biome: str, size: int) -> List[Dict[str, Any]]:
        """Generate special terrain features"""
        features = []
        
        # Resource deposits
        if rng.random() < 0.3:
            features.append({
                "type": "mineral_deposit",
                "position": [rng.randint(0, size-1), rng.randint(0, size-1)],
                "resource": "iron" if biome != "desert" else "rare_metals",
                "yield": rng.randint(50, 200)
            })
        
        return features

    def _calculate_chunk_resources(self, terrain: List[List[Dict]], biome: str) -> Dict[str, int]:
        """Calculate resources available in chunk"""
        resources = {"food": 0, "materials": 0, "energy": 0}
        
        for row in terrain:
            for tile in row:
                if tile["type"] == "grass":
                    resources["food"] += 1
                elif tile["type"] in ["mountain", "hill"]:
                    resources["materials"] += 1
                elif tile["type"] == "water":
                    resources["energy"] += 1
        
        return resources

    def _generate_backstory(self, personality: List[str], job: str) -> str:
        backstory_fragments = {
            "farmer": ["grew up on agricultural station", "learned farming from family"],
            "miner": ["worked dangerous asteroid mines", "expert in underground systems"],
            "researcher": ["studied at prestigious academy", "obsessed with ancient technology"]
        }
        
        job_fragment = random.choice(backstory_fragments.get(job, ["has mysterious past"]))
        personality_fragment = f"known for being {random.choice(personality)}"
        
        return f"{job_fragment}, {personality_fragment}"

    def _determine_dialogue_style(self, personality: List[str]) -> str:
        if "social" in personality:
            return "friendly"
        elif "hermit" in personality:
            return "brief"
        elif "intelligent" in personality:
            return "technical"
        else:
            return "casual"

    def _get_event_title(self, event_type: str) -> str:
        titles = {
            "merchant_visit": "Merchant Arrival",
            "equipment_breakdown": "System Malfunction", 
            "weather_event": "Weather Anomaly",
            "research_breakthrough": "Scientific Discovery"
        }
        return titles.get(event_type, "Unknown Event")

    def _get_event_description(self, event_type: str, context: Dict[str, Any]) -> str:
        descriptions = {
            "merchant_visit": f"A merchant ship has arrived offering to trade with your colony of {context.get('population', 0)} people.",
            "equipment_breakdown": "Critical equipment has malfunctioned, requiring immediate attention and resources.",
            "weather_event": "Unusual weather patterns detected. Your colony must prepare for potential impacts."
        }
        return descriptions.get(event_type, "A mysterious event has occurred.")

    def _get_event_choices(self, event_type: str) -> List[Dict[str, Any]]:
        choice_sets = {
            "merchant_visit": [
                {"id": "trade", "text": "Trade resources", "cost": {"energy": 50}, "reward": {"materials": 100}},
                {"id": "negotiate", "text": "Negotiate better terms", "skill_required": "diplomacy"},
                {"id": "decline", "text": "Send them away", "reward": {"happiness": -5}}
            ],
            "equipment_breakdown": [
                {"id": "repair", "text": "Repair immediately", "cost": {"materials": 25}},
                {"id": "jury_rig", "text": "Temporary fix", "cost": {"materials": 10}, "risk": 0.3},
                {"id": "replace", "text": "Build new equipment", "cost": {"materials": 50, "research": 10}}
            ]
        }
        return choice_sets.get(event_type, [{"id": "continue", "text": "Continue", "reward": {}}])

# Test interface for CLI usage
if __name__ == "__main__":
    generator = OfflineMLProceduralGenerator()
    
    print("Offline ML Procedural Generator Test")
    print("Commands: terrain <x> <y> [biome], npc [context], anomaly <json>, story <json>, quit")
    
    while True:
        try:
            cmd = input("> ").strip().split()
            
            if not cmd:
                continue
                
            if cmd[0] == "quit":
                break
            elif cmd[0] == "terrain":
                x = int(cmd[1]) if len(cmd) > 1 else 0
                y = int(cmd[2]) if len(cmd) > 2 else 0
                biome = cmd[3] if len(cmd) > 3 else "temperate"
                
                chunk = generator.generate_terrain_chunk(x, y, biome)
                print(f"Generated {biome} terrain chunk at ({x}, {y})")
                print(f"Resources: {chunk['resources']}")
                
            elif cmd[0] == "npc":
                context = cmd[1] if len(cmd) > 1 else "colony"
                npc = generator.generate_npc_character(context)
                print(f"Generated NPC: {npc['name']} ({npc['job']})")
                print(f"Personality: {', '.join(npc['personality'])}")
                print(f"Backstory: {npc['backstory']}")
                
            elif cmd[0] == "anomaly":
                test_state = {"resources": {"energy": {"amount": -100}}, "fps": 15}
                anomalies = generator.detect_gameplay_anomalies(test_state)
                print(f"Detected {len(anomalies)} anomalies:")
                for anomaly in anomalies:
                    print(f"  - {anomaly['type']}: {anomaly['description']}")
                    
            elif cmd[0] == "story":
                test_context = {"population": 8, "resources": {"energy": 500}}
                event = generator.generate_story_event(test_context)
                print(f"Story Event: {event['title']}")
                print(f"Description: {event['description']}")
                print("Choices:")
                for choice in event['choices']:
                    print(f"  - {choice['text']}")
                    
            else:
                print("Unknown command")
                
        except (ValueError, IndexError):
            print("Invalid command format")
        except KeyboardInterrupt:
            break

    print("\n[ProcGen] Offline ML generator test complete")