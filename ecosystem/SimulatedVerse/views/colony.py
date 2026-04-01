#!/usr/bin/env python3
"""
🏘️ Colony Module - RimWorld/Kenshi-style colony building
Manages colonist AI routines, building, and colony management
"""

import json
import os
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class JobType(Enum):
    IDLE = "idle"
    HAUL = "haul"
    BUILD = "build"
    RESEARCH = "research"
    CRAFT = "craft"
    FARM = "farm"
    COOK = "cook"
    CLEAN = "clean"
    GUARD = "guard"
    REPAIR = "repair"

class BuildingType(Enum):
    SHELTER = "shelter"
    WORKSHOP = "workshop"
    GREENHOUSE = "greenhouse"
    STORAGE = "storage"
    LABORATORY = "laboratory"
    KITCHEN = "kitchen"
    INFIRMARY = "infirmary"
    POWER_PLANT = "power_plant"
    COMMUNICATIONS = "communications"

@dataclass
class Colonist:
    name: str
    id: str
    x: int = 5
    y: int = 5
    job: JobType = JobType.IDLE
    skill_levels: Dict[str, int] = None
    traits: List[str] = None
    mood: int = 50  # 0-100
    health: int = 100
    energy: int = 100
    job_progress: float = 0.0
    job_target: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.skill_levels is None:
            self.skill_levels = {
                "construction": random.randint(1, 5),
                "research": random.randint(1, 5),
                "cooking": random.randint(1, 5),
                "farming": random.randint(1, 5),
                "crafting": random.randint(1, 5),
                "medical": random.randint(1, 5)
            }
        if self.traits is None:
            trait_pool = [
                "hard_worker", "creative", "patient", "social", "focused",
                "optimistic", "analytical", "empathetic", "resilient", "curious"
            ]
            self.traits = random.sample(trait_pool, random.randint(1, 3))

@dataclass
class Building:
    building_type: BuildingType
    x: int
    y: int
    width: int = 2
    height: int = 2
    integrity: int = 100
    power_consumption: int = 0
    construction_progress: float = 1.0  # 0.0 to 1.0
    active: bool = True

@dataclass
class ColonyState:
    colonists: List[Colonist]
    buildings: List[Building]
    resources: Dict[str, int]
    colony_mood: int = 60
    research_points: int = 0
    power_generation: int = 100
    power_consumption: int = 0
    day: int = 1
    time_of_day: float = 8.0  # 0-24 hours

class ColonyEngine:
    def __init__(self, state_file=".local/colony_state.json"):
        self.state_file = state_file
        self.map_width = 20
        self.map_height = 15
        
        # Initialize or load state
        self.state = self.load_state()
        
        # Job scheduling and work queues
        self.work_queue = []
        self.priority_jobs = []
    
    def load_state(self) -> ColonyState:
        """Load colony state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return ColonyState(
                        colonists=[Colonist(**c) for c in data.get('colonists', [])],
                        buildings=[Building(**b) for b in data.get('buildings', [])],
                        resources=data.get('resources', {}),
                        colony_mood=data.get('colony_mood', 60),
                        research_points=data.get('research_points', 0),
                        power_generation=data.get('power_generation', 100),
                        power_consumption=data.get('power_consumption', 0),
                        day=data.get('day', 1),
                        time_of_day=data.get('time_of_day', 8.0)
                    )
            except Exception as e:
                print(f"⚠️  Error loading colony state: {e}")
        
        # Create initial state
        return self.create_initial_colony()
    
    def create_initial_colony(self) -> ColonyState:
        """Create a new colony with basic setup"""
        # Create initial colonists
        colonists = [
            Colonist(name="Alex", id="col_001", x=5, y=5),
            Colonist(name="Blake", id="col_002", x=6, y=5),
            Colonist(name="Casey", id="col_003", x=7, y=5)
        ]
        
        # Create initial buildings
        buildings = [
            Building(BuildingType.SHELTER, x=5, y=6, width=3, height=2),
            Building(BuildingType.STORAGE, x=9, y=6, width=2, height=2),
            Building(BuildingType.POWER_PLANT, x=12, y=6, width=2, height=2)
        ]
        
        # Initial resources
        resources = {
            "food": 50,
            "materials": 100,
            "energy": 150,
            "water": 80,
            "research_data": 0,
            "tools": 10
        }
        
        return ColonyState(
            colonists=colonists,
            buildings=buildings,
            resources=resources
        )
    
    def save_state(self):
        """Save colony state to file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        data = {
            'colonists': [asdict(c) for c in self.state.colonists],
            'buildings': [asdict(b) for b in self.state.buildings],
            'resources': self.state.resources,
            'colony_mood': self.state.colony_mood,
            'research_points': self.state.research_points,
            'power_generation': self.state.power_generation,
            'power_consumption': self.state.power_consumption,
            'day': self.state.day,
            'time_of_day': self.state.time_of_day
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def assign_job(self, colonist_id: str, job_type: JobType, target_pos: Optional[Tuple[int, int]] = None) -> bool:
        """Assign a job to a colonist"""
        colonist = next((c for c in self.state.colonists if c.id == colonist_id), None)
        if not colonist:
            return False
        
        colonist.job = job_type
        colonist.job_progress = 0.0
        colonist.job_target = target_pos
        
        print(f"👤 {colonist.name} assigned to {job_type.value}")
        return True
    
    def auto_assign_jobs(self):
        """Automatically assign jobs based on colony needs"""
        idle_colonists = [c for c in self.state.colonists if c.job == JobType.IDLE and c.energy > 20]
        
        if not idle_colonists:
            return
        
        # Prioritize essential needs
        needs = self.assess_colony_needs()
        
        for need in needs[:len(idle_colonists)]:
            colonist = self.select_best_colonist_for_job(idle_colonists, need["job"])
            if colonist:
                self.assign_job(colonist.id, need["job"], need.get("target"))
                idle_colonists.remove(colonist)
    
    def assess_colony_needs(self) -> List[Dict]:
        """Assess what the colony needs most urgently"""
        needs = []
        
        # Food shortage
        if self.state.resources.get("food", 0) < 20:
            needs.append({"job": JobType.FARM, "priority": 10})
        
        # Power shortage
        if self.state.power_generation < self.state.power_consumption:
            needs.append({"job": JobType.REPAIR, "priority": 9, "target": (12, 6)})
        
        # Research opportunities
        if self.state.resources.get("research_data", 0) > 10:
            needs.append({"job": JobType.RESEARCH, "priority": 6})
        
        # Construction needed
        unfinished_buildings = [b for b in self.state.buildings if b.construction_progress < 1.0]
        if unfinished_buildings:
            building = unfinished_buildings[0]
            needs.append({
                "job": JobType.BUILD, 
                "priority": 8, 
                "target": (building.x, building.y)
            })
        
        # Cleaning and maintenance
        if random.random() < 0.3:  # 30% chance per tick
            needs.append({"job": JobType.CLEAN, "priority": 3})
        
        # Sort by priority
        needs.sort(key=lambda x: x["priority"], reverse=True)
        return needs
    
    def select_best_colonist_for_job(self, available_colonists: List[Colonist], job_type: JobType) -> Optional[Colonist]:
        """Select the best colonist for a specific job"""
        if not available_colonists:
            return None
        
        # Map job types to relevant skills
        job_skill_map = {
            JobType.BUILD: "construction",
            JobType.RESEARCH: "research", 
            JobType.FARM: "farming",
            JobType.COOK: "cooking",
            JobType.CRAFT: "crafting",
            JobType.REPAIR: "construction"
        }
        
        relevant_skill = job_skill_map.get(job_type)
        
        if relevant_skill:
            # Select colonist with highest relevant skill
            return max(available_colonists, key=lambda c: c.skill_levels.get(relevant_skill, 0))
        else:
            # For general jobs, select colonist with highest energy
            return max(available_colonists, key=lambda c: c.energy)
    
    def update_colonist_work(self, colonist: Colonist, delta_time: float = 1.0):
        """Update a colonist's work progress"""
        if colonist.job == JobType.IDLE:
            # Rest and recover energy
            colonist.energy = min(100, colonist.energy + delta_time * 2)
            return
        
        if colonist.energy <= 0:
            print(f"💤 {colonist.name} is too tired to work")
            colonist.job = JobType.IDLE
            return
        
        # Work efficiency based on skill and mood
        relevant_skill = self.get_relevant_skill(colonist.job)
        skill_level = colonist.skill_levels.get(relevant_skill, 1)
        mood_modifier = 0.5 + (colonist.mood / 100.0)  # 0.5x to 1.5x based on mood
        
        work_rate = (skill_level / 5.0) * mood_modifier * delta_time
        
        # Apply work progress
        colonist.job_progress += work_rate * 0.1  # Base progress rate
        colonist.energy -= delta_time * 1.5  # Energy consumption
        
        # Check if job is completed
        if colonist.job_progress >= 1.0:
            self.complete_job(colonist)
    
    def get_relevant_skill(self, job_type: JobType) -> str:
        """Get the relevant skill for a job type"""
        skill_map = {
            JobType.BUILD: "construction",
            JobType.RESEARCH: "research",
            JobType.FARM: "farming", 
            JobType.COOK: "cooking",
            JobType.CRAFT: "crafting",
            JobType.REPAIR: "construction",
            JobType.CLEAN: "construction"  # General skill
        }
        return skill_map.get(job_type, "construction")
    
    def complete_job(self, colonist: Colonist):
        """Complete a colonist's current job and apply results"""
        job_rewards = {
            JobType.FARM: {"food": 15, "xp": 2},
            JobType.RESEARCH: {"research_data": 5, "research_points": 1, "xp": 3},
            JobType.BUILD: {"xp": 2},
            JobType.CRAFT: {"tools": 2, "xp": 2},
            JobType.COOK: {"food": 8, "xp": 1},
            JobType.CLEAN: {"colony_mood": 2, "xp": 1},
            JobType.REPAIR: {"xp": 2}
        }
        
        rewards = job_rewards.get(colonist.job, {})
        
        # Apply resource rewards
        for resource, amount in rewards.items():
            if resource == "xp":
                # Increase relevant skill
                skill = self.get_relevant_skill(colonist.job)
                colonist.skill_levels[skill] = min(10, colonist.skill_levels[skill] + 1)
            elif resource == "colony_mood":
                self.state.colony_mood = min(100, self.state.colony_mood + amount)
            else:
                self.state.resources[resource] = self.state.resources.get(resource, 0) + amount
        
        print(f"✅ {colonist.name} completed {colonist.job.value}")
        for resource, amount in rewards.items():
            if resource != "xp":
                print(f"   +{amount} {resource}")
        
        # Increase mood for job completion
        colonist.mood = min(100, colonist.mood + 5)
        
        # Reset job
        colonist.job = JobType.IDLE
        colonist.job_progress = 0.0
        colonist.job_target = None
    
    def update_colony_systems(self, delta_time: float = 1.0):
        """Update colony-wide systems"""
        # Time progression
        self.state.time_of_day += delta_time / 60.0  # delta_time in minutes
        if self.state.time_of_day >= 24.0:
            self.state.time_of_day = 0.0
            self.state.day += 1
            print(f"🌅 Day {self.state.day} begins")
        
        # Power consumption calculation
        self.state.power_consumption = sum(
            b.power_consumption for b in self.state.buildings if b.active
        )
        
        # Resource consumption
        colonist_count = len(self.state.colonists)
        if self.state.time_of_day % 6 < delta_time / 60.0:  # Every 6 hours
            food_consumed = colonist_count * 2
            water_consumed = colonist_count * 3
            
            self.state.resources["food"] = max(0, self.state.resources.get("food", 0) - food_consumed)
            self.state.resources["water"] = max(0, self.state.resources.get("water", 0) - water_consumed)
            
            # Check for shortages
            if self.state.resources["food"] < 10:
                print("⚠️  Food shortage! Colony mood declining.")
                self.state.colony_mood = max(0, self.state.colony_mood - 5)
            
            if self.state.resources["water"] < 10:
                print("⚠️  Water shortage! Colony health at risk.")
                for colonist in self.state.colonists:
                    colonist.health = max(0, colonist.health - 5)
    
    def render_colony_view(self) -> str:
        """Render ASCII view of the colony"""
        # Create empty map
        colony_map = [["." for _ in range(self.map_width)] for _ in range(self.map_height)]
        
        # Place buildings
        for building in self.state.buildings:
            symbol_map = {
                BuildingType.SHELTER: "H",
                BuildingType.WORKSHOP: "W",
                BuildingType.GREENHOUSE: "G",
                BuildingType.STORAGE: "S",
                BuildingType.LABORATORY: "L",
                BuildingType.KITCHEN: "K",
                BuildingType.INFIRMARY: "I",
                BuildingType.POWER_PLANT: "P",
                BuildingType.COMMUNICATIONS: "C"
            }
            
            symbol = symbol_map.get(building.building_type, "B")
            if building.construction_progress < 1.0:
                symbol = "□"  # Under construction
            
            for dx in range(building.width):
                for dy in range(building.height):
                    x, y = building.x + dx, building.y + dy
                    if 0 <= x < self.map_width and 0 <= y < self.map_height:
                        colony_map[y][x] = symbol
        
        # Place colonists
        for colonist in self.state.colonists:
            if 0 <= colonist.x < self.map_width and 0 <= colonist.y < self.map_height:
                colony_map[colonist.y][colonist.x] = "@"
        
        # Convert to string
        return "\n".join("".join(row) for row in colony_map)
    
    def get_colony_status(self) -> str:
        """Get detailed colony status"""
        active_jobs = {}
        for colonist in self.state.colonists:
            job = colonist.job.value
            active_jobs[job] = active_jobs.get(job, 0) + 1
        
        power_status = "⚡ STABLE" if self.state.power_generation >= self.state.power_consumption else "⚠️  SHORTAGE"
        
        return f"""
🏘️  COLONY STATUS - Day {self.state.day}
================================
Time: {int(self.state.time_of_day):02d}:00
Colonists: {len(self.state.colonists)}
Buildings: {len(self.state.buildings)}
Colony Mood: {self.state.colony_mood}/100

🔋 Power: {self.state.power_generation - self.state.power_consumption} ({power_status})
📊 Research Points: {self.state.research_points}

📦 Resources:
{chr(10).join(f"  {resource}: {amount}" for resource, amount in self.state.resources.items())}

👷 Active Jobs:
{chr(10).join(f"  {job}: {count}" for job, count in active_jobs.items()) if active_jobs else "  (all idle)"}

👤 Colonists:
{chr(10).join(f"  {c.name}: {c.job.value} (Energy: {c.energy}/100, Mood: {c.mood}/100)" for c in self.state.colonists)}
        """.strip()
    
    def tick(self):
        """Main colony simulation tick"""
        delta_time = 1.0  # 1 second
        
        # Update all colonists
        for colonist in self.state.colonists:
            self.update_colonist_work(colonist, delta_time)
        
        # Auto-assign jobs to idle colonists
        self.auto_assign_jobs()
        
        # Update colony systems
        self.update_colony_systems(delta_time)
        
        # Save state
        self.save_state()

def main():
    """Interactive colony management"""
    engine = ColonyEngine()
    
    print("🏘️  NuSyQ Colony Engine")
    print("Commands: status, view, assign <colonist_id> <job>, tick, auto, quit")
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit":
                break
            elif command == "status":
                print(engine.get_colony_status())
            elif command == "view":
                print("\n" + engine.render_colony_view())
            elif command == "tick":
                engine.tick()
                print("⏰ Colony simulation advanced")
            elif command == "auto":
                for _ in range(10):  # Run 10 ticks
                    engine.tick()
                print("⏰ Colony simulation advanced 10 ticks")
            elif command.startswith("assign "):
                parts = command.split(" ")
                if len(parts) >= 3:
                    colonist_id = parts[1]
                    job_name = parts[2]
                    try:
                        job_type = JobType(job_name)
                        engine.assign_job(colonist_id, job_type)
                    except ValueError:
                        print(f"Unknown job type: {job_name}")
                        print("Available jobs:", [j.value for j in JobType])
                else:
                    print("Usage: assign <colonist_id> <job_type>")
            else:
                print("Unknown command. Try: status, view, assign <id> <job>, tick, auto, quit")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()