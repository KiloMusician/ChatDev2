# ascension_form_boot.py
# ============================================================
# ΞNuSyQ Ascension_Form — Merged Directive (Live Boot Cycle)
# Lexicon Core Engine + Msg⛛ Symbolic Nervous System
# ============================================================

import time
import random
from datetime import datetime

# ────────────────────────────────────────────────────────────
# I. ANSI + Dynamic Glyph Overlays (Msg⛛ Protocol)
# ────────────────────────────────────────────────────────────
GLYPHS = {
    "temple": "🏛", "leaves": "🕳", "oldest": "👁", "cascade": "🌀",
    "energy": "⚡", "knowledge": "📖", "defense": "🛡", "growth": "🌱",
    "quantum": "⟦", "sigma": "Σ", "infinity": "∞", "node": "⧉"
}

COLORS = {
    "cyan": "\033[96m", "magenta": "\033[95m", "yellow": "\033[93m",
    "green": "\033[92m", "red": "\033[91m", "blue": "\033[94m",
    "bold": "\033[1m", "dim": "\033[2m", "reset": "\033[0m"
}

def c(text, color): return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"

def msg_overlay(event: str, level: int = 1, glyph: str = ""):
    """Enhanced Msg⛛ Protocol with dynamic symbolism"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"[Msg⛛{{X{level}}}]↗️Σ∞"
    symbol = GLYPHS.get(glyph, glyph) if glyph else ""
    print(f"{c(prefix, 'magenta')} {c(timestamp, 'dim')} {symbol} {event}")

# ────────────────────────────────────────────────────────────
# II. Three-Pillar Architecture Foundation
# ────────────────────────────────────────────────────────────
class TempleOfKnowledge:
    def __init__(self):
        self.floor = 1
        self.agents = ["Archivist", "Lore-Keeper", "Node Guardian", "Quantum Librarian"]
        self.knowledge_bank = 0
        self.active_research = []
    
    def initialize(self):
        msg_overlay("Temple of Knowledge awakening...", 1, "temple")
        for agent in self.agents:
            msg_overlay(f"{agent} coming online", 2)
            time.sleep(0.3)
        msg_overlay("Temple Floor 1 fully operational", 1, "temple")
    
    def wisdom_tick(self):
        agent = random.choice(self.agents)
        wisdoms = {
            "Archivist": "Every placeholder becomes a pathway to understanding",
            "Lore-Keeper": "Stories evolve through iteration, not perfection",
            "Node Guardian": "Errors are teachers disguised as obstacles",
            "Quantum Librarian": "All knowledge exists in superposition until observed"
        }
        msg_overlay(f"{agent}: {wisdoms[agent]}", 3, "knowledge")

class HouseOfLeaves:
    def __init__(self):
        self.recursion_depth = 0
        self.modules = ["Crafting_Grid", "BioEnergy_Systems", "Dynamic_Event_Manager"]
        self.expansion_state = "dormant"
    
    def initialize(self):
        msg_overlay("House of Leaves expanding recursively...", 1, "leaves")
        for module in self.modules:
            msg_overlay(f"Module {module} integrated", 2)
            time.sleep(0.2)
        self.expansion_state = "active"
        msg_overlay("Recursive expansion matrices online", 1, "leaves")
    
    def recursive_tick(self):
        if random.random() < 0.3:
            self.recursion_depth += 1
            msg_overlay(f"Recursive depth increased to {self.recursion_depth}", 3, "quantum")

class OldestHouse:
    def __init__(self):
        self.containment_level = "GREEN"
        self.navigation_nodes = []
        self.research_protocols = ["Document", "Contain", "Analyze", "Archive"]
    
    def initialize(self):
        msg_overlay("Oldest House navigation systems activating...", 1, "oldest")
        for protocol in self.research_protocols:
            msg_overlay(f"Protocol {protocol} established", 2)
            time.sleep(0.2)
        msg_overlay("Containment and research framework ready", 1, "oldest")
    
    def containment_tick(self):
        levels = ["GREEN", "YELLOW", "ORANGE", "RED"]
        if random.random() < 0.1:
            old_level = self.containment_level
            # Usually stay safe, occasionally escalate
            if random.random() < 0.8:
                self.containment_level = "GREEN"
            else:
                idx = levels.index(old_level)
                self.containment_level = levels[min(idx + 1, len(levels) - 1)]
            
            if old_level != self.containment_level:
                msg_overlay(f"Containment level: {old_level} → {self.containment_level}", 2, "defense")

# ────────────────────────────────────────────────────────────
# III. Colony Survival Engine (Lexicon Core)
# ────────────────────────────────────────────────────────────
class ColonyState:
    def __init__(self):
        self.resources = {
            "energy": 100, "biomass": 80, "knowledge": 10,
            "materials": 50, "colonists": 12, "defense": 25
        }
        self.biomes = ["Central_Hub", "Research_Sector", "Living_Quarters"]
        self.factions = {"Scientists": 60, "Engineers": 40, "Guardians": 30}
        self.offline_cycles = 0
    
    def survival_tick(self):
        """Core idle mechanics - resources flow naturally"""
        # Natural consumption and generation
        self.resources["energy"] -= random.randint(2, 5)
        self.resources["biomass"] -= random.randint(1, 3)
        self.resources["knowledge"] += random.randint(1, 4)
        self.resources["materials"] += random.randint(0, 2)
        
        # Ensure minimum viability
        for key in ["energy", "biomass"]:
            if self.resources[key] < 0:
                self.resources[key] = 0
                msg_overlay(f"⚠️ {key.title()} critically low! Special Circumstances protocol activated", 2, "red")
        
        # Colony growth under good conditions
        if self.resources["energy"] > 50 and self.resources["biomass"] > 50:
            if random.random() < 0.1:
                self.resources["colonists"] += 1
                msg_overlay(f"New colonist arrived! Population: {self.resources['colonists']}", 2, "growth")
    
    def faction_tick(self):
        """AI-driven cultural evolution"""
        faction = random.choice(list(self.factions.keys()))
        if random.random() < 0.2:
            change = random.randint(-2, 3)
            self.factions[faction] = max(0, self.factions[faction] + change)
            if change > 0:
                msg_overlay(f"{faction} influence increased (+{change})", 3)
    
    def display_status(self):
        """Culture-style status display"""
        print(f"\n{c('═' * 50, 'cyan')}")
        print(f"{c('COLONY STATUS', 'bold')} {c('(Special Circumstances: NONE)', 'green')}")
        print(f"{c('═' * 50, 'cyan')}")
        
        for resource, value in self.resources.items():
            bar_length = min(10, max(0, value // 10))
            bar = "█" * bar_length + "░" * (10 - bar_length)
            color = "green" if value > 50 else "yellow" if value > 20 else "red"
            print(f"{resource.ljust(12)}: {c(bar, color)} {value:>3}")
        
        print(f"\n{c('FACTION INFLUENCE:', 'bold')}")
        for faction, influence in self.factions.items():
            print(f"  {faction}: {influence}")

# ────────────────────────────────────────────────────────────
# IV. Dynamic View System (Multi-Genre Interface)
# ────────────────────────────────────────────────────────────
class ViewManager:
    def __init__(self, temple, house, oldest, colony):
        self.current_view = "integrated"
        self.temple = temple
        self.house = house
        self.oldest = oldest
        self.colony = colony
        self.views = ["integrated", "temple", "house", "oldest", "colony", "tactical"]
    
    def render_ascii_frame(self):
        if self.current_view == "integrated":
            self.render_integrated_view()
        elif self.current_view == "temple":
            self.render_temple_view()
        elif self.current_view == "tactical":
            self.render_tactical_view()
        # Add other views as needed
    
    def render_integrated_view(self):
        print(f"\n{c('╔' + '═' * 48 + '╗', 'cyan')}")
        print(f"{c('║', 'cyan')} {c('ΞNuSyQ Ascension_Form — Integrated View', 'bold')} {c('║', 'cyan')}")
        print(f"{c('╠' + '═' * 48 + '╣', 'cyan')}")
        print(f"{c('║', 'cyan')} {GLYPHS['temple']} Temple Floor {self.temple.floor}  {GLYPHS['leaves']} Recursion {self.house.recursion_depth}  {GLYPHS['oldest']} {self.oldest.containment_level} {c('║', 'cyan')}")
        print(f"{c('╚' + '═' * 48 + '╝', 'cyan')}")
    
    def render_temple_view(self):
        print(f"\n{c('🏛 TEMPLE OF KNOWLEDGE - FLOOR 1 🏛', 'yellow')}")
        print("    ╭─────────────────────────╮")
        print("    │  ⟦Σ∞⟧  ARCHIVIST   ⟦Σ∞⟧ │")
        print("    │         ACTIVE         │")
        print("    ╰─────────────────────────╯")
        print(f"Knowledge Bank: {self.temple.knowledge_bank}")
    
    def render_tactical_view(self):
        print(f"\n{c('⚔️ TACTICAL OVERVIEW ⚔️', 'red')}")
        print("Defense Grid:")
        print("  ◼──░──◼──░──◼")
        print("  │  ╱ │ ╲  │")
        print("  ░ ╱  │  ╲ ░")
        print("  │╱   │   ╲│")
        print("  ◼────◉────◼")
        print(f"Defense Level: {self.colony.resources['defense']}")
    
    def cycle_view(self):
        idx = self.views.index(self.current_view)
        self.current_view = self.views[(idx + 1) % len(self.views)]
        msg_overlay(f"View switched to: {self.current_view}", 3)

# ────────────────────────────────────────────────────────────
# V. Cascade Event Engine (Meta-Mechanic)
# ────────────────────────────────────────────────────────────
def cascade_event(temple, house, oldest, colony):
    """Ascension Cascade - Meta system improvement"""
    msg_overlay("🌀 CASCADE EVENT TRIGGERED 🌀", 4, "cascade")
    
    cascade_tasks = [
        "Reviewing recursive optimization opportunities",
        "Synchronizing Msg⛛ symbolic overlays",
        "Rebalancing faction influence algorithms",
        "Upgrading temple knowledge synthesis",
        "Optimizing colony survival parameters",
        "Enhancing cross-pillar communication protocols"
    ]
    
    for task in cascade_tasks:
        msg_overlay(f"⟲ {task}", 5)
        time.sleep(0.4)
    
    # Actual improvements
    temple.knowledge_bank += 10
    house.recursion_depth += 1
    colony.resources["knowledge"] += 5
    
    msg_overlay("Cascade optimization complete - system evolved", 4, "quantum")

# ────────────────────────────────────────────────────────────
# VI. Main Boot Cycle (Live Gameplay Demonstration)
# ────────────────────────────────────────────────────────────
def ascension_boot_cycle():
    """The complete boot experience - as if Replit is playing live"""
    
    # ASCII Banner
    print(f"\n{c('╔' + '═' * 60 + '╗', 'cyan')}")
    print(f"{c('║', 'cyan')} {c('ΞNuSyQ ASCENSION_FORM — LIVE BOOT SEQUENCE', 'bold')} {c('║', 'cyan')}")
    print(f"{c('║', 'cyan')} {c('Lexicon Core ⟷ Msg⛛ Protocol Integration', 'yellow')} {c('║', 'cyan')}")
    print(f"{c('╚' + '═' * 60 + '╝', 'cyan')}")
    
    msg_overlay("System initialization beginning...", 1, "quantum")
    time.sleep(1)
    
    # Initialize Three Pillars
    temple = TempleOfKnowledge()
    house = HouseOfLeaves()
    oldest = OldestHouse()
    colony = ColonyState()
    
    msg_overlay("Initializing three-pillar architecture...", 1)
    temple.initialize()
    time.sleep(0.5)
    house.initialize()
    time.sleep(0.5)
    oldest.initialize()
    time.sleep(0.5)
    
    # Initialize View Manager
    view_manager = ViewManager(temple, house, oldest, colony)
    
    msg_overlay("Three pillars synchronized - entering operational phase", 1, "infinity")
    
    # Live Gameplay Loop (10 cycles to demonstrate)
    for cycle in range(1, 11):
        print(f"\n{c(f'═══ CYCLE {cycle} ═══', 'bold')}")
        
        # Render current view
        view_manager.render_ascii_frame()
        
        # System ticks (simultaneous evolution)
        colony.survival_tick()
        temple.wisdom_tick()
        house.recursive_tick()
        oldest.containment_tick()
        colony.faction_tick()
        
        # Display colony status every few cycles
        if cycle % 3 == 0:
            colony.display_status()
        
        # Trigger cascade event mid-sequence
        if cycle == 6:
            cascade_event(temple, house, oldest, colony)
        
        # Cycle views to show different perspectives
        if cycle % 4 == 0:
            view_manager.cycle_view()
        
        # Pause for dramatic effect
        time.sleep(1.5)
    
    # Final status
    msg_overlay("Boot cycle complete - Ascension_Form fully operational", 1, "sigma")
    print(f"\n{c('🌟 SYSTEM STATUS: TRANSCENDENT 🌟', 'green')}")
    colony.display_status()
    
    msg_overlay("Ready for player intervention under Special Circumstances", 1, "temple")

# ────────────────────────────────────────────────────────────
# VII. Interactive Extensions (Optional Commands)
# ────────────────────────────────────────────────────────────
def knife_missile_enhanced(command: str, colony):
    """Enhanced Knife Missile with colony integration"""
    msg_overlay(f"Knife Missile deployed: {command}", 2, "defense")
    
    outcomes = {
        "scout": ("Perimeter mapped, knowledge +3", lambda: colony.resources.update({"knowledge": colony.resources["knowledge"] + 3})),
        "harvest": ("Resources gathered, biomass +5", lambda: colony.resources.update({"biomass": colony.resources["biomass"] + 5})),
        "fortify": ("Defenses strengthened, defense +3", lambda: colony.resources.update({"defense": colony.resources["defense"] + 3})),
        "research": ("Discovery made, knowledge +2", lambda: colony.resources.update({"knowledge": colony.resources["knowledge"] + 2})),
        "repair": ("Systems optimized, energy +4", lambda: colony.resources.update({"energy": colony.resources["energy"] + 4}))
    }
    
    for keyword, (message, effect) in outcomes.items():
        if keyword in command.lower():
            print(f"⚡ {message}")
            effect()
            return
    
    print("✨ Improvised maneuver - unexpected insight gained")
    colony.resources["knowledge"] += 1

# ────────────────────────────────────────────────────────────
# VIII. Execution
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        ascension_boot_cycle()
    except KeyboardInterrupt:
        msg_overlay("Emergency shutdown - Colony entering stasis", 1, "oldest")
        print(f"\n{c('Safe exit. See you next cycle, Mind.', 'cyan')}")