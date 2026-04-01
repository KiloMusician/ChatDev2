"""
🎮 Floor 01: Gameplay Integration
Colony mechanics, idler systems, and core game loops
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class ResourceType(Enum):
    FOOD = "food"
    POWER = "power"  
    OXYGEN = "oxygen"
    MATERIALS = "materials"
    RESEARCH = "research"
    CULTURE = "culture"

@dataclass
class Resource:
    current: float
    max_capacity: float
    production_rate: float
    consumption_rate: float
    
    def tick(self, delta_time: float = 1.0):
        """Update resource over time"""
        net_rate = self.production_rate - self.consumption_rate
        self.current = max(0, min(self.max_capacity, self.current + net_rate * delta_time))

@dataclass
class Colonist:
    id: str
    name: str
    job: str
    mood: float = 0.5  # 0.0 = miserable, 1.0 = ecstatic
    skills: Dict[str, float] = None
    traits: List[str] = None
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = {
                "research": 0.1,
                "construction": 0.1, 
                "agriculture": 0.1,
                "defense": 0.1,
                "culture": 0.1
            }
        if self.traits is None:
            self.traits = []

class ColonyState:
    """Core colony state management"""
    
    def __init__(self):
        self.day = 0
        self.population = 3
        self.colonists: List[Colonist] = []
        self.resources: Dict[ResourceType, Resource] = self._init_resources()
        self.buildings: Dict[str, int] = {"shelter": 1, "farm": 1}
        self.research_progress: Dict[str, float] = {}
        self.events_log: List[str] = []
        
        # Initialize starting colonists
        self._create_starting_colonists()
    
    def _init_resources(self) -> Dict[ResourceType, Resource]:
        """Initialize starting resources"""
        return {
            ResourceType.FOOD: Resource(30.0, 100.0, 5.0, 3.0),
            ResourceType.POWER: Resource(50.0, 100.0, 10.0, 8.0),
            ResourceType.OXYGEN: Resource(80.0, 100.0, 15.0, 3.0),
            ResourceType.MATERIALS: Resource(20.0, 200.0, 2.0, 1.0),
            ResourceType.RESEARCH: Resource(0.0, float('inf'), 1.0, 0.0),
            ResourceType.CULTURE: Resource(10.0, 100.0, 0.5, 0.1)
        }
    
    def _create_starting_colonists(self):
        """Create the initial colonist crew"""
        starting_crew = [
            Colonist("c001", "Alex Chen", "researcher", traits=["curious", "methodical"]),
            Colonist("c002", "Morgan Silva", "engineer", traits=["practical", "innovative"]), 
            Colonist("c003", "Sam Rivers", "farmer", traits=["patient", "nurturing"])
        ]
        
        # Assign specialized skills
        starting_crew[0].skills["research"] = 0.8
        starting_crew[1].skills["construction"] = 0.7
        starting_crew[2].skills["agriculture"] = 0.6
        
        self.colonists = starting_crew
    
    def daily_tick(self):
        """Process one day of colony simulation"""
        self.day += 1
        
        # Update resources
        for resource in self.resources.values():
            resource.tick()
        
        # Colonist work assignments
        self._process_work_assignments()
        
        # Random events
        self._check_random_events()
        
        # Mood updates
        self._update_colonist_moods()
        
        # Research progress
        self._process_research()
        
        return self._get_status_report()
    
    def _process_work_assignments(self):
        """Assign colonists to work and calculate production"""
        for colonist in self.colonists:
            if colonist.job == "researcher":
                research_bonus = colonist.skills["research"] * (1 + colonist.mood * 0.5)
                self.resources[ResourceType.RESEARCH].production_rate += research_bonus
            
            elif colonist.job == "farmer":
                food_bonus = colonist.skills["agriculture"] * (1 + colonist.mood * 0.3)
                self.resources[ResourceType.FOOD].production_rate += food_bonus
            
            elif colonist.job == "engineer":
                power_bonus = colonist.skills["construction"] * (1 + colonist.mood * 0.4)
                self.resources[ResourceType.POWER].production_rate += power_bonus
    
    def _check_random_events(self):
        """Generate random colony events"""
        import random
        
        if random.random() < 0.1:  # 10% chance per day
            events = [
                "A strange signal was detected from the outer rim.",
                "Solar flare increased power generation by 20%.",
                "Ancient ruins discovered during excavation.",
                "Hydroponics yielded an exceptional harvest.",
                "Equipment malfunction in the communications array."
            ]
            
            event = random.choice(events)
            self.events_log.append(f"Day {self.day}: {event}")
            
            # Some events have mechanical effects
            if "solar flare" in event:
                self.resources[ResourceType.POWER].current += 20
            elif "exceptional harvest" in event:
                self.resources[ResourceType.FOOD].current += 15
    
    def _update_colonist_moods(self):
        """Update colonist mood based on colony conditions"""
        base_mood_change = 0.0
        
        # Food affects mood
        food_ratio = self.resources[ResourceType.FOOD].current / self.resources[ResourceType.FOOD].max_capacity
        if food_ratio > 0.7:
            base_mood_change += 0.1
        elif food_ratio < 0.3:
            base_mood_change -= 0.2
        
        # Power affects mood  
        power_ratio = self.resources[ResourceType.POWER].current / self.resources[ResourceType.POWER].max_capacity
        if power_ratio < 0.2:
            base_mood_change -= 0.1
        
        # Apply mood changes
        for colonist in self.colonists:
            colonist.mood = max(0.0, min(1.0, colonist.mood + base_mood_change))
    
    def _process_research(self):
        """Advance research projects"""
        research_points = self.resources[ResourceType.RESEARCH].current
        
        if research_points > 0:
            # Automatically advance the most beneficial research
            if "hydroponic_efficiency" not in self.research_progress:
                self.research_progress["hydroponic_efficiency"] = 0.0
            
            self.research_progress["hydroponic_efficiency"] += research_points * 0.1
            
            if self.research_progress["hydroponic_efficiency"] >= 100.0:
                self.resources[ResourceType.FOOD].production_rate *= 1.5
                self.events_log.append(f"Day {self.day}: Hydroponic efficiency research completed!")
                self.research_progress["hydroponic_efficiency"] = 100.0
    
    def _get_status_report(self) -> Dict:
        """Generate status report for UI"""
        return {
            "day": self.day,
            "population": len(self.colonists),
            "resources": {rt.value: r.current for rt, r in self.resources.items()},
            "average_mood": sum(c.mood for c in self.colonists) / len(self.colonists),
            "recent_events": self.events_log[-3:],  # Last 3 events
            "research": dict(self.research_progress)
        }

# Idler mechanics integration
class IdlerProgression:
    """Idle game progression mechanics"""
    
    def __init__(self):
        self.prestige_level = 0
        self.lifetime_research = 0.0
        self.unlocked_technologies = set()
        self.automation_level = 0
    
    def calculate_prestige_bonus(self) -> float:
        """Calculate bonus from prestige levels"""
        return 1.0 + (self.prestige_level * 0.25)
    
    def check_automation_unlocks(self, colony: ColonyState):
        """Check if new automation is available"""
        if colony.resources[ResourceType.RESEARCH].current > 1000 and self.automation_level == 0:
            self.automation_level = 1
            colony.events_log.append("Basic automation systems online!")
            
            # Automation reduces manual resource management
            for resource in colony.resources.values():
                resource.production_rate *= 1.2

# Integration with ASCII interface
def render_colony_status_ascii(colony: ColonyState) -> str:
    """Render colony status for ASCII interface"""
    status = colony._get_status_report()
    
    lines = [
        f"🏛️  COLONY STATUS - DAY {status['day']}",
        "═" * 40,
        f"👥 Population: {status['population']}",
        f"😊 Avg Mood: {status['average_mood']:.1f}",
        "",
        "📊 RESOURCES:",
    ]
    
    # Resource bars using ASCII
    for resource_name, amount in status['resources'].items():
        if resource_name != 'research':  # Research is infinite
            max_val = 100  # Simplified for display
            filled = int((amount / max_val) * 20)
            bar = "█" * filled + "░" * (20 - filled)
            lines.append(f"{resource_name:10}: {bar} {amount:.1f}")
    
    lines.extend([
        "",
        "🔬 RESEARCH:",
        f"Points: {status['resources']['research']:.1f}",
    ])
    
    for tech, progress in status['research'].items():
        prog_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        lines.append(f"{tech}: {prog_bar} {progress:.0f}%")
    
    if status['recent_events']:
        lines.extend(["", "📰 RECENT EVENTS:"])
        lines.extend(status['recent_events'])
    
    return "\n".join(lines)